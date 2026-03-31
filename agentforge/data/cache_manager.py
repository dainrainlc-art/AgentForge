"""
Cache Manager - Multi-level caching with Redis
"""
from typing import Optional, Any, Dict, List, Callable
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel, Field
import json
import redis.asyncio as redis
from loguru import logger
import hashlib

from agentforge.config import settings


class CacheLevel(str, Enum):
    """Cache level enumeration"""
    LOCAL = "local"
    REDIS = "redis"
    BOTH = "both"


class CacheEntry(BaseModel):
    """Cache entry model"""
    key: str
    value: Any
    ttl: int = 3600  # Time to live in seconds
    level: CacheLevel = CacheLevel.LOCAL
    created_at: datetime = Field(default_factory=datetime.now)
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        if self.ttl <= 0:
            return False
        return datetime.now() > self.created_at + timedelta(seconds=self.ttl)


class CacheStats(BaseModel):
    """Cache statistics model"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    size: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total


class CacheManager:
    """Multi-level cache manager with Redis backend"""
    
    _instance: Optional['CacheManager'] = None
    
    DEFAULT_TTL = 3600  # 1 hour
    SHORT_TTL = 300     # 5 minutes
    LONG_TTL = 86400    # 24 hours
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._redis = None
            cls._instance._local_cache: Dict[str, Any] = {}
            cls._instance._local_cache_max_size = 1000
            cls._instance._stats = CacheStats()
        return cls._instance
    
    async def initialize(self):
        """Initialize Redis connection"""
        if self._redis is not None:
            return
        
        try:
            self._redis = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                password=settings.redis_password,
                decode_responses=True,
                socket_timeout=5.0,
                socket_connect_timeout=5.0
            )
            await self._redis.ping()
            logger.info("Redis cache initialized")
        except Exception as e:
            logger.warning(f"Redis connection failed, using local cache only: {e}")
            self._redis = None
    
    async def close(self):
        """Close Redis connection"""
        if self._redis is not None:
            await self._redis.close()
            self._redis = None
            logger.info("Redis connection closed")
    
    def _generate_key(self, key: str, namespace: str = "default") -> str:
        """Generate namespaced cache key"""
        return f"agentforge:{namespace}:{key}"
    
    def _hash_key(self, data: Any) -> str:
        """Generate hash key from data"""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.md5(data_str.encode(), usedforsecurity=False).hexdigest()
    
    async def get(self, key: str, namespace: str = "default") -> Optional[Any]:
        """Get value from cache"""
        full_key = self._generate_key(key, namespace)
        
        if full_key in self._local_cache:
            logger.debug(f"Cache hit (local): {key}")
            self._stats.hits += 1
            return self._local_cache[full_key]
        
        if self._redis is not None:
            try:
                value = await self._redis.get(full_key)
                if value is not None:
                    logger.debug(f"Cache hit (redis): {key}")
                    result = json.loads(value)
                    self._local_cache[full_key] = result
                    self._stats.hits += 1
                    return result
            except Exception as e:
                logger.warning(f"Redis get error: {e}")
        
        logger.debug(f"Cache miss: {key}")
        self._stats.misses += 1
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = None,
        namespace: str = "default"
    ) -> bool:
        """Set value in cache"""
        full_key = self._generate_key(key, namespace)
        ttl = ttl or self.DEFAULT_TTL
        
        if len(self._local_cache) >= self._local_cache_max_size:
            self._local_cache.clear()
        self._local_cache[full_key] = value
        
        if self._redis is not None:
            try:
                await self._redis.setex(
                    full_key,
                    ttl,
                    json.dumps(value)
                )
                logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
                return True
            except Exception as e:
                logger.warning(f"Redis set error: {e}")
        
        return False
    
    async def delete(self, key: str, namespace: str = "default") -> bool:
        """Delete value from cache"""
        full_key = self._generate_key(key, namespace)
        
        if full_key in self._local_cache:
            del self._local_cache[full_key]
        
        if self._redis is not None:
            try:
                await self._redis.delete(full_key)
                logger.debug(f"Cache deleted: {key}")
                return True
            except Exception as e:
                logger.warning(f"Redis delete error: {e}")
        
        return False
    
    async def delete_pattern(self, pattern: str, namespace: str = "default") -> int:
        """Delete all keys matching pattern"""
        full_pattern = self._generate_key(pattern, namespace)
        count = 0
        
        keys_to_delete = [k for k in self._local_cache if k.startswith(full_pattern.replace("*", ""))]
        for k in keys_to_delete:
            del self._local_cache[k]
            count += 1
        
        if self._redis is not None:
            try:
                keys = await self._redis.keys(full_pattern)
                if keys:
                    await self._redis.delete(*keys)
                    count += len(keys)
                logger.debug(f"Cache pattern deleted: {pattern} ({count} keys)")
            except Exception as e:
                logger.warning(f"Redis delete pattern error: {e}")
        
        return count
    
    async def get_or_set(
        self,
        key: str,
        factory: Callable,
        ttl: int = None,
        namespace: str = "default"
    ) -> Any:
        """Get from cache or compute and set"""
        value = await self.get(key, namespace)
        
        if value is not None:
            return value
        
        value = await factory() if callable(factory) else factory
        await self.set(key, value, ttl, namespace)
        
        return value
    
    async def increment(self, key: str, namespace: str = "default") -> int:
        """Increment counter"""
        full_key = self._generate_key(key, namespace)
        
        if self._redis is not None:
            try:
                return await self._redis.incr(full_key)
            except Exception as e:
                logger.warning(f"Redis increment error: {e}")
        
        current = self._local_cache.get(full_key, 0)
        self._local_cache[full_key] = current + 1
        return current + 1
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        stats = {
            "local_cache_size": len(self._local_cache),
            "redis_connected": self._redis is not None,
            "hits": self._stats.hits,
            "misses": self._stats.misses,
            "evictions": self._stats.evictions,
            "hit_rate": self._stats.hit_rate
        }
        
        if self._redis is not None:
            try:
                info = await self._redis.info("memory")
                stats["redis_used_memory"] = info.get("used_memory_human", "unknown")
                stats["redis_keys"] = await self._redis.dbsize()
            except Exception:
                pass
        
        return stats


cache_manager = CacheManager()


def cached(ttl: int = 3600, namespace: str = "default"):
    """Decorator for caching function results"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            cache_key = cache_manager._hash_key({
                "func": func.__name__,
                "args": args,
                "kwargs": kwargs
            })
            
            result = await cache_manager.get(cache_key, namespace)
            if result is not None:
                return result
            
            result = await func(*args, **kwargs)
            await cache_manager.set(cache_key, result, ttl, namespace)
            
            return result
        
        return wrapper
    return decorator
