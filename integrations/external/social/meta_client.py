"""Facebook/Instagram Graph API 客户端

功能特性:
- OAuth 2.0 认证
- Facebook 页面发布
- Instagram 内容发布
- 媒体上传
- 内容管理
"""

import os
import json
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import httpx

logger = logging.getLogger(__name__)


class MediaType(Enum):
    """媒体类型"""
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    CAROUSEL = "CAROUSEL"


@dataclass
class FacebookPage:
    """Facebook 页面"""
    id: str
    name: str
    access_token: str
    category: Optional[str] = None
    fan_count: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "access_token": "***",
            "category": self.category,
            "fan_count": self.fan_count
        }


@dataclass
class FacebookPost:
    """Facebook 帖子"""
    id: str
    message: str
    created_time: Optional[datetime] = None
    permalink: Optional[str] = None
    media_url: Optional[str] = None
    media_type: Optional[MediaType] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "message": self.message,
            "created_time": self.created_time.isoformat() if self.created_time else None,
            "permalink": self.permalink,
            "media_url": self.media_url,
            "media_type": self.media_type.value if self.media_type else None
        }


@dataclass
class InstagramMedia:
    """Instagram 媒体"""
    id: str
    caption: Optional[str] = None
    media_type: MediaType = MediaType.IMAGE
    media_url: Optional[str] = None
    permalink: Optional[str] = None
    timestamp: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "caption": self.caption,
            "media_type": self.media_type.value,
            "media_url": self.media_url,
            "permalink": self.permalink,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }


class MetaClient:
    """Facebook/Instagram Graph API 客户端"""

    GRAPH_URL = "https://graph.facebook.com/v18.0"

    def __init__(
        self,
        app_id: Optional[str] = None,
        app_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        page_id: Optional[str] = None,
        instagram_account_id: Optional[str] = None
    ):
        self.app_id = app_id or os.getenv("FACEBOOK_APP_ID")
        self.app_secret = app_secret or os.getenv("FACEBOOK_APP_SECRET")
        self.access_token = access_token or os.getenv("FACEBOOK_ACCESS_TOKEN")
        self.page_id = page_id or os.getenv("FACEBOOK_PAGE_ID")
        self.instagram_account_id = instagram_account_id or os.getenv("INSTAGRAM_ACCOUNT_ID")

        self._client = httpx.AsyncClient(timeout=60.0)
        self._page_access_token: Optional[str] = None

    async def close(self):
        await self._client.aclose()

    def get_authorization_url(
        self,
        redirect_uri: str,
        scope: str = "pages_show_list,pages_read_engagement,pages_manage_posts,instagram_basic,instagram_content_publish"
    ) -> str:
        params = {
            "client_id": self.app_id,
            "redirect_uri": redirect_uri,
            "scope": scope,
            "response_type": "code"
        }
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"https://www.facebook.com/v18.0/dialog/oauth?{query_string}"

    async def exchange_code_for_token(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        response = await self._client.get(
            f"{self.GRAPH_URL}/oauth/access_token",
            params={
                "client_id": self.app_id,
                "client_secret": self.app_secret,
                "redirect_uri": redirect_uri,
                "code": code
            }
        )

        response.raise_for_status()
        token_data = response.json()
        self.access_token = token_data.get("access_token")
        return token_data

    async def get_long_lived_token(self) -> Dict[str, Any]:
        response = await self._client.get(
            f"{self.GRAPH_URL}/oauth/access_token",
            params={
                "grant_type": "fb_exchange_token",
                "client_id": self.app_id,
                "client_secret": self.app_secret,
                "fb_exchange_token": self.access_token
            }
        )

        response.raise_for_status()
        return response.json()

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        url = f"{self.GRAPH_URL}{endpoint}"

        if params is None:
            params = {}
        params["access_token"] = self._page_access_token or self.access_token

        try:
            if method == "GET":
                response = await self._client.get(url, params=params)
            elif method == "POST":
                response = await self._client.post(url, params=params, data=data)
            elif method == "DELETE":
                response = await self._client.delete(url, params=params)
            else:
                raise ValueError(f"不支持的 HTTP 方法: {method}")

            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Meta API 错误: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"请求失败: {e}")
            raise

    async def get_pages(self) -> List[FacebookPage]:
        response = await self._request("GET", "/me/accounts", params={
            "fields": "id,name,category,fan_count,access_token"
        })

        pages = []
        for page_data in response.get("data", []):
            pages.append(FacebookPage(
                id=page_data.get("id", ""),
                name=page_data.get("name", ""),
                access_token=page_data.get("access_token", ""),
                category=page_data.get("category"),
                fan_count=page_data.get("fan_count")
            ))

        return pages

    async def set_page(self, page_id: str):
        self.page_id = page_id
        pages = await self.get_pages()
        for page in pages:
            if page.id == page_id:
                self._page_access_token = page.access_token
                break

    async def post_to_page(
        self,
        message: str,
        link: Optional[str] = None,
        media_url: Optional[str] = None
    ) -> FacebookPost:
        if not self.page_id:
            raise ValueError("未设置页面 ID")

        data: Dict[str, Any] = {"message": message}

        if link:
            data["link"] = link

        endpoint = f"/{self.page_id}/feed"

        if media_url:
            data["url"] = media_url
            endpoint = f"/{self.page_id}/photos"

        response = await self._request("POST", endpoint, data=data)

        post_id = response.get("id", "") or response.get("post_id", "")

        return FacebookPost(
            id=post_id,
            message=message,
            media_url=media_url
        )

    async def post_photo_to_page(
        self,
        message: str,
        photo_url: str
    ) -> FacebookPost:
        return await self.post_to_page(message, media_url=photo_url)

    async def post_video_to_page(
        self,
        message: str,
        video_url: str,
        title: Optional[str] = None,
        description: Optional[str] = None
    ) -> FacebookPost:
        if not self.page_id:
            raise ValueError("未设置页面 ID")

        data: Dict[str, Any] = {
            "description": message,
            "file_url": video_url
        }

        if title:
            data["title"] = title
        if description:
            data["description"] = description

        response = await self._request("POST", f"/{self.page_id}/videos", data=data)

        return FacebookPost(
            id=response.get("id", ""),
            message=message,
            media_type=MediaType.VIDEO
        )

    async def delete_post(self, post_id: str) -> bool:
        try:
            await self._request("DELETE", f"/{post_id}")
            return True
        except Exception as e:
            logger.error(f"删除帖子失败: {e}")
            return False

    async def get_page_posts(
        self,
        limit: int = 25,
        since: Optional[str] = None
    ) -> List[FacebookPost]:
        if not self.page_id:
            raise ValueError("未设置页面 ID")

        params: Dict[str, Any] = {
            "fields": "id,message,created_time,permalink_url,attachments{media_type,url}",
            "limit": limit
        }

        if since:
            params["since"] = since

        response = await self._request("GET", f"/{self.page_id}/posts", params=params)

        posts = []
        for post_data in response.get("data", []):
            media_url = None
            media_type = None
            attachments = post_data.get("attachments", {}).get("data", [])
            if attachments:
                attachment = attachments[0]
                media_url = attachment.get("url")
                mt = attachment.get("media_type")
                if mt == "photo":
                    media_type = MediaType.IMAGE
                elif mt == "video":
                    media_type = MediaType.VIDEO

            posts.append(FacebookPost(
                id=post_data.get("id", ""),
                message=post_data.get("message", ""),
                created_time=self._parse_datetime(post_data.get("created_time")),
                permalink=post_data.get("permalink_url"),
                media_url=media_url,
                media_type=media_type
            ))

        return posts

    async def get_instagram_account_id(self) -> Optional[str]:
        if not self.page_id:
            return None

        response = await self._request("GET", f"/{self.page_id}", params={
            "fields": "instagram_business_account"
        })

        ig_account = response.get("instagram_business_account", {})
        self.instagram_account_id = ig_account.get("id")
        return self.instagram_account_id

    async def create_instagram_container(
        self,
        image_url: str,
        caption: Optional[str] = None
    ) -> str:
        if not self.instagram_account_id:
            await self.get_instagram_account_id()

        if not self.instagram_account_id:
            raise ValueError("无法获取 Instagram 账户 ID")

        params: Dict[str, Any] = {
            "image_url": image_url
        }

        if caption:
            params["caption"] = caption

        response = await self._request(
            "POST",
            f"/{self.instagram_account_id}/media",
            params=params
        )

        return response.get("id", "")

    async def create_instagram_video_container(
        self,
        video_url: str,
        caption: Optional[str] = None
    ) -> str:
        if not self.instagram_account_id:
            await self.get_instagram_account_id()

        if not self.instagram_account_id:
            raise ValueError("无法获取 Instagram 账户 ID")

        params: Dict[str, Any] = {
            "media_type": "VIDEO",
            "video_url": video_url
        }

        if caption:
            params["caption"] = caption

        response = await self._request(
            "POST",
            f"/{self.instagram_account_id}/media",
            params=params
        )

        return response.get("id", "")

    async def publish_instagram_media(self, creation_id: str) -> InstagramMedia:
        if not self.instagram_account_id:
            raise ValueError("未设置 Instagram 账户 ID")

        response = await self._request(
            "POST",
            f"/{self.instagram_account_id}/media_publish",
            params={"creation_id": creation_id}
        )

        return InstagramMedia(
            id=response.get("id", ""),
            media_type=MediaType.IMAGE
        )

    async def post_to_instagram(
        self,
        image_url: str,
        caption: Optional[str] = None
    ) -> InstagramMedia:
        container_id = await self.create_instagram_container(image_url, caption)

        import asyncio
        await asyncio.sleep(5)

        return await self.publish_instagram_media(container_id)

    async def get_instagram_media(
        self,
        limit: int = 25
    ) -> List[InstagramMedia]:
        if not self.instagram_account_id:
            await self.get_instagram_account_id()

        if not self.instagram_account_id:
            return []

        response = await self._request(
            "GET",
            f"/{self.instagram_account_id}/media",
            params={
                "fields": "id,caption,media_type,media_url,permalink,timestamp",
                "limit": limit
            }
        )

        media_list = []
        for media_data in response.get("data", []):
            mt = media_data.get("media_type", "IMAGE")
            media_type = MediaType.IMAGE if mt == "IMAGE" else MediaType.VIDEO if mt == "VIDEO" else MediaType.CAROUSEL

            media_list.append(InstagramMedia(
                id=media_data.get("id", ""),
                caption=media_data.get("caption"),
                media_type=media_type,
                media_url=media_data.get("media_url"),
                permalink=media_data.get("permalink"),
                timestamp=self._parse_datetime(media_data.get("timestamp"))
            ))

        return media_list

    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except:
            return None
