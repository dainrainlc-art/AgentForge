"""
Cache Manager - Redis and Local Cache Optimization
"""
import json
import hashlib
from typing import Any, Optional, Union
from functools import wraps
import asyncio
from datetime import timedelta

import redis.asyncio as redis
from loguru import logger

from agentforge.config import settings


class CacheManager:
    """Multi-level cache manager with Redis and local LRU cache"""
    
    def __init__(self):
        self._redis: Optional[redis.Redis] = None
        self._local_cache: dict = {}
        self._local_ttl: dict = {}
        self._default_ttl = 300  # 5 minutes
        self._max_local_size = 1000
        
    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self._redis = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                password=settings.redis_password or None,
                db=0,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
                health_check_interval=30
            )
            await self._redis.ping()
            logger.info("Redis cache initialized")
        except Exception as e:
            logger.warning(f"Redis not available, using local cache only: {e}")
            self._redis = None
    
    async def close(self):
        """Close Redis connection"""
        if self._redis:
            await self._redis.close()
            logger.info("Redis cache closed")
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
        hash_key = hashlib.md5(key_data.encode(), usedforsecurity=False).hexdigest()
        return f"{prefix}:{hash_key}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache (local first, then Redis)"""
        # Check local cache first
        if key in self._local_cache:
            import time
            if time.time() < self._local_ttl.get(key, 0):
                return self._local_cache[key]
            else:
                # Expired, remove from local
                del self._local_cache[key]
                del self._local_ttl[key]
        
        # Check Redis
        if self._redis:
            try:
                value = await self._redis.get(key)
                if value:
                    data = json.loads(value)
                    # Store in local cache for faster access
                    self._set_local(key, data)
                    return data
            except Exception as e:
                logger.error(f"Redis get error: {e}")
        
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        local_only: bool = False
    ):
        """Set value in cache"""
        ttl = ttl or self._default_ttl
        
        # Set in local cache
        self._set_local(key, value, ttl)
        
        # Set in Redis
        if not local_only and self._redis:
            try:
                serialized = json.dumps(value, default=str)
                await self._redis.setex(key, ttl, serialized)
            except Exception as e:
                logger.error(f"Redis set error: {e}")
    
    def _set_local(self, key: str, value: Any, ttl: int = 300):
        """Set value in local cache with LRU eviction"""
        import time
        
        # Evict oldest if at capacity
        if len(self._local_cache) >= self._max_local_size:
            oldest_key = min(self._local_ttl, key=self._local_ttl.get)
            del self._local_cache[oldest_key]
            del self._local_ttl[oldest_key]
        
        self._local_cache[key] = value
        self._local_ttl[key] = time.time() + ttl
    
    async def delete(self, key: str):
        """Delete value from cache"""
        # Delete from local
        self._local_cache.pop(key, None)
        self._local_ttl.pop(key, None)
        
        # Delete from Redis
        if self._redis:
            try:
                await self._redis.delete(key)
            except Exception as e:
                logger.error(f"Redis delete error: {e}")
    
    async def delete_pattern(self, pattern: str):
        """Delete keys matching pattern"""
        # Clear local cache if pattern matches all
        if pattern == "*":
            self._local_cache.clear()
            self._local_ttl.clear()
        
        if self._redis:
            try:
                keys = await self._redis.keys(pattern)
                if keys:
                    await self._redis.delete(*keys)
            except Exception as e:
                logger.error(f"Redis delete pattern error: {e}")
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if key in self._local_cache:
            import time
            if time.time() < self._local_ttl.get(key, 0):
                return True
        
        if self._redis:
            try:
                return await self._redis.exists(key) > 0
            except Exception as e:
                logger.error(f"Redis exists error: {e}")
        
        return False
    
    async def get_stats(self) -> dict:
        """Get cache statistics"""
        stats = {
            "local_size": len(self._local_cache),
            "local_max": self._max_local_size,
            "redis_connected": self._redis is not None
        }
        
        if self._redis:
            try:
                info = await self._redis.info()
                stats["redis_used_memory"] = info.get("used_memory_human", "N/A")
                stats["redis_connected_clients"] = info.get("connected_clients", 0)
                stats["redis_hits"] = info.get("keyspace_hits", 0)
                stats["redis_misses"] = info.get("keyspace_misses", 0)
            except Exception as e:
                logger.error(f"Redis stats error: {e}")
        
        return stats


# Global cache manager instance
cache_manager = CacheManager()


def cached(prefix: str, ttl: int = 300, key_func=None):
    """Decorator for caching function results"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = cache_manager._generate_key(
                    prefix,
                    func.__name__,
                    *args,
                    **kwargs
                )
            
            # Try to get from cache
            cached_value = await cache_manager.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_value
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            await cache_manager.set(cache_key, result, ttl)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, use asyncio.run
            return asyncio.run(async_wrapper(*args, **kwargs))
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


async def invalidate_cache(pattern: str):
    """Invalidate cache by pattern"""
    await cache_manager.delete_pattern(pattern)
    logger.info(f"Cache invalidated: {pattern}")


async def get_cache_stats() -> dict:
    """Get cache statistics"""
    return await cache_manager.get_stats()
