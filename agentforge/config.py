"""
AgentForge Configuration Module
"""
from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    app_name: str = "AgentForge"
    app_version: str = "1.0.0"
    debug: bool = False
    debug_mode: Optional[bool] = None
    
    qianfan_api_key: Optional[str] = None
    qianfan_base_url: str = "https://qianfan.baidubce.com/v2/coding"
    qianfan_default_model: str = "glm-5"
    
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "agentforge"
    postgres_user: str = "agentforge"
    postgres_password: str = ""
    
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    
    n8n_host: str = "localhost"
    n8n_port: int = 5678
    
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440
    
    log_level: str = "INFO"
    
    memory_file_path: str = "MEMORY.md"
    
    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    @property
    def redis_url(self) -> str:
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}"
        return f"redis://{self.redis_host}:{self.redis_port}"
    
    @property
    def qdrant_url(self) -> str:
        return f"http://{self.qdrant_host}:{self.qdrant_port}"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.debug_mode is not None:
            self.debug = self.debug_mode

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
