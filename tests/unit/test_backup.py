"""
Tests for Backup Module
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, AsyncMock
import os

from agentforge.backup.backup_manager import (
    DatabaseBackup,
    BackupConfig,
    BackupMetadata,
    BackupType,
    BackupStatus
)
from agentforge.backup.restore_manager import (
    DatabaseRestore,
    RestoreResult,
    RestoreStatus
)
from agentforge.backup.scheduler import (
    BackupScheduler,
    ScheduleConfig
)


class TestBackupConfig:
    """Tests for BackupConfig"""
    
    def test_default_config(self):
        config = BackupConfig()
        
        assert config.backup_dir == "/var/backups/agentforge"
        assert config.retention_days == 30
        assert config.compress is True
    
    def test_custom_config(self):
        config = BackupConfig(
            backup_dir="/custom/backup",
            retention_days=60,
            compress_level=9
        )
        
        assert config.backup_dir == "/custom/backup"
        assert config.retention_days == 60
        assert config.compress_level == 9


class TestBackupMetadata:
    """Tests for BackupMetadata"""
    
    def test_metadata_creation(self):
        metadata = BackupMetadata(
            id="backup_20240101_120000",
            timestamp=datetime.now()
        )
        
        assert metadata.id == "backup_20240101_120000"
        assert metadata.status == BackupStatus.IN_PROGRESS
        assert metadata.size_bytes == 0
    
    def test_metadata_with_components(self):
        metadata = BackupMetadata(
            id="backup_test",
            timestamp=datetime.now(),
            components={"postgres": True, "redis": True, "qdrant": False}
        )
        
        assert metadata.components["postgres"] is True
        assert metadata.components["qdrant"] is False


class TestDatabaseBackup:
    """Tests for DatabaseBackup"""
    
    @pytest.fixture
    def backup_manager(self, tmp_path):
        config = BackupConfig(backup_dir=str(tmp_path / "backups"))
        manager = DatabaseBackup(config=config)
        manager._ensure_backup_dir()
        return manager
    
    def test_generate_backup_id(self, backup_manager):
        id1 = backup_manager._generate_backup_id()
        
        assert id1.startswith("backup_")
        assert len(id1) > 10
    
    def test_ensure_backup_dir(self, backup_manager):
        assert os.path.exists(backup_manager.config.backup_dir)
        assert os.path.exists(os.path.join(backup_manager.config.backup_dir, "daily"))
        assert os.path.exists(os.path.join(backup_manager.config.backup_dir, "weekly"))
        assert os.path.exists(os.path.join(backup_manager.config.backup_dir, "monthly"))
    
    def test_list_backups_empty(self, backup_manager):
        backups = backup_manager.list_backups()
        assert backups == []
    
    def test_get_backup_not_found(self, backup_manager):
        backup = backup_manager.get_backup("nonexistent")
        assert backup is None
    
    def test_delete_backup_not_found(self, backup_manager):
        result = backup_manager.delete_backup("nonexistent")
        assert result is False
    
    def test_get_backup_stats_empty(self, backup_manager):
        stats = backup_manager.get_backup_stats()
        
        assert stats["total_backups"] == 0
        assert stats["total_size_bytes"] == 0
    
    def test_human_readable_size(self, backup_manager):
        assert backup_manager._human_readable_size(500) == "500.00 B"
        assert backup_manager._human_readable_size(1024) == "1.00 KB"
        assert backup_manager._human_readable_size(1048576) == "1.00 MB"


class TestRestoreResult:
    """Tests for RestoreResult"""
    
    def test_restore_result_creation(self):
        result = RestoreResult(backup_id="backup_test")
        
        assert result.backup_id == "backup_test"
        assert result.status == RestoreStatus.IN_PROGRESS
        assert len(result.warnings) == 0
    
    def test_restore_result_with_components(self):
        result = RestoreResult(
            backup_id="backup_test",
            components_restored={"postgres": True, "redis": False}
        )
        
        assert result.components_restored["postgres"] is True
        assert result.components_restored["redis"] is False


class TestDatabaseRestore:
    """Tests for DatabaseRestore"""
    
    @pytest.fixture
    def restore_manager(self, tmp_path):
        config = BackupConfig(backup_dir=str(tmp_path / "backups"))
        return DatabaseRestore(config=config)
    
    def test_find_backup_path_not_found(self, restore_manager):
        path = restore_manager.find_backup_path("nonexistent")
        assert path is None
    
    def test_verify_backup_not_found(self, restore_manager):
        verification = restore_manager.verify_backup("nonexistent")
        
        assert verification["valid"] is False
        assert "not found" in verification["error"]


class TestScheduleConfig:
    """Tests for ScheduleConfig"""
    
    def test_default_schedule(self):
        config = ScheduleConfig()
        
        assert config.daily_enabled is True
        assert config.daily_time == "02:00"
        assert config.weekly_enabled is True
        assert config.monthly_enabled is True
    
    def test_custom_schedule(self):
        config = ScheduleConfig(
            daily_enabled=False,
            daily_time="03:30"
        )
        
        assert config.daily_enabled is False
        assert config.daily_time == "03:30"


class TestBackupScheduler:
    """Tests for BackupScheduler"""
    
    @pytest.fixture
    def scheduler(self, tmp_path):
        config = BackupConfig(backup_dir=str(tmp_path / "backups"))
        backup_mgr = DatabaseBackup(config=config)
        restore_mgr = DatabaseRestore(config=config)
        schedule_config = ScheduleConfig()
        
        return BackupScheduler(
            backup_manager=backup_mgr,
            restore_manager=restore_mgr,
            schedule_config=schedule_config
        )
    
    def test_scheduler_initialization(self, scheduler):
        assert scheduler._running is False
        assert scheduler._last_backup is None
    
    def test_get_status(self, scheduler):
        status = scheduler.get_status()
        
        assert "running" in status
        assert "last_backup" in status
        assert "schedule_config" in status
    
    def test_list_available_backups(self, scheduler):
        backups = scheduler.list_available_backups()
        assert backups == []
    
    @pytest.mark.asyncio
    async def test_start_stop_scheduler(self, scheduler):
        await scheduler.start()
        assert scheduler._running is True
        
        await scheduler.stop()
        assert scheduler._running is False


class TestBackupType:
    """Tests for backup types"""
    
    def test_backup_type_constants(self):
        assert BackupType.FULL == "full"
        assert BackupType.INCREMENTAL == "incremental"
        assert BackupType.DIFFERENTIAL == "differential"


class TestBackupStatus:
    """Tests for backup status"""
    
    def test_backup_status_constants(self):
        assert BackupStatus.SUCCESS == "success"
        assert BackupStatus.FAILED == "failed"
        assert BackupStatus.IN_PROGRESS == "in_progress"


class TestRestoreStatus:
    """Tests for restore status"""
    
    def test_restore_status_constants(self):
        assert RestoreStatus.SUCCESS == "success"
        assert RestoreStatus.FAILED == "failed"
        assert RestoreStatus.IN_PROGRESS == "in_progress"
        assert RestoreStatus.PARTIAL == "partial"
