"""
AgentForge Application Entry Point
"""
import uvicorn
from loguru import logger

from agentforge.config import settings
from integrations.api.main import app


def main():
    """Run the application"""
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    
    uvicorn.run(
        "integrations.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    main()
