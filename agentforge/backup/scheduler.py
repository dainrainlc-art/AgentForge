"""
Backup Scheduler - Automated backup scheduling
"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from loguru import logger
import asyncio

from agentforge.backup.backup_manager import DatabaseBackup, BackupMetadata, BackupType
from agentforge.backup.restore_manager import DatabaseRestore, RestoreResult
from integrations.events.notification import notification_service


class ScheduleConfig(BaseModel):
    """Backup schedule configuration"""
    daily_enabled: bool = True
    daily_time: str = "02:00"
    
    weekly_enabled: bool = True
    weekly_day: int = 0
    weekly_time: str = "03:00"
    
    monthly_enabled: bool = True
    monthly_day: int = 1
    monthly_time: str = "04:00"
    
    incremental_enabled: bool = False
    incremental_interval_hours: int = 6
    
    retention_check_enabled: bool = True
    retention_check_time: str = "05:00"
    
    notification_on_success: bool = True
    notification_on_failure: bool = True


class BackupScheduler:
    """Automated backup scheduler"""
    
    def __init__(
        self,
        backup_manager: Optional[DatabaseBackup] = None,
        restore_manager: Optional[DatabaseRestore] = None,
        schedule_config: Optional[ScheduleConfig] = None
    ):
        self.backup_manager = backup_manager or DatabaseBackup()
        self.restore_manager = restore_manager or DatabaseRestore()
        self.schedule_config = schedule_config or ScheduleConfig()
        
        self._running = False
        self._scheduler_task: Optional[asyncio.Task] = None
        self._last_backup: Optional[datetime] = None
        self._backup_history: list = []
    
    async def start(self) -> None:
        """Start the backup scheduler"""
        if self._running:
            logger.warning("Backup scheduler already running")
            return
        
        self._running = True
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Backup scheduler started")
    
    async def stop(self) -> None:
        """Stop the backup scheduler"""
        self._running = False
        
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Backup scheduler stopped")
    
    async def _scheduler_loop(self) -> None:
        """Main scheduler loop"""
        while self._running:
            try:
                now = datetime.now()
                
                if self.schedule_config.daily_enabled:
                    await self._check_daily_backup(now)
                
                if self.schedule_config.weekly_enabled:
                    await self._check_weekly_backup(now)
                
                if self.schedule_config.monthly_enabled:
                    await self._check_monthly_backup(now)
                
                if self.schedule_config.retention_check_enabled:
                    await self._check_retention(now)
                
                await asyncio.sleep(60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                await asyncio.sleep(60)
    
    async def _check_daily_backup(self, now: datetime) -> None:
        """Check if daily backup should run"""
        target_time = datetime.strptime(self.schedule_config.daily_time, "%H:%M")
        target_hour = target_time.hour
        target_minute = target_time.minute
        
        if now.hour == target_hour and now.minute == target_minute:
            if self._last_backup and (now - self._last_backup).total_seconds() < 3600:
                return
            
            logger.info("Starting scheduled daily backup")
            await self.run_backup(BackupType.FULL)
    
    async def _check_weekly_backup(self, now: datetime) -> None:
        """Check if weekly backup should run"""
        if now.weekday() != self.schedule_config.weekly_day:
            return
        
        target_time = datetime.strptime(self.schedule_config.weekly_time, "%H:%M")
        target_hour = target_time.hour
        target_minute = target_time.minute
        
        if now.hour == target_hour and now.minute == target_minute:
            if self._last_backup and (now - self._last_backup).total_seconds() < 3600:
                return
            
            logger.info("Starting scheduled weekly backup")
            await self.run_backup(BackupType.FULL)
    
    async def _check_monthly_backup(self, now: datetime) -> None:
        """Check if monthly backup should run"""
        if now.day != self.schedule_config.monthly_day:
            return
        
        target_time = datetime.strptime(self.schedule_config.monthly_time, "%H:%M")
        target_hour = target_time.hour
        target_minute = target_time.minute
        
        if now.hour == target_hour and now.minute == target_minute:
            if self._last_backup and (now - self._last_backup).total_seconds() < 3600:
                return
            
            logger.info("Starting scheduled monthly backup")
            await self.run_backup(BackupType.FULL)
    
    async def _check_retention(self, now: datetime) -> None:
        """Check if retention policy should be applied"""
        target_time = datetime.strptime(self.schedule_config.retention_check_time, "%H:%M")
        target_hour = target_time.hour
        target_minute = target_time.minute
        
        if now.hour == target_hour and now.minute == target_minute:
            logger.info("Applying retention policy")
            deleted = self.backup_manager.apply_retention_policy()
            logger.info(f"Retention policy deleted {sum(deleted.values())} old backups")
    
    async def run_backup(
        self,
        backup_type: str = BackupType.FULL,
        include_postgres: bool = True,
        include_redis: bool = True,
        include_qdrant: bool = True
    ) -> BackupMetadata:
        """Run a backup manually"""
        
        metadata = await self.backup_manager.create_backup(
            backup_type=backup_type,
            include_postgres=include_postgres,
            include_redis=include_redis,
            include_qdrant=include_qdrant
        )
        
        self._last_backup = datetime.now()
        self._backup_history.append(metadata.model_dump())
        
        if self.schedule_config.notification_on_success and metadata.status == "success":
            await self._send_success_notification(metadata)
        elif self.schedule_config.notification_on_failure and metadata.status == "failed":
            await self._send_failure_notification(metadata)
        
        return metadata
    
    async def run_restore(
        self,
        backup_id: str,
        include_postgres: bool = True,
        include_redis: bool = True,
        include_qdrant: bool = True,
        drop_existing: bool = False
    ) -> RestoreResult:
        """Run a restore manually"""
        
        logger.warning(f"Starting restore from backup: {backup_id}")
        
        result = await self.restore_manager.restore(
            backup_id=backup_id,
            include_postgres=include_postgres,
            include_redis=include_redis,
            include_qdrant=include_qdrant,
            drop_existing=drop_existing
        )
        
        await self._send_restore_notification(result)
        
        return result
    
    async def _send_success_notification(self, metadata: BackupMetadata) -> None:
        """Send backup success notification"""
        try:
            await notification_service.send_notification(
                type="backup",
                title="Backup Completed",
                message=f"Backup {metadata.id} completed successfully. Size: {metadata.size_bytes} bytes",
                priority="normal",
                channels=["desktop"]
            )
        except Exception as e:
            logger.error(f"Failed to send success notification: {e}")
    
    async def _send_failure_notification(self, metadata: BackupMetadata) -> None:
        """Send backup failure notification"""
        try:
            await notification_service.send_notification(
                type="alert",
                title="Backup Failed",
                message=f"Backup {metadata.id} failed: {metadata.error_message}",
                priority="urgent",
                channels=["desktop", "telegram"]
            )
        except Exception as e:
            logger.error(f"Failed to send failure notification: {e}")
    
    async def _send_restore_notification(self, result: RestoreResult) -> None:
        """Send restore notification"""
        try:
            priority = "normal" if result.status == "success" else "urgent"
            await notification_service.send_notification(
                type="backup",
                title=f"Restore {result.status.title()}",
                message=f"Restore from {result.backup_id}: {result.status}",
                priority=priority,
                channels=["desktop", "telegram"]
            )
        except Exception as e:
            logger.error(f"Failed to send restore notification: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status"""
        return {
            "running": self._running,
            "last_backup": self._last_backup.isoformat() if self._last_backup else None,
            "schedule_config": self.schedule_config.model_dump(),
            "backup_stats": self.backup_manager.get_backup_stats()
        }
    
    def list_available_backups(self) -> list:
        """List all available backups"""
        return [b.model_dump() for b in self.backup_manager.list_backups()]


backup_scheduler = BackupScheduler()
