"""
AgentForge LinkedIn Integration Tests
LinkedIn 集成测试
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from integrations.external.linkedin_client import LinkedInClient, LinkedInManager
from integrations.external.linkedin_models import (
    Profile, Connection, Post, Visibility, PaginationParams
)


class TestLinkedInModels:
    """测试 LinkedIn 数据模型"""
    
    def test_profile_creation(self):
        """测试个人资料模型创建"""
        profile = Profile(
            id="test123",
            first_name="John",
            last_name="Doe",
            full_name="John Doe",
            headline="Software Engineer",
            summary="Experienced developer",
            location="San Francisco, CA",
            country="United States",
            public_profile_url="https://linkedin.com/in/johndoe",
            follower_count=1000,
            connection_count=500
        )
        
        assert profile.id == "test123"
        assert profile.full_name == "John Doe"
        assert profile.headline == "Software Engineer"
        assert profile.follower_count == 1000
        assert profile.connection_count == 500
    
    def test_connection_creation(self):
        """测试人脉模型创建"""
        connection = Connection(
            id="conn456",
            first_name="Jane",
            last_name="Smith",
            full_name="Jane Smith",
            headline="Product Manager",
            location="New York, NY",
            public_profile_url="https://linkedin.com/in/janesmith",
            connection_degree="1st"
        )
        
        assert connection.id == "conn456"
        assert connection.full_name == "Jane Smith"
        assert connection.connection_degree == "1st"
    
    def test_post_creation(self):
        """测试动态模型创建"""
        post = Post(
            id="post789",
            author_id="author123",
            text="Hello LinkedIn!",
            visibility=Visibility.PUBLIC,
            hashtags=["hello", "linkedin"]
        )
        
        assert post.id == "post789"
        assert post.text == "Hello LinkedIn!"
        assert post.visibility == Visibility.PUBLIC
        assert "hello" in post.hashtags


class TestLinkedInClient:
    """测试 LinkedIn API 客户端"""
    
    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return LinkedInClient(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="http://localhost:8000/callback"
        )
    
    def test_initialization(self, client):
        """测试客户端初始化"""
        assert client.client_id == "test_client_id"
        assert client.client_secret == "test_client_secret"
        assert client.redirect_uri == "http://localhost:8000/callback"
        assert client.access_token is None
    
    def test_get_authorization_url(self, client):
        """测试获取授权 URL"""
        state = "test_state_123"
        url = client.get_authorization_url(state)
        
        assert "https://www.linkedin.com/oauth/v2/authorization" in url
        assert "response_type=code" in url
        assert "client_id=test_client_id" in url
        assert f"state={state}" in url
        assert "redirect_uri=http://localhost:8000/callback" in url
    
    @pytest.mark.asyncio
    async def test_exchange_code_for_token(self, client):
        """测试用授权码换取令牌（Mock 测试）"""
        mock_response = {
            "access_token": "mock_access_token",
            "expires_in": 3600,
            "token_type": "Bearer"
        }
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response_obj = MagicMock()
            mock_response_obj.status_code = 200
            mock_response_obj.json.return_value = mock_response
            mock_post.return_value = mock_response_obj
            
            token = await client.exchange_code_for_token("test_auth_code")
            
            assert token == "mock_access_token"
            assert client.access_token == "mock_access_token"
            assert client._token_expires_at is not None
    
    @pytest.mark.asyncio
    async def test_get_profile(self, client):
        """测试获取个人资料（Mock 测试）"""
        mock_profile_data = {
            "id": "test123",
            "localizedFirstName": "John",
            "localizedLastName": "Doe",
            "headline": "Software Engineer",
            "summary": "Experienced developer",
            "location": {"localizedName": "San Francisco"},
            "country": {"localizedName": "United States"},
            "vanityName": "johndoe",
            "followerCount": 1000,
            "connectionCount": 500
        }
        
        mock_email_data = {
            "handle~": {
                "emailAddress": "john.doe@example.com"
            }
        }
        
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = [mock_profile_data, mock_email_data, None]
            
            profile = await client.get_profile()
            
            assert profile is not None
            assert profile.id == "test123"
            assert profile.full_name == "John Doe"
            assert profile.email == "john.doe@example.com"
    
    @pytest.mark.asyncio
    async def test_get_connections(self, client):
        """测试获取人脉列表（Mock 测试）"""
        mock_connections_data = {
            "elements": [
                {
                    "id": "conn1",
                    "firstName": "Jane",
                    "lastName": "Smith",
                    "headline": "Product Manager",
                    "location": {"localizedName": "New York"},
                    "profileUrl": "https://linkedin.com/in/janesmith"
                },
                {
                    "id": "conn2",
                    "firstName": "Bob",
                    "lastName": "Johnson",
                    "headline": "Data Scientist",
                    "location": {"localizedName": "Boston"},
                    "profileUrl": "https://linkedin.com/in/bobjohnson"
                }
            ]
        }
        
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_connections_data
            
            pagination = PaginationParams(start=0, count=10)
            connections = await client.get_connections(pagination)
            
            assert len(connections) == 2
            assert connections[0].full_name == "Jane Smith"
            assert connections[1].full_name == "Bob Johnson"
    
    @pytest.mark.asyncio
    async def test_create_post(self, client):
        """测试创建动态（Mock 测试）"""
        mock_post_data = {
            "id": "post123",
            "author": "urn:li:person:test123",
            "lifecycleState": "PUBLISHED"
        }
        
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_post_data
            with patch.object(client, '_get_person_id', new_callable=AsyncMock) as mock_get_id:
                mock_get_id.return_value = "test123"
                
                post = await client.create_post(
                    text="Hello LinkedIn!",
                    visibility=Visibility.PUBLIC,
                    hashtags=["hello", "test"]
                )
                
                assert post is not None
                assert post.id == "post123"
                assert "Hello LinkedIn!" in post.text
    
    @pytest.mark.asyncio
    async def test_delete_post(self, client):
        """测试删除动态（Mock 测试）"""
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": True}
            
            success = await client.delete_post("post123")
            
            assert success is True
            mock_request.assert_called_once_with("DELETE", "/ugcPosts/post123")
    
    @pytest.mark.asyncio
    async def test_test_connection(self, client):
        """测试连接测试（Mock 测试）"""
        mock_profile = Profile(
            id="test123",
            first_name="Test",
            last_name="User",
            full_name="Test User",
            public_profile_url="https://linkedin.com/in/testuser"
        )
        
        with patch.object(client, 'get_profile', new_callable=AsyncMock) as mock_get_profile:
            mock_get_profile.return_value = mock_profile
            
            success = await client.test_connection()
            
            assert success is True
    
    @pytest.mark.asyncio
    async def test_request_without_token(self, client):
        """测试无令牌时的请求"""
        client.access_token = None
        
        result = await client._request("GET", "/me")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_request_with_error(self, client):
        """测试请求出错时的处理"""
        with patch('httpx.AsyncClient.request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = Exception("Connection error")
            
            result = await client._request("GET", "/me")
            
            assert result is None


class TestLinkedInManager:
    """测试 LinkedIn 管理器"""
    
    @pytest.fixture
    def manager(self):
        """创建测试管理器"""
        client = LinkedInClient(
            client_id="test_client_id",
            client_secret="test_client_secret"
        )
        return LinkedInManager(client)
    
    @pytest.mark.asyncio
    async def test_sync_profile(self, manager):
        """测试同步个人资料（Mock 测试）"""
        mock_profile = Profile(
            id="test123",
            first_name="John",
            last_name="Doe",
            full_name="John Doe",
            public_profile_url="https://linkedin.com/in/johndoe"
        )
        
        with patch.object(manager.client, 'get_profile', new_callable=AsyncMock) as mock_get_profile:
            mock_get_profile.return_value = mock_profile
            
            profile = await manager.sync_profile()
            
            assert profile is not None
            assert profile.full_name == "John Doe"
    
    @pytest.mark.asyncio
    async def test_auto_post(self, manager):
        """测试自动发布动态（Mock 测试）"""
        mock_post = Post(
            id="post123",
            author_id="test123",
            text="Auto-posted content",
            visibility=Visibility.PUBLIC
        )
        
        with patch.object(manager.client, 'create_post', new_callable=AsyncMock) as mock_create_post:
            mock_create_post.return_value = mock_post
            
            success = await manager.auto_post("Auto-posted content")
            
            assert success is True
    
    @pytest.mark.asyncio
    async def test_get_network_summary(self, manager):
        """测试获取网络摘要（Mock 测试）"""
        mock_connections = [
            Connection(
                id="conn1",
                first_name="Jane",
                last_name="Smith",
                full_name="Jane Smith",
                headline="Software Engineer at Tech Company",
                location="San Francisco",
                public_profile_url="https://linkedin.com/in/janesmith"
            ),
            Connection(
                id="conn2",
                first_name="Bob",
                last_name="Johnson",
                full_name="Bob Johnson",
                headline="Finance Manager at Bank",
                location="New York",
                public_profile_url="https://linkedin.com/in/bobjohnson"
            )
        ]
        
        with patch.object(manager.client, 'get_connections', new_callable=AsyncMock) as mock_get_connections:
            mock_get_connections.return_value = mock_connections
            
            summary = await manager.get_network_summary()
            
            assert "total_connections" in summary
            assert summary["total_connections"] == 2
            assert "top_industries" in summary
            assert "recent_connections" in summary


class TestLinkedInIntegration:
    """LinkedIn 集成测试"""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """测试完整工作流程（Mock 测试）"""
        # 1. 创建客户端
        client = LinkedInClient(
            client_id="test_client_id",
            client_secret="test_client_secret"
        )
        
        # 2. 获取授权 URL
        state = "test_state"
        auth_url = client.get_authorization_url(state)
        assert "linkedin.com" in auth_url
        
        # 3. Mock 令牌交换
        mock_token_response = {
            "access_token": "mock_token",
            "expires_in": 3600
        }
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_token_response
            mock_post.return_value = mock_response
            
            token = await client.exchange_code_for_token("test_code")
            assert token == "mock_token"
        
        # 4. Mock 获取个人资料
        mock_profile_data = {
            "id": "test123",
            "localizedFirstName": "John",
            "localizedLastName": "Doe",
            "headline": "Developer",
            "vanityName": "johndoe"
        }
        
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_profile_data
            
            profile = await client.get_profile()
            assert profile is not None
            assert profile.full_name == "John Doe"
        
        # 5. 测试连接
        with patch.object(client, 'get_profile', new_callable=AsyncMock) as mock_get_profile:
            mock_profile = Profile(
                id="test123",
                first_name="John",
                last_name="Doe",
                full_name="John Doe",
                public_profile_url="https://linkedin.com/in/johndoe"
            )
            mock_get_profile.return_value = mock_profile
            
            success = await client.test_connection()
            assert success is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
