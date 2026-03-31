"""
AgentForge Cache Optimization Module
缓存策略优化模块
"""
from typing import Optional, Any, Dict, List, Callable, Awaitable
from functools import wraps
import hashlib
import json
import asyncio
from datetime import datetime, timedelta
from loguru import logger

from agentforge.memory import MemoryStore


class CacheLevel:
    """缓存级别枚举"""
    L1 = "l1"  # 内存缓存（最快）
    L2 = "l2"  # Redis 缓存（快）
    L3 = "l3"  # 数据库（持久化）


class CacheConfig:
    """缓存配置"""
    
    def __init__(
        self,
        ttl: int = 300,  # 默认 5 分钟
        level: CacheLevel = CacheLevel.L2,
        prefix: str = "cache",
        enabled: bool = True
    ):
        self.ttl = ttl
        self.level = level
        self.prefix = prefix
        self.enabled = enabled


class CacheStats:
    """缓存统计"""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.errors = 0
        self.size = 0
    
    @property
    def hit_rate(self) -> float:
        """缓存命中率"""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total * 100
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "errors": self.errors,
            "size": self.size,
            "hit_rate": f"{self.hit_rate:.2f}%"
        }


class MultiLevelCache:
    """多级缓存系统"""
    
    def __init__(self, redis_client=None, memory_store=None):
        """
        初始化多级缓存
        
        Args:
            redis_client: Redis 客户端
            memory_store: 内存存储
        """
        self._l1_cache: Dict[str, Any] = {}  # L1: 内存缓存
        self._l1_expiry: Dict[str, datetime] = {}
        self._redis = redis_client
        self._memory_store = memory_store
        
        self._stats: Dict[str, CacheStats] = {}
        self._config: Dict[str, CacheConfig] = {}
        
        # L1 缓存限制
        self._l1_max_size = 1000
        self._l1_ttl = 300  # 5 分钟
    
    def _get_stats(self, key_prefix: str) -> CacheStats:
        """获取统计信息"""
        if key_prefix not in self._stats:
            self._stats[key_prefix] = CacheStats()
        return self._stats[key_prefix]
    
    def _generate_key(self, func_name: str, *args, **kwargs) -> str:
        """生成缓存键"""
        # 序列化参数
        key_data = {
            "func": func_name,
            "args": args,
            "kwargs": kwargs
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_str.encode(), usedforsecurity=False).hexdigest()
        return f"{func_name}:{key_hash}"
    
    async def get(
        self,
        key: str,
        default: Any = None,
        level: Optional[CacheLevel] = None
    ) -> Any:
        """
        获取缓存
        
        Args:
            key: 缓存键
            default: 默认值
            level: 缓存级别
            
        Returns:
            缓存值
        """
        # L1: 内存缓存
        if level in [None, CacheLevel.L1]:
            value = self._get_l1(key)
            if value is not None:
                logger.debug(f"L1 cache hit: {key}")
                return value
        
        # L2: Redis 缓存
        if level in [None, CacheLevel.L2] and self._redis:
            try:
                value = await self._redis.get(key)
                if value:
                    logger.debug(f"L2 cache hit: {key}")
                    # 回填 L1
                    self._set_l1(key, value)
                    return json.loads(value)
            except Exception as e:
                logger.error(f"L2 cache get error: {e}")
        
        # L3: 数据库（需要自定义实现）
        if level == CacheLevel.L3 and self._memory_store:
            # 从数据库获取
            pass
        
        logger.debug(f"Cache miss: {key}")
        return default
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        level: Optional[CacheLevel] = None
    ):
        """
        设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）
            level: 缓存级别
        """
        ttl = ttl or self._l1_ttl
        
        # L1: 内存缓存
        if level in [None, CacheLevel.L1]:
            self._set_l1(key, value, ttl)
        
        # L2: Redis 缓存
        if level in [None, CacheLevel.L2] and self._redis:
            try:
                await self._redis.setex(key, ttl, json.dumps(value, default=str))
            except Exception as e:
                logger.error(f"L2 cache set error: {e}")
    
    def _set_l1(self, key: str, value: Any, ttl: Optional[int] = None):
        """设置 L1 缓存"""
        ttl = ttl or self._l1_ttl
        
        # 检查 L1 缓存大小
        if len(self._l1_cache) >= self._l1_max_size:
            self._evict_l1()
        
        self._l1_cache[key] = value
        self._l1_expiry[key] = datetime.now() + timedelta(seconds=ttl)
    
    def _get_l1(self, key: str) -> Any:
        """获取 L1 缓存"""
        if key in self._l1_cache:
            # 检查是否过期
            if datetime.now() < self._l1_expiry.get(key, datetime.now()):
                return self._l1_cache[key]
            else:
                # 过期删除
                self._del_l1(key)
        return None
    
    def _del_l1(self, key: str):
        """删除 L1 缓存"""
        self._l1_cache.pop(key, None)
        self._l1_expiry.pop(key, None)
    
    def _evict_l1(self):
        """清理 L1 缓存（LRU 策略）"""
        # 简单实现：删除一半缓存
        keys = list(self._l1_cache.keys())[:self._l1_max_size // 2]
        for key in keys:
            self._del_l1(key)
    
    async def delete(self, key: str):
        """删除缓存"""
        self._del_l1(key)
        
        if self._redis:
            try:
                await self._redis.delete(key)
            except Exception as e:
                logger.error(f"Cache delete error: {e}")
    
    async def clear(self, prefix: Optional[str] = None):
        """清空缓存"""
        if prefix:
            # 清空指定前缀的缓存
            keys_to_delete = [k for k in self._l1_cache.keys() if k.startswith(prefix)]
            for key in keys_to_delete:
                self._del_l1(key)
            
            if self._redis:
                try:
                    keys = await self._redis.keys(f"{prefix}*")
                    if keys:
                        await self._redis.delete(*keys)
                except Exception as e:
                    logger.error(f"Cache clear error: {e}")
        else:
            # 清空所有缓存
            self._l1_cache.clear()
            self._l1_expiry.clear()
            
            if self._redis:
                try:
                    await self._redis.flushdb()
                except Exception as e:
                    logger.error(f"Cache flush error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        return {
            prefix: stats.to_dict()
            for prefix, stats in self._stats.items()
        }


# 全局缓存实例
_global_cache: Optional[MultiLevelCache] = None


def get_cache() -> MultiLevelCache:
    """获取全局缓存实例"""
    global _global_cache
    if _global_cache is None:
        _global_cache = MultiLevelCache()
    return _global_cache


def cache(
    ttl: int = 300,
    level: CacheLevel = CacheLevel.L2,
    key_prefix: str = "cache",
    enabled: bool = True
):
    """
    缓存装饰器
    
    Args:
        ttl: 缓存时间（秒）
        level: 缓存级别
        key_prefix: 键前缀
        enabled: 是否启用
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable[..., Awaitable[Any]]):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not enabled:
                return await func(*args, **kwargs)
            
            cache_instance = get_cache()
            
            # 生成缓存键
            cache_key = f"{key_prefix}:{func.__name__}:{hashlib.md5(json.dumps((args, kwargs), sort_keys=True, default=str).encode(), usedforsecurity=False).hexdigest()}"
            
            # 尝试从缓存获取
            cached_value = await cache_instance.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_value
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 写入缓存
            await cache_instance.set(cache_key, result, ttl=ttl, level=level)
            logger.debug(f"Cache set: {cache_key}")
            
            return result
        
        return wrapper
    return decorator


async def warm_up_cache(
    cache_func: Callable[..., Awaitable[Any]],
    *args,
    **kwargs
):
    """
    预热缓存
    
    Args:
        cache_func: 缓存函数
        args: 参数
        kwargs: 关键字参数
    """
    try:
        await cache_func(*args, **kwargs)
        logger.info(f"Cache warmed up: {cache_func.__name__}")
    except Exception as e:
        logger.error(f"Cache warm up error: {e}")


async def invalidate_cache(
    pattern: str,
    cache_instance: Optional[MultiLevelCache] = None
):
    """
    使缓存失效
    
    Args:
        pattern: 缓存键模式
        cache_instance: 缓存实例
    """
    cache_instance = cache_instance or get_cache()
    await cache_instance.clear(pattern)
    logger.info(f"Cache invalidated: {pattern}")


class CacheManager:
    """缓存管理器"""
    
    def __init__(self, cache_instance: Optional[MultiLevelCache] = None):
        self._cache = cache_instance or get_cache()
        self._patterns: Dict[str, List[str]] = {}
    
    def register_pattern(self, name: str, pattern: str):
        """注册缓存模式"""
        self._patterns[name] = pattern
        logger.info(f"Cache pattern registered: {name}")
    
    async def invalidate_by_pattern(self, name: str):
        """按模式使缓存失效"""
        if name in self._patterns:
            await self._cache.clear(self._patterns[name])
            logger.info(f"Cache invalidated by pattern: {name}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self._cache.get_stats()
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            test_key = "health_check:test"
            await self._cache.set(test_key, "test", ttl=1)
            result = await self._cache.get(test_key)
            return result == "test"
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return False
