"""YouTube Data API 客户端

功能特性:
- OAuth 2.0 认证
- 视频上传
- Shorts 发布
- 播放列表管理
- 评论管理
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


class VideoPrivacy(Enum):
    """视频隐私设置"""
    PUBLIC = "public"
    UNLISTED = "unlisted"
    PRIVATE = "private"


class VideoStatus(Enum):
    """视频状态"""
    UPLOADED = "uploaded"
    PROCESSED = "processed"
    FAILED = "failed"
    REJECTED = "rejected"


@dataclass
class YouTubeVideo:
    """YouTube 视频"""
    id: str
    title: str
    description: Optional[str] = None
    channel_id: Optional[str] = None
    channel_title: Optional[str] = None
    published_at: Optional[datetime] = None
    duration: Optional[str] = None
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    thumbnail_url: Optional[str] = None
    privacy: VideoPrivacy = VideoPrivacy.PUBLIC
    status: VideoStatus = VideoStatus.PROCESSED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "channel_id": self.channel_id,
            "channel_title": self.channel_title,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "duration": self.duration,
            "view_count": self.view_count,
            "like_count": self.like_count,
            "comment_count": self.comment_count,
            "thumbnail_url": self.thumbnail_url,
            "privacy": self.privacy.value,
            "status": self.status.value
        }


@dataclass
class YouTubePlaylist:
    """YouTube 播放列表"""
    id: str
    title: str
    description: Optional[str] = None
    channel_id: Optional[str] = None
    item_count: int = 0
    thumbnail_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "channel_id": self.channel_id,
            "item_count": self.item_count,
            "thumbnail_url": self.thumbnail_url
        }


@dataclass
class YouTubeComment:
    """YouTube 评论"""
    id: str
    text: str
    author_name: str
    author_channel_id: str
    published_at: Optional[datetime] = None
    like_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "author_name": self.author_name,
            "author_channel_id": self.author_channel_id,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "like_count": self.like_count
        }


class YouTubeClient:
    """YouTube Data API 客户端"""

    AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    API_URL = "https://www.googleapis.com/youtube/v3"
    UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"

    SCOPES = [
        "https://www.googleapis.com/auth/youtube",
        "https://www.googleapis.com/auth/youtube.upload",
        "https://www.googleapis.com/auth/youtube.readonly"
    ]

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        self.client_id = client_id or os.getenv("YOUTUBE_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("YOUTUBE_CLIENT_SECRET")
        self.access_token = access_token or os.getenv("YOUTUBE_ACCESS_TOKEN")
        self.refresh_token = refresh_token or os.getenv("YOUTUBE_REFRESH_TOKEN")
        self.api_key = api_key or os.getenv("YOUTUBE_API_KEY")

        self._client = httpx.AsyncClient(timeout=300.0)

    async def close(self):
        await self._client.aclose()

    def get_authorization_url(
        self,
        redirect_uri: str,
        state: Optional[str] = None
    ) -> str:
        import secrets

        if not state:
            state = secrets.token_urlsafe(16)

        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.SCOPES),
            "access_type": "offline",
            "prompt": "consent",
            "state": state
        }

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.AUTH_URL}?{query_string}"

    async def exchange_code_for_token(
        self,
        code: str,
        redirect_uri: str
    ) -> Dict[str, Any]:
        response = await self._client.post(
            self.TOKEN_URL,
            data={
                "code": code,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code"
            }
        )

        response.raise_for_status()
        token_data = response.json()
        self.access_token = token_data.get("access_token")
        self.refresh_token = token_data.get("refresh_token")
        return token_data

    async def refresh_access_token(self) -> Dict[str, Any]:
        if not self.refresh_token:
            raise ValueError("没有 refresh token")

        response = await self._client.post(
            self.TOKEN_URL,
            data={
                "refresh_token": self.refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "refresh_token"
            }
        )

        response.raise_for_status()
        token_data = response.json()
        self.access_token = token_data.get("access_token")
        return token_data

    def _get_auth_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        url = f"{self.API_URL}{endpoint}"
        headers = self._get_auth_headers()

        try:
            if method == "GET":
                response = await self._client.get(url, params=params, headers=headers)
            elif method == "POST":
                response = await self._client.post(url, params=params, json=data, headers=headers)
            elif method == "PUT":
                response = await self._client.put(url, params=params, json=data, headers=headers)
            elif method == "DELETE":
                response = await self._client.delete(url, params=params, headers=headers)
            else:
                raise ValueError(f"不支持的 HTTP 方法: {method}")

            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401 and self.refresh_token:
                await self.refresh_access_token()
                headers = self._get_auth_headers()
                if method == "GET":
                    response = await self._client.get(url, params=params, headers=headers)
                elif method == "POST":
                    response = await self._client.post(url, params=params, json=data, headers=headers)
                elif method == "PUT":
                    response = await self._client.put(url, params=params, json=data, headers=headers)
                elif method == "DELETE":
                    response = await self._client.delete(url, params=params, headers=headers)
                response.raise_for_status()
                return response.json()

            logger.error(f"YouTube API 错误: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"请求失败: {e}")
            raise

    async def get_channel(self) -> Dict[str, Any]:
        response = await self._request("GET", "/channels", params={
            "part": "snippet,contentDetails,statistics",
            "mine": "true"
        })

        items = response.get("items", [])
        if items:
            channel = items[0]
            snippet = channel.get("snippet", {})
            statistics = channel.get("statistics", {})

            return {
                "id": channel.get("id"),
                "title": snippet.get("title"),
                "description": snippet.get("description"),
                "custom_url": snippet.get("customUrl"),
                "subscriber_count": int(statistics.get("subscriberCount", 0)),
                "view_count": int(statistics.get("viewCount", 0)),
                "video_count": int(statistics.get("videoCount", 0))
            }

        return {}

    async def upload_video(
        self,
        video_data: bytes,
        title: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        category_id: str = "22",
        privacy: VideoPrivacy = VideoPrivacy.PUBLIC,
        is_short: bool = False
    ) -> YouTubeVideo:
        metadata = {
            "snippet": {
                "title": title,
                "description": description or "",
                "tags": tags or [],
                "categoryId": category_id
            },
            "status": {
                "privacyStatus": privacy.value,
                "selfDeclaredMadeForKids": False
            }
        }

        if is_short:
            metadata["snippet"]["tags"] = metadata["snippet"].get("tags", []) + ["#shorts"]

        response = await self._client.post(
            f"{self.UPLOAD_URL}?part=snippet,status",
            content=video_data,
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "video/*"
            },
            params={
                "uploadType": "media",
                "part": "snippet,status"
            },
            json=metadata
        )

        response.raise_for_status()
        result = response.json()

        return YouTubeVideo(
            id=result.get("id", ""),
            title=title,
            description=description,
            privacy=privacy
        )

    async def get_video(self, video_id: str) -> Optional[YouTubeVideo]:
        response = await self._request("GET", "/videos", params={
            "part": "snippet,contentDetails,statistics,status",
            "id": video_id
        })

        items = response.get("items", [])
        if not items:
            return None

        video = items[0]
        snippet = video.get("snippet", {})
        statistics = video.get("statistics", {})
        content_details = video.get("contentDetails", {})
        status = video.get("status", {})

        thumbnails = snippet.get("thumbnails", {})
        thumbnail_url = thumbnails.get("high", thumbnails.get("medium", thumbnails.get("default", {}))).get("url")

        privacy = VideoPrivacy.PRIVATE
        if status.get("privacyStatus") == "public":
            privacy = VideoPrivacy.PUBLIC
        elif status.get("privacyStatus") == "unlisted":
            privacy = VideoPrivacy.UNLISTED

        video_status = VideoStatus.PROCESSED
        if status.get("uploadStatus") == "uploaded":
            video_status = VideoStatus.UPLOADED
        elif status.get("uploadStatus") == "failed":
            video_status = VideoStatus.FAILED

        return YouTubeVideo(
            id=video.get("id", ""),
            title=snippet.get("title", ""),
            description=snippet.get("description"),
            channel_id=snippet.get("channelId"),
            channel_title=snippet.get("channelTitle"),
            published_at=self._parse_datetime(snippet.get("publishedAt")),
            duration=content_details.get("duration"),
            view_count=int(statistics.get("viewCount", 0)),
            like_count=int(statistics.get("likeCount", 0)),
            comment_count=int(statistics.get("commentCount", 0)),
            thumbnail_url=thumbnail_url,
            privacy=privacy,
            status=video_status
        )

    async def update_video(
        self,
        video_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        privacy: Optional[VideoPrivacy] = None
    ) -> YouTubeVideo:
        video = await self.get_video(video_id)
        if not video:
            raise ValueError(f"视频不存在: {video_id}")

        snippet = {
            "title": title or video.title,
            "description": description or video.description,
            "tags": tags or [],
            "categoryId": "22"
        }

        status = {
            "privacyStatus": (privacy or video.privacy).value
        }

        response = await self._request("PUT", "/videos", params={
            "part": "snippet,status"
        }, data={
            "id": video_id,
            "snippet": snippet,
            "status": status
        })

        return YouTubeVideo(
            id=video_id,
            title=snippet["title"],
            description=snippet["description"],
            privacy=privacy or video.privacy
        )

    async def delete_video(self, video_id: str) -> bool:
        try:
            await self._request("DELETE", "/videos", params={"id": video_id})
            return True
        except Exception as e:
            logger.error(f"删除视频失败: {e}")
            return False

    async def get_playlists(self, max_results: int = 25) -> List[YouTubePlaylist]:
        response = await self._request("GET", "/playlists", params={
            "part": "snippet,contentDetails",
            "mine": "true",
            "maxResults": max_results
        })

        playlists = []
        for item in response.get("items", []):
            snippet = item.get("snippet", {})
            content_details = item.get("contentDetails", {})

            thumbnails = snippet.get("thumbnails", {})
            thumbnail_url = thumbnails.get("high", thumbnails.get("medium", thumbnails.get("default", {}))).get("url")

            playlists.append(YouTubePlaylist(
                id=item.get("id", ""),
                title=snippet.get("title", ""),
                description=snippet.get("description"),
                channel_id=snippet.get("channelId"),
                item_count=int(content_details.get("itemCount", 0)),
                thumbnail_url=thumbnail_url
            ))

        return playlists

    async def create_playlist(
        self,
        title: str,
        description: Optional[str] = None,
        privacy: VideoPrivacy = VideoPrivacy.PUBLIC
    ) -> YouTubePlaylist:
        response = await self._request("POST", "/playlists", params={
            "part": "snippet,status"
        }, data={
            "snippet": {
                "title": title,
                "description": description or ""
            },
            "status": {
                "privacyStatus": privacy.value
            }
        })

        snippet = response.get("snippet", {})

        return YouTubePlaylist(
            id=response.get("id", ""),
            title=snippet.get("title", ""),
            description=snippet.get("description")
        )

    async def add_to_playlist(
        self,
        playlist_id: str,
        video_id: str
    ) -> bool:
        try:
            await self._request("POST", "/playlistItems", params={
                "part": "snippet"
            }, data={
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": video_id
                    }
                }
            })
            return True
        except Exception as e:
            logger.error(f"添加到播放列表失败: {e}")
            return False

    async def get_comments(
        self,
        video_id: str,
        max_results: int = 100
    ) -> List[YouTubeComment]:
        response = await self._request("GET", "/commentThreads", params={
            "part": "snippet",
            "videoId": video_id,
            "maxResults": max_results,
            "order": "relevance"
        })

        comments = []
        for item in response.get("items", []):
            snippet = item.get("snippet", {})
            top_comment = snippet.get("topLevelComment", {}).get("snippet", {})

            comments.append(YouTubeComment(
                id=item.get("id", ""),
                text=top_comment.get("textDisplay", ""),
                author_name=top_comment.get("authorDisplayName", ""),
                author_channel_id=top_comment.get("authorChannelId", {}).get("value", ""),
                published_at=self._parse_datetime(top_comment.get("publishedAt")),
                like_count=int(top_comment.get("likeCount", 0))
            ))

        return comments

    async def reply_to_comment(
        self,
        comment_id: str,
        text: str
    ) -> Optional[YouTubeComment]:
        try:
            response = await self._request("POST", "/comments", params={
                "part": "snippet"
            }, data={
                "snippet": {
                    "parentId": comment_id,
                    "textOriginal": text
                }
            })

            snippet = response.get("snippet", {})

            return YouTubeComment(
                id=response.get("id", ""),
                text=snippet.get("textDisplay", ""),
                author_name=snippet.get("authorDisplayName", ""),
                author_channel_id=snippet.get("authorChannelId", {}).get("value", "")
            )
        except Exception as e:
            logger.error(f"回复评论失败: {e}")
            return None

    async def search_videos(
        self,
        query: str,
        max_results: int = 25
    ) -> List[YouTubeVideo]:
        response = await self._request("GET", "/search", params={
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": max_results
        })

        videos = []
        for item in response.get("items", []):
            snippet = item.get("snippet", {})
            thumbnails = snippet.get("thumbnails", {})
            thumbnail_url = thumbnails.get("high", thumbnails.get("medium", thumbnails.get("default", {}))).get("url")

            videos.append(YouTubeVideo(
                id=item.get("id", {}).get("videoId", ""),
                title=snippet.get("title", ""),
                description=snippet.get("description"),
                channel_id=snippet.get("channelId"),
                channel_title=snippet.get("channelTitle"),
                published_at=self._parse_datetime(snippet.get("publishedAt")),
                thumbnail_url=thumbnail_url
            ))

        return videos

    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except:
            return None
