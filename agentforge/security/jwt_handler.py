"""
JWT Handler - Secure JWT token management
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Set
import jwt
from loguru import logger

from agentforge.config import settings


class TokenBlacklist:
    """In-memory token blacklist for revoked tokens"""
    
    def __init__(self):
        self._blacklist: Set[str] = set()
    
    def add(self, token: str) -> None:
        self._blacklist.add(token)
        logger.debug(f"Token added to blacklist")
    
    def is_blacklisted(self, token: str) -> bool:
        return token in self._blacklist
    
    def remove(self, token: str) -> None:
        self._blacklist.discard(token)


token_blacklist = TokenBlacklist()


class JWTHandler:
    """Secure JWT token handler with refresh token support"""
    
    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7
    ):
        if len(secret_key) < 32:
            raise ValueError("Secret key must be at least 32 characters long")
        
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
    
    def create_access_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({
            "exp": expire,
            "type": "access",
            "iat": datetime.utcnow()
        })
        
        encoded_jwt = jwt.encode(
            to_encode,
            self.secret_key,
            algorithm=self.algorithm
        )
        
        return encoded_jwt
    
    def create_refresh_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create refresh token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        
        to_encode.update({
            "exp": expire,
            "type": "refresh",
            "iat": datetime.utcnow()
        })
        
        encoded_jwt = jwt.encode(
            to_encode,
            self.secret_key,
            algorithm=self.algorithm
        )
        
        return encoded_jwt
    
    def create_token_pair(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Create access and refresh token pair"""
        access_token = self.create_access_token(data)
        refresh_token = self.create_refresh_token(data)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Decode and validate token"""
        try:
            if token_blacklist.is_blacklisted(token):
                logger.warning("Token is blacklisted")
                return None
            
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            return payload
        
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
    def verify_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify access token"""
        payload = self.decode_token(token)
        
        if payload and payload.get("type") == "access":
            return payload
        
        return None
    
    def verify_refresh_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify refresh token"""
        payload = self.decode_token(token)
        
        if payload and payload.get("type") == "refresh":
            return payload
        
        return None
    
    def revoke_token(self, token: str) -> None:
        """Revoke a token by adding to blacklist"""
        token_blacklist.add(token)
        logger.info("Token revoked")


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create access token using global settings"""
    handler = JWTHandler(
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        access_token_expire_minutes=settings.jwt_expire_minutes
    )
    return handler.create_access_token(data, expires_delta)


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify token using global settings"""
    handler = JWTHandler(
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    return handler.verify_access_token(token)
