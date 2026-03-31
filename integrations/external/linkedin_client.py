"""
AgentForge LinkedIn Integration Client
LinkedIn API 客户端实现
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import httpx
from loguru import logger

from agentforge.config import settings
from integrations.external.linkedin_models import (
    Profile, Connection, Message, Post, Job, Comment,
    Company, Share, Notification, Analytics, LinkedInError,
    PaginationParams, Visibility
)


class LinkedInClient:
    """LinkedIn API 客户端"""
    
    BASE_URL = "https://api.linkedin.com/v2"
    AUTH_URL = "https://www.linkedin.com/oauth/v2"
    
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        redirect_uri: Optional[str] = None
    ):
        """
        初始化 LinkedIn 客户端
        
        Args:
            client_id: LinkedIn 应用 Client ID
            client_secret: LinkedIn 应用 Client Secret
            access_token: 访问令牌（可选，如果已有）
            redirect_uri: OAuth 重定向 URI
        """
        self.client_id = client_id or getattr(settings, 'linkedin_client_id', None)
        self.client_secret = client_secret or getattr(settings, 'linkedin_client_secret', None)
        self.access_token = access_token
        self.redirect_uri = redirect_uri or getattr(settings, 'linkedin_redirect_uri', None)
        
        self._token_expires_at: Optional[datetime] = None
        
        if not self.client_id or not self.client_secret:
            logger.warning("LinkedIn credentials not configured")
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        return headers
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        发送 HTTP 请求
        
        Args:
            method: HTTP 方法
            endpoint: API 端点
            params: 查询参数
            json: JSON 数据
            
        Returns:
            API 响应数据
        """
        if not self.access_token:
            logger.error("LinkedIn access token not available")
            return None
        
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self._get_headers(),
                    params=params,
                    json=json
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 401:
                    logger.error("LinkedIn authentication failed - token may be expired")
                    # 可以尝试刷新令牌
                    return None
                else:
                    error_data = response.json()
                    logger.error(f"LinkedIn API error: {error_data}")
                    return None
                    
        except Exception as e:
            logger.error(f"LinkedIn request failed: {e}")
            return None
    
    # ========== 认证相关 ==========
    
    def get_authorization_url(self, state: str = "") -> str:
        """
        获取授权 URL
        
        Args:
            state: 用于防止 CSRF 攻击的随机字符串
            
        Returns:
            授权 URL
        """
        scopes = [
            "r_liteprofile",  # 基本资料
            "r_emailaddress",  # 邮箱
            "w_member_social",  # 发布动态
            "r_basicprofile",  # 详细资料
            "r_1st_connections",  # 一度人脉
            "r_organization_social",  # 公司主页
            "w_organization_social"  # 管理公司主页
        ]
        
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "state": state,
            "scope": " ".join(scopes)
        }
        
        query = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.AUTH_URL}/authorization?{query}"
    
    async def exchange_code_for_token(self, code: str) -> Optional[str]:
        """
        用授权码换取访问令牌
        
        Args:
            code: 授权码
            
        Returns:
            访问令牌
        """
        if not self.client_id or not self.client_secret:
            logger.error("LinkedIn credentials not configured")
            return None
        
        url = f"{self.AUTH_URL}/accessToken"
        params = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    self.access_token = data.get("access_token")
                    expires_in = data.get("expires_in", 3600)
                    self._token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                    
                    logger.info("Successfully obtained access token")
                    return self.access_token
                else:
                    logger.error(f"Failed to exchange code: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Token exchange failed: {e}")
            return None
    
    async def refresh_token(self, refresh_token: str) -> Optional[str]:
        """
        刷新访问令牌
        
        Args:
            refresh_token: 刷新令牌
            
        Returns:
            新的访问令牌
        """
        if not self.client_id or not self.client_secret:
            return None
        
        url = f"{self.AUTH_URL}/accessToken"
        params = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    self.access_token = data.get("access_token")
                    expires_in = data.get("expires_in", 3600)
                    self._token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                    
                    return self.access_token
                else:
                    logger.error(f"Token refresh failed: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            return None
    
    # ========== 个人资料相关 ==========
    
    async def get_profile(self) -> Optional[Profile]:
        """
        获取个人资料
        
        Returns:
            个人资料
        """
        # 获取基本信息
        profile_data = await self._request("GET", "/me")
        if not profile_data:
            return None
        
        # 获取邮箱
        email_data = await self._request(
            "GET",
            "/emailAddress",
            params={
                "q": "members",
                "projection": "(handle~)"
            }
        )
        
        email = None
        if email_data and "handle~" in email_data:
            email = email_data["handle~"].get("emailAddress")
        
        # 获取头像
        profile_picture_data = await self._request(
            "GET",
            "/me/profilePicture",
            params={
                "q": "member",
                "projection": "(original)"
            }
        )
        
        profile_picture_url = None
        if profile_picture_data and "value" in profile_picture_data:
            profile_picture_url = profile_picture_data["value"]
        
        # 构建 Profile 对象
        profile = Profile(
            id=profile_data.get("id", ""),
            first_name=profile_data.get("localizedFirstName", ""),
            last_name=profile_data.get("localizedLastName", ""),
            full_name=f"{profile_data.get('localizedFirstName', '')} {profile_data.get('localizedLastName', '')}",
            headline=profile_data.get("headline", ""),
            summary=profile_data.get("summary", ""),
            location=profile_data.get("location", {}).get("localizedName", "") if profile_data.get("location") else "",
            country=profile_data.get("country", {}).get("localizedName", "") if profile_data.get("country") else "",
            public_profile_url=profile_data.get("vanityName", ""),
            follower_count=profile_data.get("followerCount", 0),
            connection_count=profile_data.get("connectionCount", 0),
            profile_picture_url=profile_picture_url,
            email=email
        )
        
        return profile
    
    async def update_profile(self, **kwargs) -> bool:
        """
        更新个人资料
        
        Args:
            **kwargs: 要更新的字段
            
        Returns:
            是否成功
        """
        # LinkedIn API 不支持直接更新资料，需要通过其他方式
        logger.warning("LinkedIn API does not support direct profile updates")
        return False
    
    # ========== 人脉管理相关 ==========
    
    async def get_connections(
        self,
        pagination: Optional[PaginationParams] = None
    ) -> List[Connection]:
        """
        获取人脉列表
        
        Args:
            pagination: 分页参数
            
        Returns:
            人脉列表
        """
        params = {
            "q": "viewer",
            "projection": "(elements*(firstName,lastName,headline,location,picture,profileUrl))"
        }
        
        if pagination:
            params["start"] = pagination.start
            params["count"] = pagination.count
        
        data = await self._request("GET", "/relationships/1stConnections", params=params)
        
        if not data or "elements" not in data:
            return []
        
        connections = []
        for elem in data["elements"]:
            connection = Connection(
                id=elem.get("id", ""),
                first_name=elem.get("firstName", ""),
                last_name=elem.get("lastName", ""),
                full_name=f"{elem.get('firstName', '')} {elem.get('lastName', '')}",
                headline=elem.get("headline", ""),
                location=elem.get("location", {}).get("localizedName", "") if elem.get("location") else "",
                public_profile_url=elem.get("profileUrl", ""),
                profile_picture_url=elem.get("picture", {}).get("displayImage~", {}).get("elements", [{}])[0].get("identifiers", [{}])[0].get("identifier")
            )
            connections.append(connection)
        
        return connections
    
    async def send_connection_request(
        self,
        recipient_id: str,
        message: str = ""
    ) -> bool:
        """
        发送人脉请求
        
        Args:
            recipient_id: 接收者 ID
            message: 附言
            
        Returns:
            是否成功
        """
        # LinkedIn API 不支持直接发送连接请求，需要通过前端
        logger.warning("LinkedIn API does not support sending connection requests directly")
        return False
    
    # ========== 消息相关 ==========
    
    async def send_message(self, recipient_id: str, text: str) -> Optional[Message]:
        """
        发送消息
        
        Args:
            recipient_id: 接收者 ID
            text: 消息内容
            
        Returns:
            发送的消息
        """
        # LinkedIn API 的消息功能有限，这里仅作示例
        logger.warning("LinkedIn Messaging API requires special access")
        return None
    
    async def get_conversations(self) -> List[Dict[str, Any]]:
        """获取对话列表"""
        # 需要特殊权限
        return []
    
    # ========== 动态发布相关 ==========
    
    async def create_post(
        self,
        text: str,
        visibility: Visibility = Visibility.PUBLIC,
        images: Optional[List[str]] = None,
        hashtags: Optional[List[str]] = None
    ) -> Optional[Post]:
        """
        创建动态
        
        Args:
            text: 动态内容
            visibility: 可见性
            images: 图片 URL 列表
            hashtags: 话题标签
            
        Returns:
            创建的动态
        """
        # 构建内容
        content = text
        if hashtags:
            content += "\n\n" + " ".join([f"#{tag}" for tag in hashtags])
        
        payload = {
            "author": f"urn:li:person:{await self._get_person_id()}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": content
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": visibility.value
            }
        }
        
        data = await self._request("POST", "/ugcPosts", json=payload)
        
        if not data:
            return None
        
        post = Post(
            id=data.get("id", ""),
            author_id=await self._get_person_id(),
            text=content,
            visibility=visibility,
            hashtags=hashtags or [],
            created_at=datetime.now()
        )
        
        return post
    
    async def get_posts(
        self,
        author_id: Optional[str] = None,
        pagination: Optional[PaginationParams] = None
    ) -> List[Post]:
        """
        获取动态列表
        
        Args:
            author_id: 作者 ID（不传则为当前用户）
            pagination: 分页参数
            
        Returns:
            动态列表
        """
        if not author_id:
            author_id = await self._get_person_id()
        
        params = {
            "q": "authors",
            "authors": [f"urn:li:person:{author_id}"],
            "count": pagination.count if pagination else 10,
            "start": pagination.start if pagination else 0
        }
        
        data = await self._request("GET", "/ugcPosts", params=params)
        
        if not data or "elements" not in data:
            return []
        
        posts = []
        for elem in data["elements"]:
            post = Post(
                id=elem.get("id", ""),
                author_id=author_id,
                text=elem.get("specificContent", {}).get("com.linkedin.ugc.ShareContent", {}).get("shareCommentary", {}).get("text", ""),
                visibility=elem.get("visibility", {}).get("com.linkedin.ugc.MemberNetworkVisibility", "public"),
                like_count=elem.get("specificContent", {}).get("com.linkedin.ugc.ShareContent", {}).get("shareMediaCategory", ""),
                created_at=datetime.fromtimestamp(elem.get("created", {}).get("time", 0) / 1000) if elem.get("created") else datetime.now()
            )
            posts.append(post)
        
        return posts
    
    async def delete_post(self, post_id: str) -> bool:
        """
        删除动态
        
        Args:
            post_id: 动态 ID
            
        Returns:
            是否成功
        """
        data = await self._request("DELETE", f"/ugcPosts/{post_id}")
        return data is not None
    
    # ========== 职位相关 ==========
    
    async def get_jobs(
        self,
        keywords: Optional[str] = None,
        location: Optional[str] = None,
        pagination: Optional[PaginationParams] = None
    ) -> List[Job]:
        """
        获取职位列表
        
        Args:
            keywords: 关键词
            location: 地点
            pagination: 分页参数
            
        Returns:
            职位列表
        """
        # LinkedIn Jobs API 需要特殊权限
        logger.warning("LinkedIn Jobs API requires special access")
        return []
    
    async def create_job(self, job: Job) -> Optional[Job]:
        """
        创建职位
        
        Args:
            job: 职位信息
            
        Returns:
            创建的职位
        """
        # 需要公司页面管理权限
        logger.warning("Creating jobs requires company page admin access")
        return None
    
    # ========== 公司相关 ==========
    
    async def get_company(self, company_id: str) -> Optional[Company]:
        """
        获取公司信息
        
        Args:
            company_id: 公司 ID
            
        Returns:
            公司信息
        """
        data = await self._request("GET", f"/organizations/{company_id}")
        
        if not data:
            return None
        
        company = Company(
            id=str(data.get("id", "")),
            name=data.get("localizedName", ""),
            universal_name=data.get("universalName", ""),
            description=data.get("description", ""),
            website=data.get("companyPageUrl", ""),
            industry=data.get("industry", ""),
            company_size=data.get("companySize", ""),
            company_type=data.get("type", ""),
            follower_count=data.get("followerCount", 0),
            employee_count=data.get("staffCount", 0)
        )
        
        return company
    
    async def get_company_posts(
        self,
        company_id: str,
        pagination: Optional[PaginationParams] = None
    ) -> List[Post]:
        """获取公司主页动态"""
        # 需要公司页面管理权限
        return []
    
    # ========== 分析数据相关 ==========
    
    async def get_analytics(
        self,
        period: str = "last_7_days"
    ) -> Optional[Analytics]:
        """
        获取分析数据
        
        Args:
            period: 时间段
            
        Returns:
            分析数据
        """
        # 获取个人主页浏览量
        profile_views = await self._get_profile_views(period)
        
        # 获取帖子曝光量
        post_impressions = await self._get_post_impressions(period)
        
        analytics = Analytics(
            profile_views=profile_views,
            post_impressions=post_impressions,
            period=period
        )
        
        return analytics
    
    async def _get_profile_views(self, period: str) -> int:
        """获取个人主页浏览量"""
        # 需要 Analytics API 权限
        return 0
    
    async def _get_post_impressions(self, period: str) -> int:
        """获取帖子曝光量"""
        # 需要 Analytics API 权限
        return 0
    
    # ========== 工具方法 ==========
    
    async def _get_person_id(self) -> str:
        """获取当前用户 ID"""
        profile = await self.get_profile()
        return profile.id if profile else ""
    
    async def test_connection(self) -> bool:
        """
        测试连接是否正常
        
        Returns:
            是否成功
        """
        try:
            profile = await self.get_profile()
            return profile is not None
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False


class LinkedInManager:
    """LinkedIn 管理器 - 高级封装"""
    
    def __init__(self, client: Optional[LinkedInClient] = None):
        """
        初始化 LinkedIn 管理器
        
        Args:
            client: LinkedIn 客户端
        """
        self.client = client or LinkedInClient()
    
    async def sync_profile(self) -> Optional[Profile]:
        """
        同步个人资料
        
        Returns:
            同步的个人资料
        """
        return await self.client.get_profile()
    
    async def auto_post(self, content: str, hashtags: Optional[List[str]] = None) -> bool:
        """
        自动发布动态
        
        Args:
            content: 内容
            hashtags: 话题标签
            
        Returns:
            是否成功
        """
        post = await self.client.create_post(content, hashtags=hashtags)
        return post is not None
    
    async def get_network_summary(self) -> Dict[str, Any]:
        """
        获取人脉网络摘要
        
        Returns:
            网络摘要
        """
        connections = await self.client.get_connections()
        
        # 统计行业分布
        industries = {}
        for conn in connections[:100]:  # 只统计前 100 个
            if conn.headline:
                # 简单提取行业关键词
                for keyword in ["Technology", "Finance", "Healthcare", "Education", "Marketing"]:
                    if keyword.lower() in conn.headline.lower():
                        industries[keyword] = industries.get(keyword, 0) + 1
        
        return {
            "total_connections": len(connections),
            "top_industries": industries,
            "recent_connections": [
                {
                    "name": conn.full_name,
                    "headline": conn.headline,
                    "location": conn.location
                }
                for conn in connections[:10]
            ]
        }
