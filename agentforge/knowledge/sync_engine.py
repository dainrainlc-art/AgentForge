"""知识库同步引擎 - Obsidian 与 Notion 双向同步

功能特性:
- 增量同步（基于修改时间）
- 冲突检测
- 双向同步逻辑
- 同步日志记录
- 自动同步调度
"""

import os
import json
import hashlib
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Set
from datetime import datetime
from enum import Enum
from pathlib import Path
import asyncio

from .obsidian_client import ObsidianClient, ObsidianNote
from .notion_client import NotionClient, NotionPage
from .markdown_parser import MarkdownParser

logger = logging.getLogger(__name__)


class SyncDirection(Enum):
    """同步方向"""
    TO_NOTION = "to_notion"
    TO_OBSIDIAN = "to_obsidian"
    BIDIRECTIONAL = "bidirectional"


class SyncStatus(Enum):
    """同步状态"""
    PENDING = "pending"
    SYNCED = "synced"
    CONFLICT = "conflict"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class SyncRecord:
    """同步记录"""
    id: str
    obsidian_path: Optional[str] = None
    notion_page_id: Optional[str] = None
    obsidian_hash: Optional[str] = None
    notion_hash: Optional[str] = None
    last_sync: Optional[datetime] = None
    last_obsidian_modified: Optional[datetime] = None
    last_notion_modified: Optional[datetime] = None
    status: SyncStatus = SyncStatus.PENDING
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "obsidian_path": self.obsidian_path,
            "notion_page_id": self.notion_page_id,
            "obsidian_hash": self.obsidian_hash,
            "notion_hash": self.notion_hash,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "last_obsidian_modified": self.last_obsidian_modified.isoformat() if self.last_obsidian_modified else None,
            "last_notion_modified": self.last_notion_modified.isoformat() if self.last_notion_modified else None,
            "status": self.status.value,
            "error_message": self.error_message,
            "metadata": self.metadata
        }


@dataclass
class SyncResult:
    """同步结果"""
    total: int = 0
    synced: int = 0
    conflicts: int = 0
    errors: int = 0
    skipped: int = 0
    details: List[SyncRecord] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total": self.total,
            "synced": self.synced,
            "conflicts": self.conflicts,
            "errors": self.errors,
            "skipped": self.skipped,
            "details": [r.to_dict() for r in self.details]
        }


class SyncEngine:
    """同步引擎"""

    def __init__(
        self,
        obsidian_client: ObsidianClient,
        notion_client: NotionClient,
        notion_database_id: str,
        sync_state_path: str = "./data/sync_state.json"
    ):
        self.obsidian = obsidian_client
        self.notion = notion_client
        self.notion_database_id = notion_database_id
        self.sync_state_path = Path(sync_state_path)

        self._sync_records: Dict[str, SyncRecord] = {}
        self._parser = MarkdownParser()
        self._initialized = False

    async def initialize(self) -> bool:
        """初始化同步引擎"""
        if self._initialized:
            return True

        try:
            await self.obsidian.initialize()
            self._load_sync_state()
            self._initialized = True
            logger.info("同步引擎初始化完成")
            return True
        except Exception as e:
            logger.error(f"同步引擎初始化失败: {e}")
            return False

    def _load_sync_state(self):
        """加载同步状态"""
        if self.sync_state_path.exists():
            try:
                with open(self.sync_state_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for record_data in data.get("records", []):
                        record = SyncRecord(
                            id=record_data["id"],
                            obsidian_path=record_data.get("obsidian_path"),
                            notion_page_id=record_data.get("notion_page_id"),
                            obsidian_hash=record_data.get("obsidian_hash"),
                            notion_hash=record_data.get("notion_hash"),
                            last_sync=self._parse_datetime(record_data.get("last_sync")),
                            last_obsidian_modified=self._parse_datetime(record_data.get("last_obsidian_modified")),
                            last_notion_modified=self._parse_datetime(record_data.get("last_notion_modified")),
                            status=SyncStatus(record_data.get("status", "pending")),
                            error_message=record_data.get("error_message"),
                            metadata=record_data.get("metadata", {})
                        )
                        self._sync_records[record.id] = record
                logger.info(f"加载 {len(self._sync_records)} 条同步记录")
            except Exception as e:
                logger.warning(f"加载同步状态失败: {e}")

    def _save_sync_state(self):
        """保存同步状态"""
        self.sync_state_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "records": [r.to_dict() for r in self._sync_records.values()],
            "last_updated": datetime.now().isoformat()
        }
        with open(self.sync_state_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """解析日期时间"""
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except:
            return None

    def _compute_hash(self, content: str) -> str:
        """计算内容哈希"""
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    async def sync(
        self,
        direction: SyncDirection = SyncDirection.BIDIRECTIONAL,
        force: bool = False
    ) -> SyncResult:
        """执行同步"""
        if not self._initialized:
            await self.initialize()

        result = SyncResult()

        if direction == SyncDirection.TO_NOTION:
            await self._sync_to_notion(result, force)
        elif direction == SyncDirection.TO_OBSIDIAN:
            await self._sync_to_obsidian(result, force)
        else:
            await self._sync_to_notion(result, force)
            await self._sync_to_obsidian(result, force)

        self._save_sync_state()

        result.total = len(result.details)
        return result

    async def _sync_to_notion(self, result: SyncResult, force: bool = False):
        """同步到 Notion"""
        notes = self.obsidian.list_notes()

        for note in notes:
            record = self._get_or_create_record(note.id)
            record.obsidian_path = note.path

            current_hash = self._compute_hash(note.content)

            if not force and record.obsidian_hash == current_hash:
                record.status = SyncStatus.SKIPPED
                result.skipped += 1
                result.details.append(record)
                continue

            try:
                if record.notion_page_id:
                    await self._update_notion_page(record, note)
                else:
                    await self._create_notion_page(record, note)

                record.obsidian_hash = current_hash
                record.last_sync = datetime.now()
                record.last_obsidian_modified = note.modified_at
                record.status = SyncStatus.SYNCED
                result.synced += 1

            except Exception as e:
                record.status = SyncStatus.ERROR
                record.error_message = str(e)
                result.errors += 1
                logger.error(f"同步到 Notion 失败 {note.title}: {e}")

            result.details.append(record)

    async def _sync_to_obsidian(self, result: SyncResult, force: bool = False):
        """同步到 Obsidian"""
        try:
            response = await self.notion.query_database(self.notion_database_id)
            pages = response.get("pages", [])

            for page in pages:
                record = self._find_record_by_notion_id(page.id)

                if not record:
                    record = SyncRecord(id=f"notion_{page.id}")
                    record.notion_page_id = page.id

                md_content = await self.notion.export_page_to_markdown(page.id)
                current_hash = self._compute_hash(md_content)

                if not force and record.notion_hash == current_hash:
                    record.status = SyncStatus.SKIPPED
                    result.skipped += 1
                    result.details.append(record)
                    continue

                try:
                    if record.obsidian_path:
                        await self._update_obsidian_note(record, page, md_content)
                    else:
                        await self._create_obsidian_note(record, page, md_content)

                    record.notion_hash = current_hash
                    record.last_sync = datetime.now()
                    record.last_notion_modified = page.last_edited_time
                    record.status = SyncStatus.SYNCED
                    result.synced += 1

                except Exception as e:
                    record.status = SyncStatus.ERROR
                    record.error_message = str(e)
                    result.errors += 1
                    logger.error(f"同步到 Obsidian 失败 {page.title}: {e}")

                result.details.append(record)

        except Exception as e:
            logger.error(f"查询 Notion 数据库失败: {e}")

    def _get_or_create_record(self, note_id: str) -> SyncRecord:
        """获取或创建同步记录"""
        if note_id not in self._sync_records:
            self._sync_records[note_id] = SyncRecord(id=note_id)
        return self._sync_records[note_id]

    def _find_record_by_notion_id(self, notion_page_id: str) -> Optional[SyncRecord]:
        """通过 Notion 页面 ID 查找记录"""
        for record in self._sync_records.values():
            if record.notion_page_id == notion_page_id:
                return record
        return None

    async def _create_notion_page(self, record: SyncRecord, note: ObsidianNote):
        """创建 Notion 页面"""
        page = await self.notion.create_page_from_markdown(
            database_id=self.notion_database_id,
            title=note.title,
            markdown_content=note.content,
            tags=list(note.tags)
        )
        record.notion_page_id = page.id

    async def _update_notion_page(self, record: SyncRecord, note: ObsidianNote):
        """更新 Notion 页面"""
        await self.notion.update_page(
            page_id=record.notion_page_id,
            properties={
                "Name": {
                    "title": [{"text": {"content": note.title}}]
                }
            }
        )

        blocks = self._parser.convert_to_notion_blocks(note.content)

        existing_blocks = await self.notion.get_block_children(record.notion_page_id)
        for block in existing_blocks:
            await self.notion._request("DELETE", f"/blocks/{block['id']}")

        if blocks:
            await self.notion.append_block_children(record.notion_page_id, blocks[:100])

    async def _create_obsidian_note(self, record: SyncRecord, page: NotionPage, content: str):
        """创建 Obsidian 笔记"""
        note = await self.obsidian.create_note(
            title=page.title,
            content=content,
            folder="从Notion同步"
        )
        record.obsidian_path = note.path

    async def _update_obsidian_note(self, record: SyncRecord, page: NotionPage, content: str):
        """更新 Obsidian 笔记"""
        note_id = None
        for nid, note in self.obsidian._notes.items():
            if note.path == record.obsidian_path:
                note_id = nid
                break

        if note_id:
            await self.obsidian.update_note(note_id, content=content)

    def detect_conflicts(self) -> List[SyncRecord]:
        """检测冲突"""
        conflicts = []

        for record in self._sync_records.values():
            if (record.last_obsidian_modified and record.last_notion_modified and
                record.last_sync):
                if (record.last_obsidian_modified > record.last_sync and
                    record.last_notion_modified > record.last_sync):
                    record.status = SyncStatus.CONFLICT
                    conflicts.append(record)

        return conflicts

    async def resolve_conflict(
        self,
        record_id: str,
        resolution: str
    ) -> bool:
        """解决冲突"""
        if record_id not in self._sync_records:
            return False

        record = self._sync_records[record_id]

        try:
            if resolution == "keep_obsidian":
                note = self.obsidian.get_note(record.id)
                if note:
                    await self._update_notion_page(record, note)
                    record.status = SyncStatus.SYNCED

            elif resolution == "keep_notion":
                if record.notion_page_id:
                    page = await self.notion.get_page(record.notion_page_id)
                    md_content = await self.notion.export_page_to_markdown(record.notion_page_id)
                    await self._update_obsidian_note(record, page, md_content)
                    record.status = SyncStatus.SYNCED

            elif resolution == "merge":
                pass

            record.last_sync = datetime.now()
            self._save_sync_state()
            return True

        except Exception as e:
            logger.error(f"解决冲突失败: {e}")
            return False

    def get_sync_status(self) -> Dict[str, Any]:
        """获取同步状态"""
        status_counts = {}
        for status in SyncStatus:
            status_counts[status.value] = sum(
                1 for r in self._sync_records.values() if r.status == status
            )

        return {
            "total_records": len(self._sync_records),
            "by_status": status_counts,
            "last_sync": max(
                (r.last_sync for r in self._sync_records.values() if r.last_sync),
                default=None
            )
        }

    async def start_auto_sync(self, interval_minutes: int = 360):
        """启动自动同步"""
        while True:
            try:
                logger.info("执行自动同步...")
                result = await self.sync()
                logger.info(f"同步完成: {result.to_dict()}")
            except Exception as e:
                logger.error(f"自动同步失败: {e}")

            await asyncio.sleep(interval_minutes * 60)
