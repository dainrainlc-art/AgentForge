"""文件监控器 - 监控 Obsidian Vault 文件变更

功能特性:
- 实时监控文件创建、修改、删除
- 支持事件回调
- 防抖处理
- 异步事件处理
"""

import os
import asyncio
import logging
from pathlib import Path
from typing import Callable, Optional, Set
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import time
from collections import defaultdict

logger = logging.getLogger(__name__)


class FileEventType(Enum):
    """文件事件类型"""
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    MOVED = "moved"


@dataclass
class FileEvent:
    """文件事件"""
    event_type: FileEventType
    path: str
    old_path: Optional[str] = None
    timestamp: Optional[datetime] = None
    is_directory: bool = False

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class FileWatcher:
    """文件监控器"""

    def __init__(
        self,
        watch_path: str,
        callback: Optional[Callable[[FileEvent], None]] = None,
        debounce_seconds: float = 1.0,
        ignore_patterns: Optional[list] = None
    ):
        self.watch_path = Path(watch_path)
        self.callback = callback
        self.debounce_seconds = debounce_seconds
        self.ignore_patterns = ignore_patterns or [
            ".obsidian",
            ".trash",
            ".git",
            "__pycache__",
            ".DS_Store",
            "node_modules"
        ]

        self._running = False
        self._file_mtimes: dict = {}
        self._pending_events: dict = defaultdict(list)
        self._last_check = time.time()
        self._check_interval = 0.5

    def _should_ignore(self, path: Path) -> bool:
        """检查是否应该忽略该路径"""
        path_str = str(path)
        for pattern in self.ignore_patterns:
            if pattern in path_str:
                return True
        return False

    def _is_markdown_file(self, path: Path) -> bool:
        """检查是否为 Markdown 文件"""
        return path.suffix.lower() == '.md'

    def _scan_directory(self) -> Set[Path]:
        """扫描目录获取所有 Markdown 文件"""
        files = set()
        for root, dirs, filenames in os.walk(self.watch_path):
            dirs[:] = [d for d in dirs if not self._should_ignore(Path(root) / d)]
            for filename in filenames:
                filepath = Path(root) / filename
                if self._is_markdown_file(filepath) and not self._should_ignore(filepath):
                    files.add(filepath)
        return files

    def _get_file_mtime(self, path: Path) -> Optional[float]:
        """获取文件修改时间"""
        try:
            return path.stat().st_mtime
        except FileNotFoundError:
            return None

    def _detect_changes(self) -> list:
        """检测文件变更"""
        events = []
        current_files = self._scan_directory()
        current_mtimes = {}

        for filepath in current_files:
            mtime = self._get_file_mtime(filepath)
            if mtime:
                current_mtimes[filepath] = mtime

        for filepath in current_files:
            if filepath not in self._file_mtimes:
                events.append(FileEvent(
                    event_type=FileEventType.CREATED,
                    path=str(filepath.relative_to(self.watch_path))
                ))
            elif current_mtimes.get(filepath) != self._file_mtimes.get(filepath):
                events.append(FileEvent(
                    event_type=FileEventType.MODIFIED,
                    path=str(filepath.relative_to(self.watch_path))
                ))

        for filepath in self._file_mtimes:
            if filepath not in current_files:
                events.append(FileEvent(
                    event_type=FileEventType.DELETED,
                    path=str(filepath.relative_to(self.watch_path))
                ))

        self._file_mtimes = current_mtimes
        return events

    async def _process_events(self):
        """处理事件"""
        events = self._detect_changes()

        for event in events:
            logger.debug(f"检测到文件事件: {event.event_type.value} - {event.path}")

            if self.callback:
                try:
                    if asyncio.iscoroutinefunction(self.callback):
                        await self.callback(event)
                    else:
                        self.callback(event)
                except Exception as e:
                    logger.error(f"处理事件回调失败: {e}")

    async def start(self):
        """启动监控"""
        if self._running:
            return

        self._running = True
        self._file_mtimes = {}

        current_files = self._scan_directory()
        for filepath in current_files:
            mtime = self._get_file_mtime(filepath)
            if mtime:
                self._file_mtimes[filepath] = mtime

        logger.info(f"文件监控器启动，监控目录: {self.watch_path}")

        while self._running:
            try:
                await self._process_events()
                await asyncio.sleep(self._check_interval)
            except Exception as e:
                logger.error(f"监控循环错误: {e}")
                await asyncio.sleep(1)

    def stop(self):
        """停止监控"""
        self._running = False
        logger.info("文件监控器已停止")

    def get_status(self) -> dict:
        """获取监控状态"""
        return {
            "running": self._running,
            "watch_path": str(self.watch_path),
            "tracked_files": len(self._file_mtimes),
            "check_interval": self._check_interval
        }


class DebouncedFileWatcher(FileWatcher):
    """带防抖的文件监控器"""

    def __init__(
        self,
        watch_path: str,
        callback: Optional[Callable[[FileEvent], None]] = None,
        debounce_seconds: float = 2.0,
        **kwargs
    ):
        super().__init__(watch_path, callback, debounce_seconds, **kwargs)
        self._event_buffer: dict = {}
        self._debounce_task: Optional[asyncio.Task] = None

    async def _debounce_handler(self):
        """防抖处理器"""
        while self._running:
            await asyncio.sleep(self.debounce_seconds)

            if not self._event_buffer:
                continue

            events_to_process = list(self._event_buffer.values())
            self._event_buffer.clear()

            for event in events_to_process:
                if self.callback:
                    try:
                        if asyncio.iscoroutinefunction(self.callback):
                            await self.callback(event)
                        else:
                            self.callback(event)
                    except Exception as e:
                        logger.error(f"处理事件回调失败: {e}")

    async def _process_events(self):
        """处理事件（带防抖）"""
        events = self._detect_changes()

        for event in events:
            key = f"{event.event_type.value}:{event.path}"
            self._event_buffer[key] = event

    async def start(self):
        """启动监控"""
        if self._running:
            return

        self._running = True
        self._file_mtimes = {}

        current_files = self._scan_directory()
        for filepath in current_files:
            mtime = self._get_file_mtime(filepath)
            if mtime:
                self._file_mtimes[filepath] = mtime

        self._debounce_task = asyncio.create_task(self._debounce_handler())

        logger.info(f"防抖文件监控器启动，监控目录: {self.watch_path}")

        while self._running:
            try:
                await self._process_events()
                await asyncio.sleep(self._check_interval)
            except Exception as e:
                logger.error(f"监控循环错误: {e}")
                await asyncio.sleep(1)

    def stop(self):
        """停止监控"""
        self._running = False
        if self._debounce_task:
            self._debounce_task.cancel()
        logger.info("防抖文件监控器已停止")
