"""
AgentForge Plugin API
插件系统 API 端点
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from agentforge.plugins import (
    plugin_registry,
    plugin_marketplace,
    PluginType,
    PluginStatus,
    PluginContext,
)

router = APIRouter(prefix="/plugins", tags=["plugins"])


class PluginInstallRequest(BaseModel):
    plugin_id: str
    config: Optional[Dict[str, Any]] = None


class PluginExecuteRequest(BaseModel):
    plugin_id: str
    input_data: Any
    context: Optional[Dict[str, Any]] = None


@router.get("/list")
async def list_plugins(
    type: Optional[str] = None,
    status: Optional[str] = None
) -> List[Dict[str, Any]]:
    """List all installed plugins"""
    plugin_type = PluginType(type) if type else None
    plugin_status = PluginStatus(status) if status else None
    
    return plugin_registry.list_plugins(plugin_type, plugin_status)


@router.get("/marketplace")
async def get_marketplace() -> List[Dict[str, Any]]:
    """Get available plugins from marketplace"""
    return plugin_marketplace.fetch_available_plugins()


@router.get("/info/{plugin_id}")
async def get_plugin_info(plugin_id: str) -> Dict[str, Any]:
    """Get detailed plugin information"""
    info = plugin_registry.get_plugin_info(plugin_id)
    if not info:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return info


@router.post("/install/{plugin_id}")
async def install_plugin(plugin_id: str) -> Dict[str, Any]:
    """Install a plugin from marketplace"""
    success = plugin_marketplace.install_plugin(plugin_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to install plugin")
    
    return {"status": "success", "message": f"Plugin {plugin_id} installed"}


@router.post("/uninstall/{plugin_id}")
async def uninstall_plugin(plugin_id: str) -> Dict[str, Any]:
    """Uninstall a plugin"""
    if plugin_id not in plugin_registry.plugins:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    # Disable first
    await plugin_registry.disable_plugin(plugin_id)
    
    # Uninstall
    success = plugin_registry.uninstall_plugin(plugin_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to uninstall plugin")
    
    return {"status": "success", "message": f"Plugin {plugin_id} uninstalled"}


@router.post("/{plugin_id}/enable")
async def enable_plugin(plugin_id: str) -> Dict[str, Any]:
    """Enable a plugin"""
    if plugin_id not in plugin_registry.plugins:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    result = await plugin_registry.enable_plugin(plugin_id)
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error or "Failed to enable plugin")
    
    return {"status": "success", "message": result.message}


@router.post("/{plugin_id}/disable")
async def disable_plugin(plugin_id: str) -> Dict[str, Any]:
    """Disable a plugin"""
    if plugin_id not in plugin_registry.plugins:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    result = await plugin_registry.disable_plugin(plugin_id)
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error or "Failed to disable plugin")
    
    return {"status": "success", "message": result.message}


@router.post("/execute")
async def execute_plugin(request: PluginExecuteRequest) -> Dict[str, Any]:
    """Execute a plugin"""
    if request.plugin_id not in plugin_registry.plugins:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    context = PluginContext(**request.context) if request.context else None
    
    result = await plugin_registry.execute_plugin(
        request.plugin_id,
        request.input_data,
        context
    )
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error or "Plugin execution failed")
    
    return {
        "status": "success",
        "data": result.data,
        "message": result.message
    }


@router.get("/search")
async def search_plugins(q: str) -> List[Dict[str, Any]]:
    """Search plugins"""
    installed = plugin_registry.search_plugins(q)
    marketplace_results = plugin_marketplace.search_marketplace(q)
    
    return {
        "installed": installed,
        "marketplace": marketplace_results
    }


@router.get("/popular")
async def get_popular_plugins(limit: int = 10) -> List[Dict[str, Any]]:
    """Get popular plugins from marketplace"""
    return plugin_marketplace.get_popular_plugins(limit)


@router.get("/recent")
async def get_recent_plugins(limit: int = 10) -> List[Dict[str, Any]]:
    """Get recently added plugins"""
    return plugin_marketplace.get_recent_plugins(limit)


@router.get("/stats")
async def get_plugin_stats() -> Dict[str, Any]:
    """Get plugin statistics"""
    all_plugins = plugin_registry.list_plugins()
    
    stats = {
        "total_installed": len(all_plugins),
        "active": len([p for p in all_plugins if p["status"] == "active"]),
        "disabled": len([p for p in all_plugins if p["status"] == "inactive"]),
        "by_type": {},
        "marketplace_available": len(plugin_marketplace.fetch_available_plugins())
    }
    
    for plugin in all_plugins:
        plugin_type = plugin["type"]
        if plugin_type not in stats["by_type"]:
            stats["by_type"][plugin_type] = 0
        stats["by_type"][plugin_type] += 1
    
    return stats


@router.post("/reload")
async def reload_plugins() -> Dict[str, Any]:
    """Reload all plugins from directory"""
    plugin_registry._load_plugins_from_dir()
    
    return {
        "status": "success",
        "message": "Plugins reloaded",
        "count": len(plugin_registry.plugins)
    }
