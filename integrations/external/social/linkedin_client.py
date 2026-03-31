"""LinkedIn API 客户端

功能特性:
- OAuth 2.0 认证
- 个人资料获取
- 文章/动态发布
- 图片上传
- 公司页面管理
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


class PostVisibility(Enum):
    """帖子可见性"""
    PUBLIC = "PUBLIC"
    CONNECTIONS = "CONNECTIONS"


@dataclass
class LinkedInProfile:
    """LinkedIn 个人资料"""
    id: str
    firstName: str
    lastName: str
    headline: Optional[str] = None
    profilePicture: Optional[str] = None
    vanityName: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "firstName": self.firstName,
            "lastName": self.lastName,
            "headline": self.headline,
            "profilePicture": self.profilePicture,
            "vanityName": self.vanityName
        }


@dataclass
class LinkedInPost:
    """LinkedIn 帖子"""
    id: str
    text: str
    author_id: str
    created_at: Optional[datetime] = None
    visibility: PostVisibility = PostVisibility.PUBLIC
    media_urls: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "author_id": self.author_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "visibility": self.visibility.value,
            "media_urls": self.media_urls
        }


class LinkedInClient:
    """LinkedIn API 客户端"""

    AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
    TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
    API_URL = "https://api.linkedin.com/v2"

    SCOPES = [
        "r_liteprofile",
        "r_emailaddress",
        "w_member_social",
        "r_organization_social",
        "w_organization_social"
    ]

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        redirect_uri: Optional[str] = None
    ):
        self.client_id = client_id or os.getenv("LINKEDIN_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("LINKEDIN_CLIENT_SECRET")
        self.access_token = access_token or os.getenv("LINKEDIN_ACCESS_TOKEN")
        self.redirect_uri = redirect_uri or os.getenv("LINKEDIN_REDIRECT_URI")

        self._client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        await self._client.aclose()

    def get_authorization_url(
        self,
        state: Optional[str] = None,
        scopes: Optional[List[str]] = None
    ) -> str:
        import secrets

        if not state:
            state = secrets.token_urlsafe(16)

        scope = " ".join(scopes or self.SCOPES)

        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": scope,
            "state": state
        }

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.AUTH_URL}?{query_string}"

    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        response = await self._client.post(
            self.TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self.redirect_uri,
                "client_id": self.client_id,
                "client_secret": self.client_secret
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
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
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        url = f"{self.API_URL}{endpoint}"
        headers = self._get_auth_headers()

        try:
            response = await self._client.request(
                method,
                url,
                json=data,
                params=params,
                headers=headers
            )
            response.raise_for_status()

            if response.status_code == 204:
                return {}

            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"LinkedIn API 错误: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"请求失败: {e}")
            raise

    async def get_profile(self) -> LinkedInProfile:
        response = await self._request("GET", "/me", params={
            "projection": "(id,firstName,lastName,headline,profilePicture(displayImage~:playableStreams),vanityName)"
        })

        first_name = ""
        last_name = ""
        if "firstName" in response:
            first_name = response["firstName"].get("localized", {}).get("en_US", "")
        if "lastName" in response:
            last_name = response["lastName"].get("localized", {}).get("en_US", "")

        profile_picture = None
        if "profilePicture" in response:
            elements = response["profilePicture"].get("displayImage~", {}).get("elements", [])
            if elements:
                profile_picture = elements[-1].get("identifiers", [{}])[0].get("identifier")

        return LinkedInProfile(
            id=response.get("id", ""),
            firstName=first_name,
            lastName=last_name,
            headline=response.get("headline", {}).get("localized", {}).get("en_US"),
            profilePicture=profile_picture,
            vanityName=response.get("vanityName")
        )

    async def get_email(self) -> str:
        response = await self._request("GET", "/emailAddress", params={
            "q": "members",
            "projection": "(elements*(handle~))"
        })

        elements = response.get("elements", [])
        if elements:
            return elements[0].get("handle~", {}).get("emailAddress", "")
        return ""

    async def post_text(
        self,
        text: str,
        visibility: PostVisibility = PostVisibility.PUBLIC
    ) -> LinkedInPost:
        profile = await self.get_profile()
        author_id = f"urn:li:person:{profile.id}"

        data = {
            "author": author_id,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": visibility.value
            }
        }

        response = await self._request("POST", "/ugcPosts", data=data)

        return LinkedInPost(
            id=response.get("id", ""),
            text=text,
            author_id=profile.id,
            visibility=visibility
        )

    async def post_article(
        self,
        title: str,
        text: str,
        visibility: PostVisibility = PostVisibility.PUBLIC
    ) -> LinkedInPost:
        full_text = f"{title}\n\n{text}"
        return await self.post_text(full_text, visibility)

    async def post_with_image(
        self,
        text: str,
        image_data: bytes,
        image_title: Optional[str] = None,
        image_description: Optional[str] = None,
        visibility: PostVisibility = PostVisibility.PUBLIC
    ) -> LinkedInPost:
        profile = await self.get_profile()
        author_id = f"urn:li:person:{profile.id}"

        register_response = await self._request("POST", "/assets", params={
            "action": "registerUpload"
        }, data={
            "registerUploadRequest": {
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                "owner": author_id,
                "serviceRelationships": [{
                    "relationshipType": "OWNER",
                    "identifier": "urn:li:userGeneratedContent"
                }]
            }
        })

        upload_url = register_response.get("value", {}).get("uploadMechanism", {}).get("com.linkedin.digitalmedia.uploading.MediaUpload", {}).get("uploadUrl", "")
        asset_id = register_response.get("value", {}).get("asset", "")

        if upload_url:
            upload_response = await self._client.post(
                upload_url,
                content=image_data,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "image/jpeg"
                }
            )
            upload_response.raise_for_status()

        data = {
            "author": author_id,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text
                    },
                    "shareMediaCategory": "IMAGE",
                    "media": [{
                        "status": "READY",
                        "description": {"text": image_description or ""},
                        "media": asset_id,
                        "title": {"text": image_title or ""}
                    }]
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": visibility.value
            }
        }

        response = await self._request("POST", "/ugcPosts", data=data)

        return LinkedInPost(
            id=response.get("id", ""),
            text=text,
            author_id=profile.id,
            visibility=visibility
        )

    async def delete_post(self, post_id: str) -> bool:
        try:
            await self._request("DELETE", f"/ugcPosts/{post_id}")
            return True
        except Exception as e:
            logger.error(f"删除帖子失败: {e}")
            return False

    async def get_organization_pages(self) -> List[Dict[str, Any]]:
        response = await self._request("GET", "/organizationAcls", params={
            "q": "roleAssignee",
            "role": "ADMINISTRATOR",
            "state": "APPROVED",
            "projection": "(elements*(organization~(id,name,vanityName,logoV2(original~:playableStreams))))"
        })

        pages = []
        for element in response.get("elements", []):
            org = element.get("organization~", {})
            pages.append({
                "id": org.get("id"),
                "name": org.get("name", {}).get("localized", {}).get("en_US", ""),
                "vanityName": org.get("vanityName"),
                "logo": org.get("logoV2", {}).get("original~", {}).get("elements", [{}])[0].get("identifiers", [{}])[0].get("identifier")
            })

        return pages

    async def post_as_organization(
        self,
        organization_id: str,
        text: str,
        visibility: PostVisibility = PostVisibility.PUBLIC
    ) -> LinkedInPost:
        author_id = f"urn:li:organization:{organization_id}"

        data = {
            "author": author_id,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": visibility.value
            }
        }

        response = await self._request("POST", "/ugcPosts", data=data)

        return LinkedInPost(
            id=response.get("id", ""),
            text=text,
            author_id=organization_id,
            visibility=visibility
        )
