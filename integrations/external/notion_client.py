"""
AgentForge Knowledge Base Integration
Complete integration for Notion and Obsidian
"""
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel, Field
import httpx
import json
import re
import hashlib
from pathlib import Path
from loguru import logger

from agentforge.config import settings


class KnowledgeSource(str, Enum):
    NOTION = "notion"
    OBSIDIAN = "obsidian"
    LOCAL = "local"


class DocumentType(str, Enum):
    PAGE = "page"
    NOTE = "note"
    DATABASE = "database"
    TEMPLATE = "template"
    DAILY_NOTE = "daily_note"


class DocumentStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    DELETED = "deleted"


class KnowledgeDocument(BaseModel):
    id: str
    source: KnowledgeSource
    doc_type: DocumentType
    title: str
    content: str
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    parent_id: Optional[str] = None
    url: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NotionPage(BaseModel):
    id: str
    title: str
    content: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    url: Optional[str] = None
    parent_id: Optional[str] = None


class NotionDatabase(BaseModel):
    id: str
    title: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)


class NotionBlock(BaseModel):
    id: str
    type: str
    content: str
    children: List["NotionBlock"] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NotionClient:
    BASE_URL = "https://api.notion.com/v1"
    API_VERSION = "2022-06-28"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        database_id: Optional[str] = None
    ):
        self.api_key = api_key or getattr(settings, 'notion_api_key', None)
        self.database_id = database_id or getattr(settings, 'notion_database_id', None)
        
        if not self.api_key:
            logger.warning("Notion API key not configured")
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Notion-Version": self.API_VERSION
        }
    
    async def list_databases(self) -> List[NotionDatabase]:
        if not self.api_key:
            return []
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.BASE_URL}/search",
                    headers=self._get_headers(),
                    json={
                        "filter": {
                            "property": "object",
                            "value": "database"
                        },
                        "page_size": 100
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    databases = []
                    for result in data.get("results", []):
                        title_list = result.get("title", [])
                        title = title_list[0].get("plain_text", "") if title_list else "Untitled"
                        
                        databases.append(NotionDatabase(
                            id=result["id"],
                            title=title,
                            properties=result.get("properties", {}),
                            created_at=datetime.fromisoformat(result["created_time"].replace("Z", "+00:00"))
                        ))
                    return databases
                return []
                
        except Exception as e:
            logger.error(f"Failed to list databases: {e}")
            return []
    
    async def create_database(
        self,
        parent_page_id: str,
        title: str,
        properties: Dict[str, Any]
    ) -> Optional[NotionDatabase]:
        if not self.api_key:
            return None
        
        try:
            default_properties = {
                "Name": {"title": {}},
                "Status": {
                    "select": {
                        "options": [
                            {"name": "To Do", "color": "gray"},
                            {"name": "In Progress", "color": "blue"},
                            {"name": "Done", "color": "green"}
                        ]
                    }
                },
                "Tags": {"multi_select": {"options": []}},
                "Date": {"date": {}},
                **properties
            }
            
            payload = {
                "parent": {"page_id": parent_page_id},
                "title": [{"type": "text", "text": {"content": title}}],
                "properties": default_properties
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.BASE_URL}/databases",
                    headers=self._get_headers(),
                    json=payload
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return NotionDatabase(
                        id=data["id"],
                        title=title,
                        properties=data.get("properties", {}),
                        created_at=datetime.now()
                    )
                return None
                
        except Exception as e:
            logger.error(f"Failed to create database: {e}")
            return None
    
    async def create_page(
        self,
        title: str,
        content: str,
        parent_id: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        icon: Optional[str] = None,
        cover_url: Optional[str] = None
    ) -> Optional[NotionPage]:
        if not self.api_key:
            return None
        
        try:
            parent = {"database_id": self.database_id} if not parent_id else {"page_id": parent_id}
            
            page_properties = {
                "title": [{"type": "text", "text": {"content": title}}]
            }
            
            if properties:
                for key, value in properties.items():
                    if isinstance(value, str):
                        page_properties[key] = {"rich_text": [{"text": {"content": value}}]}
                    elif isinstance(value, list):
                        page_properties[key] = {"multi_select": [{"name": tag} for tag in value]}
                    elif isinstance(value, datetime):
                        page_properties[key] = {"date": {"start": value.isoformat()}}
            
            payload = {
                "parent": parent,
                "properties": page_properties
            }
            
            if icon:
                payload["icon"] = {"type": "emoji", "emoji": icon}
            
            if cover_url:
                payload["cover"] = {"type": "external", "external": {"url": cover_url}}
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.BASE_URL}/pages",
                    headers=self._get_headers(),
                    json=payload
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if content:
                        await self._append_blocks(data["id"], content)
                    
                    return NotionPage(
                        id=data["id"],
                        title=title,
                        content=content,
                        properties=page_properties,
                        created_at=datetime.now(),
                        updated_at=datetime.now(),
                        url=data.get("url"),
                        parent_id=parent_id or self.database_id
                    )
                else:
                    logger.error(f"Notion API error: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to create page: {e}")
            return None
    
    async def _append_blocks(self, page_id: str, content: str) -> bool:
        blocks = self._parse_content_to_blocks(content)
        
        if not blocks:
            return True
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.patch(
                    f"{self.BASE_URL}/blocks/{page_id}/children",
                    headers=self._get_headers(),
                    json={"children": blocks}
                )
                
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Failed to append blocks: {e}")
            return False
    
    def _parse_content_to_blocks(self, content: str) -> List[Dict[str, Any]]:
        blocks = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith('# '):
                blocks.append({
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {"rich_text": [{"type": "text", "text": {"content": line[2:]}}]}
                })
            elif line.startswith('## '):
                blocks.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {"rich_text": [{"type": "text", "text": {"content": line[3:]}}]}
                })
            elif line.startswith('### '):
                blocks.append({
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {"rich_text": [{"type": "text", "text": {"content": line[4:]}}]}
                })
            elif line.startswith('- ') or line.startswith('* '):
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": line[2:]}}]}
                })
            elif line.startswith('1. ') or line.startswith('2. ') or line.startswith('3. '):
                blocks.append({
                    "object": "block",
                    "type": "numbered_list_item",
                    "numbered_list_item": {"rich_text": [{"type": "text", "text": {"content": line[3:]}}]}
                })
            elif line.startswith('> '):
                blocks.append({
                    "object": "block",
                    "type": "quote",
                    "quote": {"rich_text": [{"type": "text", "text": {"content": line[2:]}}]}
                })
            elif line.startswith('```'):
                pass
            elif line.startswith('- [ ]') or line.startswith('- [x]'):
                checked = line.startswith('- [x]')
                blocks.append({
                    "object": "block",
                    "type": "to_do",
                    "to_do": {
                        "rich_text": [{"type": "text", "text": {"content": line[6:]}}],
                        "checked": checked
                    }
                })
            else:
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"type": "text", "text": {"content": line}}]}
                })
        
        return blocks
    
    async def get_page(self, page_id: str) -> Optional[NotionPage]:
        if not self.api_key:
            return None
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/pages/{page_id}",
                    headers=self._get_headers()
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    title_prop = data.get("properties", {}).get("title", {})
                    title_list = title_prop.get("title", [])
                    title = title_list[0].get("plain_text", "") if title_list else "Untitled"
                    
                    content = await self._get_page_content(page_id)
                    
                    return NotionPage(
                        id=data["id"],
                        title=title,
                        content=content,
                        properties=data.get("properties", {}),
                        created_at=datetime.fromisoformat(data["created_time"].replace("Z", "+00:00")),
                        updated_at=datetime.fromisoformat(data["last_edited_time"].replace("Z", "+00:00")),
                        url=data.get("url"),
                        parent_id=data.get("parent", {}).get("page_id") or data.get("parent", {}).get("database_id")
                    )
                return None
                
        except Exception as e:
            logger.error(f"Failed to get page: {e}")
            return None
    
    async def _get_page_content(self, page_id: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/blocks/{page_id}/children",
                    headers=self._get_headers()
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content_parts = []
                    
                    for block in data.get("results", []):
                        text = self._extract_text_from_block(block)
                        if text:
                            content_parts.append(text)
                    
                    return '\n'.join(content_parts)
                return ""
                
        except Exception as e:
            logger.error(f"Failed to get page content: {e}")
            return ""
    
    def _extract_text_from_block(self, block: Dict[str, Any]) -> str:
        block_type = block.get("type", "")
        
        if block_type == "paragraph":
            rich_text = block.get("paragraph", {}).get("rich_text", [])
            return ''.join(t.get("plain_text", "") for t in rich_text)
        
        elif block_type == "heading_1":
            rich_text = block.get("heading_1", {}).get("rich_text", [])
            return '# ' + ''.join(t.get("plain_text", "") for t in rich_text)
        
        elif block_type == "heading_2":
            rich_text = block.get("heading_2", {}).get("rich_text", [])
            return '## ' + ''.join(t.get("plain_text", "") for t in rich_text)
        
        elif block_type == "heading_3":
            rich_text = block.get("heading_3", {}).get("rich_text", [])
            return '### ' + ''.join(t.get("plain_text", "") for t in rich_text)
        
        elif block_type == "bulleted_list_item":
            rich_text = block.get("bulleted_list_item", {}).get("rich_text", [])
            return '- ' + ''.join(t.get("plain_text", "") for t in rich_text)
        
        elif block_type == "numbered_list_item":
            rich_text = block.get("numbered_list_item", {}).get("rich_text", [])
            return '1. ' + ''.join(t.get("plain_text", "") for t in rich_text)
        
        elif block_type == "quote":
            rich_text = block.get("quote", {}).get("rich_text", [])
            return '> ' + ''.join(t.get("plain_text", "") for t in rich_text)
        
        elif block_type == "to_do":
            rich_text = block.get("to_do", {}).get("rich_text", [])
            checked = block.get("to_do", {}).get("checked", False)
            prefix = '- [x] ' if checked else '- [ ] '
            return prefix + ''.join(t.get("plain_text", "") for t in rich_text)
        
        elif block_type == "code":
            rich_text = block.get("code", {}).get("rich_text", [])
            language = block.get("code", {}).get("language", "")
            return f'```{language}\n' + ''.join(t.get("plain_text", "") for t in rich_text) + '\n```'
        
        return ""
    
    async def update_page(
        self,
        page_id: str,
        title: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None
    ) -> bool:
        if not self.api_key:
            return False
        
        try:
            update_properties = {}
            
            if title:
                update_properties["title"] = [{"type": "text", "text": {"content": title}}]
            
            if properties:
                for key, value in properties.items():
                    if isinstance(value, str):
                        update_properties[key] = {"rich_text": [{"text": {"content": value}}]}
                    elif isinstance(value, list):
                        update_properties[key] = {"multi_select": [{"name": tag} for tag in value]}
                    elif isinstance(value, datetime):
                        update_properties[key] = {"date": {"start": value.isoformat()}}
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.patch(
                    f"{self.BASE_URL}/pages/{page_id}",
                    headers=self._get_headers(),
                    json={"properties": update_properties}
                )
                
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Failed to update page: {e}")
            return False
    
    async def delete_page(self, page_id: str) -> bool:
        if not self.api_key:
            return False
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.patch(
                    f"{self.BASE_URL}/pages/{page_id}",
                    headers=self._get_headers(),
                    json={"archived": True}
                )
                
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Failed to delete page: {e}")
            return False
    
    async def query_database(
        self,
        database_id: Optional[str] = None,
        filter: Optional[Dict[str, Any]] = None,
        sorts: Optional[List[Dict[str, Any]]] = None,
        page_size: int = 100,
        start_cursor: Optional[str] = None
    ) -> List[NotionPage]:
        db_id = database_id or self.database_id
        if not self.api_key or not db_id:
            return []
        
        try:
            payload = {"page_size": page_size}
            
            if filter:
                payload["filter"] = filter
            
            if sorts:
                payload["sorts"] = sorts
            
            if start_cursor:
                payload["start_cursor"] = start_cursor
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.BASE_URL}/databases/{db_id}/query",
                    headers=self._get_headers(),
                    json=payload
                )
                
                if response.status_code == 200:
                    data = response.json()
                    pages = []
                    
                    for result in data.get("results", []):
                        title_prop = result.get("properties", {}).get("Name", {})
                        title_list = title_prop.get("title", [])
                        title = title_list[0].get("plain_text", "") if title_list else "Untitled"
                        
                        pages.append(NotionPage(
                            id=result["id"],
                            title=title,
                            content="",
                            properties=result.get("properties", {}),
                            created_at=datetime.fromisoformat(result["created_time"].replace("Z", "+00:00")),
                            updated_at=datetime.fromisoformat(result["last_edited_time"].replace("Z", "+00:00")),
                            url=result.get("url")
                        ))
                    
                    return pages
                return []
                
        except Exception as e:
            logger.error(f"Failed to query database: {e}")
            return []
    
    async def search(
        self,
        query: str,
        filter_type: Optional[str] = None,
        page_size: int = 10
    ) -> List[NotionPage]:
        if not self.api_key:
            return []
        
        try:
            payload = {
                "query": query,
                "page_size": page_size
            }
            
            if filter_type:
                payload["filter"] = {
                    "property": "object",
                    "value": filter_type
                }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.BASE_URL}/search",
                    headers=self._get_headers(),
                    json=payload
                )
                
                if response.status_code == 200:
                    data = response.json()
                    pages = []
                    
                    for result in data.get("results", []):
                        if result.get("object") == "page":
                            props = result.get("properties", {})
                            title_prop = props.get("title", {}) or props.get("Name", {})
                            title_list = title_prop.get("title", [])
                            title = title_list[0].get("plain_text", "") if title_list else "Untitled"
                            
                            pages.append(NotionPage(
                                id=result["id"],
                                title=title,
                                content="",
                                properties=props,
                                created_at=datetime.fromisoformat(result["created_time"].replace("Z", "+00:00")),
                                updated_at=datetime.fromisoformat(result["last_edited_time"].replace("Z", "+00:00")),
                                url=result.get("url")
                            ))
                    
                    return pages
                return []
                
        except Exception as e:
            logger.error(f"Failed to search: {e}")
            return []
    
    async def health_check(self) -> bool:
        if not self.api_key:
            return False
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/users/me",
                    headers=self._get_headers()
                )
                return response.status_code == 200
        except Exception:
            return False


class ObsidianClient:
    def __init__(
        self,
        vault_path: Optional[str] = None,
        attachments_folder: str = "attachments"
    ):
        self.vault_path = Path(vault_path or getattr(settings, 'obsidian_vault_path', '~/Obsidian'))
        self.attachments_folder = attachments_folder
        
        if isinstance(self.vault_path, str):
            self.vault_path = Path(self.vault_path).expanduser()
        
        if not self.vault_path.exists():
            logger.warning(f"Obsidian vault path does not exist: {self.vault_path}")
    
    async def list_notes(
        self,
        folder: Optional[str] = None,
        recursive: bool = True
    ) -> List[KnowledgeDocument]:
        search_path = self.vault_path / folder if folder else self.vault_path
        
        if not search_path.exists():
            return []
        
        notes = []
        
        try:
            if recursive:
                pattern = "**/*.md"
            else:
                pattern = "*.md"
            
            for md_file in search_path.glob(pattern):
                if md_file.name.startswith('.'):
                    continue
                
                note = await self._parse_markdown_file(md_file)
                if note:
                    notes.append(note)
            
            return notes
            
        except Exception as e:
            logger.error(f"Failed to list notes: {e}")
            return []
    
    async def _parse_markdown_file(self, file_path: Path) -> Optional[KnowledgeDocument]:
        try:
            content = file_path.read_text(encoding='utf-8')
            
            frontmatter = {}
            body = content
            
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    import yaml
                    try:
                        frontmatter = yaml.safe_load(parts[1]) or {}
                    except Exception:
                        pass
                    body = parts[2].strip()
            
            title = frontmatter.get('title', file_path.stem)
            tags = frontmatter.get('tags', [])
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(',')]
            
            relative_path = file_path.relative_to(self.vault_path)
            
            return KnowledgeDocument(
                id=str(relative_path),
                source=KnowledgeSource.OBSIDIAN,
                doc_type=DocumentType.NOTE,
                title=title,
                content=body,
                tags=tags,
                created_at=datetime.fromtimestamp(file_path.stat().st_ctime),
                updated_at=datetime.fromtimestamp(file_path.stat().st_mtime),
                metadata={
                    "frontmatter": frontmatter,
                    "file_path": str(file_path),
                    "relative_path": str(relative_path)
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to parse markdown file {file_path}: {e}")
            return None
    
    async def create_note(
        self,
        title: str,
        content: str,
        folder: Optional[str] = None,
        tags: Optional[List[str]] = None,
        frontmatter: Optional[Dict[str, Any]] = None,
        template: Optional[str] = None
    ) -> Optional[KnowledgeDocument]:
        try:
            note_folder = self.vault_path / folder if folder else self.vault_path
            note_folder.mkdir(parents=True, exist_ok=True)
            
            safe_title = re.sub(r'[<>:"/\\|?*]', '', title)
            file_path = note_folder / f"{safe_title}.md"
            
            if file_path.exists():
                counter = 1
                while file_path.exists():
                    file_path = note_folder / f"{safe_title} ({counter}).md"
                    counter += 1
            
            full_frontmatter = {
                "title": title,
                "created": datetime.now().isoformat(),
                "tags": tags or []
            }
            
            if frontmatter:
                full_frontmatter.update(frontmatter)
            
            if template:
                template_content = await self._load_template(template)
                if template_content:
                    content = template_content.replace("{{title}}", title)
                    content = content.replace("{{date}}", datetime.now().strftime("%Y-%m-%d"))
                    content = content.replace("{{time}}", datetime.now().strftime("%H:%M"))
            
            import yaml
            frontmatter_str = yaml.dump(full_frontmatter, default_flow_style=False)
            
            full_content = f"---\n{frontmatter_str}---\n\n{content}"
            
            file_path.write_text(full_content, encoding='utf-8')
            
            return KnowledgeDocument(
                id=str(file_path.relative_to(self.vault_path)),
                source=KnowledgeSource.OBSIDIAN,
                doc_type=DocumentType.NOTE,
                title=title,
                content=content,
                tags=tags or [],
                created_at=datetime.now(),
                updated_at=datetime.now(),
                metadata={
                    "frontmatter": full_frontmatter,
                    "file_path": str(file_path)
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to create note: {e}")
            return None
    
    async def _load_template(self, template_name: str) -> Optional[str]:
        template_path = self.vault_path / "templates" / f"{template_name}.md"
        
        if template_path.exists():
            return template_path.read_text(encoding='utf-8')
        
        return None
    
    async def get_note(self, note_path: str) -> Optional[KnowledgeDocument]:
        file_path = self.vault_path / note_path
        
        if not file_path.exists():
            return None
        
        return await self._parse_markdown_file(file_path)
    
    async def update_note(
        self,
        note_path: str,
        content: Optional[str] = None,
        tags: Optional[List[str]] = None,
        frontmatter: Optional[Dict[str, Any]] = None,
        append: bool = False
    ) -> bool:
        file_path = self.vault_path / note_path
        
        if not file_path.exists():
            return False
        
        try:
            existing = await self._parse_markdown_file(file_path)
            if not existing:
                return False
            
            existing_frontmatter = existing.metadata.get("frontmatter", {})
            
            if content:
                if append:
                    new_content = existing.content + "\n\n" + content
                else:
                    new_content = content
            else:
                new_content = existing.content
            
            if tags:
                existing_frontmatter["tags"] = tags
            
            if frontmatter:
                existing_frontmatter.update(frontmatter)
            
            existing_frontmatter["updated"] = datetime.now().isoformat()
            
            import yaml
            frontmatter_str = yaml.dump(existing_frontmatter, default_flow_style=False)
            
            full_content = f"---\n{frontmatter_str}---\n\n{new_content}"
            
            file_path.write_text(full_content, encoding='utf-8')
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update note: {e}")
            return False
    
    async def delete_note(self, note_path: str) -> bool:
        file_path = self.vault_path / note_path
        
        if not file_path.exists():
            return False
        
        try:
            trash_path = self.vault_path / ".trash"
            trash_path.mkdir(exist_ok=True)
            
            trash_file = trash_path / f"{file_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            file_path.rename(trash_file)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete note: {e}")
            return False
    
    async def search_notes(
        self,
        query: str,
        search_in_content: bool = True,
        search_in_tags: bool = True,
        case_sensitive: bool = False
    ) -> List[KnowledgeDocument]:
        all_notes = await self.list_notes()
        
        results = []
        query_lower = query.lower() if not case_sensitive else query
        
        for note in all_notes:
            match = False
            
            if query_lower in (note.title.lower() if not case_sensitive else note.title):
                match = True
            
            elif search_in_content and query_lower in (note.content.lower() if not case_sensitive else note.content):
                match = True
            
            elif search_in_tags:
                for tag in note.tags:
                    if query_lower in (tag.lower() if not case_sensitive else tag):
                        match = True
                        break
            
            if match:
                results.append(note)
        
        return results
    
    async def create_daily_note(
        self,
        date: Optional[datetime] = None,
        template: Optional[str] = None
    ) -> Optional[KnowledgeDocument]:
        note_date = date or datetime.now()
        
        folder = note_date.strftime("%Y/%m")
        title = note_date.strftime("%Y-%m-%d")
        
        return await self.create_note(
            title=title,
            content="",
            folder=folder,
            template=template or "daily",
            frontmatter={
                "date": note_date.strftime("%Y-%m-%d"),
                "type": "daily"
            }
        )
    
    async def get_backlinks(self, note_path: str) -> List[KnowledgeDocument]:
        all_notes = await self.list_notes()
        
        note_name = Path(note_path).stem
        wiki_link = f"[[{note_name}]]"
        
        backlinks = []
        
        for note in all_notes:
            if wiki_link in note.content:
                backlinks.append(note)
        
        return backlinks
    
    async def health_check(self) -> bool:
        return self.vault_path.exists() and self.vault_path.is_dir()


class KnowledgeBaseManager:
    def __init__(self):
        self.notion = NotionClient()
        self.obsidian = ObsidianClient()
    
    async def sync_notion_to_obsidian(
        self,
        database_id: Optional[str] = None,
        target_folder: str = "notion-sync"
    ) -> List[KnowledgeDocument]:
        pages = await self.notion.query_database(database_id)
        
        synced = []
        
        for page in pages:
            full_page = await self.notion.get_page(page.id)
            if full_page:
                note = await self.obsidian.create_note(
                    title=full_page.title,
                    content=full_page.content,
                    folder=target_folder,
                    tags=["notion-sync"],
                    frontmatter={
                        "notion_id": full_page.id,
                        "notion_url": full_page.url,
                        "synced_at": datetime.now().isoformat()
                    }
                )
                
                if note:
                    synced.append(note)
        
        return synced
    
    async def sync_obsidian_to_notion(
        self,
        folder: Optional[str] = None,
        tags_filter: Optional[List[str]] = None
    ) -> List[NotionPage]:
        notes = await self.obsidian.list_notes(folder)
        
        synced = []
        
        for note in notes:
            if tags_filter:
                if not any(tag in note.tags for tag in tags_filter):
                    continue
            
            page = await self.notion.create_page(
                title=note.title,
                content=note.content,
                properties={
                    "Tags": note.tags,
                    "Source": "obsidian"
                }
            )
            
            if page:
                synced.append(page)
        
        return synced
    
    async def search_all(
        self,
        query: str,
        sources: Optional[List[KnowledgeSource]] = None
    ) -> Dict[str, List[KnowledgeDocument]]:
        results = {}
        
        sources_to_search = sources or [KnowledgeSource.NOTION, KnowledgeSource.OBSIDIAN]
        
        if KnowledgeSource.NOTION in sources_to_search:
            notion_pages = await self.notion.search(query)
            results["notion"] = [
                KnowledgeDocument(
                    id=p.id,
                    source=KnowledgeSource.NOTION,
                    doc_type=DocumentType.PAGE,
                    title=p.title,
                    content=p.content,
                    tags=[],
                    created_at=p.created_at,
                    updated_at=p.updated_at,
                    url=p.url,
                    metadata={"properties": p.properties}
                )
                for p in notion_pages
            ]
        
        if KnowledgeSource.OBSIDIAN in sources_to_search:
            obsidian_notes = await self.obsidian.search_notes(query)
            results["obsidian"] = obsidian_notes
        
        return results
    
    async def health_check(self) -> Dict[str, bool]:
        return {
            "notion": await self.notion.health_check(),
            "obsidian": await self.obsidian.health_check()
        }
