"""
Authentication API Endpoints - Security Enhanced
"""
from fastapi import APIRouter, HTTPException, Depends, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime, timedelta
from loguru import logger

from agentforge.config import settings
from agentforge.security import (
    JWTHandler,
    PasswordHandler,
    RateLimiter,
    login_attempt_manager
)
from agentforge.security.rate_limiter import endpoint_rate_limiter


router = APIRouter()
security = HTTPBearer()


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        is_valid, issues = PasswordHandler.validate_strength(v)
        if not is_valid:
            raise ValueError('; '.join(issues))
        return v


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int


class TokenRefresh(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str]
    created_at: str


class PasswordChange(BaseModel):
    old_password: str
    new_password: str
    
    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
        is_valid, issues = PasswordHandler.validate_strength(v)
        if not is_valid:
            raise ValueError('; '.join(issues))
        return v


# 惰性初始化密码哈希，避免 passlib bcrypt bug
class FakeUsersDB:
    """Lazy-loaded fake users database to avoid passlib bcrypt initialization bug"""
    
    def __init__(self):
        self._db = None
    
    def _load(self):
        if self._db is None:
            self._db = {
                "admin": {
                    "id": "user_admin",
                    "email": "admin@agentforge.local",
                    "password_hash": PasswordHandler.hash_password("Admin@123"),
                    "name": "Administrator",
                    "created_at": "2024-01-01T00:00:00",
                    "role": "admin"
                }
            }
        return self._db
    
    def __getitem__(self, key):
        return self._load()[key]
    
    def __contains__(self, key):
        return key in self._load()
    
    def get(self, key, default=None):
        return self._load().get(key, default)
    
    def __iter__(self):
        return iter(self._load())
    
    def items(self):
        return self._load().items()
    
    def values(self):
        return self._load().values()
    
    def keys(self):
        return self._load().keys()

fake_users_db = FakeUsersDB()

jwt_handler = JWTHandler(
    secret_key=settings.jwt_secret_key,
    algorithm=settings.jwt_algorithm,
    access_token_expire_minutes=settings.jwt_expire_minutes
)


def get_client_ip(request: Request) -> str:
    """Get client IP address"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/register", response_model=UserResponse)
async def register(user: UserRegister, request: Request):
    """Register new user"""
    client_ip = get_client_ip(request)
    
    if not await endpoint_rate_limiter.check("/api/auth/register", client_ip):
        raise HTTPException(
            status_code=429,
            detail="请求过于频繁，请稍后再试"
        )
    
    username = user.email.split("@")[0]
    if username in fake_users_db:
        raise HTTPException(status_code=400, detail="用户已存在")
    
    user_id = f"user_{len(fake_users_db) + 1}"
    fake_users_db[username] = {
        "id": user_id,
        "email": user.email,
        "password_hash": PasswordHandler.hash_password(user.password),
        "name": user.name,
        "created_at": datetime.now().isoformat(),
        "role": "user"
    }
    
    logger.info(f"New user registered: {user.email} from {client_ip}")
    
    return UserResponse(
        id=user_id,
        email=user.email,
        name=user.name,
        created_at=fake_users_db[username]["created_at"]
    )


@router.post("/login", response_model=Token)
async def login(user: UserLogin, request: Request):
    """Login and get access token"""
    client_ip = get_client_ip(request)
    
    if not await endpoint_rate_limiter.check("/api/auth/login", client_ip):
        raise HTTPException(
            status_code=429,
            detail="请求过于频繁，请稍后再试"
        )
    
    is_locked, remaining = login_attempt_manager.is_locked_out(user.username)
    if is_locked:
        raise HTTPException(
            status_code=423,
            detail=f"账户已锁定，请在{remaining}秒后重试"
        )
    
    if user.username not in fake_users_db:
        login_attempt_manager.record_attempt(user.username, False)
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    stored_user = fake_users_db[user.username]
    
    if not PasswordHandler.verify_password(user.password, stored_user["password_hash"]):
        login_attempt_manager.record_attempt(user.username, False)
        remaining_attempts = login_attempt_manager.get_remaining_attempts(user.username)
        raise HTTPException(
            status_code=401,
            detail=f"用户名或密码错误，剩余尝试次数: {remaining_attempts}"
        )
    
    login_attempt_manager.record_attempt(user.username, True)
    
    token_pair = jwt_handler.create_token_pair(
        data={"sub": user.username, "user_id": stored_user["id"], "role": stored_user.get("role", "user")}
    )
    
    logger.info(f"User logged in: {user.username} from {client_ip}")
    
    return Token(
        access_token=token_pair["access_token"],
        refresh_token=token_pair["refresh_token"],
        expires_in=settings.jwt_expire_minutes * 60
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(token_data: TokenRefresh, request: Request):
    """Refresh access token"""
    client_ip = get_client_ip(request)
    
    payload = jwt_handler.verify_refresh_token(token_data.refresh_token)
    if not payload:
        raise HTTPException(status_code=401, detail="无效的刷新令牌")
    
    username = payload.get("sub")
    if username not in fake_users_db:
        raise HTTPException(status_code=401, detail="用户不存在")
    
    jwt_handler.revoke_token(token_data.refresh_token)
    
    stored_user = fake_users_db[username]
    token_pair = jwt_handler.create_token_pair(
        data={"sub": username, "user_id": stored_user["id"], "role": stored_user.get("role", "user")}
    )
    
    logger.info(f"Token refreshed for: {username} from {client_ip}")
    
    return Token(
        access_token=token_pair["access_token"],
        refresh_token=token_pair["refresh_token"],
        expires_in=settings.jwt_expire_minutes * 60
    )


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Logout and revoke token"""
    token = credentials.credentials
    jwt_handler.revoke_token(token)
    
    return {"status": "logged_out"}


@router.get("/verify")
async def verify_auth(payload: dict = Depends(lambda: verify_token_dependency)):
    """Verify authentication status"""
    return {"valid": True, "user_id": payload.get("user_id")}


@router.get("/me", response_model=UserResponse)
async def get_current_user(payload: dict = Depends(lambda: verify_token_dependency)):
    """Get current user info"""
    username = payload.get("sub")
    if username not in fake_users_db:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    user = fake_users_db[username]
    return UserResponse(
        id=user["id"],
        email=user["email"],
        name=user.get("name"),
        created_at=user["created_at"]
    )


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    payload: dict = Depends(lambda: verify_token_dependency)
):
    """Change user password"""
    username = payload.get("sub")
    if username not in fake_users_db:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    stored_user = fake_users_db[username]
    
    if not PasswordHandler.verify_password(password_data.old_password, stored_user["password_hash"]):
        raise HTTPException(status_code=400, detail="原密码错误")
    
    stored_user["password_hash"] = PasswordHandler.hash_password(password_data.new_password)
    
    logger.info(f"Password changed for: {username}")
    
    return {"status": "password_changed"}


async def verify_token_dependency(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Dependency for verifying tokens"""
    token = credentials.credentials
    payload = jwt_handler.verify_access_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=401,
            detail="无效或过期的令牌",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return payload
