"""AI 技能市场 - 技能管理 API."""

from typing import Any

from fastapi import APIRouter, HTTPException

from agentforge.core.schemas.skill_schema import SkillDefinition
from agentforge.core.skill_manager import SkillManager
from agentforge.core.trigger_system import TriggerSystem

router = APIRouter(prefix="/skills", tags=["skills"])

# 全局技能管理器实例
_skill_manager: SkillManager | None = None
_trigger_system: TriggerSystem | None = None


def get_skill_manager() -> SkillManager:
    """获取技能管理器."""
    if _skill_manager is None:
        raise HTTPException(status_code=500, detail="技能管理器未初始化")
    return _skill_manager


def get_trigger_system() -> TriggerSystem:
    """获取触发器系统."""
    if _trigger_system is None:
        raise HTTPException(status_code=500, detail="触发器系统未初始化")
    return _trigger_system


async def initialize_skill_api(skill_manager: SkillManager, trigger_system: TriggerSystem):
    """初始化技能 API."""
    global _skill_manager, _trigger_system
    _skill_manager = skill_manager
    _trigger_system = trigger_system
    await skill_manager.initialize()
    await trigger_system.start()


@router.get("", summary="获取技能列表")
async def list_skills(
    tag: str | None = None,
    enabled: bool | None = None,
):
    """获取技能列表."""
    manager = get_skill_manager()
    skills = manager.list_skills(tag=tag, enabled=enabled)

    return {
        "count": len(skills),
        "skills": [skill.model_dump() for skill in skills],
    }


@router.get("/{skill_name}", summary="获取技能详情")
async def get_skill(skill_name: str):
    """获取技能详情."""
    manager = get_skill_manager()
    skill = manager.get_skill(skill_name)

    if not skill:
        raise HTTPException(status_code=404, detail=f"技能不存在：{skill_name}")

    return skill.model_dump()


@router.post("", summary="创建技能")
async def create_skill(skill_data: SkillDefinition):
    """创建新技能."""
    manager = get_skill_manager()

    # 检查技能是否已存在
    if manager.get_skill(skill_data.name):
        raise HTTPException(status_code=400, detail=f"技能已存在：{skill_data.name}")

    manager.register_skill(skill_data, save=True)

    return {
        "success": True,
        "message": f"技能已创建：{skill_data.name}",
        "skill": skill_data.model_dump(),
    }


@router.put("/{skill_name}", summary="更新技能")
async def update_skill(skill_name: str, skill_data: SkillDefinition):
    """更新技能."""
    manager = get_skill_manager()

    # 检查技能是否存在
    existing_skill = manager.get_skill(skill_name)
    if not existing_skill:
        raise HTTPException(status_code=404, detail=f"技能不存在：{skill_name}")

    # 注销旧技能
    manager.unregister_skill(skill_name, delete=False)

    # 注册新技能
    manager.register_skill(skill_data, save=True)

    return {
        "success": True,
        "message": f"技能已更新：{skill_data.name}",
        "skill": skill_data.model_dump(),
    }


@router.delete("/{skill_name}", summary="删除技能")
async def delete_skill(skill_name: str):
    """删除技能."""
    manager = get_skill_manager()

    success = manager.unregister_skill(skill_name, delete=True)
    if not success:
        raise HTTPException(status_code=404, detail=f"技能不存在：{skill_name}")

    return {
        "success": True,
        "message": f"技能已删除：{skill_name}",
    }


@router.post("/{skill_name}/enable", summary="启用技能")
async def enable_skill(skill_name: str):
    """启用技能."""
    manager = get_skill_manager()
    skill = manager.get_skill(skill_name)

    if not skill:
        raise HTTPException(status_code=404, detail=f"技能不存在：{skill_name}")

    skill.enabled = True
    manager.register_skill(skill, save=True)

    return {
        "success": True,
        "message": f"技能已启用：{skill_name}",
    }


@router.post("/{skill_name}/disable", summary="禁用技能")
async def disable_skill(skill_name: str):
    """禁用技能."""
    manager = get_skill_manager()
    skill = manager.get_skill(skill_name)

    if not skill:
        raise HTTPException(status_code=404, detail=f"技能不存在：{skill_name}")

    skill.enabled = False
    manager.register_skill(skill, save=True)

    return {
        "success": True,
        "message": f"技能已禁用：{skill_name}",
    }


@router.post("/{skill_name}/trigger", summary="手动触发技能")
async def trigger_skill(skill_name: str, variables: dict[str, Any] | None = None):
    """手动触发技能."""
    trigger_system = get_trigger_system()

    result = await trigger_system.trigger_manual(skill_name, variables)

    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "触发失败"),
        )

    return result


@router.get("/events/types", summary="获取事件类型列表")
async def get_event_types():
    """获取所有事件类型."""
    manager = get_skill_manager()
    event_types = manager.get_event_types()

    return {
        "count": len(event_types),
        "event_types": event_types,
    }


@router.get("/events/{event_type}", summary="获取事件相关的技能")
async def get_skills_by_event(event_type: str):
    """获取监听指定事件的技能列表."""
    manager = get_skill_manager()
    skills = manager.get_skills_by_event(event_type)

    return {
        "count": len(skills),
        "event_type": event_type,
        "skills": [skill.model_dump() for skill in skills],
    }


@router.get("/running", summary="获取运行中的技能")
async def get_running_skills():
    """获取正在运行的技能列表."""
    # 注意：需要从 SkillEngine 获取
    return {
        "running_skills": [],
    }
