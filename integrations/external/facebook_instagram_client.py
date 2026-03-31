"""
AgentForge Facebook and Instagram API Clients
Complete integration for Facebook Graph API and Instagram Graph API
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import httpx
import hashlib
import hmac
import base64
import secrets
import json
from pathlib import Path
from loguru import logger

from agentforge.config import settings


class FacebookClient:
    BASE_URL = "https://graph.facebook.com/v18.0"
    
    def __init__(
        self,
        app_id: Optional[str] = None,
        app_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        page_id: Optional[str] = None
    ):
        self.app_id = app_id or getattr(settings, 'facebook_app_id', None)
        self.app_secret = app_secret or getattr(settings, 'facebook_app_secret', None)
        self.access_token = access_token or getattr(settings, 'facebook_access_token', None)
        self.page_id = page_id or getattr(settings, 'facebook_page_id', None)
    
    async def get_long_lived_token(self) -> Optional[str]:
        if not all([self.app_id, self.app_secret, self.access_token]):
            return None
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/oauth/access_token",
                    params={
                        "grant_type": "fb_exchange_token",
                        "client_id": self.app_id,
                        "client_secret": self.app_secret,
                        "fb_exchange_token": self.access_token
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("access_token")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get long-lived token: {e}")
            return None
    
    async def get_page_access_token(self) -> Optional[str]:
        if not self.access_token:
            return None
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/me/accounts",
                    params={"access_token": self.access_token}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    for page in data.get("data", []):
                        if page.get("id") == self.page_id:
                            return page.get("access_token")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get page token: {e}")
            return None
    
    async def get_page_info(self) -> Optional[Dict[str, Any]]:
        if not self.page_id or not self.access_token:
            return None
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/{self.page_id}",
                    params={
                        "fields": "id,name,fan_count,website,about,category",
                        "access_token": self.access_token
                    }
                )
                
                if response.status_code == 200:
                    return response.json()
                return None
                
        except Exception as e:
            logger.error(f"Failed to get page info: {e}")
            return None
    
    async def create_post(
        self,
        message: str,
        link: Optional[str] = None,
        photos: Optional[List[str]] = None,
        scheduled_time: Optional[datetime] = None
    ) -> Optional[Dict[str, Any]]:
        if not self.page_id or not self.access_token:
            logger.warning("Facebook page not configured")
            return None
        
        try:
            page_token = await self.get_page_access_token()
            token = page_token or self.access_token
            
            if photos and len(photos) > 0:
                return await self._create_photo_post(message, photos, token, scheduled_time)
            
            params = {
                "message": message,
                "access_token": token
            }
            
            if link:
                params["link"] = link
            
            if scheduled_time:
                params["published"] = "false"
                params["scheduled_publish_time"] = str(int(scheduled_time.timestamp()))
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.BASE_URL}/{self.page_id}/feed",
                    params=params
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "post_id": data.get("id"),
                        "success": True
                    }
                else:
                    error = response.json().get("error", {})
                    logger.error(f"Facebook API error: {error.get('message', response.text)}")
                    return {
                        "success": False,
                        "error": error.get("message", "Unknown error")
                    }
                    
        except Exception as e:
            logger.error(f"Failed to create Facebook post: {e}")
            return {"success": False, "error": str(e)}
    
    async def _create_photo_post(
        self,
        message: str,
        photos: List[str],
        token: str,
        scheduled_time: Optional[datetime] = None
    ) -> Optional[Dict[str, Any]]:
        if len(photos) == 1:
            params = {
                "url": photos[0],
                "caption": message,
                "access_token": token
            }
            
            if scheduled_time:
                params["published"] = "false"
                params["scheduled_publish_time"] = str(int(scheduled_time.timestamp()))
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.BASE_URL}/{self.page_id}/photos",
                    params=params
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {"post_id": data.get("id"), "success": True}
        else:
            attached_media = []
            
            for photo_url in photos[:5]:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        f"{self.BASE_URL}/{self.page_id}/photos",
                        params={
                            "url": photo_url,
                            "published": "false",
                            "access_token": token
                        }
                    )
                    
                    if response.status_code == 200:
                        media_id = response.json().get("id")
                        attached_media.append({"media_fbid": media_id})
            
            if attached_media:
                params = {
                    "message": message,
                    "attached_media": json.dumps(attached_media),
                    "access_token": token
                }
                
                if scheduled_time:
                    params["published"] = "false"
                    params["scheduled_publish_time"] = str(int(scheduled_time.timestamp()))
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        f"{self.BASE_URL}/{self.page_id}/feed",
                        params=params
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        return {"post_id": data.get("id"), "success": True}
        
        return {"success": False, "error": "Failed to upload photos"}
    
    async def get_post(self, post_id: str) -> Optional[Dict[str, Any]]:
        if not self.access_token:
            return None
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/{post_id}",
                    params={
                        "fields": "id,message,created_time,permalink_url,likes.summary(true),comments.summary(true),shares",
                        "access_token": self.access_token
                    }
                )
                
                if response.status_code == 200:
                    return response.json()
                return None
                
        except Exception as e:
            logger.error(f"Failed to get Facebook post: {e}")
            return None
    
    async def delete_post(self, post_id: str) -> bool:
        if not self.access_token:
            return False
        
        try:
            page_token = await self.get_page_access_token()
            token = page_token or self.access_token
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.delete(
                    f"{self.BASE_URL}/{post_id}",
                    params={"access_token": token}
                )
                
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Failed to delete Facebook post: {e}")
            return False
    
    async def get_posts(
        self,
        limit: int = 25,
        since: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        if not self.page_id or not self.access_token:
            return []
        
        try:
            params = {
                "fields": "id,message,created_time,permalink_url,likes.summary(true),comments.summary(true)",
                "limit": limit,
                "access_token": self.access_token
            }
            
            if since:
                params["since"] = since
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/{self.page_id}/posts",
                    params=params
                )
                
                if response.status_code == 200:
                    return response.json().get("data", [])
                return []
                
        except Exception as e:
            logger.error(f"Failed to get Facebook posts: {e}")
            return []
    
    async def get_insights(
        self,
        post_id: str
    ) -> Optional[Dict[str, Any]]:
        if not self.access_token:
            return None
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/{post_id}/insights",
                    params={
                        "metric": "post_impressions,post_engaged_users,post_clicks",
                        "access_token": self.access_token
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    insights = {}
                    
                    for item in data.get("data", []):
                        name = item.get("name")
                        values = item.get("values", [])
                        if values:
                            insights[name] = values[0].get("value", 0)
                    
                    return insights
                return None
                
        except Exception as e:
            logger.error(f"Failed to get Facebook insights: {e}")
            return None
    
    async def get_comments(
        self,
        post_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        if not self.access_token:
            return []
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/{post_id}/comments",
                    params={
                        "fields": "id,message,from,created_time,like_count",
                        "limit": limit,
                        "access_token": self.access_token
                    }
                )
                
                if response.status_code == 200:
                    return response.json().get("data", [])
                return []
                
        except Exception as e:
            logger.error(f"Failed to get Facebook comments: {e}")
            return []
    
    async def reply_to_comment(
        self,
        comment_id: str,
        message: str
    ) -> bool:
        if not self.access_token:
            return False
        
        try:
            page_token = await self.get_page_access_token()
            token = page_token or self.access_token
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.BASE_URL}/{comment_id}/comments",
                    params={
                        "message": message,
                        "access_token": token
                    }
                )
                
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Failed to reply to comment: {e}")
            return False


class InstagramClient:
    BASE_URL = "https://graph.facebook.com/v18.0"
    
    def __init__(
        self,
        access_token: Optional[str] = None,
        ig_user_id: Optional[str] = None
    ):
        self.access_token = access_token or getattr(settings, 'instagram_access_token', None)
        self.ig_user_id = ig_user_id or getattr(settings, 'instagram_user_id', None)
    
    async def get_user_info(self) -> Optional[Dict[str, Any]]:
        if not self.ig_user_id or not self.access_token:
            return None
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/{self.ig_user_id}",
                    params={
                        "fields": "id,username,account_type,media_count,followers_count,follows_count",
                        "access_token": self.access_token
                    }
                )
                
                if response.status_code == 200:
                    return response.json()
                return None
                
        except Exception as e:
            logger.error(f"Failed to get Instagram user info: {e}")
            return None
    
    async def create_media_container(
        self,
        image_url: str,
        caption: str = "",
        media_type: str = "IMAGE"
    ) -> Optional[str]:
        if not self.ig_user_id or not self.access_token:
            return None
        
        try:
            params = {
                "image_url": image_url,
                "caption": caption,
                "access_token": self.access_token
            }
            
            if media_type == "VIDEO":
                params["media_type"] = "VIDEO"
                params["video_url"] = image_url
            
            if media_type == "CAROUSEL":
                params["media_type"] = "CAROUSEL"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.BASE_URL}/{self.ig_user_id}/media",
                    params=params
                )
                
                if response.status_code == 200:
                    return response.json().get("id")
                else:
                    error = response.json().get("error", {})
                    logger.error(f"Instagram container error: {error.get('message', response.text)}")
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to create Instagram media container: {e}")
            return None
    
    async def create_carousel_container(
        self,
        image_urls: List[str],
        caption: str = ""
    ) -> Optional[str]:
        if not self.ig_user_id or not self.access_token:
            return None
        
        try:
            children = []
            for url in image_urls[:10]:
                container_id = await self.create_media_container(url, "", "CAROUSEL")
                if container_id:
                    children.append(container_id)
            
            if not children:
                return None
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.BASE_URL}/{self.ig_user_id}/media",
                    params={
                        "media_type": "CAROUSEL",
                        "children": ",".join(children),
                        "caption": caption,
                        "access_token": self.access_token
                    }
                )
                
                if response.status_code == 200:
                    return response.json().get("id")
                return None
                
        except Exception as e:
            logger.error(f"Failed to create Instagram carousel: {e}")
            return None
    
    async def publish_media(self, creation_id: str) -> Optional[Dict[str, Any]]:
        if not self.ig_user_id or not self.access_token:
            return None
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.BASE_URL}/{self.ig_user_id}/media_publish",
                    params={
                        "creation_id": creation_id,
                        "access_token": self.access_token
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "media_id": data.get("id"),
                        "success": True
                    }
                else:
                    error = response.json().get("error", {})
                    return {
                        "success": False,
                        "error": error.get("message", "Unknown error")
                    }
                    
        except Exception as e:
            logger.error(f"Failed to publish Instagram media: {e}")
            return {"success": False, "error": str(e)}
    
    async def create_post(
        self,
        image_url: str,
        caption: str,
        media_type: str = "IMAGE"
    ) -> Optional[Dict[str, Any]]:
        container_id = await self.create_media_container(image_url, caption, media_type)
        
        if not container_id:
            return {"success": False, "error": "Failed to create container"}
        
        return await self.publish_media(container_id)
    
    async def create_carousel_post(
        self,
        image_urls: List[str],
        caption: str
    ) -> Optional[Dict[str, Any]]:
        container_id = await self.create_carousel_container(image_urls, caption)
        
        if not container_id:
            return {"success": False, "error": "Failed to create carousel container"}
        
        return await self.publish_media(container_id)
    
    async def get_media(self, media_id: str) -> Optional[Dict[str, Any]]:
        if not self.access_token:
            return None
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/{media_id}",
                    params={
                        "fields": "id,caption,media_type,media_url,permalink,thumbnail_url,timestamp,like_count,comments_count",
                        "access_token": self.access_token
                    }
                )
                
                if response.status_code == 200:
                    return response.json()
                return None
                
        except Exception as e:
            logger.error(f"Failed to get Instagram media: {e}")
            return None
    
    async def get_media_list(
        self,
        limit: int = 25,
        after: Optional[str] = None
    ) -> Dict[str, Any]:
        if not self.ig_user_id or not self.access_token:
            return {"data": [], "paging": {}}
        
        try:
            params = {
                "fields": "id,caption,media_type,media_url,permalink,timestamp,like_count,comments_count",
                "limit": limit,
                "access_token": self.access_token
            }
            
            if after:
                params["after"] = after
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/{self.ig_user_id}/media",
                    params=params
                )
                
                if response.status_code == 200:
                    return response.json()
                return {"data": [], "paging": {}}
                
        except Exception as e:
            logger.error(f"Failed to get Instagram media list: {e}")
            return {"data": [], "paging": {}}
    
    async def get_insights(
        self,
        media_id: str
    ) -> Optional[Dict[str, Any]]:
        if not self.access_token:
            return None
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/{media_id}/insights",
                    params={
                        "metric": "impressions,reach,engagement,saved,video_views",
                        "access_token": self.access_token
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    insights = {}
                    
                    for item in data.get("data", []):
                        name = item.get("name")
                        values = item.get("values", [])
                        if values:
                            insights[name] = values[0].get("value", 0)
                    
                    return insights
                return None
                
        except Exception as e:
            logger.error(f"Failed to get Instagram insights: {e}")
            return None
    
    async def get_comments(
        self,
        media_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        if not self.access_token:
            return []
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/{media_id}/comments",
                    params={
                        "fields": "id,text,from,timestamp,like_count",
                        "limit": limit,
                        "access_token": self.access_token
                    }
                )
                
                if response.status_code == 200:
                    return response.json().get("data", [])
                return []
                
        except Exception as e:
            logger.error(f"Failed to get Instagram comments: {e}")
            return []
    
    async def reply_to_comment(
        self,
        comment_id: str,
        message: str
    ) -> bool:
        if not self.access_token:
            return False
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.BASE_URL}/{comment_id}/replies",
                    params={
                        "message": message,
                        "access_token": self.access_token
                    }
                )
                
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Failed to reply to Instagram comment: {e}")
            return False
    
    async def delete_comment(self, comment_id: str) -> bool:
        if not self.access_token:
            return False
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.delete(
                    f"{self.BASE_URL}/{comment_id}",
                    params={"access_token": self.access_token}
                )
                
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Failed to delete Instagram comment: {e}")
            return False
    
    async def get_hashtag_id(self, hashtag: str) -> Optional[str]:
        if not self.ig_user_id or not self.access_token:
            return None
        
        try:
            clean_hashtag = hashtag.lstrip('#')
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/ig_hashtag_search",
                    params={
                        "user_id": self.ig_user_id,
                        "q": clean_hashtag,
                        "access_token": self.access_token
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("data", [{}])[0].get("id")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get Instagram hashtag ID: {e}")
            return None
    
    async def get_hashtag_media(
        self,
        hashtag: str,
        limit: int = 25
    ) -> List[Dict[str, Any]]:
        hashtag_id = await self.get_hashtag_id(hashtag)
        
        if not hashtag_id:
            return []
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/{hashtag_id}/recent_media",
                    params={
                        "user_id": self.ig_user_id,
                        "fields": "id,caption,media_type,media_url,permalink,timestamp",
                        "limit": limit,
                        "access_token": self.access_token
                    }
                )
                
                if response.status_code == 200:
                    return response.json().get("data", [])
                return []
                
        except Exception as e:
            logger.error(f"Failed to get Instagram hashtag media: {e}")
            return []
