"""
AgentForge Feishu Integration Tests
飞书集成测试
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

from integrations.external.feishu_client import FeishuClient, FeishuBotManager
from integrations.external.feishu_models import (
    User, Notification, NotificationType, Subscriber, CalendarEvent, Document
)


class TestFeishuModels:
    """测试飞书数据模型"""
    
    def test_user_creation(self):
        """测试用户模型创建"""
        user = User(
            user_id="test123",
            open_id="ou_test123",
            union_id="un_test123",
            name="张三",
            email="zhangsan@example.com",
            mobile="13800138000"
        )
        
        assert user.user_id == "test123"
        assert user.name == "张三"
        assert user.email == "zhangsan@example.com"
    
    def test_notification_creation(self):
        """测试通知模型创建"""
        notification = Notification(
            id="notif_123",
            type=NotificationType.TASK_COMPLETED,
            title="任务完成",
            content="任务已成功完成",
            receiver_id="ou_test123",
            receiver_type="user"
        )
        
        assert notification.id == "notif_123"
        assert notification.type == NotificationType.TASK_COMPLETED
        assert notification.receiver_id == "ou_test123"
    
    def test_calendar_event_creation(self):
        """测试日历事件模型创建"""
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=1)
        
        event = CalendarEvent(
            event_id="event_123",
            summary="团队会议",
            description="每周例会",
            start_time=start_time,
            end_time=end_time,
            organizer_id="ou_test123",
            attendee_ids=["ou_test456"]
        )
        
        assert event.event_id == "event_123"
        assert event.summary == "团队会议"
        assert len(event.attendee_ids) == 1


class TestFeishuClient:
    """测试飞书客户端"""
    
    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return FeishuClient(
            app_id="test_app_id",
            app_secret="test_app_secret"
        )
    
    def test_initialization(self, client):
        """测试客户端初始化"""
        assert client.app_id == "test_app_id"
        assert client.app_secret == "test_app_secret"
        assert client._tenant_access_token is None
    
    @pytest.mark.asyncio
    async def test_get_tenant_access_token(self, client):
        """测试获取 tenant_access_token（Mock 测试）"""
        mock_response = {
            "tenant_access_token": "test_token_123",
            "expire": 7200
        }
        
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            await client._get_tenant_access_token()
            
            assert client._tenant_access_token == "test_token_123"
            assert client._token_expires_at is not None
    
    @pytest.mark.asyncio
    async def test_get_user_info(self, client):
        """测试获取用户信息（Mock 测试）"""
        mock_response = {
            "user": {
                "user_id": "test123",
                "open_id": "ou_test123",
                "union_id": "un_test123",
                "name": "张三",
                "email": "zhangsan@example.com",
                "mobile": "13800138000",
                "gender": 1,
                "status": {"is_activated": 1}
            }
        }
        
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            user = await client.get_user_info("test123")
            
            assert user is not None
            assert user.user_id == "test123"
            assert user.name == "张三"
    
    @pytest.mark.asyncio
    async def test_send_text_message(self, client):
        """测试发送文本消息（Mock 测试）"""
        mock_response = {
            "message_id": "msg_123",
            "sender_id": "bot_456",
            "create_time": int(datetime.now().timestamp() * 1000)
        }
        
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            message = await client.send_text_message(
                chat_id="chat_123",
                text="Hello, Feishu!",
                receive_id="ou_test123"
            )
            
            assert message is not None
            assert message.message_id == "msg_123"
    
    @pytest.mark.asyncio
    async def test_send_notification(self, client):
        """测试发送通知（Mock 测试）"""
        notification = Notification(
            id="notif_123",
            type=NotificationType.TASK_COMPLETED,
            title="任务完成",
            content="任务已成功完成",
            receiver_id="ou_test123",
            receiver_type="user"
        )
        
        mock_response = {
            "message_id": "msg_123",
            "create_time": int(datetime.now().timestamp() * 1000)
        }
        
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            success = await client.send_notification(notification)
            
            assert success is True
            assert notification.sent is True
    
    @pytest.mark.asyncio
    async def test_broadcast_notification(self, client):
        """测试广播通知（Mock 测试）"""
        subscribers = [
            Subscriber(
                user_id="user1",
                open_id="ou_user1",
                name="User1",
                subscribed_types=[NotificationType.TASK_COMPLETED],
                enabled=True
            ),
            Subscriber(
                user_id="user2",
                open_id="ou_user2",
                name="User2",
                subscribed_types=[NotificationType.ERROR_ALERT],
                enabled=True
            )
        ]
        
        notification = Notification(
            id="notif_broadcast",
            type=NotificationType.TASK_COMPLETED,
            title="任务完成",
            content="任务已完成",
            receiver_id="0"
        )
        
        with patch.object(client, 'send_notification', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True
            
            stats = await client.broadcast_notification(notification, subscribers)
            
            assert stats["sent"] == 1  # 只有 1 个用户订阅了 TASK_COMPLETED
            assert stats["failed"] == 0
    
    @pytest.mark.asyncio
    async def test_create_calendar_event(self, client):
        """测试创建日历事件（Mock 测试）"""
        mock_response = {
            "event_id": "event_123"
        }
        
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=1)
        
        event = CalendarEvent(
            event_id="",
            summary="团队会议",
            start_time=start_time,
            end_time=end_time,
            organizer_id="ou_test123"
        )
        
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            created_event = await client.create_calendar_event(event)
            
            assert created_event is not None
            assert created_event.event_id == "event_123"
    
    @pytest.mark.asyncio
    async def test_get_calendar_events(self, client):
        """测试获取日历事件（Mock 测试）"""
        mock_response = {
            "items": [
                {
                    "event_id": "event_1",
                    "summary": "会议 1",
                    "start_time": {"timestamp": int(datetime.now().timestamp())},
                    "organizer_id": "ou_test123"
                }
            ]
        }
        
        time_min = datetime.now()
        time_max = time_min + timedelta(days=1)
        
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            events = await client.get_calendar_events(time_min, time_max)
            
            assert len(events) == 1
            assert events[0].event_id == "event_1"
    
    @pytest.mark.asyncio
    async def test_get_document(self, client):
        """测试获取文档（Mock 测试）"""
        mock_response = {
            "document_id": "doc_123",
            "title": "测试文档",
            "doc_type": "doc",
            "owner_id": "ou_test123",
            "create_time": int(datetime.now().timestamp() * 1000),
            "update_time": int(datetime.now().timestamp() * 1000)
        }
        
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            doc = await client.get_document("doc_123")
            
            assert doc is not None
            assert doc.doc_id == "doc_123"
            assert doc.title == "测试文档"
    
    @pytest.mark.asyncio
    async def test_test_connection(self, client):
        """测试连接（Mock 测试）"""
        mock_response = {
            "name": "测试用户",
            "user_id": "test123"
        }
        
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            success = await client.test_connection()
            
            assert success is True
    
    def test_verify_webhook_signature(self, client):
        """测试 Webhook 签名验证"""
        client.verification_token = "test_token"
        
        timestamp = "1234567890"
        body = '{"test": "data"}'
        
        import hashlib
        import base64
        import hmac
        
        string_to_sign = timestamp + "test_token" + body
        signature = base64.b64encode(
            hmac.new(
                "test_token".encode(),
                string_to_sign.encode(),
                hashlib.sha256
            ).digest()
        ).decode()
        
        result = client.verify_webhook_signature(signature, timestamp, body)
        assert result is True


class TestFeishuBotManager:
    """测试飞书 Bot 管理器"""
    
    @pytest.fixture
    def manager(self):
        """创建测试管理器"""
        client = FeishuClient(app_id="test", app_secret="test")
        return FeishuBotManager(client)
    
    @pytest.mark.asyncio
    async def test_initialize(self, manager):
        """测试初始化"""
        with patch.object(manager.client, 'test_connection', new_callable=AsyncMock) as mock_test:
            mock_test.return_value = True
            
            await manager.initialize()
    
    @pytest.mark.asyncio
    async def test_send_system_notification(self, manager):
        """测试发送系统通知"""
        with patch.object(manager.client, 'send_notification', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True
            
            await manager.send_system_notification(
                notification_type=NotificationType.TASK_CREATED,
                title="新任务",
                content="任务创建",
                receiver_id="ou_test123"
            )
            
            mock_send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_notify_task_created(self, manager):
        """测试通知任务创建"""
        with patch.object(manager, 'send_system_notification', new_callable=AsyncMock) as mock_notify:
            mock_notify.return_value = None
            
            await manager.notify_task_created(
                task_id="task_123",
                task_type="fiverr_order",
                description="新订单",
                user_id="ou_test123"
            )
            
            mock_notify.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_notify_task_completed(self, manager):
        """测试通知任务完成"""
        with patch.object(manager, 'send_system_notification', new_callable=AsyncMock) as mock_notify:
            mock_notify.return_value = None
            
            await manager.notify_task_completed(
                task_id="task_123",
                task_type="fiverr_order",
                result="成功",
                user_id="ou_test123"
            )
            
            mock_notify.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_notify_error(self, manager):
        """测试通知错误"""
        with patch.object(manager, 'send_system_notification', new_callable=AsyncMock) as mock_notify:
            mock_notify.return_value = None
            
            await manager.notify_error(
                error="测试错误",
                level="ERROR",
                user_id="ou_test123"
            )
            
            mock_notify.assert_called_once()


class TestFeishuIntegration:
    """飞书集成测试"""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """测试完整工作流程（Mock 测试）"""
        # 1. 创建客户端
        client = FeishuClient(app_id="test", app_secret="test")
        
        # 2. Mock 获取 token
        mock_token = {"tenant_access_token": "test_token", "expire": 7200}
        
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_token
            
            await client._get_tenant_access_token()
            assert client._tenant_access_token == "test_token"
        
        # 3. Mock 获取用户信息
        mock_user_data = {
            "user": {
                "user_id": "test123",
                "name": "测试用户",
                "email": "test@example.com"
            }
        }
        
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_user_data
            
            user = await client.get_user_info("test123")
            assert user is not None
            assert user.name == "测试用户"
        
        # 4. Mock 发送消息
        mock_message_data = {
            "message_id": "msg_123",
            "create_time": int(datetime.now().timestamp() * 1000)
        }
        
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_message_data
            
            message = await client.send_text_message(
                chat_id="chat_123",
                text="Hello",
                receive_id="ou_test123"
            )
            
            assert message is not None
            assert message.message_id == "msg_123"
        
        # 5. 测试连接
        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"name": "Test", "user_id": "test123"}
            
            success = await client.test_connection()
            assert success is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
