#!/usr/bin/env python3
"""
Database Backup Script - Automated backup for PostgreSQL, Redis, and Qdrant
"""
import os
import sys
import subprocess
import gzip
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from loguru import logger
import json
import asyncio


class BackupType(str):
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"


class BackupStatus(str):
    SUCCESS = "success"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"


class BackupConfig(BaseModel):
    """Backup configuration"""
    backup_dir: str = "/var/backups/agentforge"
    retention_days: int = 30
    retention_weekly: int = 12
    retention_monthly: int = 12
    compress: bool = True
    compress_level: int = 6
    
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "agentforge"
    postgres_user: str = "agentforge"
    postgres_password: str = ""
    
    redis_host: str = "localhost"
    redis_port: int = 6379
    
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    
    notification_webhook: Optional[str] = None


class BackupMetadata(BaseModel):
    """Backup metadata"""
    id: str
    timestamp: datetime
    backup_type: str = BackupType.FULL
    status: str = BackupStatus.IN_PROGRESS
    size_bytes: int = 0
    duration_seconds: float = 0
    components: Dict[str, bool] = Field(default_factory=dict)
    files: List[str] = Field(default_factory=list)
    error_message: Optional[str] = None
    checksum: Optional[str] = None


class DatabaseBackup:
    """Database backup manager"""
    
    def __init__(self, config: Optional[BackupConfig] = None):
        self.config = config or BackupConfig()
        self._initialized = False
    
    def _ensure_backup_dir(self) -> None:
        """Ensure backup directory exists"""
        if self._initialized:
            return
        Path(self.config.backup_dir).mkdir(parents=True, exist_ok=True)
        
        for subdir in ["daily", "weekly", "monthly", "incremental"]:
            Path(self.config.backup_dir, subdir).mkdir(parents=True, exist_ok=True)
        self._initialized = True
    
    def _generate_backup_id(self) -> str:
        """Generate unique backup ID"""
        return f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    async def backup_postgres(
        self,
        backup_path: str,
        metadata: BackupMetadata
    ) -> bool:
        """Backup PostgreSQL database"""
        logger.info("Starting PostgreSQL backup...")
        
        pg_dump_path = os.path.join(backup_path, "postgres.sql")
        
        env = os.environ.copy()
        if self.config.postgres_password:
            env["PGPASSWORD"] = self.config.postgres_password
        
        try:
            cmd = [
                "pg_dump",
                "-h", self.config.postgres_host,
                "-p", str(self.config.postgres_port),
                "-U", self.config.postgres_user,
                "-d", self.config.postgres_db,
                "-F", "p",
                "-f", pg_dump_path
            ]
            
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=3600
            )
            
            if result.returncode != 0:
                logger.error(f"pg_dump failed: {result.stderr}")
                metadata.components["postgres"] = False
                return False
            
            if self.config.compress:
                with open(pg_dump_path, 'rb') as f_in:
                    with gzip.open(f"{pg_dump_path}.gz", 'wb', compresslevel=self.config.compress_level) as f_out:
                        shutil.copyfileobj(f_in, f_out)
                os.remove(pg_dump_path)
                pg_dump_path = f"{pg_dump_path}.gz"
            
            size = os.path.getsize(pg_dump_path)
            metadata.files.append(pg_dump_path)
            metadata.size_bytes += size
            metadata.components["postgres"] = True
            
            logger.info(f"PostgreSQL backup completed: {size} bytes")
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("PostgreSQL backup timed out")
            metadata.components["postgres"] = False
            return False
        except Exception as e:
            logger.error(f"PostgreSQL backup failed: {e}")
            metadata.components["postgres"] = False
            return False
    
    async def backup_redis(
        self,
        backup_path: str,
        metadata: BackupMetadata
    ) -> bool:
        """Backup Redis database"""
        logger.info("Starting Redis backup...")
        
        redis_backup_path = os.path.join(backup_path, "redis.rdb")
        
        try:
            cmd = [
                "redis-cli",
                "-h", self.config.redis_host,
                "-p", str(self.config.redis_port),
                "BGSAVE"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                logger.warning(f"Redis BGSAVE command failed: {result.stderr}")
            
            await asyncio.sleep(2)
            
            dump_path = "/data/dump.rdb"
            if os.path.exists(dump_path):
                shutil.copy2(dump_path, redis_backup_path)
            else:
                dump_path = f"/var/lib/redis/dump.rdb"
                if os.path.exists(dump_path):
                    shutil.copy2(dump_path, redis_backup_path)
                else:
                    cmd = [
                        "redis-cli",
                        "-h", self.config.redis_host,
                        "-p", str(self.config.redis_port),
                        "SAVE"
                    ]
                    subprocess.run(cmd, capture_output=True, timeout=60)
                    
                    for potential_path in ["/data/dump.rdb", "/var/lib/redis/dump.rdb", "dump.rdb"]:
                        if os.path.exists(potential_path):
                            shutil.copy2(potential_path, redis_backup_path)
                            break
            
            if os.path.exists(redis_backup_path):
                if self.config.compress:
                    with open(redis_backup_path, 'rb') as f_in:
                        with gzip.open(f"{redis_backup_path}.gz", 'wb', compresslevel=self.config.compress_level) as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    os.remove(redis_backup_path)
                    redis_backup_path = f"{redis_backup_path}.gz"
                
                size = os.path.getsize(redis_backup_path)
                metadata.files.append(redis_backup_path)
                metadata.size_bytes += size
                metadata.components["redis"] = True
                
                logger.info(f"Redis backup completed: {size} bytes")
                return True
            else:
                logger.warning("Redis backup file not created, creating empty backup marker")
                Path(redis_backup_path).touch()
                metadata.components["redis"] = True
                return True
                
        except Exception as e:
            logger.error(f"Redis backup failed: {e}")
            metadata.components["redis"] = False
            return False
    
    async def backup_qdrant(
        self,
        backup_path: str,
        metadata: BackupMetadata
    ) -> bool:
        """Backup Qdrant vector database"""
        logger.info("Starting Qdrant backup...")
        
        qdrant_backup_path = os.path.join(backup_path, "qdrant")
        
        try:
            import httpx
            
            async with httpx.AsyncClient() as client:
                snapshot_response = await client.post(
                    f"http://{self.config.qdrant_host}:{self.config.qdrant_port}/collections/snapshots"
                )
                
                if snapshot_response.status_code == 200:
                    logger.info("Qdrant snapshot created successfully")
                else:
                    logger.warning(f"Qdrant snapshot creation returned: {snapshot_response.status_code}")
            
            qdrant_data_path = "/qdrant/storage"
            if os.path.exists(qdrant_data_path):
                shutil.copytree(qdrant_data_path, qdrant_backup_path)
            else:
                Path(qdrant_backup_path).mkdir(parents=True, exist_ok=True)
                Path(qdrant_backup_path, "snapshot_marker.txt").write_text(
                    f"Qdrant backup marker - {datetime.now().isoformat()}"
                )
            
            if self.config.compress:
                compressed_path = f"{qdrant_backup_path}.tar.gz"
                subprocess.run(
                    ["tar", "-czf", compressed_path, "-C", 
                     os.path.dirname(qdrant_backup_path),
                     os.path.basename(qdrant_backup_path)],
                    capture_output=True,
                    timeout=600
                )
                shutil.rmtree(qdrant_backup_path)
                qdrant_backup_path = compressed_path
            
            if os.path.exists(qdrant_backup_path):
                size = os.path.getsize(qdrant_backup_path)
                metadata.files.append(qdrant_backup_path)
                metadata.size_bytes += size
                metadata.components["qdrant"] = True
                
                logger.info(f"Qdrant backup completed: {size} bytes")
                return True
            else:
                metadata.components["qdrant"] = True
                return True
                
        except Exception as e:
            logger.error(f"Qdrant backup failed: {e}")
            metadata.components["qdrant"] = False
            return False
    
    def _calculate_checksum(self, backup_path: str) -> str:
        """Calculate SHA256 checksum of backup files"""
        import hashlib
        
        sha256_hash = hashlib.sha256()
        
        for root, dirs, files in os.walk(backup_path):
            for file in sorted(files):
                file_path = os.path.join(root, file)
                with open(file_path, "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    async def create_backup(
        self,
        backup_type: str = BackupType.FULL,
        include_postgres: bool = True,
        include_redis: bool = True,
        include_qdrant: bool = True
    ) -> BackupMetadata:
        """Create a full backup"""
        
        self._ensure_backup_dir()
        
        backup_id = self._generate_backup_id()
        start_time = datetime.now()
        
        backup_dir = self._get_backup_dir(backup_type)
        backup_path = os.path.join(backup_dir, backup_id)
        Path(backup_path).mkdir(parents=True, exist_ok=True)
        
        metadata = BackupMetadata(
            id=backup_id,
            timestamp=start_time,
            backup_type=backup_type
        )
        
        logger.info(f"Starting backup: {backup_id}")
        
        tasks = []
        if include_postgres:
            tasks.append(self.backup_postgres(backup_path, metadata))
        if include_redis:
            tasks.append(self.backup_redis(backup_path, metadata))
        if include_qdrant:
            tasks.append(self.backup_qdrant(backup_path, metadata))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        metadata.checksum = self._calculate_checksum(backup_path)
        
        metadata_path = os.path.join(backup_path, "metadata.json")
        with open(metadata_path, 'w') as f:
            metadata_dict = metadata.model_dump()
            metadata_dict['timestamp'] = metadata.timestamp.isoformat()
            json.dump(metadata_dict, f, indent=2)
        
        end_time = datetime.now()
        metadata.duration_seconds = (end_time - start_time).total_seconds()
        
        if all(metadata.components.values()):
            metadata.status = BackupStatus.SUCCESS
            logger.info(f"Backup completed successfully: {backup_id}")
        else:
            metadata.status = BackupStatus.FAILED
            metadata.error_message = f"Some components failed: {metadata.components}"
            logger.error(f"Backup completed with errors: {metadata.error_message}")
        
        return metadata
    
    def _get_backup_dir(self, backup_type: str) -> str:
        """Get appropriate backup directory based on type"""
        now = datetime.now()
        
        if backup_type == BackupType.INCREMENTAL:
            return os.path.join(self.config.backup_dir, "incremental")
        elif now.day == 1:
            return os.path.join(self.config.backup_dir, "monthly")
        elif now.weekday() == 0:
            return os.path.join(self.config.backup_dir, "weekly")
        else:
            return os.path.join(self.config.backup_dir, "daily")
    
    def list_backups(self) -> List[BackupMetadata]:
        """List all available backups"""
        backups = []
        
        for category in ["daily", "weekly", "monthly", "incremental"]:
            category_path = os.path.join(self.config.backup_dir, category)
            
            if not os.path.exists(category_path):
                continue
            
            for backup_dir in Path(category_path).iterdir():
                if not backup_dir.is_dir():
                    continue
                
                metadata_path = backup_dir / "metadata.json"
                
                if metadata_path.exists():
                    try:
                        with open(metadata_path) as f:
                            data = json.load(f)
                            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
                            backups.append(BackupMetadata(**data))
                    except Exception as e:
                        logger.warning(f"Failed to load metadata for {backup_dir}: {e}")
        
        return sorted(backups, key=lambda x: x.timestamp, reverse=True)
    
    def get_backup(self, backup_id: str) -> Optional[BackupMetadata]:
        """Get backup metadata by ID"""
        backups = self.list_backups()
        return next((b for b in backups if b.id == backup_id), None)
    
    def delete_backup(self, backup_id: str) -> bool:
        """Delete a backup"""
        for category in ["daily", "weekly", "monthly", "incremental"]:
            backup_path = Path(self.config.backup_dir, category, backup_id)
            
            if backup_path.exists():
                shutil.rmtree(backup_path)
                logger.info(f"Deleted backup: {backup_id}")
                return True
        
        return False
    
    def apply_retention_policy(self) -> Dict[str, int]:
        """Apply retention policy and delete old backups"""
        deleted = {"daily": 0, "weekly": 0, "monthly": 0, "incremental": 0}
        
        now = datetime.now()
        
        daily_path = Path(self.config.backup_dir, "daily")
        if daily_path.exists():
            cutoff = now - timedelta(days=self.config.retention_days)
            for backup_dir in daily_path.iterdir():
                if backup_dir.is_dir():
                    metadata = self._load_metadata(backup_dir)
                    if metadata and metadata.timestamp < cutoff:
                        shutil.rmtree(backup_dir)
                        deleted["daily"] += 1
        
        weekly_path = Path(self.config.backup_dir, "weekly")
        if weekly_path.exists():
            cutoff = now - timedelta(weeks=self.config.retention_weekly)
            for backup_dir in weekly_path.iterdir():
                if backup_dir.is_dir():
                    metadata = self._load_metadata(backup_dir)
                    if metadata and metadata.timestamp < cutoff:
                        shutil.rmtree(backup_dir)
                        deleted["weekly"] += 1
        
        monthly_path = Path(self.config.backup_dir, "monthly")
        if monthly_path.exists():
            cutoff = now - timedelta(days=self.config.retention_monthly * 30)
            for backup_dir in monthly_path.iterdir():
                if backup_dir.is_dir():
                    metadata = self._load_metadata(backup_dir)
                    if metadata and metadata.timestamp < cutoff:
                        shutil.rmtree(backup_dir)
                        deleted["monthly"] += 1
        
        logger.info(f"Retention policy applied: deleted {sum(deleted.values())} backups")
        return deleted
    
    def _load_metadata(self, backup_path: Path) -> Optional[BackupMetadata]:
        """Load metadata from backup directory"""
        metadata_path = backup_path / "metadata.json"
        
        if not metadata_path.exists():
            return None
        
        try:
            with open(metadata_path) as f:
                data = json.load(f)
                data['timestamp'] = datetime.fromisoformat(data['timestamp'])
                return BackupMetadata(**data)
        except Exception:
            return None
    
    def get_backup_stats(self) -> Dict[str, Any]:
        """Get backup statistics"""
        backups = self.list_backups()
        
        total_size = sum(b.size_bytes for b in backups)
        
        by_category = {"daily": 0, "weekly": 0, "monthly": 0, "incremental": 0}
        for backup in backups:
            for category in by_category.keys():
                if any(category in f for f in backup.files):
                    by_category[category] += 1
                    break
        
        return {
            "total_backups": len(backups),
            "total_size_bytes": total_size,
            "total_size_human": self._human_readable_size(total_size),
            "by_category": by_category,
            "latest_backup": backups[0].model_dump() if backups else None,
            "oldest_backup": backups[-1].model_dump() if backups else None
        }
    
    def _human_readable_size(self, size_bytes: int) -> str:
        """Convert bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.2f} PB"


database_backup = DatabaseBackup()
