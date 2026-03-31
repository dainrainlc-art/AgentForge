"""Obsidian 本地知识库集成客户端

功能特性:
- 读取和写入 Markdown 文件
- 解析 Obsidian 特有格式（双向链接、标签、属性）
- 监控文件变更
- 搜索和检索笔记
"""

import os
import re
import json
import hashlib
import frontmatter
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any, Set
from datetime import datetime
from enum import Enum
import asyncio
import aiofiles
import logging

logger = logging.getLogger(__name__)


class NoteType(Enum):
    """笔记类型"""
    KNOWLEDGE = "knowledge"
    PROJECT = "project"
    CLIENT = "client"
    TEMPLATE = "template"
    DAILY = "daily"
    UNKNOWN = "unknown"


@dataclass
class ObsidianNote:
    """Obsidian 笔记数据结构"""
    id: str
    title: str
    path: str
    content: str
    frontmatter: Dict[str, Any] = field(default_factory=dict)
    tags: Set[str] = field(default_factory=set)
    links: List[str] = field(default_factory=list)
    backlinks: List[str] = field(default_factory=list)
    embeddings: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    note_type: NoteType = NoteType.UNKNOWN
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "path": self.path,
            "content": self.content,
            "frontmatter": self.frontmatter,
            "tags": list(self.tags),
            "links": self.links,
            "backlinks": self.backlinks,
            "embeddings": self.embeddings,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "modified_at": self.modified_at.isoformat() if self.modified_at else None,
            "note_type": self.note_type.value,
            "metadata": self.metadata
        }


@dataclass
class SearchResult:
    """搜索结果"""
    note: ObsidianNote
    score: float
    highlights: List[str]
    match_type: str


class ObsidianClient:
    """Obsidian 本地知识库客户端"""

    def __init__(self, vault_path: str = "./data/obsidian_vault"):
        self.vault_path = Path(vault_path)
        self._notes: Dict[str, ObsidianNote] = {}
        self._link_graph: Dict[str, Set[str]] = {}
        self._tag_index: Dict[str, Set[str]] = {}
        self._initialized = False

        self._ensure_vault_structure()

    def _ensure_vault_structure(self):
        """确保 Vault 目录结构存在"""
        directories = [
            "专业知识库",
            "项目经验库",
            "客户资料库",
            "模板库",
            ".obsidian"
        ]
        for d in directories:
            (self.vault_path / d).mkdir(parents=True, exist_ok=True)

        obsidian_config = {
            "attachmentFolderPath": "attachments",
            "newFileLocation": "current",
            "promptDelete": False
        }
        config_path = self.vault_path / ".obsidian" / "app.json"
        if not config_path.exists():
            config_path.write_text(json.dumps(obsidian_config, indent=2))

    async def initialize(self) -> bool:
        """初始化客户端，加载所有笔记"""
        if self._initialized:
            return True

        try:
            await self._load_all_notes()
            self._build_indexes()
            self._initialized = True
            logger.info(f"Obsidian 客户端初始化完成，加载 {len(self._notes)} 篇笔记")
            return True
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            return False

    async def _load_all_notes(self):
        """加载所有 Markdown 笔记"""
        for md_file in self.vault_path.rglob("*.md"):
            if md_file.name.startswith("."):
                continue
            try:
                note = await self._load_note(md_file)
                if note:
                    self._notes[note.id] = note
            except Exception as e:
                logger.warning(f"加载笔记失败 {md_file}: {e}")

    async def _load_note(self, file_path: Path) -> Optional[ObsidianNote]:
        """加载单个笔记文件"""
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            content = await f.read()

        stat = file_path.stat()

        note_id = self._generate_id(str(file_path.relative_to(self.vault_path)))

        try:
            post = frontmatter.loads(content)
            fm = dict(post.metadata)
            body = post.content
        except:
            fm = {}
            body = content

        title = self._extract_title(body, file_path)
        tags = self._extract_tags(body, fm)
        links = self._extract_links(body)
        note_type = self._determine_note_type(file_path)

        return ObsidianNote(
            id=note_id,
            title=title,
            path=str(file_path.relative_to(self.vault_path)),
            content=body,
            frontmatter=fm,
            tags=tags,
            links=links,
            created_at=datetime.fromtimestamp(stat.st_ctime),
            modified_at=datetime.fromtimestamp(stat.st_mtime),
            note_type=note_type
        )

    def _generate_id(self, path: str) -> str:
        """生成笔记 ID"""
        return hashlib.md5(path.encode(), usedforsecurity=False).hexdigest()[:12]

    def _extract_title(self, content: str, file_path: Path) -> str:
        """提取笔记标题"""
        match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        return file_path.stem

    def _extract_tags(self, content: str, frontmatter: Dict) -> Set[str]:
        """提取标签"""
        tags = set()

        if 'tags' in frontmatter:
            fm_tags = frontmatter['tags']
            if isinstance(fm_tags, list):
                tags.update(fm_tags)
            elif isinstance(fm_tags, str):
                tags.add(fm_tags)

        inline_tags = re.findall(r'#(\w+(?:/\w+)*)', content)
        tags.update(inline_tags)

        return tags

    def _extract_links(self, content: str) -> List[str]:
        """提取双向链接"""
        wikilinks = re.findall(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', content)
        mdlinks = re.findall(r'\[([^\]]+)\]\(([^)]+\.md)\)', content)
        return list(set(wikilinks + [link[1] for link in mdlinks]))

    def _determine_note_type(self, file_path: Path) -> NoteType:
        """确定笔记类型"""
        parts = file_path.relative_to(self.vault_path).parts
        if len(parts) < 2:
            return NoteType.UNKNOWN

        category = parts[0]
        type_map = {
            "专业知识库": NoteType.KNOWLEDGE,
            "项目经验库": NoteType.PROJECT,
            "客户资料库": NoteType.CLIENT,
            "模板库": NoteType.TEMPLATE,
        }
        return type_map.get(category, NoteType.UNKNOWN)

    def _build_indexes(self):
        """构建索引"""
        self._link_graph.clear()
        self._tag_index.clear()

        for note_id, note in self._notes.items():
            for link in note.links:
                if link not in self._link_graph:
                    self._link_graph[link] = set()
                self._link_graph[link].add(note_id)

            for tag in note.tags:
                if tag not in self._tag_index:
                    self._tag_index[tag] = set()
                self._tag_index[tag].add(note_id)

        for note_id, note in self._notes.items():
            note.backlinks = list(self._link_graph.get(note.title, set()))

    async def create_note(
        self,
        title: str,
        content: str,
        folder: str = "",
        tags: Optional[List[str]] = None,
        frontmatter_data: Optional[Dict] = None
    ) -> ObsidianNote:
        """创建新笔记"""
        folder_path = self.vault_path / folder if folder else self.vault_path
        folder_path.mkdir(parents=True, exist_ok=True)

        safe_title = re.sub(r'[<>:"/\\|?*]', '', title)
        file_path = folder_path / f"{safe_title}.md"

        fm = frontmatter_data or {}
        if tags:
            fm['tags'] = tags
        fm['created'] = datetime.now().isoformat()
        fm['id'] = self._generate_id(str(file_path.relative_to(self.vault_path)))

        full_content = "---\n"
        full_content += yaml.dump(fm, allow_unicode=True, default_flow_style=False)
        full_content += "---\n\n"
        full_content += f"# {title}\n\n"
        full_content += content

        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
            await f.write(full_content)

        note = await self._load_note(file_path)
        if note:
            self._notes[note.id] = note
            self._update_indexes(note)

        return note

    async def update_note(
        self,
        note_id: str,
        content: Optional[str] = None,
        tags: Optional[List[str]] = None,
        frontmatter_data: Optional[Dict] = None
    ) -> Optional[ObsidianNote]:
        """更新笔记"""
        if note_id not in self._notes:
            return None

        note = self._notes[note_id]
        file_path = self.vault_path / note.path

        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            existing = await f.read()

        try:
            post = frontmatter.loads(existing)
        except:
            post = frontmatter.Post(existing)

        if content is not None:
            post.content = content

        if tags is not None:
            post.metadata['tags'] = tags

        if frontmatter_data:
            post.metadata.update(frontmatter_data)

        post.metadata['modified'] = datetime.now().isoformat()

        new_content = frontmatter.dumps(post)

        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
            await f.write(new_content)

        updated_note = await self._load_note(file_path)
        if updated_note:
            self._notes[note_id] = updated_note
            self._update_indexes(updated_note)

        return updated_note

    async def delete_note(self, note_id: str) -> bool:
        """删除笔记"""
        if note_id not in self._notes:
            return False

        note = self._notes[note_id]
        file_path = self.vault_path / note.path

        if file_path.exists():
            file_path.unlink()

        self._remove_from_indexes(note)
        del self._notes[note_id]

        return True

    def _update_indexes(self, note: ObsidianNote):
        """更新索引"""
        for tag in note.tags:
            if tag not in self._tag_index:
                self._tag_index[tag] = set()
            self._tag_index[tag].add(note.id)

        for link in note.links:
            if link not in self._link_graph:
                self._link_graph[link] = set()
            self._link_graph[link].add(note.id)

    def _remove_from_indexes(self, note: ObsidianNote):
        """从索引中移除"""
        for tag in note.tags:
            if tag in self._tag_index:
                self._tag_index[tag].discard(note.id)

        for link in note.links:
            if link in self._link_graph:
                self._link_graph[link].discard(note.id)

    async def search(
        self,
        query: str,
        tags: Optional[List[str]] = None,
        note_type: Optional[NoteType] = None,
        limit: int = 20
    ) -> List[SearchResult]:
        """搜索笔记"""
        results = []
        query_lower = query.lower()

        for note_id, note in self._notes.items():
            if note_type and note.note_type != note_type:
                continue

            if tags and not all(tag in note.tags for tag in tags):
                continue

            score = 0.0
            highlights = []
            match_type = "none"

            if query_lower in note.title.lower():
                score += 10.0
                highlights.append(f"标题: {note.title}")
                match_type = "title"

            if query_lower in note.content.lower():
                score += 5.0
                idx = note.content.lower().find(query_lower)
                start = max(0, idx - 50)
                end = min(len(note.content), idx + len(query) + 50)
                highlight = note.content[start:end]
                highlights.append(f"内容: ...{highlight}...")
                if match_type == "none":
                    match_type = "content"

            if query_lower in note.tags:
                score += 8.0
                highlights.append(f"标签: {query}")
                if match_type == "none":
                    match_type = "tag"

            if score > 0:
                results.append(SearchResult(
                    note=note,
                    score=score,
                    highlights=highlights,
                    match_type=match_type
                ))

        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]

    def get_note(self, note_id: str) -> Optional[ObsidianNote]:
        """获取笔记"""
        return self._notes.get(note_id)

    def get_note_by_title(self, title: str) -> Optional[ObsidianNote]:
        """通过标题获取笔记"""
        for note in self._notes.values():
            if note.title == title:
                return note
        return None

    def get_backlinks(self, note_id: str) -> List[ObsidianNote]:
        """获取反向链接"""
        if note_id not in self._notes:
            return []

        note = self._notes[note_id]
        backlinks = []
        for link_note_id in note.backlinks:
            if link_note_id in self._notes:
                backlinks.append(self._notes[link_note_id])
        return backlinks

    def get_notes_by_tag(self, tag: str) -> List[ObsidianNote]:
        """通过标签获取笔记"""
        note_ids = self._tag_index.get(tag, set())
        return [self._notes[nid] for nid in note_ids if nid in self._notes]

    def list_notes(
        self,
        note_type: Optional[NoteType] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ObsidianNote]:
        """列出笔记"""
        notes = list(self._notes.values())

        if note_type:
            notes = [n for n in notes if n.note_type == note_type]

        notes.sort(key=lambda x: x.modified_at or datetime.min, reverse=True)
        return notes[offset:offset + limit]

    def get_graph_data(self) -> Dict[str, Any]:
        """获取知识图谱数据"""
        nodes = []
        links = []

        for note_id, note in self._notes.items():
            nodes.append({
                "id": note_id,
                "title": note.title,
                "type": note.note_type.value,
                "tags": list(note.tags)
            })

            for link in note.links:
                target_note = self.get_note_by_title(link)
                if target_note:
                    links.append({
                        "source": note_id,
                        "target": target_note.id
                    })

        return {"nodes": nodes, "links": links}

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        type_counts = {}
        for note in self._notes.values():
            t = note.note_type.value
            type_counts[t] = type_counts.get(t, 0) + 1

        return {
            "total_notes": len(self._notes),
            "total_tags": len(self._tag_index),
            "total_links": len(self._link_graph),
            "by_type": type_counts
        }


import yaml
