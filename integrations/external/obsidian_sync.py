"""
AgentForge Enhanced Obsidian Integration
增强版Obsidian本地知识库双向同步
"""
from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel, Field
from pathlib import Path
import json
import re
import hashlib
import yaml
import shutil
from dataclasses import dataclass
from loguru import logger

from agentforge.config import settings


class SyncDirection(str, Enum):
    TO_OBSIDIAN = "to_obsidian"
    FROM_OBSIDIAN = "from_obsidian"
    BIDIRECTIONAL = "bidirectional"


class ConflictResolution(str, Enum):
    KEEP_LOCAL = "keep_local"
    KEEP_REMOTE = "keep_remote"
    KEEP_NEWER = "keep_newer"
    MERGE = "merge"
    MANUAL = "manual"


class SyncStatus(str, Enum):
    SYNCED = "synced"
    PENDING = "pending"
    CONFLICT = "conflict"
    ERROR = "error"


@dataclass
class SyncResult:
    status: SyncStatus
    message: str
    local_path: Optional[str] = None
    remote_id: Optional[str] = None
    conflicts: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.conflicts is None:
            self.conflicts = []


class NoteMetadata(BaseModel):
    title: str
    created: datetime
    updated: datetime
    tags: List[str] = Field(default_factory=list)
    aliases: List[str] = Field(default_factory=list)
    source: Optional[str] = None
    source_id: Optional[str] = None
    sync_status: SyncStatus = SyncStatus.SYNCED
    last_sync: Optional[datetime] = None
    checksum: Optional[str] = None
    custom: Dict[str, Any] = Field(default_factory=dict)


class ObsidianNote(BaseModel):
    path: str
    metadata: NoteMetadata
    content: str
    frontmatter: Dict[str, Any] = Field(default_factory=dict)


class SyncState(BaseModel):
    note_path: str
    remote_id: str
    local_checksum: str
    remote_checksum: str
    last_sync: datetime
    sync_direction: SyncDirection


class EnhancedObsidianClient:
    def __init__(
        self,
        vault_path: Optional[str] = None,
        attachments_folder: str = "attachments",
        templates_folder: str = "templates",
        sync_folder: str = ".agentforge_sync"
    ):
        self.vault_path = Path(vault_path or getattr(settings, 'obsidian_vault_path', '~/Obsidian')).expanduser()
        self.attachments_folder = attachments_folder
        self.templates_folder = templates_folder
        self.sync_folder = sync_folder
        
        self.sync_state_path = self.vault_path / sync_folder / "sync_state.json"
        self.conflict_folder = self.vault_path / sync_folder / "conflicts"
        
        self._ensure_directories()
        self._sync_state: Dict[str, SyncState] = {}
        self._load_sync_state()
    
    def _ensure_directories(self):
        directories = [
            self.vault_path / self.attachments_folder,
            self.vault_path / self.templates_folder,
            self.vault_path / self.sync_folder,
            self.conflict_folder
        ]
        for d in directories:
            d.mkdir(parents=True, exist_ok=True)
    
    def _load_sync_state(self):
        if self.sync_state_path.exists():
            try:
                with open(self.sync_state_path, 'r') as f:
                    data = json.load(f)
                    for key, value in data.items():
                        self._sync_state[key] = SyncState(**value)
            except Exception as e:
                logger.error(f"Failed to load sync state: {e}")
    
    def _save_sync_state(self):
        try:
            with open(self.sync_state_path, 'w') as f:
                json.dump({
                    k: v.model_dump() for k, v in self._sync_state.items()
                }, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save sync state: {e}")
    
    def _calculate_checksum(self, content: str) -> str:
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _parse_frontmatter(self, content: str) -> Tuple[Dict[str, Any], str]:
        if not content.startswith('---'):
            return {}, content
        
        parts = content.split('---', 2)
        if len(parts) < 3:
            return {}, content
        
        try:
            frontmatter = yaml.safe_load(parts[1]) or {}
            body = parts[2].strip()
            return frontmatter, body
        except Exception:
            return {}, content
    
    def _generate_frontmatter(self, metadata: NoteMetadata, extra: Dict[str, Any] = None) -> str:
        fm = {
            "title": metadata.title,
            "created": metadata.created.isoformat(),
            "updated": metadata.updated.isoformat(),
            "tags": metadata.tags,
            "aliases": metadata.aliases,
            "source": metadata.source,
            "source_id": metadata.source_id,
            "sync_status": metadata.sync_status.value,
            "last_sync": metadata.last_sync.isoformat() if metadata.last_sync else None,
            "checksum": metadata.checksum,
            **(extra or {})
        }
        
        fm = {k: v for k, v in fm.items() if v is not None and v != [] and v != ""}
        
        return f"---\n{yaml.dump(fm, default_flow_style=False, allow_unicode=True)}---\n\n"
    
    def read_note(self, note_path: str) -> Optional[ObsidianNote]:
        full_path = self.vault_path / note_path
        
        if not full_path.exists():
            return None
        
        try:
            content = full_path.read_text(encoding='utf-8')
            frontmatter, body = self._parse_frontmatter(content)
            
            metadata = NoteMetadata(
                title=frontmatter.get('title', full_path.stem),
                created=datetime.fromisoformat(frontmatter['created']) if 'created' in frontmatter else datetime.fromtimestamp(full_path.stat().st_ctime),
                updated=datetime.fromisoformat(frontmatter['updated']) if 'updated' in frontmatter else datetime.fromtimestamp(full_path.stat().st_mtime),
                tags=frontmatter.get('tags', []),
                aliases=frontmatter.get('aliases', []),
                source=frontmatter.get('source'),
                source_id=frontmatter.get('source_id'),
                sync_status=SyncStatus(frontmatter.get('sync_status', 'synced')),
                last_sync=datetime.fromisoformat(frontmatter['last_sync']) if 'last_sync' in frontmatter else None,
                checksum=frontmatter.get('checksum'),
                custom={k: v for k, v in frontmatter.items() if k not in {'title', 'created', 'updated', 'tags', 'aliases', 'source', 'source_id', 'sync_status', 'last_sync', 'checksum'}}
            )
            
            return ObsidianNote(
                path=note_path,
                metadata=metadata,
                content=body,
                frontmatter=frontmatter
            )
        except Exception as e:
            logger.error(f"Failed to read note {note_path}: {e}")
            return None
    
    def write_note(
        self,
        note_path: str,
        content: str,
        metadata: Optional[NoteMetadata] = None,
        overwrite: bool = True
    ) -> bool:
        full_path = self.vault_path / note_path
        
        if full_path.exists() and not overwrite:
            return False
        
        try:
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            if metadata is None:
                now = datetime.now()
                metadata = NoteMetadata(
                    title=full_path.stem,
                    created=now,
                    updated=now
                )
            
            metadata.updated = datetime.now()
            metadata.checksum = self._calculate_checksum(content)
            
            frontmatter_str = self._generate_frontmatter(metadata)
            full_content = frontmatter_str + content
            
            full_path.write_text(full_content, encoding='utf-8')
            
            return True
        except Exception as e:
            logger.error(f"Failed to write note {note_path}: {e}")
            return False
    
    def delete_note(self, note_path: str, trash: bool = True) -> bool:
        full_path = self.vault_path / note_path
        
        if not full_path.exists():
            return False
        
        try:
            if trash:
                trash_path = self.conflict_folder / f"{full_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                shutil.move(str(full_path), str(trash_path))
            else:
                full_path.unlink()
            
            return True
        except Exception as e:
            logger.error(f"Failed to delete note {note_path}: {e}")
            return False
    
    def list_notes(
        self,
        folder: Optional[str] = None,
        recursive: bool = True,
        include_synced: bool = True
    ) -> List[ObsidianNote]:
        search_path = self.vault_path / folder if folder else self.vault_path
        
        if not search_path.exists():
            return []
        
        notes = []
        
        try:
            pattern = "**/*.md" if recursive else "*.md"
            
            for md_file in search_path.glob(pattern):
                if md_file.name.startswith('.'):
                    continue
                
                if self.sync_folder in str(md_file):
                    continue
                
                relative_path = str(md_file.relative_to(self.vault_path))
                note = self.read_note(relative_path)
                
                if note:
                    if include_synced or note.metadata.sync_status != SyncStatus.SYNCED:
                        notes.append(note)
            
            return notes
        except Exception as e:
            logger.error(f"Failed to list notes: {e}")
            return []
    
    def search_notes(
        self,
        query: str,
        search_in_content: bool = True,
        search_in_tags: bool = True,
        case_sensitive: bool = False
    ) -> List[ObsidianNote]:
        all_notes = self.list_notes()
        results = []
        
        search_query = query if case_sensitive else query.lower()
        
        for note in all_notes:
            match = False
            
            title = note.metadata.title if case_sensitive else note.metadata.title.lower()
            if search_query in title:
                match = True
            
            elif search_in_content:
                content = note.content if case_sensitive else note.content.lower()
                if search_query in content:
                    match = True
            
            elif search_in_tags:
                for tag in note.metadata.tags:
                    tag_lower = tag if case_sensitive else tag.lower()
                    if search_query in tag_lower:
                        match = True
                        break
            
            if match:
                results.append(note)
        
        return results
    
    def get_backlinks(self, note_path: str) -> List[ObsidianNote]:
        all_notes = self.list_notes()
        note_name = Path(note_path).stem
        
        wiki_link_patterns = [
            f"[[{note_name}]]",
            f"[[{note_name}|",
        ]
        
        backlinks = []
        
        for note in all_notes:
            for pattern in wiki_link_patterns:
                if pattern in note.content:
                    backlinks.append(note)
                    break
        
        return backlinks
    
    def create_daily_note(
        self,
        date: Optional[datetime] = None,
        template: Optional[str] = None
    ) -> Optional[ObsidianNote]:
        note_date = date or datetime.now()
        
        folder = note_date.strftime("%Y/%m")
        title = note_date.strftime("%Y-%m-%d")
        note_path = f"{folder}/{title}.md"
        
        template_content = ""
        if template:
            template_path = self.vault_path / self.templates_folder / f"{template}.md"
            if template_path.exists():
                template_content = template_path.read_text(encoding='utf-8')
                template_content = template_content.replace("{{date}}", note_date.strftime("%Y-%m-%d"))
                template_content = template_content.replace("{{time}}", note_date.strftime("%H:%M"))
        
        now = datetime.now()
        metadata = NoteMetadata(
            title=title,
            created=now,
            updated=now,
            tags=["daily-note"],
            custom={"date": note_date.strftime("%Y-%m-%d"), "type": "daily"}
        )
        
        if self.write_note(note_path, template_content, metadata):
            return self.read_note(note_path)
        
        return None


class BidirectionalSyncManager:
    def __init__(
        self,
        obsidian_client: EnhancedObsidianClient,
        notion_client = None,
        conflict_resolution: ConflictResolution = ConflictResolution.KEEP_NEWER
    ):
        self.obsidian = obsidian_client
        self.notion = notion_client
        self.conflict_resolution = conflict_resolution
    
    async def sync_to_obsidian(
        self,
        remote_id: str,
        content: str,
        title: str,
        tags: List[str] = None,
        folder: str = "synced"
    ) -> SyncResult:
        safe_title = re.sub(r'[<>:"/\\|?*]', '', title)
        note_path = f"{folder}/{safe_title}.md"
        
        existing_note = self.obsidian.read_note(note_path)
        
        now = datetime.now()
        metadata = NoteMetadata(
            title=title,
            created=existing_note.metadata.created if existing_note else now,
            updated=now,
            tags=tags or [],
            source="notion",
            source_id=remote_id,
            last_sync=now
        )
        
        if existing_note:
            local_checksum = existing_note.metadata.checksum
            remote_checksum = self.obsidian._calculate_checksum(content)
            
            if local_checksum != remote_checksum:
                if existing_note.metadata.updated > now - timedelta(hours=1):
                    return SyncResult(
                        status=SyncStatus.CONFLICT,
                        message="Local note was modified after last sync",
                        local_path=note_path,
                        remote_id=remote_id,
                        conflicts=[{
                            "local_checksum": local_checksum,
                            "remote_checksum": remote_checksum,
                            "local_updated": existing_note.metadata.updated.isoformat()
                        }]
                    )
        
        if self.obsidian.write_note(note_path, content, metadata):
            return SyncResult(
                status=SyncStatus.SYNCED,
                message="Successfully synced to Obsidian",
                local_path=note_path,
                remote_id=remote_id
            )
        
        return SyncResult(
            status=SyncStatus.ERROR,
            message="Failed to write note to Obsidian"
        )
    
    async def sync_from_obsidian(
        self,
        note_path: str
    ) -> SyncResult:
        note = self.obsidian.read_note(note_path)
        
        if not note:
            return SyncResult(
                status=SyncStatus.ERROR,
                message=f"Note not found: {note_path}"
            )
        
        if not self.notion:
            return SyncResult(
                status=SyncStatus.ERROR,
                message="Notion client not configured"
            )
        
        if note.metadata.source_id:
            success = await self.notion.update_page(
                note.metadata.source_id,
                title=note.metadata.title,
                properties={"Tags": note.metadata.tags}
            )
            
            if success:
                now = datetime.now()
                note.metadata.last_sync = now
                note.metadata.sync_status = SyncStatus.SYNCED
                self.obsidian.write_note(note_path, note.content, note.metadata)
                
                return SyncResult(
                    status=SyncStatus.SYNCED,
                    message="Successfully synced to Notion",
                    local_path=note_path,
                    remote_id=note.metadata.source_id
                )
        else:
            page = await self.notion.create_page(
                title=note.metadata.title,
                content=note.content,
                properties={"Tags": note.metadata.tags}
            )
            
            if page:
                now = datetime.now()
                note.metadata.source_id = page.id
                note.metadata.source = "notion"
                note.metadata.last_sync = now
                note.metadata.sync_status = SyncStatus.SYNCED
                self.obsidian.write_note(note_path, note.content, note.metadata)
                
                return SyncResult(
                    status=SyncStatus.SYNCED,
                    message="Successfully created in Notion",
                    local_path=note_path,
                    remote_id=page.id
                )
        
        return SyncResult(
            status=SyncStatus.ERROR,
            message="Failed to sync to Notion"
        )
    
    async def full_sync(
        self,
        direction: SyncDirection = SyncDirection.BIDIRECTIONAL
    ) -> Dict[str, SyncResult]:
        results = {}
        
        if direction in [SyncDirection.FROM_OBSIDIAN, SyncDirection.BIDIRECTIONAL]:
            obsidian_notes = self.obsidian.list_notes()
            
            for note in obsidian_notes:
                if note.metadata.sync_status == SyncStatus.PENDING:
                    result = await self.sync_from_obsidian(note.path)
                    results[f"obsidian:{note.path}"] = result
        
        if direction in [SyncDirection.TO_OBSIDIAN, SyncDirection.BIDIRECTIONAL]:
            if self.notion:
                notion_pages = await self.notion.query_database()
                
                for page in notion_pages:
                    note_path = f"synced/{page.title}.md"
                    existing = self.obsidian.read_note(note_path)
                    
                    if not existing or existing.metadata.source_id == page.id:
                        full_page = await self.notion.get_page(page.id)
                        if full_page:
                            result = await self.sync_to_obsidian(
                                page.id,
                                full_page.content,
                                full_page.title,
                                []
                            )
                            results[f"notion:{page.id}"] = result
        
        return results
    
    def resolve_conflict(
        self,
        note_path: str,
        resolution: ConflictResolution,
        custom_content: Optional[str] = None
    ) -> bool:
        note = self.obsidian.read_note(note_path)
        if not note:
            return False
        
        if custom_content:
            note.content = custom_content
        elif resolution == ConflictResolution.KEEP_LOCAL:
            pass
        elif resolution == ConflictResolution.KEEP_REMOTE:
            return False
        
        note.metadata.sync_status = SyncStatus.SYNCED
        note.metadata.last_sync = datetime.now()
        
        return self.obsidian.write_note(note_path, note.content, note.metadata)


class KnowledgeGraphBuilder:
    def __init__(self, obsidian_client: EnhancedObsidianClient):
        self.obsidian = obsidian_client
    
    def build_graph(self) -> Dict[str, Any]:
        notes = self.obsidian.list_notes()
        
        nodes = []
        edges = []
        node_map = {}
        
        for note in notes:
            node_id = note.path
            node_map[note.path] = len(nodes)
            
            nodes.append({
                "id": node_id,
                "title": note.metadata.title,
                "tags": note.metadata.tags,
                "created": note.metadata.created.isoformat(),
                "updated": note.metadata.updated.isoformat(),
                "word_count": len(note.content.split())
            })
        
        for note in notes:
            source_idx = node_map[note.path]
            
            wiki_links = re.findall(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', note.content)
            
            for link in wiki_links:
                for other_note in notes:
                    if other_note.metadata.title.lower() == link.lower():
                        target_idx = node_map[other_note.path]
                        edges.append({
                            "source": source_idx,
                            "target": target_idx,
                            "type": "wiki_link"
                        })
                        break
        
        return {
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "total_notes": len(nodes),
                "total_links": len(edges),
                "avg_links_per_note": len(edges) / len(nodes) if nodes else 0
            }
        }
    
    def find_orphan_notes(self) -> List[ObsidianNote]:
        notes = self.obsidian.list_notes()
        orphan_notes = []
        
        for note in notes:
            backlinks = self.obsidian.get_backlinks(note.path)
            if not backlinks:
                orphan_notes.append(note)
        
        return orphan_notes
    
    def find_unlinked_clusters(self) -> List[List[str]]:
        notes = self.obsidian.list_notes()
        graph = self.build_graph()
        
        visited = set()
        clusters = []
        
        def dfs(node_idx: int, cluster: List[int]):
            if node_idx in visited:
                return
            visited.add(node_idx)
            cluster.append(node_idx)
            
            for edge in graph["edges"]:
                if edge["source"] == node_idx and edge["target"] not in visited:
                    dfs(edge["target"], cluster)
                elif edge["target"] == node_idx and edge["source"] not in visited:
                    dfs(edge["source"], cluster)
        
        for i in range(len(graph["nodes"])):
            if i not in visited:
                cluster = []
                dfs(i, cluster)
                if len(cluster) > 1:
                    clusters.append([graph["nodes"][idx]["id"] for idx in cluster])
        
        return clusters


class ConflictType(str, Enum):
    CONTENT_MODIFIED = "content_modified"
    METADATA_MODIFIED = "metadata_modified"
    DELETED_MODIFIED = "deleted_modified"
    BOTH_MODIFIED = "both_modified"
    RENAME_CONFLICT = "rename_conflict"


class ConflictRecord(BaseModel):
    id: str
    note_path: str
    conflict_type: ConflictType
    local_content: str
    remote_content: str
    base_content: Optional[str] = None
    local_metadata: Dict[str, Any]
    remote_metadata: Dict[str, Any]
    detected_at: datetime = Field(default_factory=datetime.now)
    resolved: bool = False
    resolution: Optional[ConflictResolution] = None
    resolved_content: Optional[str] = None
    resolved_at: Optional[datetime] = None


class ContentDiff(BaseModel):
    additions: List[Tuple[int, str]]
    deletions: List[Tuple[int, str]]
    modifications: List[Tuple[int, str, str]]
    similarity_score: float


class EnhancedConflictDetector:
    def __init__(self, obsidian_client: EnhancedObsidianClient):
        self.obsidian = obsidian_client
        self._conflict_history: Dict[str, List[ConflictRecord]] = {}
        self._base_versions: Dict[str, str] = {}
    
    def save_base_version(self, note_path: str, content: str):
        self._base_versions[note_path] = content
    
    def detect_conflict(
        self,
        note_path: str,
        local_content: str,
        remote_content: str,
        local_metadata: Dict[str, Any],
        remote_metadata: Dict[str, Any]
    ) -> Optional[ConflictRecord]:
        base_content = self._base_versions.get(note_path)
        
        local_changed = local_content != base_content
        remote_changed = remote_content != base_content
        
        if not local_changed and not remote_changed:
            return None
        
        if local_changed and not remote_changed:
            return None
        
        if not local_changed and remote_changed:
            return None
        
        import secrets
        conflict = ConflictRecord(
            id=f"conflict_{secrets.token_hex(4)}",
            note_path=note_path,
            conflict_type=ConflictType.BOTH_MODIFIED,
            local_content=local_content,
            remote_content=remote_content,
            base_content=base_content,
            local_metadata=local_metadata,
            remote_metadata=remote_metadata
        )
        
        if note_path not in self._conflict_history:
            self._conflict_history[note_path] = []
        self._conflict_history[note_path].append(conflict)
        
        return conflict
    
    def compute_diff(
        self,
        content1: str,
        content2: str
    ) -> ContentDiff:
        lines1 = content1.split('\n')
        lines2 = content2.split('\n')
        
        additions = []
        deletions = []
        modifications = []
        
        from difflib import SequenceMatcher
        matcher = SequenceMatcher(None, lines1, lines2)
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'insert':
                for i, line in enumerate(lines2[j1:j2]):
                    additions.append((j1 + i + 1, line))
            elif tag == 'delete':
                for i, line in enumerate(lines1[i1:i2]):
                    deletions.append((i1 + i + 1, line))
            elif tag == 'replace':
                for i, (old, new) in enumerate(zip(lines1[i1:i2], lines2[j1:j2])):
                    modifications.append((i1 + i + 1, old, new))
                if len(lines1[i1:i2]) < len(lines2[j1:j2]):
                    for i, line in enumerate(lines2[j1 + len(lines1[i1:i2]):j2]):
                        additions.append((j1 + i + 1, line))
                elif len(lines1[i1:i2]) > len(lines2[j1:j2]):
                    for i, line in enumerate(lines1[i1 + len(lines2[j1:j2]):i2]):
                        deletions.append((i1 + i + 1, line))
        
        similarity = matcher.ratio()
        
        return ContentDiff(
            additions=additions,
            deletions=deletions,
            modifications=modifications,
            similarity_score=similarity
        )
    
    def three_way_merge(
        self,
        base: str,
        local: str,
        remote: str
    ) -> Tuple[str, List[str]]:
        from difflib import SequenceMatcher
        
        base_lines = base.split('\n') if base else []
        local_lines = local.split('\n')
        remote_lines = remote.split('\n')
        
        local_changes = self._get_changes(base_lines, local_lines)
        remote_changes = self._get_changes(base_lines, remote_lines)
        
        merged_lines = base_lines.copy()
        conflicts = []
        
        all_indices = set(local_changes.keys()) | set(remote_changes.keys())
        
        for idx in sorted(all_indices):
            local_change = local_changes.get(idx)
            remote_change = remote_changes.get(idx)
            
            if local_change and remote_change:
                if local_change == remote_change:
                    if idx < len(merged_lines):
                        merged_lines[idx] = local_change
                    else:
                        merged_lines.append(local_change)
                else:
                    conflicts.append(f"Line {idx + 1}: conflict between local and remote changes")
                    merged_lines.insert(idx, f"<<<<<<< LOCAL\n{local_change}\n=======\n{remote_change}\n>>>>>>> REMOTE")
            elif local_change:
                if idx < len(merged_lines):
                    merged_lines[idx] = local_change
                else:
                    merged_lines.append(local_change)
            elif remote_change:
                if idx < len(merged_lines):
                    merged_lines[idx] = remote_change
                else:
                    merged_lines.append(remote_change)
        
        return '\n'.join(merged_lines), conflicts
    
    def _get_changes(self, base: List[str], modified: List[str]) -> Dict[int, str]:
        changes = {}
        
        from difflib import SequenceMatcher
        matcher = SequenceMatcher(None, base, modified)
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag in ('replace', 'insert'):
                for i, line in enumerate(modified[j1:j2]):
                    changes[i1 + i] = line
        
        return changes
    
    def auto_resolve(
        self,
        conflict: ConflictRecord,
        strategy: ConflictResolution = ConflictResolution.KEEP_NEWER
    ) -> str:
        if strategy == ConflictResolution.KEEP_LOCAL:
            return conflict.local_content
        
        elif strategy == ConflictResolution.KEEP_REMOTE:
            return conflict.remote_content
        
        elif strategy == ConflictResolution.KEEP_NEWER:
            local_time = conflict.local_metadata.get('updated', datetime.min)
            remote_time = conflict.remote_metadata.get('updated', datetime.min)
            
            if isinstance(local_time, str):
                local_time = datetime.fromisoformat(local_time)
            if isinstance(remote_time, str):
                remote_time = datetime.fromisoformat(remote_time)
            
            return conflict.local_content if local_time > remote_time else conflict.remote_content
        
        elif strategy == ConflictResolution.MERGE:
            merged, _ = self.three_way_merge(
                conflict.base_content or "",
                conflict.local_content,
                conflict.remote_content
            )
            return merged
        
        return conflict.local_content
    
    def get_conflict_history(self, note_path: str) -> List[ConflictRecord]:
        return self._conflict_history.get(note_path, [])
    
    def generate_conflict_report(
        self,
        conflict: ConflictRecord
    ) -> str:
        diff = self.compute_diff(conflict.local_content, conflict.remote_content)
        
        report = [
            f"# Conflict Report: {conflict.note_path}",
            f"",
            f"**Conflict ID**: {conflict.id}",
            f"**Type**: {conflict.conflict_type.value}",
            f"**Detected**: {conflict.detected_at.isoformat()}",
            f"",
            f"## Statistics",
            f"- Similarity Score: {diff.similarity_score:.2%}",
            f"- Additions: {len(diff.additions)}",
            f"- Deletions: {len(diff.deletions)}",
            f"- Modifications: {len(diff.modifications)}",
            f"",
            f"## Local Changes",
        ]
        
        for line_num, line in diff.additions[:10]:
            report.append(f"+ Line {line_num}: {line[:50]}...")
        
        report.extend(["", "## Remote Changes"])
        
        for line_num, line in diff.deletions[:10]:
            report.append(f"- Line {line_num}: {line[:50]}...")
        
        return '\n'.join(report)


class SmartConflictResolver:
    def __init__(
        self,
        detector: EnhancedConflictDetector,
        auto_resolve_threshold: float = 0.9
    ):
        self.detector = detector
        self.auto_resolve_threshold = auto_resolve_threshold
    
    async def analyze_and_resolve(
        self,
        conflict: ConflictRecord
    ) -> Tuple[str, bool, str]:
        diff = self.detector.compute_diff(
            conflict.local_content,
            conflict.remote_content
        )
        
        if diff.similarity_score >= self.auto_resolve_threshold:
            merged, conflicts = self.detector.three_way_merge(
                conflict.base_content or "",
                conflict.local_content,
                conflict.remote_content
            )
            
            if not conflicts:
                return merged, True, "Auto-merged successfully (high similarity)"
        
        if diff.additions and not diff.deletions and not diff.modifications:
            return conflict.remote_content, True, "Auto-resolved: remote only has additions"
        
        if diff.deletions and not diff.additions and not diff.modifications:
            return conflict.remote_content, True, "Auto-resolved: remote only has deletions"
        
        from agentforge.llm.model_router import ModelRouter
        llm = ModelRouter()
        
        prompt = f"""Analyze this content conflict and suggest the best resolution.

Local content:
```
{conflict.local_content[:1000]}
```

Remote content:
```
{conflict.remote_content[:1000]}
```

Similarity: {diff.similarity_score:.2%}

Changes:
- Additions: {len(diff.additions)}
- Deletions: {len(diff.deletions)}
- Modifications: {len(diff.modifications)}

Provide:
1. Recommended resolution: "local", "remote", or "merged"
2. Merged content (if applicable)
3. Reason for recommendation

Format as JSON:
{{"resolution": "...", "merged_content": "...", "reason": "..."}}"""

        try:
            response = await llm.chat_with_failover(
                message=prompt,
                task_type="analysis"
            )
            
            import json
            result = json.loads(response)
            
            if result.get("resolution") == "local":
                return conflict.local_content, False, f"AI suggests local: {result.get('reason')}"
            elif result.get("resolution") == "remote":
                return conflict.remote_content, False, f"AI suggests remote: {result.get('reason')}"
            elif result.get("resolution") == "merged":
                return result.get("merged_content", conflict.local_content), False, f"AI merged: {result.get('reason')}"
        except Exception as e:
            logger.warning(f"AI conflict resolution failed: {e}")
        
        return conflict.local_content, False, "Manual resolution required"
