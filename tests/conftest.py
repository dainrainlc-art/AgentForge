"""
Pytest Configuration
"""
import pytest
import asyncio
from typing import Generator


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_config():
    """Test configuration"""
    return {
        "test_user": {
            "username": "testuser",
            "password": "Test@12345",
            "email": "test@example.com"
        },
        "test_api_key": "test_api_key_12345"
    }
