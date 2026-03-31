"""Twitter/X API 客户端

功能特性:
- OAuth 2.0 PKCE 认证
- 推文发布
- 线程发布
- 媒体上传
- 定时发布
- 互动管理
"""

import os
import json
import base64
import hashlib
import secrets
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import httpx

logger = logging.getLogger(__name__)


class TweetType(Enum):
    """推文类型"""
    TWEET = "tweet"
    REPLY = "reply"
    QUOTE = "quote"
    THREAD = "thread"


@dataclass
class Tweet:
    """推文数据"""
    id: str
    text: str
    author_id: str
    created_at: Optional[datetime] = None
    public_metrics: Dict[str, int] = field(default_factory=dict)
    in_reply_to: Optional[str] = None
    referenced_tweets: List[Dict[str, str]] = field(default_factory=list)
    media_urls: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "author_id": self.author_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "public_metrics": self.public_metrics,
            "in_reply_to": self.in_reply_to,
            "referenced_tweets": self.referenced_tweets,
            "media_urls": self.media_urls
        }


@dataclass
class TwitterUser:
    """Twitter 用户"""
    id: str
    username: str
    name: str
    profile_image_url: Optional[str] = None
    description: Optional[str] = None
    public_metrics: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "username": self.username,
            "name": self.name,
            "profile_image_url": self.profile_image_url,
            "description": self.description,
            "public_metrics": self.public_metrics
        }


class TwitterClient:
    """Twitter/X API 客户端"""

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
        self.api_key = api_key or os.getenv("TWITTER_API_KEY")
        self.api_secret = api_secret or os.getenv("TWITTER_API_SECRET")
        self.access_token = access_token or os.getenv("TWITTER_ACCESS_TOKEN")
        self.access_secret = access_secret or os.getenv("TWITTER_ACCESS_SECRET")
        self.bearer_token = bearer_token or os.getenv("TWITTER_BEARER_TOKEN")

        self._client = httpx.AsyncClient(timeout=30.0)
        self._oauth_token: Optional[str] = None
        self._oauth_token_secret: Optional[str] = None

    async def close(self):
        await self._client.aclose()

    def _generate_pkce_verifier(self) -> str:
        code_verifier = secrets.token_urlsafe(96)
        return code_verifier[:128]

    def _generate_pkce_challenge(self, verifier: str) -> str:
        digest = hashlib.sha256(verifier.encode()).digest()
        return base64.urlsafe_b64encode(digest).decode().rstrip('=')

    def get_authorization_url(
        self,
        redirect_uri: str,
        scope: str = "tweet.read tweet.write users.read offline.access",
        state: Optional[str] = None
    ) -> Dict[str, str]:
        code_verifier = self._generate_pkce_verifier()
        code_challenge = self._generate_pkce_challenge(code_verifier)

        if not state:
            state = secrets.token_urlsafe(16)

        params = {
            "response_type": "code",
            "client_id": self.api_key,
            "redirect_uri": redirect_uri,
            "scope": scope,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256"
        }

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        auth_url = f"https://twitter.com/i/oauth2/authorize?{query_string}"

        return {
            "authorization_url": auth_url,
            "state": state,
            "code_verifier": code_verifier
        }

    async def exchange_code_for_token(
        self,
        code: str,
        code_verifier: str,
        redirect_uri: str
    ) -> Dict[str, Any]:
        credentials = f"{self.api_key}:{self.api_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        response = await self._client.post(
            "https://api.twitter.com/2/oauth2/token",
            data={
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
                "code_verifier": code_verifier
            },
            headers={
                "Authorization": f"Basic {encoded_credentials}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )

        response.raise_for_status()
        token_data = response.json()

        self._oauth_token = token_data.get("access_token")
        return token_data

    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        credentials = f"{self.api_key}:{self.api_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        response = await self._client.post(
            "https://api.twitter.com/2/oauth2/token",
            data={
                "refresh_token": refresh_token,
                "grant_type": "refresh_token"
            },
            headers={
                "Authorization": f"Basic {encoded_credentials}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )

        response.raise_for_status()
        return response.json()

    def _get_auth_headers(self) -> Dict[str, str]:
        if self._oauth_token:
            return {"Authorization": f"Bearer {self._oauth_token}"}
        elif self.bearer_token:
            return {"Authorization": f"Bearer {self.bearer_token}"}
        return {}

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        headers = self._get_auth_headers()
        headers["Content-Type"] = "application/json"

        url = f"{self.BASE_URL}{endpoint}"

        try:
            response = await self._client.request(
                method,
                url,
                json=data,
                params=params,
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Twitter API 错误: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"请求失败: {e}")
            raise

    async def get_me(self) -> TwitterUser:
        response = await self._request("GET", "/users/me", params={
            "user.fields": "id,name,username,profile_image_url,description,public_metrics"
        })

        user_data = response.get("data", {})
        return TwitterUser(
            id=user_data.get("id", ""),
            username=user_data.get("username", ""),
            name=user_data.get("name", ""),
            profile_image_url=user_data.get("profile_image_url"),
            description=user_data.get("description"),
            public_metrics=user_data.get("public_metrics", {})
        )

    async def post_tweet(
        self,
        text: str,
        in_reply_to: Optional[str] = None,
        quote_tweet_id: Optional[str] = None,
        media_ids: Optional[List[str]] = None
    ) -> Tweet:
        data: Dict[str, Any] = {"text": text}

        if in_reply_to:
            data["reply"] = {"in_reply_to_tweet_id": in_reply_to}

        if quote_tweet_id:
            data["quote_tweet_id"] = quote_tweet_id

        if media_ids:
            data["media"] = {"media_ids": media_ids}

        response = await self._request("POST", "/tweets", data=data)
        tweet_data = response.get("data", {})

        return Tweet(
            id=tweet_data.get("id", ""),
            text=text,
            author_id=""
        )

    async def post_thread(self, tweets: List[str]) -> List[Tweet]:
        posted_tweets: List[Tweet] = []
        previous_tweet_id: Optional[str] = None

        for tweet_text in tweets:
            tweet = await self.post_tweet(
                text=tweet_text,
                in_reply_to=previous_tweet_id
            )
            posted_tweets.append(tweet)
            previous_tweet_id = tweet.id

        return posted_tweets

    async def delete_tweet(self, tweet_id: str) -> bool:
        try:
            await self._request("DELETE", f"/tweets/{tweet_id}")
            return True
        except Exception as e:
            logger.error(f"删除推文失败: {e}")
            return False

    async def get_tweet(self, tweet_id: str) -> Optional[Tweet]:
        try:
            response = await self._request("GET", f"/tweets/{tweet_id}", params={
                "tweet.fields": "created_at,public_metrics,in_reply_to_user_id,referenced_tweets",
                "expansions": "attachments.media_keys",
                "media.fields": "url"
            })

            tweet_data = response.get("data", {})
            includes = response.get("includes", {})

            media_urls = []
            if "media" in includes:
                media_urls = [m.get("url", "") for m in includes["media"]]

            return Tweet(
                id=tweet_data.get("id", ""),
                text=tweet_data.get("text", ""),
                author_id=tweet_data.get("author_id", ""),
                created_at=self._parse_datetime(tweet_data.get("created_at")),
                public_metrics=tweet_data.get("public_metrics", {}),
                in_reply_to=tweet_data.get("in_reply_to_user_id"),
                referenced_tweets=tweet_data.get("referenced_tweets", []),
                media_urls=media_urls
            )
        except Exception as e:
            logger.error(f"获取推文失败: {e}")
            return None

    async def get_mentions(
        self,
        user_id: str,
        max_results: int = 100,
        since_id: Optional[str] = None
    ) -> List[Tweet]:
        params = {
            "max_results": max_results,
            "tweet.fields": "created_at,public_metrics,in_reply_to_user_id"
        }

        if since_id:
            params["since_id"] = since_id

        response = await self._request(
            "GET",
            f"/users/{user_id}/mentions",
            params=params
        )

        tweets = []
        for tweet_data in response.get("data", []):
            tweets.append(Tweet(
                id=tweet_data.get("id", ""),
                text=tweet_data.get("text", ""),
                author_id=tweet_data.get("author_id", ""),
                created_at=self._parse_datetime(tweet_data.get("created_at")),
                public_metrics=tweet_data.get("public_metrics", {})
            ))

        return tweets

    async def like_tweet(self, user_id: str, tweet_id: str) -> bool:
        try:
            await self._request("POST", f"/users/{user_id}/likes", data={"tweet_id": tweet_id})
            return True
        except Exception as e:
            logger.error(f"点赞失败: {e}")
            return False

    async def retweet(self, user_id: str, tweet_id: str) -> bool:
        try:
            await self._request("POST", f"/users/{user_id}/retweets", data={"tweet_id": tweet_id})
            return True
        except Exception as e:
            logger.error(f"转发失败: {e}")
            return False

    async def upload_media(self, media_data: bytes, media_type: str = "image/jpeg") -> str:
        base64_media = base64.b64encode(media_data).decode()

        response = await self._client.post(
            f"{self.UPLOAD_URL}/media/upload.json",
            data={
                "media_data": base64_media,
                "media_category": "tweet_image"
            },
            headers=self._get_auth_headers()
        )

        response.raise_for_status()
        result = response.json()
        return result.get("media_id_string", "")

    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except:
            return None

    async def search_tweets(
        self,
        query: str,
        max_results: int = 100,
        next_token: Optional[str] = None
    ) -> Dict[str, Any]:
        params = {
            "query": query,
            "max_results": max_results,
            "tweet.fields": "created_at,public_metrics,author_id"
        }

        if next_token:
            params["next_token"] = next_token

        response = await self._request("GET", "/tweets/search/recent", params=params)

        tweets = []
        for tweet_data in response.get("data", []):
            tweets.append(Tweet(
                id=tweet_data.get("id", ""),
                text=tweet_data.get("text", ""),
                author_id=tweet_data.get("author_id", ""),
                created_at=self._parse_datetime(tweet_data.get("created_at")),
                public_metrics=tweet_data.get("public_metrics", {})
            ))

        return {
            "tweets": tweets,
            "count": len(tweets),
            "next_token": response.get("meta", {}).get("next_token")
        }
