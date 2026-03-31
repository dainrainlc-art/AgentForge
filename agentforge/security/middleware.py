"""
Security Middleware - Security headers and request validation
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from typing import Dict, List, Optional
import re
from loguru import logger


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    def __init__(
        self,
        app: ASGIApp,
        content_security_policy: Optional[str] = None,
        strict_transport_security: bool = True
    ):
        super().__init__(app)
        self.content_security_policy = content_security_policy
        self.strict_transport_security = strict_transport_security
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), camera=(), geolocation=(), gyroscope=(), "
            "magnetometer=(), microphone=(), payment=(), usb=()"
        )
        
        if self.content_security_policy:
            response.headers["Content-Security-Policy"] = self.content_security_policy
        
        if self.strict_transport_security and request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        
        return response


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Validate incoming requests"""
    
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
    BLOCKED_USER_AGENTS = [
        "sqlmap",
        "nikto",
        "nmap",
        "masscan",
        "zgrab"
    ]
    SUSPICIOUS_PATTERNS = [
        r"<script.*?>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"union\s+select",
        r"or\s+1\s*=\s*1",
        r";\s*drop\s+table",
        r"'\s*or\s*'",
    ]
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self._compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.SUSPICIOUS_PATTERNS]
    
    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.MAX_CONTENT_LENGTH:
            logger.warning(f"Request too large: {content_length} bytes")
            return Response(
                content="Request entity too large",
                status_code=413
            )
        
        user_agent = request.headers.get("user-agent", "").lower()
        for blocked in self.BLOCKED_USER_AGENTS:
            if blocked in user_agent:
                logger.warning(f"Blocked user agent: {user_agent}")
                return Response(
                    content="Forbidden",
                    status_code=403
                )
        
        query_string = str(request.url.query)
        if self._check_suspicious_patterns(query_string):
            logger.warning(f"Suspicious query string detected: {query_string}")
            return Response(
                content="Bad Request",
                status_code=400
            )
        
        response = await call_next(request)
        return response
    
    def _check_suspicious_patterns(self, content: str) -> bool:
        for pattern in self._compiled_patterns:
            if pattern.search(content):
                return True
        return False


class CORSSecurityMiddleware(BaseHTTPMiddleware):
    """Enhanced CORS middleware with security checks"""
    
    def __init__(
        self,
        app: ASGIApp,
        allowed_origins: List[str],
        allowed_methods: List[str] = None,
        allowed_headers: List[str] = None,
        allow_credentials: bool = True,
        max_age: int = 600
    ):
        super().__init__(app)
        self.allowed_origins = set(allowed_origins)
        self.allowed_methods = allowed_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        self.allowed_headers = allowed_headers or ["*"]
        self.allow_credentials = allow_credentials
        self.max_age = max_age
    
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")
        
        if request.method == "OPTIONS":
            response = Response(status_code=204)
        else:
            response = await call_next(request)
        
        if origin:
            if origin in self.allowed_origins or "*" in self.allowed_origins:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allowed_methods)
                response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allowed_headers)
                
                if self.allow_credentials:
                    response.headers["Access-Control-Allow-Credentials"] = "true"
                
                response.headers["Access-Control-Max-Age"] = str(self.max_age)
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests for audit purposes"""
    
    SENSITIVE_HEADERS = ["authorization", "cookie", "set-cookie"]
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        import time
        start_time = time.time()
        
        response = await call_next(request)
        
        duration = time.time() - start_time
        
        headers = dict(request.headers)
        for header in self.SENSITIVE_HEADERS:
            if header in headers:
                headers[header] = "[REDACTED]"
        
        log_data = {
            "method": request.method,
            "path": request.url.path,
            "query": str(request.url.query),
            "status_code": response.status_code,
            "duration_ms": round(duration * 1000, 2),
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("user-agent", "")
        }
        
        if response.status_code >= 400:
            logger.warning(f"Request: {log_data}")
        else:
            logger.info(f"Request: {log_data}")
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
