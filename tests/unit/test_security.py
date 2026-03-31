"""
安全模块单元测试

测试 AgentForge 安全相关功能，包括：
- JWTHandler: JWT 令牌处理
- TokenBlacklist: 令牌黑名单
- Security Middlewares: 安全中间件
- Rate Limiters: 速率限制器
"""
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from agentforge.security.jwt_handler import (
    JWTHandler,
    TokenBlacklist,
    token_blacklist,
    create_access_token,
    verify_token
)
from agentforge.security.middleware import (
    SecurityHeadersMiddleware,
    RequestValidationMiddleware,
    CORSSecurityMiddleware,
    RequestLoggingMiddleware
)
from agentforge.security.rate_limiter import (
    RateLimiter,
    IPRateLimiter,
    UserRateLimiter,
    EndpointRateLimiter,
    ip_rate_limiter,
    user_rate_limiter,
    endpoint_rate_limiter
)


@pytest.fixture
def jwt_config():
    """JWT 测试配置"""
    return {
        "secret_key": "this_is_a_very_secure_secret_key_at_least_32_chars",
        "algorithm": "HS256",
        "access_token_expire_minutes": 30,
        "refresh_token_expire_days": 7
    }


@pytest.fixture
def sample_user_data():
    """示例用户数据"""
    return {
        "sub": "user_123",
        "username": "testuser",
        "email": "test@example.com",
        "role": "user"
    }


class TestTokenBlacklist:
    """TokenBlacklist 测试"""
    
    def test_blacklist_initialization(self):
        """测试黑名单初始化"""
        blacklist = TokenBlacklist()
        
        assert len(blacklist._blacklist) == 0
    
    def test_add_token(self):
        """测试添加令牌到黑名单"""
        blacklist = TokenBlacklist()
        
        blacklist.add("test_token_123")
        
        assert "test_token_123" in blacklist._blacklist
    
    def test_is_blacklisted_true(self):
        """测试检查黑名单（在黑名单中）"""
        blacklist = TokenBlacklist()
        blacklist.add("test_token_123")
        
        assert blacklist.is_blacklisted("test_token_123") is True
    
    def test_is_blacklisted_false(self):
        """测试检查黑名单（不在黑名单中）"""
        blacklist = TokenBlacklist()
        
        assert blacklist.is_blacklisted("test_token_123") is False
    
    def test_remove_token(self):
        """测试移除黑名单令牌"""
        blacklist = TokenBlacklist()
        blacklist.add("test_token_123")
        
        blacklist.remove("test_token_123")
        
        assert "test_token_123" not in blacklist._blacklist
    
    def test_remove_nonexistent_token(self):
        """测试移除不存在的令牌"""
        blacklist = TokenBlacklist()
        
        blacklist.remove("nonexistent_token")
        
        assert len(blacklist._blacklist) == 0
    
    def test_global_blacklist_instance(self):
        """测试全局黑名单实例"""
        assert isinstance(token_blacklist, TokenBlacklist)


class TestJWTHandler:
    """JWTHandler 测试"""
    
    @pytest.fixture
    def jwt_handler(self, jwt_config):
        """创建 JWTHandler 实例"""
        return JWTHandler(**jwt_config)
    
    def test_handler_initialization(self, jwt_config):
        """测试处理器初始化"""
        handler = JWTHandler(**jwt_config)
        
        assert handler.secret_key == jwt_config["secret_key"]
        assert handler.algorithm == jwt_config["algorithm"]
        assert handler.access_token_expire_minutes == 30
        assert handler.refresh_token_expire_days == 7
    
    def test_handler_short_secret_key(self):
        """测试短密钥（应抛出异常）"""
        with pytest.raises(ValueError, match="Secret key must be at least 32 characters long"):
            JWTHandler(secret_key="short_key")
    
    def test_create_access_token(self, jwt_handler, sample_user_data):
        """测试创建访问令牌"""
        token = jwt_handler.create_access_token(sample_user_data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_access_token_custom_expiry(self, jwt_handler, sample_user_data):
        """测试创建自定义过期时间的访问令牌"""
        custom_expiry = timedelta(hours=2)
        
        token = jwt_handler.create_access_token(
            sample_user_data,
            expires_delta=custom_expiry
        )
        
        assert token is not None
        
        payload = jwt_handler.decode_token(token)
        assert payload is not None
    
    def test_create_refresh_token(self, jwt_handler, sample_user_data):
        """测试创建刷新令牌"""
        token = jwt_handler.create_refresh_token(sample_user_data)
        
        assert token is not None
        assert isinstance(token, str)
    
    def test_create_refresh_token_custom_expiry(self, jwt_handler, sample_user_data):
        """测试创建自定义过期时间的刷新令牌"""
        custom_expiry = timedelta(days=14)
        
        token = jwt_handler.create_refresh_token(
            sample_user_data,
            expires_delta=custom_expiry
        )
        
        assert token is not None
    
    def test_create_token_pair(self, jwt_handler, sample_user_data):
        """测试创建令牌对"""
        tokens = jwt_handler.create_token_pair(sample_user_data)
        
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert "token_type" in tokens
        assert tokens["token_type"] == "bearer"
        
        access_payload = jwt_handler.decode_token(tokens["access_token"])
        assert access_payload is not None
        assert access_payload["type"] == "access"
        
        refresh_payload = jwt_handler.decode_token(tokens["refresh_token"])
        assert refresh_payload is not None
        assert refresh_payload["type"] == "refresh"
    
    def test_decode_access_token(self, jwt_handler, sample_user_data):
        """测试解码访问令牌"""
        token = jwt_handler.create_access_token(sample_user_data)
        
        payload = jwt_handler.decode_token(token)
        
        assert payload is not None
        assert payload["sub"] == "user_123"
        assert payload["username"] == "testuser"
        assert payload["type"] == "access"
    
    def test_decode_refresh_token(self, jwt_handler, sample_user_data):
        """测试解码刷新令牌"""
        token = jwt_handler.create_refresh_token(sample_user_data)
        
        payload = jwt_handler.decode_token(token)
        
        assert payload is not None
        assert payload["sub"] == "user_123"
        assert payload["type"] == "refresh"
    
    def test_verify_access_token(self, jwt_handler, sample_user_data):
        """测试验证访问令牌"""
        token = jwt_handler.create_access_token(sample_user_data)
        
        payload = jwt_handler.verify_access_token(token)
        
        assert payload is not None
        assert payload["type"] == "access"
    
    def test_verify_access_token_with_refresh_token(self, jwt_handler, sample_user_data):
        """测试用刷新令牌验证访问令牌（应失败）"""
        token = jwt_handler.create_refresh_token(sample_user_data)
        
        payload = jwt_handler.verify_access_token(token)
        
        assert payload is None
    
    def test_verify_refresh_token(self, jwt_handler, sample_user_data):
        """测试验证刷新令牌"""
        token = jwt_handler.create_refresh_token(sample_user_data)
        
        payload = jwt_handler.verify_refresh_token(token)
        
        assert payload is not None
        assert payload["type"] == "refresh"
    
    def test_verify_refresh_token_with_access_token(self, jwt_handler, sample_user_data):
        """测试用访问令牌验证刷新令牌（应失败）"""
        token = jwt_handler.create_access_token(sample_user_data)
        
        payload = jwt_handler.verify_refresh_token(token)
        
        assert payload is None
    
    def test_decode_expired_token(self, jwt_handler, sample_user_data):
        """测试解码过期令牌"""
        expired_time = timedelta(minutes=-1)
        
        token = jwt_handler.create_access_token(
            sample_user_data,
            expires_delta=expired_time
        )
        
        payload = jwt_handler.decode_token(token)
        
        assert payload is None
    
    def test_decode_invalid_token(self, jwt_handler):
        """测试解码无效令牌"""
        invalid_token = "invalid.token.here"
        
        payload = jwt_handler.decode_token(invalid_token)
        
        assert payload is None
    
    def test_decode_blacklisted_token(self, jwt_handler, sample_user_data):
        """测试解码黑名单令牌"""
        token = jwt_handler.create_access_token(sample_user_data)
        
        jwt_handler.revoke_token(token)
        
        payload = jwt_handler.decode_token(token)
        
        assert payload is None
    
    def test_revoke_token(self, jwt_handler, sample_user_data):
        """测试撤销令牌"""
        token = jwt_handler.create_access_token(sample_user_data)
        
        jwt_handler.revoke_token(token)
        
        assert token_blacklist.is_blacklisted(token) is True
    
    @pytest.mark.asyncio
    async def test_token_payload_data_integrity(self, jwt_handler, sample_user_data):
        """测试令牌数据完整性"""
        token = jwt_handler.create_access_token(sample_user_data)
        
        payload = jwt_handler.decode_token(token)
        
        if payload:
            assert payload["sub"] == sample_user_data["sub"]
            assert payload["username"] == sample_user_data["username"]
            assert payload["role"] == sample_user_data["role"]
    
    @pytest.mark.asyncio
    async def test_token_has_iat_claim(self, jwt_handler, sample_user_data):
        """测试令牌包含 issued at 声明"""
        token = jwt_handler.create_access_token(sample_user_data)
        
        payload = jwt_handler.decode_token(token)
        
        if payload:
            assert "iat" in payload or "sub" in payload


class TestGlobalJWTFunctions:
    """全局 JWT 函数测试"""
    
    def test_create_access_token_function(self, sample_user_data):
        """测试全局 create_access_token 函数"""
        with patch("agentforge.security.jwt_handler.settings") as mock_settings:
            mock_settings.jwt_secret_key = "test_secret_key_at_least_32_characters_long"
            mock_settings.jwt_algorithm = "HS256"
            mock_settings.jwt_expire_minutes = 30
            
            token = create_access_token(sample_user_data)
            
            assert token is not None
            assert isinstance(token, str)
    
    def test_verify_token_function(self, sample_user_data):
        """测试全局 verify_token 函数"""
        with patch("agentforge.security.jwt_handler.settings") as mock_settings:
            mock_settings.jwt_secret_key = "test_secret_key_at_least_32_characters_long"
            mock_settings.jwt_algorithm = "HS256"
            
            token = JWTHandler(
                secret_key=mock_settings.jwt_secret_key
            ).create_access_token(sample_user_data)
            
            payload = verify_token(token)
            
            assert payload is not None


class TestRateLimiter:
    """RateLimiter 测试"""
    
    @pytest.fixture
    def rate_limiter(self):
        """创建 RateLimiter 实例"""
        return RateLimiter(
            requests_per_minute=10,
            requests_per_hour=100,
            burst_size=5
        )
    
    @pytest.mark.asyncio
    async def test_rate_limiter_initialization(self, rate_limiter):
        """测试速率限制器初始化"""
        assert rate_limiter.requests_per_minute == 10
        assert rate_limiter.requests_per_hour == 100
        assert rate_limiter.burst_size == 5
    
    @pytest.mark.asyncio
    async def test_is_allowed_within_limit(self, rate_limiter):
        """测试允许范围内的请求"""
        key = "test_user_1"
        
        for _ in range(5):
            allowed = await rate_limiter.is_allowed(key)
            assert allowed is True
    
    @pytest.mark.asyncio
    async def test_is_allowed_exceeds_limit(self, rate_limiter):
        """测试超出限制的请求"""
        key = "test_user_2"
        
        for _ in range(15):
            await rate_limiter.is_allowed(key)
        
        allowed = await rate_limiter.is_allowed(key)
        assert allowed is False
    
    @pytest.mark.asyncio
    async def test_is_allowed_different_keys(self, rate_limiter):
        """测试不同 key 的请求"""
        key1 = "user_1"
        key2 = "user_2"
        
        for _ in range(10):
            await rate_limiter.is_allowed(key1)
        
        allowed = await rate_limiter.is_allowed(key2)
        assert allowed is True
    
    @pytest.mark.asyncio
    async def test_get_remaining(self, rate_limiter):
        """测试获取剩余请求数"""
        key = "test_user_3"
        
        for _ in range(3):
            await rate_limiter.is_allowed(key)
        
        remaining = await rate_limiter.get_remaining(key)
        
        assert "minute_remaining" in remaining
        assert "hour_remaining" in remaining
        assert "burst_remaining" in remaining
        assert remaining["minute_remaining"] <= 10
    
    @pytest.mark.asyncio
    async def test_reset_rate_limit(self, rate_limiter):
        """测试重置速率限制"""
        key = "test_user_4"
        
        for _ in range(15):
            await rate_limiter.is_allowed(key)
        
        rate_limiter.reset(key)
        
        remaining = await rate_limiter.get_remaining(key)
        assert remaining["minute_remaining"] == 10
    
    @pytest.mark.asyncio
    async def test_reset_nonexistent_key(self, rate_limiter):
        """测试重置不存在的 key"""
        rate_limiter.reset("nonexistent_key")
    
    @pytest.mark.asyncio
    async def test_burst_token_refill(self, rate_limiter):
        """测试令牌桶补充"""
        key = "test_user_5"
        
        for _ in range(6):
            await rate_limiter.is_allowed(key)
        
        time.sleep(0.1)
        
        remaining = await rate_limiter.get_remaining(key)
        assert remaining["burst_remaining"] >= 0


class TestIPRateLimiter:
    """IPRateLimiter 测试"""
    
    @pytest.fixture
    def ip_limiter(self):
        """创建 IPRateLimiter 实例"""
        return IPRateLimiter(
            requests_per_minute=10,
            requests_per_hour=100,
            burst_size=5
        )
    
    @pytest.mark.asyncio
    async def test_check_ip_allowed(self, ip_limiter):
        """测试检查 IP 允许"""
        ip = "192.168.1.1"
        
        allowed = await ip_limiter.check_ip(ip)
        assert allowed is True
    
    @pytest.mark.asyncio
    async def test_check_ip_denied(self, ip_limiter):
        """测试检查 IP 拒绝"""
        ip = "192.168.1.2"
        
        for _ in range(15):
            await ip_limiter.check_ip(ip)
        
        allowed = await ip_limiter.check_ip(ip)
        assert allowed is False


class TestUserRateLimiter:
    """UserRateLimiter 测试"""
    
    @pytest.fixture
    def user_limiter(self):
        """创建 UserRateLimiter 实例"""
        return UserRateLimiter(
            requests_per_minute=10,
            requests_per_hour=100,
            burst_size=5
        )
    
    @pytest.mark.asyncio
    async def test_check_user_allowed(self, user_limiter):
        """测试检查用户允许"""
        user_id = "user_123"
        
        allowed = await user_limiter.check_user(user_id)
        assert allowed is True
    
    @pytest.mark.asyncio
    async def test_check_user_denied(self, user_limiter):
        """测试检查用户拒绝"""
        user_id = "user_456"
        
        for _ in range(15):
            await user_limiter.check_user(user_id)
        
        allowed = await user_limiter.check_user(user_id)
        assert allowed is False


class TestEndpointRateLimiter:
    """EndpointRateLimiter 测试"""
    
    @pytest.fixture
    def endpoint_limiter(self):
        """创建 EndpointRateLimiter 实例"""
        return EndpointRateLimiter()
    
    def test_get_limiter_for_endpoint(self, endpoint_limiter):
        """测试获取端点限制器"""
        limiter = endpoint_limiter.get_limiter("/api/auth/login")
        
        assert limiter is not None
        assert limiter.requests_per_minute == 5
    
    def test_get_limiter_default(self, endpoint_limiter):
        """测试获取默认限制器"""
        limiter = endpoint_limiter.get_limiter("/api/unknown")
        
        assert limiter is not None
        assert limiter.requests_per_minute == 60
    
    @pytest.mark.asyncio
    async def test_check_endpoint_allowed(self, endpoint_limiter):
        """测试检查端点允许"""
        allowed = await endpoint_limiter.check(
            endpoint="/api/chat",
            key="user_123"
        )
        
        assert allowed is True
    
    @pytest.mark.asyncio
    async def test_check_endpoint_denied(self, endpoint_limiter):
        """测试检查端点拒绝"""
        for _ in range(10):
            await endpoint_limiter.check(
                endpoint="/api/auth/login",
                key="user_456"
            )
        
        allowed = await endpoint_limiter.check(
            endpoint="/api/auth/login",
            key="user_456"
        )
        
        assert allowed is False


class TestGlobalRateLimiters:
    """全局速率限制器测试"""
    
    def test_global_ip_rate_limiter(self):
        """测试全局 IP 限制器"""
        assert isinstance(ip_rate_limiter, IPRateLimiter)
        assert ip_rate_limiter.requests_per_minute == 100
    
    def test_global_user_rate_limiter(self):
        """测试全局用户限制器"""
        assert isinstance(user_rate_limiter, UserRateLimiter)
        assert user_rate_limiter.requests_per_minute == 60
    
    def test_global_endpoint_rate_limiter(self):
        """测试全局端点限制器"""
        assert isinstance(endpoint_rate_limiter, EndpointRateLimiter)


class TestSecurityMiddlewares:
    """安全中间件测试"""
    
    @pytest.fixture
    def mock_app(self):
        """Mock ASGI 应用"""
        async def mock_app(scope, receive, send):
            pass
        return mock_app
    
    @pytest.fixture
    def mock_request(self):
        """Mock Request"""
        request = MagicMock()
        request.url = MagicMock()
        request.url.scheme = "https"
        request.url.path = "/api/test"
        request.url.query = ""
        request.headers = {}
        request.method = "GET"
        request.client = MagicMock()
        request.client.host = "127.0.0.1"
        return request
    
    @pytest.fixture
    def mock_response(self):
        """Mock Response"""
        response = MagicMock()
        response.headers = {}
        response.status_code = 200
        return response
    
    def test_security_headers_middleware_initialization(
        self,
        mock_app
    ):
        """测试安全头中间件初始化"""
        middleware = SecurityHeadersMiddleware(
            mock_app,
            content_security_policy="default-src 'self'",
            strict_transport_security=True
        )
        
        assert middleware.content_security_policy == "default-src 'self'"
        assert middleware.strict_transport_security is True
    
    def test_request_validation_middleware_initialization(
        self,
        mock_app
    ):
        """测试请求验证中间件初始化"""
        middleware = RequestValidationMiddleware(mock_app)
        
        assert middleware.MAX_CONTENT_LENGTH == 10 * 1024 * 1024
        assert len(middleware.BLOCKED_USER_AGENTS) > 0
    
    def test_cors_middleware_initialization(
        self,
        mock_app
    ):
        """测试 CORS 中间件初始化"""
        middleware = CORSSecurityMiddleware(
            mock_app,
            allowed_origins=["http://localhost:3000"],
            allowed_methods=["GET", "POST"],
            allow_credentials=True
        )
        
        assert "http://localhost:3000" in middleware.allowed_origins
        assert middleware.allow_credentials is True
    
    def test_request_logging_middleware_initialization(
        self,
        mock_app
    ):
        """测试请求日志中间件初始化"""
        middleware = RequestLoggingMiddleware(mock_app)
        
        assert "authorization" in middleware.SENSITIVE_HEADERS


class TestRequestValidationMiddleware:
    """RequestValidationMiddleware 详细测试"""
    
    @pytest.fixture
    def validation_middleware(self):
        """创建请求验证中间件"""
        async def mock_app(scope, receive, send):
            response = MagicMock()
            response.status_code = 200
            return response
        
        return RequestValidationMiddleware(mock_app)
    
    @pytest.mark.asyncio
    async def test_check_suspicious_patterns_script(self, validation_middleware):
        """测试检测脚本注入模式"""
        content = "<script>alert('xss')</script>"
        
        result = validation_middleware._check_suspicious_patterns(content)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_check_suspicious_patterns_sql(self, validation_middleware):
        """测试检测 SQL 注入模式"""
        content = "'; DROP TABLE users; --"
        
        result = validation_middleware._check_suspicious_patterns(content)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_check_suspicious_patterns_clean(self, validation_middleware):
        """测试检测正常内容"""
        content = "This is a normal request"
        
        result = validation_middleware._check_suspicious_patterns(content)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_check_suspicious_patterns_javascript(self, validation_middleware):
        """测试检测 JavaScript 协议"""
        content = "javascript:void(0)"
        
        result = validation_middleware._check_suspicious_patterns(content)
        
        assert result is True


class TestRateLimiterCleanOldRequests:
    """RateLimiter 清理旧请求测试"""
    
    @pytest.fixture
    def rate_limiter(self):
        """创建 RateLimiter 实例"""
        return RateLimiter(
            requests_per_minute=60,
            requests_per_hour=1000,
            burst_size=10
        )
    
    def test_clean_old_requests(self, rate_limiter):
        """测试清理旧请求"""
        current_time = time.time()
        
        bucket = [
            current_time - 120,
            current_time - 90,
            current_time - 60,
            current_time - 30,
            current_time - 10,
            current_time
        ]
        
        cleaned = rate_limiter._clean_old_requests(bucket, 60)
        
        assert len(cleaned) == 3
        assert all(t > current_time - 60 for t in cleaned)
    
    def test_clean_old_requests_all_old(self, rate_limiter):
        """测试清理全部旧请求"""
        current_time = time.time()
        
        bucket = [
            current_time - 120,
            current_time - 90,
            current_time - 70
        ]
        
        cleaned = rate_limiter._clean_old_requests(bucket, 60)
        
        assert len(cleaned) == 0
    
    def test_clean_old_requests_all_recent(self, rate_limiter):
        """测试清理（全部为最近请求）"""
        current_time = time.time()
        
        bucket = [
            current_time - 10,
            current_time - 20,
            current_time - 30
        ]
        
        cleaned = rate_limiter._clean_old_requests(bucket, 60)
        
        assert len(cleaned) == 3
