"""
AgentForge Audit Workflow API
AI内容审核工作流后端接口
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Depends
from loguru import logger

from agentforge.security.auth import get_current_user


router = APIRouter(prefix="/api/audit", tags=["audit"])


class AuditType(str, Enum):
    SOCIAL_POST = "social_post"
    MESSAGE_REPLY = "message_reply"
    CONTENT_CREATION = "content_creation"
    QUOTATION = "quotation"


class AuditStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"


class AuditItem(BaseModel):
    id: str
    type: AuditType
    platform: Optional[str] = None
    content: str
    original_content: Optional[str] = None
    generated_at: datetime = Field(default_factory=datetime.now)
    status: AuditStatus = AuditStatus.PENDING
    confidence: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    rejection_reason: Optional[str] = None


class AuditStats(BaseModel):
    pending: int = 0
    approved: int = 0
    rejected: int = 0
    today_total: int = 0


class AuditSettings(BaseModel):
    auto_approve_threshold: float = 0.9
    enable_auto_approve: bool = False
    notify_channels: List[str] = Field(default_factory=lambda: ["telegram", "email"])
    review_timeout: int = 24


_audit_items: Dict[str, AuditItem] = {}
_audit_settings = AuditSettings()


def _generate_id() -> str:
    import secrets
    return secrets.token_hex(8)


@router.get("/items", response_model=Dict[str, Any])
async def get_audit_items(
    status: Optional[str] = "pending",
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    items = list(_audit_items.values())
    
    if status and status != "all":
        items = [i for i in items if i.status == status]
    
    items.sort(key=lambda x: x.generated_at, reverse=True)
    
    total = len(items)
    items = items[offset:offset + limit]
    
    stats = AuditStats(
        pending=len([i for i in _audit_items.values() if i.status == AuditStatus.PENDING]),
        approved=len([i for i in _audit_items.values() if i.status == AuditStatus.APPROVED]),
        rejected=len([i for i in _audit_items.values() if i.status == AuditStatus.REJECTED]),
        today_total=len([i for i in _audit_items.values() if i.generated_at.date() == datetime.now().date()])
    )
    
    return {
        "items": [i.model_dump() for i in items],
        "total": total,
        "stats": stats.model_dump()
    }


@router.get("/history", response_model=Dict[str, Any])
async def get_audit_history(
    limit: int = 20,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    items = [i for i in _audit_items.values() if i.status != AuditStatus.PENDING]
    items.sort(key=lambda x: x.reviewed_at or x.generated_at, reverse=True)
    
    total = len(items)
    items = items[offset:offset + limit]
    
    return {
        "items": [i.model_dump() for i in items],
        "total": total
    }


@router.post("/submit", response_model=AuditItem)
async def submit_for_audit(
    type: AuditType,
    content: str,
    platform: Optional[str] = None,
    original_content: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    confidence: float = 0.0,
    current_user: dict = Depends(get_current_user)
) -> AuditItem:
    item = AuditItem(
        id=_generate_id(),
        type=type,
        platform=platform,
        content=content,
        original_content=original_content,
        confidence=confidence,
        metadata=metadata or {}
    )
    
    if _audit_settings.enable_auto_approve and confidence >= _audit_settings.auto_approve_threshold:
        item.status = AuditStatus.APPROVED
        item.reviewed_at = datetime.now()
        item.reviewed_by = "auto"
        logger.info(f"Auto-approved audit item {item.id} with confidence {confidence}")
    else:
        await _send_audit_notification(item)
    
    _audit_items[item.id] = item
    logger.info(f"Submitted audit item {item.id} of type {type}")
    
    return item


@router.post("/{item_id}/approve", response_model=AuditItem)
async def approve_item(
    item_id: str,
    current_user: dict = Depends(get_current_user)
) -> AuditItem:
    if item_id not in _audit_items:
        raise HTTPException(status_code=404, detail="Audit item not found")
    
    item = _audit_items[item_id]
    item.status = AuditStatus.APPROVED
    item.reviewed_at = datetime.now()
    item.reviewed_by = current_user.get("user_id", "unknown")
    
    await _execute_approved_action(item)
    
    logger.info(f"Approved audit item {item_id}")
    return item


@router.post("/{item_id}/reject", response_model=AuditItem)
async def reject_item(
    item_id: str,
    reason: str,
    current_user: dict = Depends(get_current_user)
) -> AuditItem:
    if item_id not in _audit_items:
        raise HTTPException(status_code=404, detail="Audit item not found")
    
    item = _audit_items[item_id]
    item.status = AuditStatus.REJECTED
    item.reviewed_at = datetime.now()
    item.reviewed_by = current_user.get("user_id", "unknown")
    item.rejection_reason = reason
    
    await _record_rejection_for_learning(item)
    
    logger.info(f"Rejected audit item {item_id}: {reason}")
    return item


@router.post("/{item_id}/modify", response_model=AuditItem)
async def modify_item(
    item_id: str,
    content: str,
    current_user: dict = Depends(get_current_user)
) -> AuditItem:
    if item_id not in _audit_items:
        raise HTTPException(status_code=404, detail="Audit item not found")
    
    item = _audit_items[item_id]
    item.content = content
    item.status = AuditStatus.MODIFIED
    item.reviewed_at = datetime.now()
    item.reviewed_by = current_user.get("user_id", "unknown")
    
    await _execute_approved_action(item)
    
    logger.info(f"Modified and approved audit item {item_id}")
    return item


@router.post("/{item_id}/regenerate", response_model=AuditItem)
async def regenerate_item(
    item_id: str,
    current_user: dict = Depends(get_current_user)
) -> AuditItem:
    if item_id not in _audit_items:
        raise HTTPException(status_code=404, detail="Audit item not found")
    
    item = _audit_items[item_id]
    
    new_content = await _regenerate_content(item)
    item.content = new_content
    item.confidence = 0.0
    
    logger.info(f"Regenerated content for audit item {item_id}")
    return item


@router.get("/settings", response_model=AuditSettings)
async def get_settings(
    current_user: dict = Depends(get_current_user)
) -> AuditSettings:
    return _audit_settings


@router.post("/settings", response_model=AuditSettings)
async def update_settings(
    settings: AuditSettings,
    current_user: dict = Depends(get_current_user)
) -> AuditSettings:
    global _audit_settings
    _audit_settings = settings
    logger.info(f"Updated audit settings: {settings}")
    return _audit_settings


@router.get("/stats", response_model=AuditStats)
async def get_stats(
    current_user: dict = Depends(get_current_user)
) -> AuditStats:
    return AuditStats(
        pending=len([i for i in _audit_items.values() if i.status == AuditStatus.PENDING]),
        approved=len([i for i in _audit_items.values() if i.status == AuditStatus.APPROVED]),
        rejected=len([i for i in _audit_items.values() if i.status == AuditStatus.REJECTED]),
        today_total=len([i for i in _audit_items.values() if i.generated_at.date() == datetime.now().date())
    )


async def _send_audit_notification(item: AuditItem):
    from integrations.events.notification import NotificationService
    
    notification = NotificationService()
    
    message = f"📋 新内容待审核\n\n类型: {item.type.value}\n内容预览: {item.content[:100]}..."
    
    for channel in _audit_settings.notify_channels:
        try:
            if channel == "telegram":
                await notification.send_telegram(message)
            elif channel == "email":
                await notification.send_email(
                    subject="AgentForge - 新内容待审核",
                    body=message
                )
        except Exception as e:
            logger.error(f"Failed to send notification via {channel}: {e}")


async def _execute_approved_action(item: AuditItem):
    if item.type == AuditType.SOCIAL_POST:
        from integrations.external.social_client import SocialMediaClient
        client = SocialMediaClient()
        if item.platform:
            await client.post_to_platform(
                platform=item.platform,
                content=item.content,
                **item.metadata
            )
    
    elif item.type == AuditType.MESSAGE_REPLY:
        from integrations.external.fiverr_client import FiverrClient
        client = FiverrClient()
        order_id = item.metadata.get("order_id")
        if order_id:
            await client.send_message(order_id, item.content)
    
    elif item.type == AuditType.QUOTATION:
        from integrations.external.fiverr_client import FiverrClient
        client = FiverrClient()
        await client.submit_quote(**item.metadata)
    
    logger.info(f"Executed approved action for {item.type}")


async def _record_rejection_for_learning(item: AuditItem):
    from agentforge.core.self_evolution import SelfEvolutionEngine
    
    engine = SelfEvolutionEngine()
    await engine.record_feedback(
        task_type=item.type.value,
        content=item.content,
        feedback="rejected",
        reason=item.rejection_reason,
        metadata=item.metadata
    )
    
    logger.info(f"Recorded rejection for learning: {item.id}")


async def _regenerate_content(item: AuditItem) -> str:
    from agentforge.llm.model_router import ModelRouter
    
    router = ModelRouter()
    
    if item.type == AuditType.SOCIAL_POST:
        prompt = f"请重新生成一条社交媒体帖子，主题是: {item.original_content or item.metadata.get('topic', '')}"
    elif item.type == AuditType.MESSAGE_REPLY:
        prompt = f"请重新生成一条客户回复，原始消息: {item.original_content or ''}"
    elif item.type == AuditType.CONTENT_CREATION:
        prompt = f"请重新创作内容，主题: {item.metadata.get('topic', '')}"
    else:
        prompt = f"请重新生成: {item.original_content or item.content[:100]}"
    
    response = await router.generate(prompt)
    return response.content


def init_sample_data():
    sample_items = [
        AuditItem(
            id=_generate_id(),
            type=AuditType.SOCIAL_POST,
            platform="twitter",
            content="🚀 今天完成了一个令人兴奋的项目！使用AI技术帮助客户实现了业务自动化，效率提升了200%。#AI #自动化 #效率提升",
            original_content="分享项目成功案例",
            confidence=0.85,
            metadata={"hashtags": ["AI", "自动化", "效率提升"]}
        ),
        AuditItem(
            id=_generate_id(),
            type=AuditType.MESSAGE_REPLY,
            content="感谢您的咨询！我很乐意帮助您完成这个项目。根据您的需求，我预计需要3-5个工作日完成。如果您有任何问题，随时可以联系我。",
            original_content="客户询问项目时间和意向",
            confidence=0.92,
            metadata={"order_id": "sample_order_123"}
        ),
        AuditItem(
            id=_generate_id(),
            type=AuditType.QUOTATION,
            content="项目报价建议：\n- 基础功能开发：$200\n- 高级功能定制：$150\n- 测试和优化：$50\n总计：$400\n交付时间：5个工作日",
            confidence=0.88,
            metadata={"service_type": "web_development", "complexity": "medium"}
        ),
        AuditItem(
            id=_generate_id(),
            type=AuditType.CONTENT_CREATION,
            content="在当今数字化时代，AI正在重塑我们的工作方式。从自动化日常任务到提供智能决策支持，AI已经成为提升效率的关键工具。本文将探讨如何利用AI技术优化您的工作流程...",
            original_content="写一篇关于AI提升工作效率的文章",
            confidence=0.75,
            metadata={"topic": "AI效率提升", "word_count": 500}
        )
    ]
    
    for item in sample_items:
        _audit_items[item.id] = item


init_sample_data()
