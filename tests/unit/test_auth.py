"""
Test Authentication Module
"""
import pytest
from fastapi.testclient import TestClient

from agentforge.security import PasswordHandler, JWTHandler


class TestPasswordHandler:
    """Test password handling"""
    
    def test_hash_password(self):
        """Test password hashing"""
        password = "TestPassword@123"
        hashed = PasswordHandler.hash_password(password)
        
        assert hashed != password
        assert hashed.startswith("$2b$")
    
    def test_verify_password(self):
        """Test password verification"""
        password = "TestPassword@123"
        hashed = PasswordHandler.hash_password(password)
        
        assert PasswordHandler.verify_password(password, hashed)
        assert not PasswordHandler.verify_password("wrong_password", hashed)
    
    def test_validate_strength_valid(self):
        """Test password strength validation - valid"""
        password = "StrongPass@123"
        is_valid, issues = PasswordHandler.validate_strength(password)
        
        assert is_valid
        assert len(issues) == 0
    
    def test_validate_strength_weak(self):
        """Test password strength validation - weak"""
        password = "weak"
        is_valid, issues = PasswordHandler.validate_strength(password)
        
        assert not is_valid
        assert len(issues) > 0
    
    def test_get_strength_score(self):
        """Test password strength score"""
        weak_score = PasswordHandler.get_strength_score("weak")
        strong_score = PasswordHandler.get_strength_score("StrongPass@123!")
        
        assert weak_score < strong_score
        assert strong_score >= 60


class TestJWTHandler:
    """Test JWT handling"""
    
    def test_create_access_token(self):
        """Test access token creation"""
        handler = JWTHandler(
            secret_key="test_secret_key_at_least_32_characters_long",
            access_token_expire_minutes=30
        )
        
        token = handler.create_access_token({"user_id": "123", "username": "test"})
        
        assert token is not None
        assert isinstance(token, str)
    
    def test_verify_access_token(self):
        """Test access token verification"""
        handler = JWTHandler(
            secret_key="test_secret_key_at_least_32_characters_long",
            access_token_expire_minutes=30
        )
        
        token = handler.create_access_token({"user_id": "123", "username": "test"})
        payload = handler.verify_access_token(token)
        
        assert payload is not None
        assert payload["user_id"] == "123"
        assert payload["username"] == "test"
    
    def test_verify_invalid_token(self):
        """Test invalid token verification"""
        handler = JWTHandler(
            secret_key="test_secret_key_at_least_32_characters_long"
        )
        
        payload = handler.verify_access_token("invalid_token")
        
        assert payload is None
    
    def test_create_token_pair(self):
        """Test token pair creation"""
        handler = JWTHandler(
            secret_key="test_secret_key_at_least_32_characters_long"
        )
        
        tokens = handler.create_token_pair({"user_id": "123"})
        
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"
    
    def test_token_blacklist(self):
        """Test token blacklist"""
        from agentforge.security import token_blacklist
        
        token = "test_token_123"
        token_blacklist.add(token)
        
        assert token_blacklist.is_blacklisted(token)
        
        token_blacklist.remove(token)
        assert not token_blacklist.is_blacklisted(token)
