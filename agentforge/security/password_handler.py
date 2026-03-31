"""
Password Handler - Secure password hashing and validation
"""
import re
from typing import Tuple, List, Optional
from passlib.context import CryptContext
from loguru import logger


class PasswordHandler:
    """Secure password handling with bcrypt"""
    
    MIN_LENGTH = 8
    MAX_LENGTH = 128
    _pwd_context = None
    
    @classmethod
    def _get_context(cls):
        """Lazy initialization of CryptContext to avoid passlib bcrypt bug"""
        if cls._pwd_context is None:
            cls._pwd_context = CryptContext(
                schemes=["bcrypt"],
                deprecated="auto",
                bcrypt__rounds=12
            )
        return cls._pwd_context
    
    @classmethod
    def hash_password(cls, password: str) -> str:
        """Hash password using bcrypt"""
        return cls._get_context().hash(password)
    
    @classmethod
    def verify_password(cls, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return cls._get_context().verify(plain_password, hashed_password)
    
    @classmethod
    def validate_strength(cls, password: str) -> Tuple[bool, List[str]]:
        """
        Validate password strength.
        Returns (is_valid, list_of_issues)
        """
        issues = []
        
        if len(password) < cls.MIN_LENGTH:
            issues.append(f"密码长度至少{cls.MIN_LENGTH}个字符")
        
        if len(password) > cls.MAX_LENGTH:
            issues.append(f"密码长度不能超过{cls.MAX_LENGTH}个字符")
        
        if not re.search(r"[a-z]", password):
            issues.append("密码必须包含小写字母")
        
        if not re.search(r"[A-Z]", password):
            issues.append("密码必须包含大写字母")
        
        if not re.search(r"\d", password):
            issues.append("密码必须包含数字")
        
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            issues.append("密码必须包含特殊字符")
        
        common_passwords = [
            "password", "123456", "qwerty", "abc123", 
            "password123", "admin", "letmein", "welcome"
        ]
        if password.lower() in common_passwords:
            issues.append("密码过于常见，请选择更复杂的密码")
        
        is_valid = len(issues) == 0
        return is_valid, issues
    
    @classmethod
    def get_strength_score(cls, password: str) -> int:
        """
        Calculate password strength score (0-100)
        """
        score = 0
        
        if len(password) >= cls.MIN_LENGTH:
            score += 20
        if len(password) >= 12:
            score += 10
        if len(password) >= 16:
            score += 10
        
        if re.search(r"[a-z]", password):
            score += 10
        if re.search(r"[A-Z]", password):
            score += 10
        if re.search(r"\d", password):
            score += 10
        if re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            score += 15
        
        unique_chars = len(set(password))
        if unique_chars >= len(password) * 0.7:
            score += 15
        
        return min(score, 100)
    
    @classmethod
    def get_strength_level(cls, password: str) -> str:
        """Get password strength level"""
        score = cls.get_strength_score(password)
        
        if score >= 80:
            return "强"
        elif score >= 60:
            return "中"
        elif score >= 40:
            return "弱"
        else:
            return "非常弱"


class LoginAttemptManager:
    """Manage login attempts and lockout"""
    
    MAX_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 15
    
    def __init__(self):
        self._attempts: dict = {}
    
    def record_attempt(self, username: str, success: bool) -> None:
        """Record a login attempt"""
        if success:
            self._attempts.pop(username, None)
            logger.info(f"Login successful for {username}")
        else:
            if username not in self._attempts:
                self._attempts[username] = {"count": 0, "first_attempt": None}
            
            from datetime import datetime
            if self._attempts[username]["count"] == 0:
                self._attempts[username]["first_attempt"] = datetime.utcnow()
            
            self._attempts[username]["count"] += 1
            logger.warning(f"Failed login attempt {self._attempts[username]['count']} for {username}")
    
    def is_locked_out(self, username: str) -> Tuple[bool, Optional[int]]:
        """Check if account is locked out"""
        if username not in self._attempts:
            return False, None
        
        attempt_data = self._attempts[username]
        
        if attempt_data["count"] >= self.MAX_ATTEMPTS:
            from datetime import datetime, timedelta
            
            first_attempt = attempt_data["first_attempt"]
            if first_attempt:
                lockout_end = first_attempt + timedelta(minutes=self.LOCKOUT_DURATION_MINUTES)
                remaining = (lockout_end - datetime.utcnow()).total_seconds()
                
                if remaining > 0:
                    return True, int(remaining)
                else:
                    self._attempts.pop(username, None)
        
        return False, None
    
    def get_remaining_attempts(self, username: str) -> int:
        """Get remaining attempts before lockout"""
        if username not in self._attempts:
            return self.MAX_ATTEMPTS
        
        return max(0, self.MAX_ATTEMPTS - self._attempts[username]["count"])


login_attempt_manager = LoginAttemptManager()
