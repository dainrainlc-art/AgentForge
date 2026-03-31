"""
Test Rate Limiter
"""
import pytest
import asyncio

from agentforge.security import RateLimiter, IPRateLimiter, UserRateLimiter


class TestRateLimiter:
    """Test rate limiter"""
    
    @pytest.fixture
    def limiter(self):
        return RateLimiter(
            requests_per_minute=10,
            requests_per_hour=100,
            burst_size=5
        )
    
    @pytest.mark.asyncio
    async def test_allow_request(self, limiter):
        """Test request is allowed"""
        result = await limiter.is_allowed("test_key")
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_burst_limit(self, limiter):
        """Test burst limit"""
        for _ in range(5):
            await limiter.is_allowed("test_key")
        
        result = await limiter.is_allowed("test_key")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_different_keys(self, limiter):
        """Test different keys have separate limits"""
        for _ in range(5):
            await limiter.is_allowed("key1")
        
        result = await limiter.is_allowed("key2")
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_get_remaining(self, limiter):
        """Test get remaining requests"""
        await limiter.is_allowed("test_key")
        
        remaining = await limiter.get_remaining("test_key")
        
        assert remaining["burst_remaining"] < 5
    
    def test_reset(self, limiter):
        """Test reset rate limiter"""
        limiter.reset("test_key")
        
        assert "test_key" not in limiter._burst_tokens


class TestIPRateLimiter:
    """Test IP rate limiter"""
    
    @pytest.fixture
    def limiter(self):
        return IPRateLimiter(requests_per_minute=10, burst_size=5)
    
    @pytest.mark.asyncio
    async def test_check_ip(self, limiter):
        """Test IP check"""
        result = await limiter.check_ip("192.168.1.1")
        
        assert result is True


class TestUserRateLimiter:
    """Test user rate limiter"""
    
    @pytest.fixture
    def limiter(self):
        return UserRateLimiter(requests_per_minute=10, burst_size=5)
    
    @pytest.mark.asyncio
    async def test_check_user(self, limiter):
        """Test user check"""
        result = await limiter.check_user("user123")
        
        assert result is True
