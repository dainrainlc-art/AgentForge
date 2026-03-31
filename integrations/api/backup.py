"""
Backup API - Backup and restore endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional
from loguru import logger

from integrations.api.auth import verify_token_dependency
from agentforge.backup import backup_scheduler, database_backup, database_restore


router = APIRouter()


class BackupRequest(BaseModel):
    backup_type: str = "full"
    include_postgres: bool = True
    include_redis: bool = True
    include_qdrant: bool = True


class RestoreRequest(BaseModel):
    backup_id: str
    include_postgres: bool = True
    include_redis: bool = True
    include_qdrant: bool = True
    drop_existing: bool = False


class ScheduleUpdateRequest(BaseModel):
    daily_enabled: Optional[bool] = None
    daily_time: Optional[str] = None
    weekly_enabled: Optional[bool] = None
    weekly_day: Optional[int] = None
    retention_days: Optional[int] = None


@router.get("/status")
async def get_backup_status(payload: dict = Depends(verify_token_dependency)):
    """Get backup scheduler status"""
    return backup_scheduler.get_status()


@router.post("/create")
async def create_backup(request: BackupRequest, payload: dict = Depends(verify_token_dependency)):
    """Create a new backup"""
    try:
        metadata = await backup_scheduler.run_backup(
            backup_type=request.backup_type,
            include_postgres=request.include_postgres,
            include_redis=request.include_redis,
            include_qdrant=request.include_qdrant
        )
        return {"success": metadata.status == "success", "backup": metadata.model_dump()}
    except Exception as e:
        logger.error(f"Backup creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restore")
async def restore_backup(request: RestoreRequest, payload: dict = Depends(verify_token_dependency)):
    """Restore from a backup"""
    try:
        result = await backup_scheduler.run_restore(
            backup_id=request.backup_id,
            include_postgres=request.include_postgres,
            include_redis=request.include_redis,
            include_qdrant=request.include_qdrant,
            drop_existing=request.drop_existing
        )
        return {"success": result.status == "success", "result": result.model_dump()}
    except Exception as e:
        logger.error(f"Restore failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_backups(limit: int = Query(20, ge=1, le=100), payload: dict = Depends(verify_token_dependency)):
    """List available backups"""
    backups = backup_scheduler.list_available_backups()
    return {"total": len(backups), "backups": backups[:limit]}


@router.get("/{backup_id}")
async def get_backup(backup_id: str, payload: dict = Depends(verify_token_dependency)):
    """Get backup details"""
    backup = database_backup.get_backup(backup_id)
    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")
    return backup.model_dump()


@router.delete("/{backup_id}")
async def delete_backup(backup_id: str, payload: dict = Depends(verify_token_dependency)):
    """Delete a backup"""
    result = database_backup.delete_backup(backup_id)
    if not result:
        raise HTTPException(status_code=404, detail="Backup not found")
    return {"success": True, "message": f"Backup {backup_id} deleted"}


@router.get("/{backup_id}/verify")
async def verify_backup(backup_id: str, payload: dict = Depends(verify_token_dependency)):
    """Verify backup integrity"""
    return database_restore.verify_backup(backup_id)


@router.post("/retention/apply")
async def apply_retention_policy(payload: dict = Depends(verify_token_dependency)):
    """Apply retention policy"""
    deleted = database_backup.apply_retention_policy()
    return {"success": True, "deleted": deleted, "total_deleted": sum(deleted.values())}


@router.get("/stats/summary")
async def get_backup_stats(payload: dict = Depends(verify_token_dependency)):
    """Get backup statistics"""
    return database_backup.get_backup_stats()


@router.put("/schedule")
async def update_schedule(request: ScheduleUpdateRequest, payload: dict = Depends(verify_token_dependency)):
    """Update backup schedule configuration"""
    config = backup_scheduler.schedule_config
    
    if request.daily_enabled is not None:
        config.daily_enabled = request.daily_enabled
    if request.daily_time is not None:
        config.daily_time = request.daily_time
    if request.weekly_enabled is not None:
        config.weekly_enabled = request.weekly_enabled
    if request.weekly_day is not None:
        config.weekly_day = request.weekly_day
    if request.retention_days is not None:
        backup_scheduler.backup_manager.config.retention_days = request.retention_days
    
    return {"success": True, "config": config.model_dump()}
