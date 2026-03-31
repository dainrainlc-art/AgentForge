"""Notion API 客户端 - 云端协作知识库集成

功能特性:
- OAuth 2.0 认证
- 数据库操作 (CRUD)
- 页面操作
- 块操作 (Block API)
- 搜索功能
"""

import os
import json
import hashlib
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, AsyncGenerator
from datetime import datetime
from enum import Enum
import httpx

logger = logging.getLogger(__name__)


class NotionObjectType(Enum):
    """Notion 对象类型"""
    PAGE = "page"
    DATABASE = "database"
    BLOCK = "block"
    USER = "user"


@dataclass
class NotionPage:
    """Notion 页面"""
    id: str
    title: str
    url: str
    parent_id: Optional[str] = None
    parent_type: Optional[str] = None
    created_time: Optional[datetime] = None
    last_edited_time: Optional[datetime] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    children: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "parent_id": self.parent_id,
            "parent_type": self.parent_type,
            "created_time": self.created_time.isoformat() if self.created_time else None,
            "last_edited_time": self.last_edited_time.isoformat() if self.last_edited_time else None,
            "properties": self.properties,
            "children": self.children
        }


@dataclass
class NotionDatabase:
    """Notion 数据库"""
    id: str
    title: str
    url: str
    properties: Dict[str, Any] = field(default_factory=dict)
    created_time: Optional[datetime] = None
    last_edited_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "properties": self.properties,
            "created_time": self.created_time.isoformat() if self.created_time else None,
            "last_edited_time": self.last_edited_time.isoformat() if self.last_edited_time else None
        }


class NotionClient:
    """Notion API 客户端"""

    BASE_URL = "https://api.notion.com/v1"
    API_VERSION = "2022-06-28"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("NOTION_API_KEY")
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Notion-Version": self.API_VERSION,
                "Content-Type": "application/json"
            },
            timeout=30.0
        )

    async def close(self):
        """关闭客户端"""
        await self._client.aclose()

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """发送请求"""
        try:
            response = await self._client.request(
                method,
                endpoint,
                json=data,
                params=params
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Notion API 错误: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"请求失败: {e}")
            raise

    async def list_databases(self) -> List[NotionDatabase]:
        """列出所有数据库"""
        databases = []

        response = await self._request("POST", "/search", data={
            "filter": {
                "property": "object",
                "value": "database"
            }
        })

        for result in response.get("results", []):
            db = self._parse_database(result)
            databases.append(db)

        return databases

    async def get_database(self, database_id: str) -> NotionDatabase:
        """获取数据库"""
        response = await self._request("GET", f"/databases/{database_id}")
        return self._parse_database(response)

    async def query_database(
        self,
        database_id: str,
        filter_conditions: Optional[Dict] = None,
        sorts: Optional[List[Dict]] = None,
        page_size: int = 100,
        start_cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """查询数据库"""
        data = {"page_size": page_size}

        if filter_conditions:
            data["filter"] = filter_conditions
        if sorts:
            data["sorts"] = sorts
        if start_cursor:
            data["start_cursor"] = start_cursor

        response = await self._request("POST", f"/databases/{database_id}/query", data=data)

        pages = [self._parse_page(p) for p in response.get("results", [])]

        return {
            "pages": pages,
            "has_more": response.get("has_more", False),
            "next_cursor": response.get("next_cursor")
        }

    async def create_page(
        self,
        parent_id: str,
        title: str,
        properties: Optional[Dict] = None,
        children: Optional[List[Dict]] = None
    ) -> NotionPage:
        """创建页面"""
        data = {
            "parent": {"database_id": parent_id},
            "properties": {
                "Name": {
                    "title": [{"text": {"content": title}}]
                }
            }
        }

        if properties:
            data["properties"].update(properties)

        if children:
            data["children"] = children

        response = await self._request("POST", "/pages", data=data)
        return self._parse_page(response)

    async def get_page(self, page_id: str) -> NotionPage:
        """获取页面"""
        response = await self._request("GET", f"/pages/{page_id}")
        return self._parse_page(response)

    async def update_page(
        self,
        page_id: str,
        properties: Optional[Dict] = None,
        archived: Optional[bool] = None
    ) -> NotionPage:
        """更新页面"""
        data = {}
        if properties:
            data["properties"] = properties
        if archived is not None:
            data["archived"] = archived

        response = await self._request("PATCH", f"/pages/{page_id}", data=data)
        return self._parse_page(response)

    async def delete_page(self, page_id: str) -> bool:
        """删除页面（归档）"""
        try:
            await self.update_page(page_id, archived=True)
            return True
        except Exception as e:
            logger.error(f"删除页面失败: {e}")
            return False

    async def get_block_children(self, block_id: str) -> List[Dict[str, Any]]:
        """获取块的子块"""
        response = await self._request("GET", f"/blocks/{block_id}/children")
        return response.get("results", [])

    async def append_block_children(
        self,
        block_id: str,
        children: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """追加子块"""
        data = {"children": children}
        response = await self._request("PATCH", f"/blocks/{block_id}/children", data=data)
        return response.get("results", [])

    async def create_block(
        self,
        parent_id: str,
        block_type: str,
        content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """创建块"""
        data = {
            "parent": {"block_id": parent_id},
            "type": block_type,
            block_type: content
        }
        response = await self._request("POST", "/blocks", data=data)
        return response

    async def search(
        self,
        query: str,
        filter_type: Optional[str] = None,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """搜索"""
        data = {
            "query": query,
            "page_size": page_size
        }

        if filter_type:
            data["filter"] = {
                "property": "object",
                "value": filter_type
            }

        response = await self._request("POST", "/search", data=data)

        results = []
        for result in response.get("results", []):
            if result.get("object") == "page":
                results.append(self._parse_page(result))
            elif result.get("object") == "database":
                results.append(self._parse_database(result))

        return {
            "results": results,
            "has_more": response.get("has_more", False),
            "next_cursor": response.get("next_cursor")
        }

    def _parse_page(self, data: Dict) -> NotionPage:
        """解析页面数据"""
        title = ""
        properties = data.get("properties", {})

        for prop_name, prop_value in properties.items():
            if prop_value.get("type") == "title":
                title_list = prop_value.get("title", [])
                if title_list:
                    title = title_list[0].get("plain_text", "")
                break

        parent = data.get("parent", {})

        return NotionPage(
            id=data.get("id", ""),
            title=title,
            url=data.get("url", ""),
            parent_id=parent.get("database_id") or parent.get("page_id"),
            parent_type=parent.get("type"),
            created_time=self._parse_datetime(data.get("created_time")),
            last_edited_time=self._parse_datetime(data.get("last_edited_time")),
            properties=properties
        )

    def _parse_database(self, data: Dict) -> NotionDatabase:
        """解析数据库数据"""
        title = ""
        title_list = data.get("title", [])
        if title_list:
            title = title_list[0].get("plain_text", "")

        return NotionDatabase(
            id=data.get("id", ""),
            title=title,
            url=data.get("url", ""),
            properties=data.get("properties", {}),
            created_time=self._parse_datetime(data.get("created_time")),
            last_edited_time=self._parse_datetime(data.get("last_edited_time"))
        )

    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """解析日期时间"""
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except:
            return None

    async def create_page_from_markdown(
        self,
        database_id: str,
        title: str,
        markdown_content: str,
        tags: Optional[List[str]] = None
    ) -> NotionPage:
        """从 Markdown 创建页面"""
        from .markdown_parser import MarkdownParser

        parser = MarkdownParser()
        parsed = parser.parse(markdown_content)

        properties = {}

        if tags:
            properties["Tags"] = {
                "multi_select": [{"name": tag} for tag in tags]
            }

        children = parser.convert_to_notion_blocks(markdown_content)

        return await self.create_page(
            parent_id=database_id,
            title=title,
            properties=properties,
            children=children[:100]
        )

    async def export_page_to_markdown(self, page_id: str) -> str:
        """导出页面为 Markdown"""
        page = await self.get_page(page_id)
        blocks = await self.get_block_children(page_id)

        md_content = f"# {page.title}\n\n"

        for block in blocks:
            md_content += self._block_to_markdown(block)

        return md_content

    def _block_to_markdown(self, block: Dict, indent: int = 0) -> str:
        """将块转换为 Markdown"""
        block_type = block.get("type", "")
        content = ""

        if block_type == "paragraph":
            text = self._extract_rich_text(block.get("paragraph", {}).get("rich_text", []))
            content = f"{'  ' * indent}{text}\n\n"

        elif block_type.startswith("heading_"):
            level = int(block_type.split("_")[1])
            text = self._extract_rich_text(block.get(block_type, {}).get("rich_text", []))
            content = f"{'#' * level} {text}\n\n"

        elif block_type == "bulleted_list_item":
            text = self._extract_rich_text(block.get("bulleted_list_item", {}).get("rich_text", []))
            content = f"{'  ' * indent}- {text}\n"

        elif block_type == "numbered_list_item":
            text = self._extract_rich_text(block.get("numbered_list_item", {}).get("rich_text", []))
            content = f"{'  ' * indent}1. {text}\n"

        elif block_type == "code":
            code_block = block.get("code", {})
            language = code_block.get("language", "")
            code = self._extract_rich_text(code_block.get("rich_text", []))
            content = f"```{language}\n{code}\n```\n\n"

        elif block_type == "quote":
            text = self._extract_rich_text(block.get("quote", {}).get("rich_text", []))
            content = f"> {text}\n\n"

        elif block_type == "divider":
            content = "---\n\n"

        return content

    def _extract_rich_text(self, rich_text: List[Dict]) -> str:
        """提取富文本内容"""
        return "".join(rt.get("plain_text", "") for rt in rich_text)
