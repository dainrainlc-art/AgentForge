"""
Rate Limiter - Request rate limiting
"""
import time
from typing import Dict, Optional, Callable
from collections import defaultdict
from loguru import logger
import asyncio


class RateLimiter:
    """Token bucket rate limiter"""
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        burst_size: int = 10
    ):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst_size = burst_size
        
        self._minute_buckets: Dict[str, list] = defaultdict(list)
        self._hour_buckets: Dict[str, list] = defaultdict(list)
        self._burst_tokens: Dict[str, int] = defaultdict(lambda: burst_size)
        self._last_refill: Dict[str, float] = defaultdict(time.time)
        
        self._lock = asyncio.Lock()
    
    def _clean_old_requests(self, bucket: list, window_seconds: int) -> list:
        """Remove requests older than the window"""
        current_time = time.time()
        cutoff = current_time - window_seconds
        return [t for t in bucket if t > cutoff]
    
    async def is_allowed(self, key: str) -> bool:
        """Check if request is allowed for the given key"""
        async with self._lock:
            current_time = time.time()
            
            self._minute_buckets[key] = self._clean_old_requests(
                self._minute_buckets[key], 60
            )
            self._hour_buckets[key] = self._clean_old_requests(
                self._hour_buckets[key], 3600
            )
            
            if self._burst_tokens[key] < self.burst_size:
                time_passed = current_time - self._last_refill[key]
                tokens_to_add = int(time_passed * (self.requests_per_minute / 60))
                if tokens_to_add > 0:
                    self._burst_tokens[key] = min(
                        self.burst_size,
                        self._burst_tokens[key] + tokens_to_add
                    )
                    self._last_refill[key] = current_time
            
            minute_count = len(self._minute_buckets[key])
            hour_count = len(self._hour_buckets[key])
            
            if minute_count >= self.requests_per_minute:
                logger.warning(f"Rate limit exceeded (minute) for {key}")
                return False
            
            if hour_count >= self.requests_per_hour:
                logger.warning(f"Rate limit exceeded (hour) for {key}")
                return False
            
            if self._burst_tokens[key] > 0:
                self._burst_tokens[key] -= 1
            else:
                if minute_count >= self.burst_size:
                    logger.warning(f"Burst rate limit exceeded for {key}")
                    return False
            
            self._minute_buckets[key].append(current_time)
            self._hour_buckets[key].append(current_time)
            
            return True
    
    async def get_remaining(self, key: str) -> Dict[str, int]:
        """Get remaining requests for the key"""
        async with self._lock:
            current_time = time.time()
            
            self._minute_buckets[key] = self._clean_old_requests(
                self._minute_buckets[key], 60
            )
            self._hour_buckets[key] = self._clean_old_requests(
                self._hour_buckets[key], 3600
            )
            
            return {
                "minute_remaining": self.requests_per_minute - len(self._minute_buckets[key]),
                "hour_remaining": self.requests_per_hour - len(self._hour_buckets[key]),
                "burst_remaining": self._burst_tokens[key]
            }
    
    def reset(self, key: str) -> None:
        """Reset rate limit for a key"""
        self._minute_buckets.pop(key, None)
        self._hour_buckets.pop(key, None)
        self._burst_tokens.pop(key, None)
        self._last_refill.pop(key, None)
        logger.info(f"Rate limit reset for {key}")


class IPRateLimiter(RateLimiter):
    """Rate limiter keyed by IP address"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    async def check_ip(self, ip: str) -> bool:
        """Check if IP is allowed"""
        return await self.is_allowed(f"ip:{ip}")


class UserRateLimiter(RateLimiter):
    """Rate limiter keyed by user ID"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    async def check_user(self, user_id: str) -> bool:
        """Check if user is allowed"""
        return await self.is_allowed(f"user:{user_id}")


class EndpointRateLimiter:
    """Rate limiter for specific endpoints"""
    
    DEFAULT_LIMITS = {
        "/api/auth/login": {"requests_per_minute": 5, "burst_size": 3},
        "/api/auth/register": {"requests_per_minute": 3, "burst_size": 2},
        "/api/chat": {"requests_per_minute": 30, "burst_size": 5},
        "default": {"requests_per_minute": 60, "burst_size": 10}
    }
    
    def __init__(self):
        self._limiters: Dict[str, RateLimiter] = {}
        
        for endpoint, config in self.DEFAULT_LIMITS.items():
            self._limiters[endpoint] = RateLimiter(**config)
    
    def get_limiter(self, endpoint: str) -> RateLimiter:
        """Get rate limiter for endpoint"""
        if endpoint in self._limiters:
            return self._limiters[endpoint]
        return self._limiters["default"]
    
    async def check(self, endpoint: str, key: str) -> bool:
        """Check if request is allowed"""
        limiter = self.get_limiter(endpoint)
        return await limiter.is_allowed(f"{endpoint}:{key}")


ip_rate_limiter = IPRateLimiter(
    requests_per_minute=100,
    requests_per_hour=2000,
    burst_size=20
)

user_rate_limiter = UserRateLimiter(
    requests_per_minute=60,
    requests_per_hour=1000,
    burst_size=10
)

endpoint_rate_limiter = EndpointRateLimiter()
