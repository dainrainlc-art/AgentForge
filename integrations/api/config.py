"""
Configuration Management API Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from loguru import logger
import asyncio
import httpx

from agentforge.config import settings, get_settings
from agentforge.llm import QianfanClient


router = APIRouter()
security = HTTPBearer()


class ConfigSection(BaseModel):
    """Configuration section model"""
    title: str
    icon: str
    fields: list


class ConfigField(BaseModel):
    """Configuration field model"""
    key: str
    label: str
    type: str
    value: Any
    description: Optional[str] = None
    placeholder: Optional[str] = None
    required: bool = False
    sensitive: bool = False
    options: Optional[list] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None


class ConfigGroup(BaseModel):
    """Configuration group model"""
    id: str
    title: str
    icon: str
    description: str
    fields: list[ConfigField]


class ConfigResponse(BaseModel):
    """Configuration response model"""
    groups: list[ConfigGroup]
    last_updated: Optional[str] = None


class ConfigUpdateRequest(BaseModel):
    """Configuration update request model"""
    key: str
    value: Any


class ConfigTestResult(BaseModel):
    """Configuration test result model"""
    service: str
    status: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ConfigSaveResponse(BaseModel):
    """Configuration save response model"""
    success: bool
    message: str
    requires_restart: bool = False


async def verify_admin_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Verify admin token"""
    token = credentials.credentials
    
    if not token or token != settings.jwt_secret_key:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return {"admin": True}


def get_config_groups() -> list[ConfigGroup]:
    """Get all configuration groups"""
    
    groups = [
        ConfigGroup(
            id="ai_model",
            title="AI 模型配置",
            icon="🤖",
            description="配置百度千帆 AI 模型相关参数",
            fields=[
                ConfigField(
                    key="qianfan_api_key",
                    label="百度千帆 API Key",
                    type="password",
                    value=settings.qianfan_api_key or "",
                    description="百度千帆 Coding Plan Pro API 密钥",
                    placeholder="请输入 API Key",
                    required=True,
                    sensitive=True
                ),
                ConfigField(
                    key="qianfan_base_url",
                    label="API 基础 URL",
                    type="text",
                    value=settings.qianfan_base_url,
                    description="百度千帆 API 基础地址",
                    placeholder="https://qianfan.baidubce.com/v2/coding"
                ),
                ConfigField(
                    key="qianfan_default_model",
                    label="默认模型",
                    type="select",
                    value=settings.qianfan_default_model,
                    description="默认使用的 AI 模型",
                    options=[
                        {"value": "glm-5", "label": "GLM-5 (核心模型)"},
                        {"value": "kimi-k2.5", "label": "Kimi-K2.5 (长上下文)"},
                        {"value": "deepseek-v3.2", "label": "DeepSeek-V3.2 (代码)"},
                        {"value": "minimax-m2.5", "label": "MiniMax-M2.5 (创意)"}
                    ]
                )
            ]
        ),
        ConfigGroup(
            id="database",
            title="数据库配置",
            icon="🗄️",
            description="配置 PostgreSQL 主数据库",
            fields=[
                ConfigField(
                    key="postgres_host",
                    label="数据库主机",
                    type="text",
                    value=settings.postgres_host,
                    description="PostgreSQL 服务器地址",
                    placeholder="localhost"
                ),
                ConfigField(
                    key="postgres_port",
                    label="数据库端口",
                    type="number",
                    value=settings.postgres_port,
                    description="PostgreSQL 服务器端口",
                    min_value=1,
                    max_value=65535
                ),
                ConfigField(
                    key="postgres_db",
                    label="数据库名称",
                    type="text",
                    value=settings.postgres_db,
                    description="PostgreSQL 数据库名",
                    placeholder="agentforge"
                ),
                ConfigField(
                    key="postgres_user",
                    label="数据库用户",
                    type="text",
                    value=settings.postgres_user,
                    description="PostgreSQL 用户名",
                    placeholder="agentforge"
                ),
                ConfigField(
                    key="postgres_password",
                    label="数据库密码",
                    type="password",
                    value=settings.postgres_password,
                    description="PostgreSQL 密码",
                    placeholder="请输入密码",
                    sensitive=True
                )
            ]
        ),
        ConfigGroup(
            id="cache",
            title="缓存配置",
            icon="⚡",
            description="配置 Redis 缓存层",
            fields=[
                ConfigField(
                    key="redis_host",
                    label="Redis 主机",
                    type="text",
                    value=settings.redis_host,
                    description="Redis 服务器地址",
                    placeholder="localhost"
                ),
                ConfigField(
                    key="redis_port",
                    label="Redis 端口",
                    type="number",
                    value=settings.redis_port,
                    description="Redis 服务器端口",
                    min_value=1,
                    max_value=65535
                ),
                ConfigField(
                    key="redis_password",
                    label="Redis 密码",
                    type="password",
                    value=settings.redis_password or "",
                    description="Redis 密码（可选）",
                    placeholder="请输入密码",
                    sensitive=True
                )
            ]
        ),
        ConfigGroup(
            id="vector_db",
            title="向量数据库",
            icon="🔍",
            description="配置 Qdrant 向量数据库",
            fields=[
                ConfigField(
                    key="qdrant_host",
                    label="Qdrant 主机",
                    type="text",
                    value=settings.qdrant_host,
                    description="Qdrant 服务器地址",
                    placeholder="localhost"
                ),
                ConfigField(
                    key="qdrant_port",
                    label="Qdrant 端口",
                    type="number",
                    value=settings.qdrant_port,
                    description="Qdrant 服务器端口",
                    min_value=1,
                    max_value=65535
                )
            ]
        ),
        ConfigGroup(
            id="workflow",
            title="工作流引擎",
            icon="⚙️",
            description="配置 n8n 工作流引擎",
            fields=[
                ConfigField(
                    key="n8n_host",
                    label="n8n 主机",
                    type="text",
                    value=settings.n8n_host,
                    description="n8n 服务器地址",
                    placeholder="localhost"
                ),
                ConfigField(
                    key="n8n_port",
                    label="n8n 端口",
                    type="number",
                    value=settings.n8n_port,
                    description="n8n 服务器端口",
                    min_value=1,
                    max_value=65535
                )
            ]
        ),
        ConfigGroup(
            id="security",
            title="安全配置",
            icon="🔒",
            description="配置 JWT 认证和安全参数",
            fields=[
                ConfigField(
                    key="jwt_secret_key",
                    label="JWT 密钥",
                    type="password",
                    value=settings.jwt_secret_key,
                    description="JWT 签名密钥",
                    placeholder="请输入密钥",
                    required=True,
                    sensitive=True
                ),
                ConfigField(
                    key="jwt_algorithm",
                    label="JWT 算法",
                    type="select",
                    value=settings.jwt_algorithm,
                    description="JWT 签名算法",
                    options=[
                        {"value": "HS256", "label": "HS256"},
                        {"value": "HS384", "label": "HS384"},
                        {"value": "HS512", "label": "HS512"}
                    ]
                ),
                ConfigField(
                    key="jwt_expire_minutes",
                    label="Token 有效期 (分钟)",
                    type="number",
                    value=settings.jwt_expire_minutes,
                    description="JWT Token 有效期（分钟）",
                    min_value=1,
                    max_value=10080
                )
            ]
        ),
        ConfigGroup(
            id="system",
            title="系统配置",
            icon="🔧",
            description="配置系统级参数",
            fields=[
                ConfigField(
                    key="log_level",
                    label="日志级别",
                    type="select",
                    value=settings.log_level,
                    description="应用程序日志级别",
                    options=[
                        {"value": "DEBUG", "label": "DEBUG"},
                        {"value": "INFO", "label": "INFO"},
                        {"value": "WARNING", "label": "WARNING"},
                        {"value": "ERROR", "label": "ERROR"}
                    ]
                ),
                ConfigField(
                    key="debug",
                    label="调试模式",
                    type="boolean",
                    value=settings.debug,
                    description="启用调试模式"
                ),
                ConfigField(
                    key="memory_file_path",
                    label="记忆文件路径",
                    type="text",
                    value=settings.memory_file_path,
                    description="AI 记忆文件存储路径",
                    placeholder="MEMORY.md"
                )
            ]
        )
    ]
    
    return groups


@router.get("/config", response_model=ConfigResponse)
async def get_config(
    admin: dict = Depends(verify_admin_token)
):
    """Get all configuration settings"""
    
    groups = get_config_groups()
    
    return ConfigResponse(
        groups=groups,
        last_updated=None
    )


@router.post("/config/test", response_model=ConfigTestResult)
async def test_config(
    request: ConfigUpdateRequest,
    admin: dict = Depends(verify_admin_token)
):
    """Test a specific configuration setting"""
    
    key = request.key
    value = request.value
    
    try:
        if key == "qianfan_api_key":
            client = QianfanClient(api_key=value)
            healthy = await client.health_check()
            return ConfigTestResult(
                service="百度千帆 AI",
                status="success" if healthy else "error",
                message="连接成功" if healthy else "连接失败",
                details={"api_key_configured": bool(value)}
            )
        
        elif key in ["postgres_host", "postgres_port", "postgres_db", "postgres_user", "postgres_password"]:
            import asyncpg
            try:
                conn = await asyncpg.connect(
                    host=settings.postgres_host if key != "postgres_host" else value,
                    port=settings.postgres_port if key != "postgres_port" else value,
                    database=settings.postgres_db if key != "postgres_db" else value,
                    user=settings.postgres_user if key != "postgres_user" else value,
                    password=settings.postgres_password if key != "postgres_password" else value,
                    timeout=5
                )
                await conn.close()
                return ConfigTestResult(
                    service="PostgreSQL",
                    status="success",
                    message="数据库连接成功",
                    details={"connected": True}
                )
            except Exception as e:
                return ConfigTestResult(
                    service="PostgreSQL",
                    status="error",
                    message=f"数据库连接失败：{str(e)}",
                    details={"connected": False}
                )
        
        elif key in ["redis_host", "redis_port", "redis_password"]:
            import redis.asyncio as redis
            try:
                r = redis.Redis(
                    host=settings.redis_host if key != "redis_host" else value,
                    port=settings.redis_port if key != "redis_port" else value,
                    password=settings.redis_password if key != "redis_password" else value,
                    socket_timeout=5
                )
                await r.ping()
                await r.close()
                return ConfigTestResult(
                    service="Redis",
                    status="success",
                    message="Redis 连接成功",
                    details={"connected": True}
                )
            except Exception as e:
                return ConfigTestResult(
                    service="Redis",
                    status="error",
                    message=f"Redis 连接失败：{str(e)}",
                    details={"connected": False}
                )
        
        elif key in ["qdrant_host", "qdrant_port"]:
            from qdrant_client import QdrantClient
            try:
                client = QdrantClient(
                    host=settings.qdrant_host if key != "qdrant_host" else value,
                    port=settings.qdrant_port if key != "qdrant_port" else value,
                    timeout=5
                )
                await client.get_collections()
                return ConfigTestResult(
                    service="Qdrant",
                    status="success",
                    message="Qdrant 连接成功",
                    details={"connected": True}
                )
            except Exception as e:
                return ConfigTestResult(
                    service="Qdrant",
                    status="error",
                    message=f"Qdrant 连接失败：{str(e)}",
                    details={"connected": False}
                )
        
        elif key in ["n8n_host", "n8n_port"]:
            try:
                host = settings.n8n_host if key != "n8n_host" else value
                port = settings.n8n_port if key != "n8n_port" else value
                async with httpx.AsyncClient(timeout=5) as client:
                    response = await client.get(f"http://{host}:{port}/health")
                    healthy = response.status_code == 200
                    return ConfigTestResult(
                        service="n8n",
                        status="success" if healthy else "error",
                        message="n8n 服务正常" if healthy else "n8n 服务异常",
                        details={"healthy": healthy}
                    )
            except Exception as e:
                return ConfigTestResult(
                    service="n8n",
                    status="error",
                    message=f"n8n 服务不可达：{str(e)}",
                    details={"healthy": False}
                )
        
        else:
            return ConfigTestResult(
                service="未知服务",
                status="warning",
                message=f"不支持测试配置项：{key}",
                details={"key": key}
            )
    
    except Exception as e:
        return ConfigTestResult(
            service="测试失败",
            status="error",
            message=f"测试过程中出错：{str(e)}",
            details={"error": str(e)}
        )


@router.post("/config/save", response_model=ConfigSaveResponse)
async def save_config(
    request: ConfigUpdateRequest,
    admin: dict = Depends(verify_admin_token)
):
    """Save a configuration setting"""
    
    key = request.key
    value = request.value
    
    try:
        valid_keys = [
            "qianfan_api_key", "qianfan_base_url", "qianfan_default_model",
            "postgres_host", "postgres_port", "postgres_db", "postgres_user", "postgres_password",
            "redis_host", "redis_port", "redis_password",
            "qdrant_host", "qdrant_port",
            "n8n_host", "n8n_port",
            "jwt_secret_key", "jwt_algorithm", "jwt_expire_minutes",
            "log_level", "debug", "memory_file_path"
        ]
        
        if key not in valid_keys:
            raise HTTPException(status_code=400, detail=f"无效的配置项：{key}")
        
        env_file_path = ".env"
        
        env_lines = []
        try:
            with open(env_file_path, "r", encoding="utf-8") as f:
                env_lines = f.readlines()
        except FileNotFoundError:
            pass
        
        updated = False
        new_lines = []
        for line in env_lines:
            if line.strip().startswith(f"{key.upper()}="):
                new_lines.append(f"{key.upper()}={value}\n")
                updated = True
            else:
                new_lines.append(line)
        
        if not updated:
            new_lines.append(f"{key.upper()}={value}\n")
        
        with open(env_file_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        
        get_settings.cache_clear()
        new_settings = get_settings()
        
        requires_restart = key in [
            "postgres_host", "postgres_port", "postgres_db", "postgres_user", "postgres_password",
            "redis_host", "redis_port", "redis_password",
            "qdrant_host", "qdrant_port",
            "n8n_host", "n8n_port",
            "jwt_secret_key", "jwt_algorithm",
            "log_level"
        ]
        
        message = "配置已保存"
        if requires_restart:
            message += "，需要重启服务后生效"
        
        logger.info(f"Configuration updated: {key}={value}")
        
        return ConfigSaveResponse(
            success=True,
            message=message,
            requires_restart=requires_restart
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save configuration: {e}")
        raise HTTPException(status_code=500, detail=f"保存配置失败：{str(e)}")


@router.get("/config/status")
async def get_config_status():
    """Get configuration status without authentication"""
    
    status = {
        "qianfan_configured": bool(settings.qianfan_api_key),
        "postgres_configured": bool(settings.postgres_host and settings.postgres_db),
        "redis_configured": bool(settings.redis_host),
        "qdrant_configured": bool(settings.qdrant_host),
        "n8n_configured": bool(settings.n8n_host),
        "debug_mode": settings.debug,
        "app_version": settings.app_version
    }
    
    return status
