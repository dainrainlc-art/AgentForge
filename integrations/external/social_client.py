"""
AgentForge Social Media API Client
Complete integration for Twitter/X, LinkedIn, YouTube, Facebook, Instagram
"""
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
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


class SocialPlatform(str, Enum):
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    YOUTUBE = "youtube"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"


class PostStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"
    DELETED = "deleted"


class MediaType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    GIF = "gif"
    CAROUSEL = "carousel"


class SocialPost(BaseModel):
    id: str = Field(default_factory=lambda: secrets.token_hex(8))
    platform: SocialPlatform
    content: str
    status: PostStatus = PostStatus.DRAFT
    media_urls: List[str] = Field(default_factory=list)
    media_type: Optional[MediaType] = None
    hashtags: List[str] = Field(default_factory=list)
    mentions: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    published_at: Optional[datetime] = None
    scheduled_at: Optional[datetime] = None
    external_id: Optional[str] = None
    engagement_stats: Dict[str, int] = Field(default_factory=dict)
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SocialAnalytics(BaseModel):
    platform: SocialPlatform
    post_id: str
    impressions: int = 0
    reach: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    saves: int = 0
    clicks: int = 0
    engagement_rate: float = 0.0
    video_views: int = 0
    profile_visits: int = 0
    collected_at: datetime = Field(default_factory=datetime.now)


class TwitterClient:
    BASE_URL = "https://api.twitter.com/2"
    UPLOAD_URL = "https://upload.twitter.com/1.1"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        access_secret: Optional[str] = None,
        bearer_token: Optional[str] = None
    ):
        self.api_key = api_key or getattr(settings, 'twitter_api_key', None)
        self.api_secret = api_secret or getattr(settings, 'twitter_api_secret', None)
        self.access_token = access_token or getattr(settings, 'twitter_access_token', None)
        self.access_secret = access_secret or getattr(settings, 'twitter_access_secret', None)
        self.bearer_token = bearer_token or getattr(settings, 'twitter_bearer_token', None)
    
    def _generate_oauth_signature(
        self,
        method: str,
        url: str,
        params: Dict[str, str]
    ) -> str:
        if not all([self.api_key, self.api_secret, self.access_token, self.access_secret]):
            return ""
        
        oauth_params = {
            'oauth_consumer_key': self.api_key,
            'oauth_nonce': secrets.token_hex(16),
            'oauth_signature_method': 'HMAC-SHA1',
            'oauth_timestamp': str(int(datetime.now().timestamp())),
            'oauth_token': self.access_token,
            'oauth_version': '1.0'
        }
        
        all_params = {**params, **oauth_params}
        param_string = '&'.join(f'{k}={v}' for k, v in sorted(all_params.items()))
        
        base_string = f'{method.upper()}&{url}&{param_string}'
        signing_key = f'{self.api_secret}&{self.access_secret}'
        
        signature = hmac.new(
            signing_key.encode(),
            base_string.encode(),
            hashlib.sha1
        ).digest()
        
        return base64.b64encode(signature).decode()
    
    def _build_auth_header(self, signature: str, oauth_params: Dict[str, str]) -> str:
        auth_items = [f'{k}="{v}"' for k, v in oauth_params.items()]
        auth_items.append(f'oauth_signature="{signature}"')
        return f'OAuth {", ".join(auth_items)}'
    
    async def create_tweet(
        self,
        text: str,
        media_ids: Optional[List[str]] = None,
        reply_to: Optional[str] = None,
        quote_tweet_id: Optional[str] = None
    ) -> Optional[SocialPost]:
        if not self.bearer_token:
            logger.warning("Twitter bearer token not configured")
            return None
        
        try:
            headers = {
                "Authorization": f"Bearer {self.bearer_token}",
                "Content-Type": "application/json"
            }
            
            payload = {"text": text}
            
            if media_ids:
                payload["media"] = {"media_ids": media_ids}
            
            if reply_to:
                payload["reply"] = {"in_reply_to_tweet_id": reply_to}
            
            if quote_tweet_id:
                payload["quote_tweet_id"] = quote_tweet_id
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.BASE_URL}/tweets",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 201:
                    data = response.json()
                    tweet_id = data["data"]["id"]
                    
                    hashtags = [w for w in text.split() if w.startswith('#')]
                    mentions = [w for w in text.split() if w.startswith('@')]
                    
                    return SocialPost(
                        external_id=tweet_id,
                        platform=SocialPlatform.TWITTER,
                        content=text,
                        status=PostStatus.PUBLISHED,
                        hashtags=hashtags,
                        mentions=mentions,
                        published_at=datetime.now(),
                        metadata={"edit_history_tweet_ids": data["data"].get("edit_history_tweet_ids", [])}
                    )
                else:
                    error_data = response.json() if response.content else {}
                    logger.error(f"Twitter API error: {response.status_code} - {error_data}")
                    return SocialPost(
                        platform=SocialPlatform.TWITTER,
                        content=text,
                        status=PostStatus.FAILED,
                        error_message=str(error_data.get("detail", response.text))
                    )
                    
        except Exception as e:
            logger.error(f"Failed to create tweet: {e}")
            return SocialPost(
                platform=SocialPlatform.TWITTER,
                content=text,
                status=PostStatus.FAILED,
                error_message=str(e)
            )
    
    async def upload_media(self, media_path: str, media_type: str = "image") -> Optional[str]:
        if not all([self.api_key, self.api_secret, self.access_token, self.access_secret]):
            logger.warning("Twitter OAuth 1.0a credentials not configured for media upload")
            return None
        
        try:
            media_file = Path(media_path)
            if not media_file.exists():
                logger.error(f"Media file not found: {media_path}")
                return None
            
            media_data = media_file.read_bytes()
            media_category = "tweet_image" if media_type == "image" else "tweet_video"
            
            url = f"{self.UPLOAD_URL}/media/upload.json"
            
            params = {
                'command': 'INIT',
                'media_type': 'image/jpeg' if media_type == 'image' else 'video/mp4',
                'total_bytes': str(len(media_data)),
                'media_category': media_category
            }
            
            signature = self._generate_oauth_signature("POST", url, params)
            oauth_params = {
                'oauth_consumer_key': self.api_key,
                'oauth_nonce': secrets.token_hex(16),
                'oauth_signature_method': 'HMAC-SHA1',
                'oauth_timestamp': str(int(datetime.now().timestamp())),
                'oauth_token': self.access_token,
                'oauth_version': '1.0'
            }
            auth_header = self._build_auth_header(signature, oauth_params)
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                init_response = await client.post(
                    url,
                    params=params,
                    headers={"Authorization": auth_header}
                )
                
                if init_response.status_code != 202:
                    logger.error(f"Twitter media init failed: {init_response.text}")
                    return None
                
                media_id = init_response.json()["media_id"]
                
                chunk_size = 4 * 1024 * 1024
                for i in range(0, len(media_data), chunk_size):
                    chunk = media_data[i:i + chunk_size]
                    
                    append_params = {
                        'command': 'APPEND',
                        'media_id': str(media_id),
                        'segment_index': str(i // chunk_size)
                    }
                    
                    files = {'media': chunk}
                    await client.post(
                        url,
                        params=append_params,
                        files=files,
                        headers={"Authorization": auth_header}
                    )
                
                finalize_params = {
                    'command': 'FINALIZE',
                    'media_id': str(media_id)
                }
                
                finalize_response = await client.post(
                    url,
                    params=finalize_params,
                    headers={"Authorization": auth_header}
                )
                
                if finalize_response.status_code == 200:
                    return str(media_id)
                else:
                    logger.error(f"Twitter media finalize failed: {finalize_response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to upload media to Twitter: {e}")
            return None
    
    async def get_tweet(self, tweet_id: str) -> Optional[Dict[str, Any]]:
        if not self.bearer_token:
            return None
        
        try:
            headers = {"Authorization": f"Bearer {self.bearer_token}"}
            params = {
                "tweet.fields": "created_at,public_metrics,entities,context_annotations",
                "expansions": "author_id,attachments.media_keys",
                "media.fields": "url,preview_image_url,type"
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/tweets/{tweet_id}",
                    headers=headers,
                    params=params
                )
                
                if response.status_code == 200:
                    return response.json()
                return None
                
        except Exception as e:
            logger.error(f"Failed to get tweet: {e}")
            return None
    
    async def delete_tweet(self, tweet_id: str) -> bool:
        if not all([self.api_key, self.api_secret, self.access_token, self.access_secret]):
            return False
        
        try:
            url = f"{self.BASE_URL}/tweets/{tweet_id}"
            signature = self._generate_oauth_signature("DELETE", url, {})
            oauth_params = {
                'oauth_consumer_key': self.api_key,
                'oauth_nonce': secrets.token_hex(16),
                'oauth_signature_method': 'HMAC-SHA1',
                'oauth_timestamp': str(int(datetime.now().timestamp())),
                'oauth_token': self.access_token,
                'oauth_version': '1.0'
            }
            auth_header = self._build_auth_header(signature, oauth_params)
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.delete(
                    url,
                    headers={"Authorization": auth_header}
                )
                
                return response.status_code == 204
                
        except Exception as e:
            logger.error(f"Failed to delete tweet: {e}")
            return False
    
    async def get_user_timeline(
        self,
        user_id: str,
        max_results: int = 10,
        since_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        if not self.bearer_token:
            return []
        
        try:
            headers = {"Authorization": f"Bearer {self.bearer_token}"}
            params = {
                "max_results": str(max_results),
                "tweet.fields": "created_at,public_metrics",
                "exclude": "retweets,replies"
            }
            
            if since_id:
                params["since_id"] = since_id
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/users/{user_id}/tweets",
                    headers=headers,
                    params=params
                )
                
                if response.status_code == 200:
                    return response.json().get("data", [])
                return []
                
        except Exception as e:
            logger.error(f"Failed to get user timeline: {e}")
            return []
    
    async def get_analytics(
        self,
        tweet_id: str
    ) -> Optional[SocialAnalytics]:
        tweet_data = await self.get_tweet(tweet_id)
        
        if not tweet_data:
            return None
        
        data = tweet_data.get("data", {})
        metrics = data.get("public_metrics", {})
        
        return SocialAnalytics(
            platform=SocialPlatform.TWITTER,
            post_id=tweet_id,
            impressions=metrics.get("impression_count", 0),
            likes=metrics.get("like_count", 0),
            comments=metrics.get("reply_count", 0),
            shares=metrics.get("retweet_count", 0),
            engagement_rate=self._calculate_engagement_rate(metrics)
        )
    
    def _calculate_engagement_rate(self, metrics: Dict[str, int]) -> float:
        impressions = metrics.get("impression_count", 1)
        if impressions == 0:
            return 0.0
        
        engagements = (
            metrics.get("like_count", 0) +
            metrics.get("retweet_count", 0) +
            metrics.get("reply_count", 0) +
            metrics.get("quote_count", 0)
        )
        
        return round((engagements / impressions) * 100, 2)


class LinkedInClient:
    BASE_URL = "https://api.linkedin.com/v2"
    
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None
    ):
        self.client_id = client_id or getattr(settings, 'linkedin_client_id', None)
        self.client_secret = client_secret or getattr(settings, 'linkedin_client_secret', None)
        self.access_token = access_token or getattr(settings, 'linkedin_access_token', None)
        self.refresh_token = refresh_token or getattr(settings, 'linkedin_refresh_token', None)
    
    async def refresh_access_token(self) -> Optional[str]:
        if not all([self.client_id, self.client_secret, self.refresh_token]):
            return None
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://www.linkedin.com/oauth/v2/accessToken",
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": self.refresh_token,
                        "client_id": self.client_id,
                        "client_secret": self.client_secret
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.access_token = data.get("access_token")
                    return self.access_token
                return None
                
        except Exception as e:
            logger.error(f"Failed to refresh LinkedIn token: {e}")
            return None
    
    async def get_profile(self) -> Optional[Dict[str, Any]]:
        if not self.access_token:
            return None
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/me",
                    headers=headers
                )
                
                if response.status_code == 200:
                    return response.json()
                return None
                
        except Exception as e:
            logger.error(f"Failed to get LinkedIn profile: {e}")
            return None
    
    async def create_post(
        self,
        text: str,
        media_urn: Optional[str] = None,
        visibility: str = "PUBLIC"
    ) -> Optional[SocialPost]:
        if not self.access_token:
            logger.warning("LinkedIn access token not configured")
            return None
        
        try:
            profile = await self.get_profile()
            if not profile:
                return SocialPost(
                    platform=SocialPlatform.LINKEDIN,
                    content=text,
                    status=PostStatus.FAILED,
                    error_message="Failed to get profile"
                )
            
            author_urn = f"urn:li:person:{profile['id']}"
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0"
            }
            
            share_content = {
                "shareCommentary": {
                    "text": text
                },
                "shareMediaCategory": "NONE"
            }
            
            if media_urn:
                share_content["shareMediaCategory"] = "IMAGE"
                share_content["media"] = [{
                    "status": "READY",
                    "description": {"text": text},
                    "media": media_urn
                }]
            
            payload = {
                "author": author_urn,
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": share_content
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": visibility
                }
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.BASE_URL}/ugcPosts",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 201:
                    data = response.json()
                    post_urn = data.get("id", "")
                    
                    hashtags = [w for w in text.split() if w.startswith('#')]
                    
                    return SocialPost(
                        external_id=post_urn,
                        platform=SocialPlatform.LINKEDIN,
                        content=text,
                        status=PostStatus.PUBLISHED,
                        hashtags=hashtags,
                        published_at=datetime.now(),
                        metadata={"author_urn": author_urn}
                    )
                else:
                    error_text = response.text
                    logger.error(f"LinkedIn API error: {response.status_code} - {error_text}")
                    return SocialPost(
                        platform=SocialPlatform.LINKEDIN,
                        content=text,
                        status=PostStatus.FAILED,
                        error_message=error_text
                    )
                    
        except Exception as e:
            logger.error(f"Failed to create LinkedIn post: {e}")
            return SocialPost(
                platform=SocialPlatform.LINKEDIN,
                content=text,
                status=PostStatus.FAILED,
                error_message=str(e)
            )
    
    async def upload_image(self, image_path: str) -> Optional[str]:
        if not self.access_token:
            return None
        
        try:
            profile = await self.get_profile()
            if not profile:
                return None
            
            image_file = Path(image_path)
            if not image_file.exists():
                logger.error(f"Image file not found: {image_path}")
                return None
            
            register_payload = {
                "initializeUploadRequest": {
                    "owner": f"urn:li:person:{profile['id']}"
                }
            }
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.BASE_URL}/assets?action=registerUpload",
                    headers=headers,
                    json=register_payload
                )
                
                if response.status_code != 200:
                    logger.error(f"LinkedIn image register failed: {response.text}")
                    return None
                
                data = response.json()
                upload_url = data["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
                asset_urn = data["value"]["asset"]
                
                image_data = image_file.read_bytes()
                
                upload_response = await client.post(
                    upload_url,
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/octet-stream"
                    },
                    content=image_data
                )
                
                if upload_response.status_code == 201:
                    return asset_urn
                else:
                    logger.error(f"LinkedIn image upload failed: {upload_response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to upload image to LinkedIn: {e}")
            return None
    
    async def create_article(
        self,
        title: str,
        content: str,
        url: Optional[str] = None,
        image_url: Optional[str] = None
    ) -> Optional[SocialPost]:
        if not self.access_token:
            return None
        
        try:
            profile = await self.get_profile()
            if not profile:
                return None
            
            author_urn = f"urn:li:person:{profile['id']}"
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            article_content = {
                "title": title,
                "description": content[:300] if len(content) > 300 else content
            }
            
            if url:
                article_content["source"] = {"url": url}
            
            if image_url:
                article_content["thumbnail"] = {"url": image_url}
            
            payload = {
                "author": author_urn,
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {"text": f"{title}\n\n{content[:500]}"},
                        "shareMediaCategory": "ARTICLE",
                        "media": [{
                            "status": "PUBLISHED",
                            "originalUrl": url or "",
                            **article_content
                        }]
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.BASE_URL}/ugcPosts",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 201:
                    data = response.json()
                    return SocialPost(
                        external_id=data.get("id", ""),
                        platform=SocialPlatform.LINKEDIN,
                        content=f"{title}\n\n{content}",
                        status=PostStatus.PUBLISHED,
                        published_at=datetime.now()
                    )
                return None
                
        except Exception as e:
            logger.error(f"Failed to create LinkedIn article: {e}")
            return None
    
    async def get_analytics(
        self,
        post_urn: str
    ) -> Optional[SocialAnalytics]:
        if not self.access_token:
            return None
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/socialActions/{post_urn}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    return SocialAnalytics(
                        platform=SocialPlatform.LINKEDIN,
                        post_id=post_urn,
                        likes=data.get("likesSummary", {}).get("totalLikes", 0),
                        comments=data.get("commentsSummary", {}).get("totalComments", 0),
                        shares=data.get("sharesSummary", {}).get("totalShares", 0)
                    )
                return None
                
        except Exception as e:
            logger.error(f"Failed to get LinkedIn analytics: {e}")
            return None


class YouTubeClient:
    BASE_URL = "https://www.googleapis.com/youtube/v3"
    UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None
    ):
        self.api_key = api_key or getattr(settings, 'youtube_api_key', None)
        self.access_token = access_token or getattr(settings, 'youtube_access_token', None)
        self.refresh_token = refresh_token or getattr(settings, 'youtube_refresh_token', None)
        self.client_id = client_id or getattr(settings, 'youtube_client_id', None)
        self.client_secret = client_secret or getattr(settings, 'youtube_client_secret', None)
    
    async def refresh_access_token(self) -> Optional[str]:
        if not all([self.client_id, self.client_secret, self.refresh_token]):
            return None
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "refresh_token": self.refresh_token,
                        "grant_type": "refresh_token"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.access_token = data.get("access_token")
                    return self.access_token
                return None
                
        except Exception as e:
            logger.error(f"Failed to refresh YouTube token: {e}")
            return None
    
    async def get_channel_info(self) -> Optional[Dict[str, Any]]:
        if not self.api_key:
            return None
        
        try:
            params = {
                "part": "snippet,statistics",
                "mine": "true",
                "key": self.api_key
            }
            
            headers = {}
            if self.access_token:
                headers["Authorization"] = f"Bearer {self.access_token}"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/channels",
                    headers=headers,
                    params=params
                )
                
                if response.status_code == 200:
                    return response.json()
                return None
                
        except Exception as e:
            logger.error(f"Failed to get YouTube channel info: {e}")
            return None
    
    async def upload_video(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: Optional[List[str]] = None,
        category_id: str = "22",
        privacy_status: str = "public",
        made_for_kids: bool = False
    ) -> Optional[SocialPost]:
        if not self.access_token:
            logger.warning("YouTube access token not configured")
            return None
        
        try:
            video_file = Path(video_path)
            if not video_file.exists():
                logger.error(f"Video file not found: {video_path}")
                return None
            
            snippet = {
                "title": title[:100],
                "description": description[:5000],
                "tags": tags or [],
                "categoryId": category_id
            }
            
            status = {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": made_for_kids
            }
            
            metadata = {"snippet": snippet, "status": status}
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            video_data = video_file.read_bytes()
            
            async with httpx.AsyncClient(timeout=600.0) as client:
                response = await client.post(
                    f"{self.UPLOAD_URL}?uploadType=resumable&part=snippet,status",
                    headers=headers,
                    json=metadata
                )
                
                if response.status_code != 200:
                    logger.error(f"YouTube upload init failed: {response.text}")
                    return SocialPost(
                        platform=SocialPlatform.YOUTUBE,
                        content=f"{title}\n\n{description}",
                        status=PostStatus.FAILED,
                        error_message=response.text
                    )
                
                upload_url = response.headers.get("Location")
                
                upload_response = await client.put(
                    upload_url,
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "video/*"
                    },
                    content=video_data
                )
                
                if upload_response.status_code == 200:
                    data = upload_response.json()
                    video_id = data["id"]
                    
                    return SocialPost(
                        external_id=video_id,
                        platform=SocialPlatform.YOUTUBE,
                        content=f"{title}\n\n{description}",
                        status=PostStatus.PUBLISHED,
                        hashtags=tags or [],
                        media_type=MediaType.VIDEO,
                        published_at=datetime.now(),
                        metadata={
                            "video_url": f"https://www.youtube.com/watch?v={video_id}",
                            "privacy_status": privacy_status
                        }
                    )
                else:
                    logger.error(f"YouTube video upload failed: {upload_response.text}")
                    return SocialPost(
                        platform=SocialPlatform.YOUTUBE,
                        content=f"{title}\n\n{description}",
                        status=PostStatus.FAILED,
                        error_message=upload_response.text
                    )
                    
        except Exception as e:
            logger.error(f"Failed to upload video to YouTube: {e}")
            return SocialPost(
                platform=SocialPlatform.YOUTUBE,
                content=f"{title}\n\n{description}",
                status=PostStatus.FAILED,
                error_message=str(e)
            )
    
    async def get_video(self, video_id: str) -> Optional[Dict[str, Any]]:
        if not self.api_key:
            return None
        
        try:
            params = {
                "part": "snippet,statistics,contentDetails",
                "id": video_id,
                "key": self.api_key
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/videos",
                    params=params
                )
                
                if response.status_code == 200:
                    items = response.json().get("items", [])
                    return items[0] if items else None
                return None
                
        except Exception as e:
            logger.error(f"Failed to get YouTube video: {e}")
            return None
    
    async def update_video(
        self,
        video_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        if not self.access_token:
            return False
        
        try:
            video_data = await self.get_video(video_id)
            if not video_data:
                return False
            
            snippet = video_data["snippet"]
            
            if title:
                snippet["title"] = title[:100]
            if description:
                snippet["description"] = description[:5000]
            if tags:
                snippet["tags"] = tags
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.put(
                    f"{self.BASE_URL}/videos?part=snippet",
                    headers=headers,
                    json={"id": video_id, "snippet": snippet}
                )
                
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Failed to update YouTube video: {e}")
            return False
    
    async def delete_video(self, video_id: str) -> bool:
        if not self.access_token:
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.delete(
                    f"{self.BASE_URL}/videos?id={video_id}",
                    headers=headers
                )
                
                return response.status_code == 204
                
        except Exception as e:
            logger.error(f"Failed to delete YouTube video: {e}")
            return False
    
    async def get_analytics(
        self,
        video_id: str
    ) -> Optional[SocialAnalytics]:
        video_data = await self.get_video(video_id)
        
        if not video_data:
            return None
        
        stats = video_data.get("statistics", {})
        
        return SocialAnalytics(
            platform=SocialPlatform.YOUTUBE,
            post_id=video_id,
            likes=int(stats.get("likeCount", 0)),
            comments=int(stats.get("commentCount", 0)),
            video_views=int(stats.get("viewCount", 0)),
            engagement_rate=self._calculate_engagement_rate(stats)
        )
    
    def _calculate_engagement_rate(self, stats: Dict[str, str]) -> float:
        views = int(stats.get("viewCount", 1))
        if views == 0:
            return 0.0
        
        likes = int(stats.get("likeCount", 0))
        comments = int(stats.get("commentCount", 0))
        
        return round(((likes + comments) / views) * 100, 2)


from integrations.external.facebook_instagram_client import FacebookClient, InstagramClient


class SocialMediaClient:
    def __init__(self):
        self.twitter = TwitterClient()
        self.linkedin = LinkedInClient()
        self.youtube = YouTubeClient()
        self.facebook = FacebookClient()
        self.instagram = InstagramClient()
    
    async def post_to_platform(
        self,
        platform: SocialPlatform,
        content: str,
        media_paths: Optional[List[str]] = None,
        media_urls: Optional[List[str]] = None,
        **kwargs
    ) -> Optional[SocialPost]:
        if platform == SocialPlatform.TWITTER:
            media_ids = []
            if media_paths:
                for path in media_paths[:4]:
                    media_id = await self.twitter.upload_media(path)
                    if media_id:
                        media_ids.append(media_id)
            
            return await self.twitter.create_tweet(
                text=content,
                media_ids=media_ids if media_ids else None,
                **kwargs
            )
        
        elif platform == SocialPlatform.LINKEDIN:
            media_urn = None
            if media_paths and len(media_paths) > 0:
                media_urn = await self.linkedin.upload_image(media_paths[0])
            
            return await self.linkedin.create_post(
                text=content,
                media_urn=media_urn,
                **kwargs
            )
        
        elif platform == SocialPlatform.YOUTUBE:
            if not media_paths or len(media_paths) == 0:
                return SocialPost(
                    platform=SocialPlatform.YOUTUBE,
                    content=content,
                    status=PostStatus.FAILED,
                    error_message="YouTube requires a video file"
                )
            
            return await self.youtube.upload_video(
                video_path=media_paths[0],
                title=kwargs.get("title", "Untitled"),
                description=content,
                tags=kwargs.get("tags"),
                **{k: v for k, v in kwargs.items() if k not in ["title", "tags"]}
            )
        
        elif platform == SocialPlatform.FACEBOOK:
            result = await self.facebook.create_post(
                message=content,
                link=kwargs.get("link"),
                photos=media_urls,
                scheduled_time=kwargs.get("scheduled_time")
            )
            
            if result and result.get("success"):
                return SocialPost(
                    external_id=result.get("post_id", ""),
                    platform=SocialPlatform.FACEBOOK,
                    content=content,
                    status=PostStatus.PUBLISHED,
                    published_at=datetime.now()
                )
            else:
                return SocialPost(
                    platform=SocialPlatform.FACEBOOK,
                    content=content,
                    status=PostStatus.FAILED,
                    error_message=result.get("error", "Unknown error") if result else "Failed to post"
                )
        
        elif platform == SocialPlatform.INSTAGRAM:
            if not media_urls or len(media_urls) == 0:
                return SocialPost(
                    platform=SocialPlatform.INSTAGRAM,
                    content=content,
                    status=PostStatus.FAILED,
                    error_message="Instagram requires media URL"
                )
            
            if len(media_urls) == 1:
                result = await self.instagram.create_post(
                    image_url=media_urls[0],
                    caption=content,
                    media_type=kwargs.get("media_type", "IMAGE")
                )
            else:
                result = await self.instagram.create_carousel_post(
                    image_urls=media_urls,
                    caption=content
                )
            
            if result and result.get("success"):
                return SocialPost(
                    external_id=result.get("media_id", ""),
                    platform=SocialPlatform.INSTAGRAM,
                    content=content,
                    status=PostStatus.PUBLISHED,
                    published_at=datetime.now()
                )
            else:
                return SocialPost(
                    platform=SocialPlatform.INSTAGRAM,
                    content=content,
                    status=PostStatus.FAILED,
                    error_message=result.get("error", "Unknown error") if result else "Failed to post"
                )
        
        else:
            logger.warning(f"Unsupported platform: {platform}")
            return None
    
    async def get_analytics(
        self,
        platform: SocialPlatform,
        post_id: str
    ) -> Optional[SocialAnalytics]:
        if platform == SocialPlatform.TWITTER:
            return await self.twitter.get_analytics(post_id)
        elif platform == SocialPlatform.LINKEDIN:
            return await self.linkedin.get_analytics(post_id)
        elif platform == SocialPlatform.YOUTUBE:
            return await self.youtube.get_analytics(post_id)
        elif platform == SocialPlatform.FACEBOOK:
            insights = await self.facebook.get_insights(post_id)
            if insights:
                return SocialAnalytics(
                    platform=SocialPlatform.FACEBOOK,
                    post_id=post_id,
                    impressions=insights.get("post_impressions", 0),
                    reach=insights.get("post_engaged_users", 0),
                    clicks=insights.get("post_clicks", 0)
                )
        elif platform == SocialPlatform.INSTAGRAM:
            insights = await self.instagram.get_insights(post_id)
            if insights:
                return SocialAnalytics(
                    platform=SocialPlatform.INSTAGRAM,
                    post_id=post_id,
                    impressions=insights.get("impressions", 0),
                    reach=insights.get("reach", 0),
                    likes=insights.get("engagement", 0),
                    saves=insights.get("saved", 0)
                )
        return None
    
    async def health_check(self) -> Dict[str, bool]:
        return {
            "twitter": bool(self.twitter.bearer_token),
            "linkedin": bool(self.linkedin.access_token),
            "youtube": bool(self.youtube.api_key),
            "facebook": bool(self.facebook.access_token),
            "instagram": bool(self.instagram.access_token)
        }
    
    async def get_all_platforms_status(self) -> Dict[str, Dict[str, Any]]:
        status = {}
        
        if self.twitter.bearer_token:
            try:
                timeline = await self.twitter.get_user_timeline("me", max_results=1)
                status["twitter"] = {"connected": True, "recent_posts": len(timeline)}
            except Exception:
                status["twitter"] = {"connected": False, "error": "API error"}
        else:
            status["twitter"] = {"connected": False, "error": "Not configured"}
        
        if self.linkedin.access_token:
            try:
                profile = await self.linkedin.get_profile()
                status["linkedin"] = {
                    "connected": True,
                    "profile_name": profile.get("localizedFirstName", "") if profile else ""
                }
            except Exception:
                status["linkedin"] = {"connected": False, "error": "API error"}
        else:
            status["linkedin"] = {"connected": False, "error": "Not configured"}
        
        if self.youtube.api_key:
            try:
                channel = await self.youtube.get_channel_info()
                status["youtube"] = {"connected": True, "has_channel": bool(channel)}
            except Exception:
                status["youtube"] = {"connected": False, "error": "API error"}
        else:
            status["youtube"] = {"connected": False, "error": "Not configured"}
        
        if self.facebook.access_token:
            try:
                page_info = await self.facebook.get_page_info()
                status["facebook"] = {
                    "connected": True,
                    "page_name": page_info.get("name", "") if page_info else "",
                    "fan_count": page_info.get("fan_count", 0) if page_info else 0
                }
            except Exception:
                status["facebook"] = {"connected": False, "error": "API error"}
        else:
            status["facebook"] = {"connected": False, "error": "Not configured"}
        
        if self.instagram.access_token:
            try:
                user_info = await self.instagram.get_user_info()
                status["instagram"] = {
                    "connected": True,
                    "username": user_info.get("username", "") if user_info else "",
                    "followers": user_info.get("followers_count", 0) if user_info else 0
                }
            except Exception:
                status["instagram"] = {"connected": False, "error": "API error"}
        else:
            status["instagram"] = {"connected": False, "error": "Not configured"}
        
        return status
