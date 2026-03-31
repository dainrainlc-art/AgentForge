"""
AgentForge FastAPI Application - Production Ready
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import BaseModel
import sys

from agentforge.config import settings
from agentforge.security import (
    SecurityHeadersMiddleware,
    RequestValidationMiddleware,
    RequestLoggingMiddleware
)
from integrations.api.auth import router as auth_router
from integrations.api.health import router as health_router
from integrations.api.chat import router as chat_router
from integrations.api.orders import router as orders_router
from integrations.api.knowledge import router as knowledge_router
from integrations.api.websocket import router as websocket_router
from integrations.api.fiverr_analytics import router as fiverr_analytics_router
from integrations.api.backup import router as backup_router
from integrations.api.config import router as config_router
from integrations.api.linkedin import router as linkedin_router
from integrations.api.telegram import router as telegram_router
from integrations.api.feishu import router as feishu_router
from integrations.api.docs_generator import APIDocGenerator, init_api_docs


def setup_logging():
    """Configure loguru logging"""
    logger.remove()
    logger.add(
        sys.stdout,
        level=settings.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    logger.add(
        "logs/app.log",
        rotation="10 MB",
        retention="7 days",
        level=settings.log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        serialize=True
    )


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AgentForge - AI 驱动的 Fiverr 运营自动化智能助理系统",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None
)

doc_generator: APIDocGenerator = None

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestValidationMiddleware)
app.add_middleware(RequestLoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api", tags=["health"])
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
app.include_router(orders_router, prefix="/api/orders", tags=["orders"])
app.include_router(knowledge_router, prefix="/api/knowledge", tags=["knowledge"])
app.include_router(websocket_router, tags=["websocket"])
app.include_router(fiverr_analytics_router, prefix="/api/fiverr", tags=["fiverr"])
app.include_router(backup_router, prefix="/api/backup", tags=["backup"])
app.include_router(config_router, prefix="/api", tags=["config"])
app.include_router(linkedin_router, tags=["linkedin"])
app.include_router(telegram_router, tags=["telegram"])
app.include_router(feishu_router, tags=["feishu"])


@app.on_event("startup")
async def startup_event():
    """Application startup tasks"""
    global doc_generator
    setup_logging()
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Environment: {'development' if settings.debug else 'production'}")
    
    doc_generator = init_api_docs(app)
    
    if settings.debug:
        logger.info("Debug mode enabled, generating API documentation...")
        try:
            doc_generator.export_openapi_json("docs/api/openapi.json")
            doc_generator.export_openapi_yaml("docs/api/openapi.yaml")
            doc_generator.generate_markdown_docs("docs/api/README.md")
            logger.info("API documentation generated successfully")
        except Exception as e:
            logger.error(f"Failed to generate API documentation: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks"""
    logger.info(f"Shutting down {settings.app_name}")


class DocsGenerateRequest(BaseModel):
    """Request model for docs generation"""
    formats: list[str] = ["json", "yaml", "markdown"]
    output_dir: str = "docs/api"


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs" if settings.debug else "disabled"
    }


@app.post("/api/docs/generate")
async def generate_docs(request: DocsGenerateRequest = None):
    """Manually trigger API documentation generation
    
    Args:
        request: Generation options including formats and output directory
        
    Returns:
        Generation results with file paths and status
    """
    if not doc_generator:
        raise HTTPException(status_code=500, detail="Document generator not initialized")
    
    if request is None:
        request = DocsGenerateRequest()
    
    results = {
        "success": True,
        "generated_files": [],
        "failed_files": [],
        "timestamp": None
    }
    
    from datetime import datetime
    results["timestamp"] = datetime.utcnow().isoformat() + "Z"
    
    try:
        if "json" in request.formats:
            json_path = f"{request.output_dir}/openapi.json"
            if doc_generator.export_openapi_json(json_path):
                results["generated_files"].append(json_path)
            else:
                results["failed_files"].append(json_path)
        
        if "yaml" in request.formats:
            yaml_path = f"{request.output_dir}/openapi.yaml"
            if doc_generator.export_openapi_yaml(yaml_path):
                results["generated_files"].append(yaml_path)
            else:
                results["failed_files"].append(yaml_path)
        
        if "markdown" in request.formats:
            md_path = f"{request.output_dir}/README.md"
            if doc_generator.generate_markdown_docs(md_path):
                results["generated_files"].append(md_path)
            else:
                results["failed_files"].append(md_path)
        
        if results["failed_files"]:
            results["success"] = False
            
        logger.info(f"Manual docs generation completed: {len(results['generated_files'])} files generated")
        
        return JSONResponse(content=results)
        
    except Exception as e:
        logger.error(f"Failed to generate documentation: {e}")
        raise HTTPException(status_code=500, detail=f"Documentation generation failed: {str(e)}")
