"""工作流模板市场 - 工作流管理 API."""

from typing import Any

from fastapi import APIRouter, HTTPException

from agentforge.core.schemas.workflow_schema import WorkflowDefinition
from agentforge.core.workflow_manager import WorkflowManager

router = APIRouter(prefix="/workflows", tags=["workflows"])

# 全局工作流管理器实例
_workflow_manager: WorkflowManager | None = None


def get_workflow_manager() -> WorkflowManager:
    """获取工作流管理器."""
    if _workflow_manager is None:
        raise HTTPException(status_code=500, detail="工作流管理器未初始化")
    return _workflow_manager


async def initialize_workflow_api(workflow_manager: WorkflowManager):
    """初始化工作流 API."""
    global _workflow_manager
    _workflow_manager = workflow_manager
    await workflow_manager.initialize()


@router.get("", summary="获取工作流列表")
async def list_workflows(
    tag: str | None = None,
    enabled: bool | None = None,
):
    """获取工作流列表."""
    manager = get_workflow_manager()
    workflows = manager.list_workflows(tag=tag, enabled=enabled)

    return {
        "count": len(workflows),
        "workflows": [workflow.model_dump() for workflow in workflows],
    }


@router.get("/{workflow_name}", summary="获取工作流详情")
async def get_workflow(workflow_name: str):
    """获取工作流详情."""
    manager = get_workflow_manager()
    workflow = manager.get_workflow(workflow_name)

    if not workflow:
        raise HTTPException(status_code=404, detail=f"工作流不存在：{workflow_name}")

    return workflow.model_dump()


@router.post("", summary="创建工作流")
async def create_workflow(workflow_data: WorkflowDefinition):
    """创建工作流."""
    manager = get_workflow_manager()

    # 检查工作流是否已存在
    if manager.get_workflow(workflow_data.name):
        raise HTTPException(status_code=400, detail=f"工作流已存在：{workflow_data.name}")

    manager.register_workflow(workflow_data, save=True)

    return {
        "success": True,
        "message": f"工作流已创建：{workflow_data.name}",
        "workflow": workflow_data.model_dump(),
    }


@router.put("/{workflow_name}", summary="更新工作流")
async def update_workflow(workflow_name: str, workflow_data: WorkflowDefinition):
    """更新工作流."""
    manager = get_workflow_manager()

    # 检查工作流是否存在
    existing_workflow = manager.get_workflow(workflow_name)
    if not existing_workflow:
        raise HTTPException(status_code=404, detail=f"工作流不存在：{workflow_name}")

    # 注销旧工作流
    manager.unregister_workflow(workflow_name, delete=False)

    # 注册新工作流
    manager.register_workflow(workflow_data, save=True)

    return {
        "success": True,
        "message": f"工作流已更新：{workflow_data.name}",
        "workflow": workflow_data.model_dump(),
    }


@router.delete("/{workflow_name}", summary="删除工作流")
async def delete_workflow(workflow_name: str):
    """删除工作流."""
    manager = get_workflow_manager()

    success = manager.unregister_workflow(workflow_name, delete=True)
    if not success:
        raise HTTPException(status_code=404, detail=f"工作流不存在：{workflow_name}")

    return {
        "success": True,
        "message": f"工作流已删除：{workflow_name}",
    }


@router.post("/{workflow_name}/enable", summary="启用工作流")
async def enable_workflow(workflow_name: str):
    """启用工作流."""
    manager = get_workflow_manager()
    workflow = manager.get_workflow(workflow_name)

    if not workflow:
        raise HTTPException(status_code=404, detail=f"工作流不存在：{workflow_name}")

    workflow.enabled = True
    manager.register_workflow(workflow, save=True)

    return {
        "success": True,
        "message": f"工作流已启用：{workflow_name}",
    }


@router.post("/{workflow_name}/disable", summary="禁用工作流")
async def disable_workflow(workflow_name: str):
    """禁用工作流."""
    manager = get_workflow_manager()
    workflow = manager.get_workflow(workflow_name)

    if not workflow:
        raise HTTPException(status_code=404, detail=f"工作流不存在：{workflow_name}")

    workflow.enabled = False
    manager.register_workflow(workflow, save=True)

    return {
        "success": True,
        "message": f"工作流已禁用：{workflow_name}",
    }


@router.post("/{workflow_name}/execute", summary="执行工作流")
async def execute_workflow(workflow_name: str, variables: dict[str, Any] | None = None):
    """执行工作流."""
    manager = get_workflow_manager()

    workflow = manager.get_workflow(workflow_name)
    if not workflow:
        raise HTTPException(status_code=404, detail=f"工作流不存在：{workflow_name}")

    if not workflow.enabled:
        raise HTTPException(status_code=400, detail="工作流已禁用")

    result = await manager.execute_workflow(workflow_name, variables)

    if not result:
        raise HTTPException(status_code=500, detail="工作流执行失败")

    return {
        "success": True,
        "workflow_name": workflow_name,
        "status": result.status,
        "history": result.history,
        "error": result.error,
    }


@router.get("/running", summary="获取运行中的工作流")
async def get_running_workflows():
    """获取正在运行的工作流列表."""
    manager = get_workflow_manager()
    # 需要从 WorkflowEngine 获取
    return {
        "running_workflows": [],
    }
