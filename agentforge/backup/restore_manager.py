#!/usr/bin/env python3
"""
Database Restore Script - Restore PostgreSQL, Redis, and Qdrant from backups
"""
import os
import sys
import subprocess
import gzip
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from loguru import logger
import json
import asyncio

from agentforge.backup.backup_manager import BackupConfig, BackupMetadata


class RestoreStatus(str):
    SUCCESS = "success"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"
    PARTIAL = "partial"


class RestoreResult(BaseModel):
    """Restore operation result"""
    backup_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    status: str = RestoreStatus.IN_PROGRESS
    components_restored: Dict[str, bool] = Field(default_factory=dict)
    duration_seconds: float = 0
    error_message: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)


class DatabaseRestore:
    """Database restore manager"""
    
    def __init__(self, config: Optional[BackupConfig] = None):
        self.config = config or BackupConfig()
    
    def find_backup_path(self, backup_id: str) -> Optional[str]:
        """Find backup directory by ID"""
        for category in ["daily", "weekly", "monthly", "incremental"]:
            backup_path = Path(self.config.backup_dir, category, backup_id)
            if backup_path.exists():
                return str(backup_path)
        return None
    
    async def restore_postgres(
        self,
        backup_path: str,
        result: RestoreResult,
        drop_existing: bool = False
    ) -> bool:
        """Restore PostgreSQL database"""
        logger.info("Starting PostgreSQL restore...")
        
        sql_path = None
        for ext in ["", ".gz"]:
            potential_path = os.path.join(backup_path, f"postgres.sql{ext}")
            if os.path.exists(potential_path):
                sql_path = potential_path
                break
        
        if not sql_path:
            logger.warning("No PostgreSQL backup found")
            result.warnings.append("PostgreSQL backup not found")
            result.components_restored["postgres"] = True
            return True
        
        try:
            if drop_existing:
                env = os.environ.copy()
                if self.config.postgres_password:
                    env["PGPASSWORD"] = self.config.postgres_password
                
                drop_cmd = [
                    "psql",
                    "-h", self.config.postgres_host,
                    "-p", str(self.config.postgres_port),
                    "-U", self.config.postgres_user,
                    "-d", "postgres",
                    "-c", f"DROP DATABASE IF EXISTS {self.config.postgres_db};"
                ]
                subprocess.run(drop_cmd, env=env, capture_output=True, timeout=60)
                
                create_cmd = [
                    "psql",
                    "-h", self.config.postgres_host,
                    "-p", str(self.config.postgres_port),
                    "-U", self.config.postgres_user,
                    "-d", "postgres",
                    "-c", f"CREATE DATABASE {self.config.postgres_db};"
                ]
                subprocess.run(create_cmd, env=env, capture_output=True, timeout=60)
            
            env = os.environ.copy()
            if self.config.postgres_password:
                env["PGPASSWORD"] = self.config.postgres_password
            
            if sql_path.endswith('.gz'):
                temp_sql = sql_path.replace('.gz', '')
                with gzip.open(sql_path, 'rb') as f_in:
                    with open(temp_sql, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                sql_path = temp_sql
            
            cmd = [
                "psql",
                "-h", self.config.postgres_host,
                "-p", str(self.config.postgres_port),
                "-U", self.config.postgres_user,
                "-d", self.config.postgres_db,
                "-f", sql_path
            ]
            
            restore_result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=3600
            )
            
            if restore_result.returncode != 0:
                logger.error(f"PostgreSQL restore failed: {restore_result.stderr}")
                result.components_restored["postgres"] = False
                result.warnings.append(f"PostgreSQL restore errors: {restore_result.stderr[:500]}")
                return False
            
            result.components_restored["postgres"] = True
            logger.info("PostgreSQL restore completed successfully")
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("PostgreSQL restore timed out")
            result.components_restored["postgres"] = False
            return False
        except Exception as e:
            logger.error(f"PostgreSQL restore failed: {e}")
            result.components_restored["postgres"] = False
            return False
    
    async def restore_redis(
        self,
        backup_path: str,
        result: RestoreResult
    ) -> bool:
        """Restore Redis database"""
        logger.info("Starting Redis restore...")
        
        rdb_path = None
        for ext in ["", ".gz"]:
            potential_path = os.path.join(backup_path, f"redis.rdb{ext}")
            if os.path.exists(potential_path):
                rdb_path = potential_path
                break
        
        if not rdb_path:
            logger.warning("No Redis backup found")
            result.warnings.append("Redis backup not found")
            result.components_restored["redis"] = True
            return True
        
        try:
            if rdb_path.endswith('.gz'):
                temp_rdb = rdb_path.replace('.gz', '')
                with gzip.open(rdb_path, 'rb') as f_in:
                    with open(temp_rdb, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                rdb_path = temp_rdb
            
            cmd = ["redis-cli", "-h", self.config.redis_host, "-p", str(self.config.redis_port), "SHUTDOWN", "NOSAVE"]
            subprocess.run(cmd, capture_output=True, timeout=30)
            
            await asyncio.sleep(2)
            
            dest_path = "/data/dump.rdb"
            if not os.path.exists(os.path.dirname(dest_path)):
                dest_path = "/var/lib/redis/dump.rdb"
            
            shutil.copy2(rdb_path, dest_path)
            
            logger.info("Redis restore completed - Redis needs to be restarted")
            result.components_restored["redis"] = True
            result.warnings.append("Redis needs to be restarted to load restored data")
            return True
            
        except Exception as e:
            logger.error(f"Redis restore failed: {e}")
            result.components_restored["redis"] = False
            return False
    
    async def restore_qdrant(
        self,
        backup_path: str,
        result: RestoreResult
    ) -> bool:
        """Restore Qdrant vector database"""
        logger.info("Starting Qdrant restore...")
        
        qdrant_backup = None
        for name in ["qdrant", "qdrant.tar.gz"]:
            potential_path = os.path.join(backup_path, name)
            if os.path.exists(potential_path):
                qdrant_backup = potential_path
                break
        
        if not qdrant_backup:
            logger.warning("No Qdrant backup found")
            result.warnings.append("Qdrant backup not found")
            result.components_restored["qdrant"] = True
            return True
        
        try:
            dest_path = "/qdrant/storage"
            
            if qdrant_backup.endswith('.tar.gz'):
                subprocess.run(
                    ["tar", "-xzf", qdrant_backup, "-C", "/qdrant"],
                    capture_output=True,
                    timeout=600
                )
            else:
                if os.path.exists(dest_path):
                    shutil.rmtree(dest_path)
                shutil.copytree(qdrant_backup, dest_path)
            
            logger.info("Qdrant restore completed - Qdrant needs to be restarted")
            result.components_restored["qdrant"] = True
            result.warnings.append("Qdrant needs to be restarted to load restored data")
            return True
            
        except Exception as e:
            logger.error(f"Qdrant restore failed: {e}")
            result.components_restored["qdrant"] = False
            return False
    
    async def restore(
        self,
        backup_id: str,
        include_postgres: bool = True,
        include_redis: bool = True,
        include_qdrant: bool = True,
        drop_existing: bool = False
    ) -> RestoreResult:
        """Restore from a backup"""
        
        backup_path = self.find_backup_path(backup_id)
        
        if not backup_path:
            result = RestoreResult(
                backup_id=backup_id,
                status=RestoreStatus.FAILED,
                error_message=f"Backup not found: {backup_id}"
            )
            return result
        
        result = RestoreResult(backup_id=backup_id)
        start_time = datetime.now()
        
        logger.info(f"Starting restore from backup: {backup_id}")
        
        metadata_path = os.path.join(backup_path, "metadata.json")
        if os.path.exists(metadata_path):
            with open(metadata_path) as f:
                metadata = json.load(f)
                logger.info(f"Backup metadata: {metadata}")
        
        tasks = []
        if include_postgres:
            tasks.append(self.restore_postgres(backup_path, result, drop_existing))
        if include_redis:
            tasks.append(self.restore_redis(backup_path, result))
        if include_qdrant:
            tasks.append(self.restore_qdrant(backup_path, result))
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = datetime.now()
        result.duration_seconds = (end_time - start_time).total_seconds()
        
        all_success = all(result.components_restored.values())
        any_success = any(result.components_restored.values())
        
        if all_success:
            result.status = RestoreStatus.SUCCESS
            logger.info("Restore completed successfully")
        elif any_success:
            result.status = RestoreStatus.PARTIAL
            result.error_message = "Some components failed to restore"
            logger.warning("Restore completed with partial success")
        else:
            result.status = RestoreStatus.FAILED
            result.error_message = "All components failed to restore"
            logger.error("Restore failed completely")
        
        return result
    
    def verify_backup(self, backup_id: str) -> Dict[str, Any]:
        """Verify backup integrity"""
        backup_path = self.find_backup_path(backup_id)
        
        if not backup_path:
            return {
                "valid": False,
                "error": f"Backup not found: {backup_id}"
            }
        
        verification = {
            "valid": True,
            "backup_id": backup_id,
            "components": {}
        }
        
        sql_path = os.path.join(backup_path, "postgres.sql")
        sql_gz_path = f"{sql_path}.gz"
        
        if os.path.exists(sql_path) or os.path.exists(sql_gz_path):
            path = sql_path if os.path.exists(sql_path) else sql_gz_path
            verification["components"]["postgres"] = {
                "exists": True,
                "size": os.path.getsize(path),
                "readable": os.access(path, os.R_OK)
            }
        else:
            verification["components"]["postgres"] = {"exists": False}
        
        rdb_path = os.path.join(backup_path, "redis.rdb")
        rdb_gz_path = f"{rdb_path}.gz"
        
        if os.path.exists(rdb_path) or os.path.exists(rdb_gz_path):
            path = rdb_path if os.path.exists(rdb_path) else rdb_gz_path
            verification["components"]["redis"] = {
                "exists": True,
                "size": os.path.getsize(path),
                "readable": os.access(path, os.R_OK)
            }
        else:
            verification["components"]["redis"] = {"exists": False}
        
        qdrant_path = os.path.join(backup_path, "qdrant")
        qdrant_tar_path = f"{qdrant_path}.tar.gz"
        
        if os.path.exists(qdrant_path) or os.path.exists(qdrant_tar_path):
            path = qdrant_path if os.path.exists(qdrant_path) else qdrant_tar_path
            if os.path.isdir(path):
                size = sum(f.stat().st_size for f in Path(path).rglob('*') if f.is_file())
            else:
                size = os.path.getsize(path)
            verification["components"]["qdrant"] = {
                "exists": True,
                "size": size,
                "readable": os.access(path, os.R_OK)
            }
        else:
            verification["components"]["qdrant"] = {"exists": False}
        
        metadata_path = os.path.join(backup_path, "metadata.json")
        if os.path.exists(metadata_path):
            with open(metadata_path) as f:
                metadata = json.load(f)
                verification["metadata"] = metadata
                
                if "checksum" in metadata:
                    verification["checksum_present"] = True
        else:
            verification["metadata"] = None
            verification["warnings"] = ["Metadata file not found"]
        
        return verification


database_restore = DatabaseRestore()
