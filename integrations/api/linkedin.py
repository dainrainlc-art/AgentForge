"""
AgentForge LinkedIn Integration API
LinkedIn API 端点
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from loguru import logger

from integrations.external.linkedin_client import LinkedInClient, LinkedInManager
from integrations.external.linkedin_models import (
    Profile, Connection, Post, Job, Company, Analytics,
    Visibility, PaginationParams
)

router = APIRouter(prefix="/api/linkedin", tags=["linkedin"])

# 全局客户端实例
_linkedin_client: Optional[LinkedInClient] = None
_linkedin_manager: Optional[LinkedInManager] = None


def get_linkedin_client() -> LinkedInClient:
    """获取 LinkedIn 客户端实例"""
    global _linkedin_client
    if _linkedin_client is None:
        _linkedin_client = LinkedInClient()
    return _linkedin_client


def get_linkedin_manager() -> LinkedInManager:
    """获取 LinkedIn 管理器实例"""
    global _linkedin_manager
    if _linkedin_manager is None:
        _linkedin_manager = LinkedInManager(get_linkedin_client())
    return _linkedin_manager


class AuthorizationUrlResponse(BaseModel):
    """授权 URL 响应"""
    authorization_url: str
    state: str


class TokenExchangeRequest(BaseModel):
    """令牌交换请求"""
    code: str
    state: str


class TokenExchangeResponse(BaseModel):
    """令牌交换响应"""
    access_token: str
    expires_in: int
    token_type: str = "Bearer"


class PostCreateRequest(BaseModel):
    """创建动态请求"""
    text: str
    visibility: Visibility = Visibility.PUBLIC
    images: List[str] = Field(default_factory=list)
    hashtags: List[str] = Field(default_factory=list)


class PostResponse(BaseModel):
    """动态响应"""
    id: str
    text: str
    visibility: str
    created_at: str
    success: bool


class ConnectionsResponse(BaseModel):
    """人脉列表响应"""
    connections: List[Dict[str, Any]]
    total: int
    start: int
    count: int


class ProfileResponse(BaseModel):
    """个人资料响应"""
    profile: Optional[Dict[str, Any]]
    success: bool


class AnalyticsResponse(BaseModel):
    """分析数据响应"""
    analytics: Optional[Dict[str, Any]]
    period: str
    success: bool


@router.get("/auth/url", response_model=AuthorizationUrlResponse)
async def get_authorization_url():
    """
    获取 LinkedIn 授权 URL
    
    用于启动 OAuth 2.0 授权流程
    
    Returns:
        授权 URL 和状态参数
    """
    import secrets
    
    client = get_linkedin_client()
    
    if not client.client_id:
        raise HTTPException(status_code=500, detail="LinkedIn credentials not configured")
    
    # 生成随机状态参数（防止 CSRF 攻击）
    state = secrets.token_urlsafe(32)
    
    # 存储状态参数（实际应用中应该存储到 Redis 或数据库）
    # await redis.set(f"linkedin_state:{state}", "1", ex=600)
    
    authorization_url = client.get_authorization_url(state)
    
    logger.info(f"Generated LinkedIn authorization URL for state: {state[:8]}...")
    
    return AuthorizationUrlResponse(
        authorization_url=authorization_url,
        state=state
    )


@router.post("/auth/token", response_model=TokenExchangeResponse)
async def exchange_token(request: TokenExchangeRequest):
    """
    用授权码换取访问令牌
    
    Args:
        code: 授权码
        state: 状态参数
        
    Returns:
        访问令牌信息
    """
    client = get_linkedin_client()
    
    # 验证状态参数（防止 CSRF 攻击）
    # stored_state = await redis.get(f"linkedin_state:{request.state}")
    # if not stored_state:
    #     raise HTTPException(status_code=400, detail="Invalid or expired state parameter")
    
    access_token = await client.exchange_code_for_token(request.code)
    
    if not access_token:
        raise HTTPException(status_code=400, detail="Failed to exchange authorization code")
    
    # 删除已使用的状态参数
    # await redis.delete(f"linkedin_state:{request.state}")
    
    logger.info("Successfully exchanged authorization code for access token")
    
    return TokenExchangeResponse(
        access_token=access_token,
        expires_in=3600,  # LinkedIn 令牌默认 1 小时过期
        token_type="Bearer"
    )


@router.get("/profile", response_model=ProfileResponse)
async def get_profile():
    """
    获取个人资料
    
    Returns:
        个人资料信息
    """
    try:
        client = get_linkedin_client()
        profile = await client.get_profile()
        
        if not profile:
            raise HTTPException(status_code=404, detail="Failed to retrieve profile")
        
        logger.info(f"Retrieved LinkedIn profile for: {profile.full_name}")
        
        return ProfileResponse(
            profile=profile.dict(),
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get LinkedIn profile: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve profile: {str(e)}")


@router.get("/connections", response_model=ConnectionsResponse)
async def get_connections(
    start: int = Query(0, ge=0, description="起始位置"),
    count: int = Query(10, ge=1, le=100, description="返回数量")
):
    """
    获取人脉列表
    
    Args:
        start: 起始位置
        count: 返回数量（1-100）
        
    Returns:
        人脉列表
    """
    try:
        client = get_linkedin_client()
        
        pagination = PaginationParams(start=start, count=count)
        connections = await client.get_connections(pagination)
        
        logger.info(f"Retrieved {len(connections)} LinkedIn connections")
        
        return ConnectionsResponse(
            connections=[conn.dict() for conn in connections],
            total=len(connections),
            start=start,
            count=count
        )
        
    except Exception as e:
        logger.error(f"Failed to get LinkedIn connections: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve connections: {str(e)}")


@router.post("/post", response_model=PostResponse)
async def create_post(request: PostCreateRequest):
    """
    创建动态
    
    Args:
        text: 动态内容
        visibility: 可见性
        images: 图片 URL 列表
        hashtags: 话题标签
        
    Returns:
        创建的动态信息
    """
    try:
        client = get_linkedin_client()
        
        post = await client.create_post(
            text=request.text,
            visibility=request.visibility,
            images=request.images,
            hashtags=request.hashtags
        )
        
        if not post:
            raise HTTPException(status_code=500, detail="Failed to create post")
        
        logger.info(f"Created LinkedIn post: {post.id}")
        
        return PostResponse(
            id=post.id,
            text=post.text,
            visibility=post.visibility.value,
            created_at=post.created_at.isoformat(),
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create LinkedIn post: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create post: {str(e)}")


@router.get("/posts")
async def get_posts(
    author_id: Optional[str] = Query(None, description="作者 ID"),
    start: int = Query(0, ge=0, description="起始位置"),
    count: int = Query(10, ge=1, le=100, description="返回数量")
):
    """
    获取动态列表
    
    Args:
        author_id: 作者 ID（不传则为当前用户）
        start: 起始位置
        count: 返回数量（1-100）
        
    Returns:
        动态列表
    """
    try:
        client = get_linkedin_client()
        
        pagination = PaginationParams(start=start, count=count)
        posts = await client.get_posts(author_id=author_id, pagination=pagination)
        
        logger.info(f"Retrieved {len(posts)} LinkedIn posts")
        
        return {
            "posts": [post.dict() for post in posts],
            "total": len(posts),
            "start": start,
            "count": count
        }
        
    except Exception as e:
        logger.error(f"Failed to get LinkedIn posts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve posts: {str(e)}")


@router.delete("/post/{post_id}")
async def delete_post(post_id: str):
    """
    删除动态
    
    Args:
        post_id: 动态 ID
        
    Returns:
        删除结果
    """
    try:
        client = get_linkedin_client()
        
        success = await client.delete_post(post_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete post")
        
        logger.info(f"Deleted LinkedIn post: {post_id}")
        
        return {
            "success": True,
            "post_id": post_id,
            "message": "Post deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete LinkedIn post: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete post: {str(e)}")


@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(
    period: str = Query("last_7_days", description="时间段")
):
    """
    获取分析数据
    
    Args:
        period: 时间段（last_7_days, last_30_days, last_90_days）
        
    Returns:
        分析数据
    """
    try:
        client = get_linkedin_client()
        
        analytics = await client.get_analytics(period)
        
        if not analytics:
            raise HTTPException(status_code=404, detail="Failed to retrieve analytics")
        
        logger.info(f"Retrieved LinkedIn analytics for period: {period}")
        
        return AnalyticsResponse(
            analytics=analytics.dict(),
            period=period,
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get LinkedIn analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve analytics: {str(e)}")


@router.get("/test")
async def test_connection():
    """
    测试 LinkedIn API 连接
    
    Returns:
        测试结果
    """
    try:
        client = get_linkedin_client()
        success = await client.test_connection()
        
        if success:
            logger.info("LinkedIn API connection test successful")
            return {
                "success": True,
                "message": "Successfully connected to LinkedIn API"
            }
        else:
            logger.warning("LinkedIn API connection test failed")
            return {
                "success": False,
                "message": "Failed to connect to LinkedIn API"
            }
            
    except Exception as e:
        logger.error(f"LinkedIn API connection test failed: {e}")
        return {
            "success": False,
            "message": f"Connection test failed: {str(e)}"
        }


@router.post("/sync")
async def sync_profile():
    """
    同步个人资料
    
    Returns:
        同步结果
    """
    try:
        manager = get_linkedin_manager()
        profile = await manager.sync_profile()
        
        if not profile:
            raise HTTPException(status_code=500, detail="Failed to sync profile")
        
        logger.info(f"Synced LinkedIn profile: {profile.full_name}")
        
        return {
            "success": True,
            "profile": profile.dict(),
            "message": "Profile synced successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to sync LinkedIn profile: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to sync profile: {str(e)}")


@router.post("/auto-post")
async def auto_post(
    content: str = Query(..., description="动态内容"),
    hashtags: Optional[str] = Query(None, description="话题标签（逗号分隔）")
):
    """
    自动发布动态
    
    Args:
        content: 动态内容
        hashtags: 话题标签（逗号分隔）
        
    Returns:
        发布结果
    """
    try:
        manager = get_linkedin_manager()
        
        hashtag_list = [tag.strip() for tag in hashtags.split(",")] if hashtags else None
        success = await manager.auto_post(content, hashtags=hashtag_list)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to post")
        
        logger.info("Auto-posted to LinkedIn successfully")
        
        return {
            "success": True,
            "message": "Posted to LinkedIn successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to auto-post to LinkedIn: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to post: {str(e)}")


@router.get("/network/summary")
async def get_network_summary():
    """
    获取人脉网络摘要
    
    Returns:
        网络摘要信息
    """
    try:
        manager = get_linkedin_manager()
        summary = await manager.get_network_summary()
        
        logger.info("Retrieved LinkedIn network summary")
        
        return {
            "success": True,
            "summary": summary
        }
        
    except Exception as e:
        logger.error(f"Failed to get LinkedIn network summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve network summary: {str(e)}")
