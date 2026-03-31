"""
AgentForge Telegram Bot Integration Tests
Telegram Bot 集成测试
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from integrations.external.telegram_bot import TelegramBot, TelegramBotManager
from integrations.external.telegram_models import (
    User, Chat, Message, Notification, NotificationType, Subscriber,
    BotInfo, WebhookInfo, Update
)


class TestTelegramModels:
    """测试 Telegram 数据模型"""
    
    def test_user_creation(self):
        """测试用户模型创建"""
        user = User(
            id=123456,
            is_bot=False,
            first_name="John",
            last_name="Doe",
            username="johndoe",
            language_code="en"
        )
        
        assert user.id == 123456
        assert user.first_name == "John"
        assert user.username == "johndoe"
        assert user.is_bot is False
    
    def test_chat_creation(self):
        """测试聊天模型创建"""
        chat = Chat(
            id=789012,
            type="private",
            first_name="John",
            username="johndoe"
        )
        
        assert chat.id == 789012
        assert chat.type == "private"
        assert chat.first_name == "John"
    
    def test_message_creation(self):
        """测试消息模型创建"""
        chat = Chat(id=123, type="private")
        user = User(id=456, first_name="Test", is_bot=False)
        
        message = Message(
            message_id=1,
            chat=chat,
            from_user=user,
            date=datetime.now(),
            text="Hello, Telegram!",
        )
        
        assert message.message_id == 1
        assert message.text == "Hello, Telegram!"
        assert message.from_user.first_name == "Test"
    
    def test_notification_creation(self):
        """测试通知模型创建"""
        notification = Notification(
            id="notif_123",
            type=NotificationType.SYSTEM_STATUS,
            title="System Status",
            message="All systems operational",
            chat_id=123456
        )
        
        assert notification.id == "notif_123"
        assert notification.type == NotificationType.SYSTEM_STATUS
        assert notification.chat_id == 123456
        assert notification.sent is False
    
    def test_subscriber_creation(self):
        """测试订阅者模型创建"""
        subscriber = Subscriber(
            user_id=123456,
            chat_id=123456,
            username="johndoe",
            first_name="John",
            subscribed_types=[NotificationType.SYSTEM_STATUS, NotificationType.ERROR_ALERT]
        )
        
        assert subscriber.user_id == 123456
        assert subscriber.username == "johndoe"
        assert len(subscriber.subscribed_types) == 2


class TestTelegramBot:
    """测试 Telegram Bot 客户端"""
    
    @pytest.fixture
    def bot(self):
        """创建测试 Bot"""
        return TelegramBot(token="test_token_123")
    
    def test_initialization(self, bot):
        """测试 Bot 初始化"""
        assert bot.token == "test_token_123"
        assert bot._running is False
        assert len(bot._command_handlers) == 0
    
    def test_get_url(self, bot):
        """测试 URL 生成"""
        url = bot._get_url("getMe")
        assert url == "https://api.telegram.org/bottest_token_123/getMe"
    
    @pytest.mark.asyncio
    async def test_get_me(self, bot):
        """测试获取机器人信息（Mock 测试）"""
        mock_response = {
            "id": 123456,
            "is_bot": True,
            "first_name": "TestBot",
            "username": "test_bot",
            "can_join_groups": True,
            "can_read_all_group_messages": False,
            "supports_inline_queries": False
        }
        
        with patch.object(bot, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            bot_info = await bot.get_me()
            
            assert bot_info is not None
            assert bot_info.id == 123456
            assert bot_info.username == "test_bot"
            assert bot_info.is_bot is True
    
    @pytest.mark.asyncio
    async def test_send_message(self, bot):
        """测试发送消息（Mock 测试）"""
        mock_response = {
            "message_id": 1,
            "from": {
                "id": 123456,
                "is_bot": True,
                "first_name": "TestBot",
                "username": "test_bot"
            },
            "chat": {
                "id": 789012,
                "first_name": "John",
                "type": "private"
            },
            "date": int(datetime.now().timestamp()),
            "text": "Hello!"
        }
        
        with patch.object(bot, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            message = await bot.send_message(
                chat_id=789012,
                text="Hello!"
            )
            
            assert message is not None
            assert message.message_id == 1
            assert message.text == "Hello!"
    
    @pytest.mark.asyncio
    async def test_send_photo(self, bot):
        """测试发送照片（Mock 测试）"""
        mock_response = {
            "message_id": 2,
            "from": {"id": 123456, "is_bot": True, "first_name": "TestBot"},
            "chat": {"id": 789012, "type": "private"},
            "date": int(datetime.now().timestamp()),
            "photo": [{"file_id": "photo123", "width": 800, "height": 600}]
        }
        
        with patch.object(bot, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            message = await bot.send_photo(
                chat_id=789012,
                photo="https://example.com/photo.jpg",
                caption="Check this out!"
            )
            
            assert message is not None
            assert message.message_id == 2
    
    @pytest.mark.asyncio
    async def test_delete_message(self, bot):
        """测试删除消息（Mock 测试）"""
        with patch.object(bot, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = True
            
            success = await bot.delete_message(
                chat_id=789012,
                message_id=1
            )
            
            assert success is True
            mock_request.assert_called_once_with(
                "POST",
                "deleteMessage",
                json={"chat_id": 789012, "message_id": 1}
            )
    
    @pytest.mark.asyncio
    async def test_set_webhook(self, bot):
        """测试设置 Webhook（Mock 测试）"""
        with patch.object(bot, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = True
            
            success = await bot.set_webhook(
                url="https://example.com/webhook",
                max_connections=40
            )
            
            assert success is True
            assert bot._webhook_url == "https://example.com/webhook"
    
    @pytest.mark.asyncio
    async def test_get_webhook_info(self, bot):
        """测试获取 Webhook 信息（Mock 测试）"""
        mock_response = {
            "url": "https://example.com/webhook",
            "has_custom_certificate": False,
            "pending_update_count": 0,
            "max_connections": 40
        }
        
        with patch.object(bot, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            info = await bot.get_webhook_info()
            
            assert info is not None
            assert info.url == "https://example.com/webhook"
            assert info.max_connections == 40
    
    @pytest.mark.asyncio
    async def test_get_updates(self, bot):
        """测试获取更新（Mock 测试）"""
        mock_response = [
            {
                "update_id": 1,
                "message": {
                    "message_id": 1,
                    "from": {"id": 123, "is_bot": False, "first_name": "John"},
                    "chat": {"id": 123, "type": "private"},
                    "date": int(datetime.now().timestamp()),
                    "text": "/start"
                }
            }
        ]
        
        with patch.object(bot, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            updates = await bot.get_updates(offset=0, limit=100)
            
            assert len(updates) == 1
            assert updates[0].update_id == 1
    
    @pytest.mark.asyncio
    async def test_send_notification(self, bot):
        """测试发送通知（Mock 测试）"""
        notification = Notification(
            id="notif_123",
            type=NotificationType.SYSTEM_STATUS,
            title="System Status",
            message="All systems operational",
            chat_id=123456
        )
        
        mock_response = {
            "message_id": 1,
            "from": {"id": 123456, "is_bot": True, "first_name": "TestBot"},
            "chat": {"id": 123456, "type": "private"},
            "date": int(datetime.now().timestamp()),
            "text": "<b>System Status</b>\n\nAll systems operational"
        }
        
        with patch.object(bot, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            success = await bot.send_notification(notification)
            
            assert success is True
            assert notification.sent is True
    
    @pytest.mark.asyncio
    async def test_broadcast_notification(self, bot):
        """测试广播通知（Mock 测试）"""
        subscribers = [
            Subscriber(
                user_id=1,
                chat_id=101,
                first_name="User1",
                subscribed_types=[NotificationType.SYSTEM_STATUS],
                enabled=True
            ),
            Subscriber(
                user_id=2,
                chat_id=102,
                first_name="User2",
                subscribed_types=[NotificationType.ERROR_ALERT],
                enabled=True
            )
        ]
        
        notification = Notification(
            id="notif_123",
            type=NotificationType.SYSTEM_STATUS,
            title="System Status",
            message="All systems operational",
            chat_id=0
        )
        
        with patch.object(bot, 'send_notification', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True
            
            stats = await bot.broadcast_notification(notification, subscribers)
            
            # 只有订阅了 SYSTEM_STATUS 的用户会收到
            assert stats["sent"] == 1
            assert stats["failed"] == 0
    
    @pytest.mark.asyncio
    async def test_test_connection(self, bot):
        """测试连接测试（Mock 测试）"""
        mock_bot_info = BotInfo(
            id=123456,
            is_bot=True,
            first_name="TestBot",
            username="test_bot"
        )
        
        with patch.object(bot, 'get_me', new_callable=AsyncMock) as mock_get_me:
            mock_get_me.return_value = mock_bot_info
            
            success = await bot.test_connection()
            
            assert success is True
    
    @pytest.mark.asyncio
    async def test_request_without_token(self):
        """测试无 Token 时的请求"""
        bot = TelegramBot(token=None)
        
        result = await bot._request("GET", "getMe")
        
        assert result is None
    
    def test_register_command(self, bot):
        """测试注册命令处理器"""
        async def handler(message):
            pass
        
        bot.register_command("start", handler)
        
        assert "start" in bot._command_handlers
        assert bot._command_handlers["start"] == handler


class TestTelegramBotManager:
    """测试 Telegram Bot 管理器"""
    
    @pytest.fixture
    def manager(self):
        """创建测试管理器"""
        bot = TelegramBot(token="test_token")
        return TelegramBotManager(bot)
    
    @pytest.mark.asyncio
    async def test_initialize(self, manager):
        """测试初始化"""
        mock_bot_info = BotInfo(
            id=123456,
            is_bot=True,
            first_name="TestBot",
            username="test_bot"
        )
        
        with patch.object(manager.bot, 'get_me', new_callable=AsyncMock) as mock_get_me:
            mock_get_me.return_value = mock_bot_info
            
            await manager.initialize()
            
            # 检查默认命令是否注册
            assert "start" in manager.bot._command_handlers
            assert "help" in manager.bot._command_handlers
            assert "status" in manager.bot._command_handlers
    
    @pytest.mark.asyncio
    async def test_handle_start_command(self, manager):
        """测试处理 /start 命令"""
        chat = Chat(id=123456, type="private")
        user = User(id=789012, first_name="John", is_bot=False)
        message = Message(
            message_id=1,
            chat=chat,
            from_user=user,
            date=datetime.now(),
            text="/start"
        )
        
        with patch.object(manager.bot, 'send_message', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = message
            
            await manager._handle_start(message)
            
            mock_send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_help_command(self, manager):
        """测试处理 /help 命令"""
        chat = Chat(id=123456, type="private")
        message = Message(
            message_id=1,
            chat=chat,
            date=datetime.now(),
            text="/help"
        )
        
        with patch.object(manager.bot, 'send_message', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = message
            
            await manager._handle_help(message)
            
            mock_send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_status_command(self, manager):
        """测试处理 /status 命令"""
        chat = Chat(id=123456, type="private")
        message = Message(
            message_id=1,
            chat=chat,
            date=datetime.now(),
            text="/status"
        )
        
        with patch.object(manager.bot, 'send_message', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = message
            
            await manager._handle_status(message)
            
            mock_send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_subscribe_command(self, manager):
        """测试处理 /subscribe 命令"""
        chat = Chat(id=123456, type="private")
        user = User(id=789012, first_name="John", is_bot=False, username="johndoe")
        message = Message(
            message_id=1,
            chat=chat,
            from_user=user,
            date=datetime.now(),
            text="/subscribe"
        )
        
        with patch.object(manager.bot, 'send_message', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = message
            
            await manager._handle_subscribe(message)
            
            assert len(manager._subscribers) == 1
            assert manager._subscribers[0].user_id == 789012
            mock_send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_unsubscribe_command(self, manager):
        """测试处理 /unsubscribe 命令"""
        # 先添加订阅者
        manager._subscribers.append(
            Subscriber(
                user_id=789012,
                chat_id=123456,
                first_name="John",
                username="johndoe"
            )
        )
        
        chat = Chat(id=123456, type="private")
        user = User(id=789012, first_name="John", is_bot=False)
        message = Message(
            message_id=1,
            chat=chat,
            from_user=user,
            date=datetime.now(),
            text="/unsubscribe"
        )
        
        with patch.object(manager.bot, 'send_message', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = message
            
            await manager._handle_unsubscribe(message)
            
            assert len(manager._subscribers) == 0
            mock_send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_notify_task_created(self, manager):
        """测试通知任务创建"""
        with patch.object(manager, 'send_system_notification', new_callable=AsyncMock) as mock_notify:
            mock_notify.return_value = None
            
            await manager.notify_task_created(
                task_id="task_123",
                task_type="fiverr_order",
                description="New order received"
            )
            
            mock_notify.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_notify_error(self, manager):
        """测试通知错误"""
        with patch.object(manager, 'send_system_notification', new_callable=AsyncMock) as mock_notify:
            mock_notify.return_value = None
            
            await manager.notify_error(
                error="Database connection failed",
                level="CRITICAL"
            )
            
            mock_notify.assert_called_once()


class TestTelegramIntegration:
    """Telegram 集成测试"""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """测试完整工作流程（Mock 测试）"""
        # 1. 创建 Bot
        bot = TelegramBot(token="test_token")
        
        # 2. Mock 获取机器人信息
        mock_bot_info = BotInfo(
            id=123456,
            is_bot=True,
            first_name="TestBot",
            username="test_bot"
        )
        
        with patch.object(bot, 'get_me', new_callable=AsyncMock) as mock_get_me:
            mock_get_me.return_value = mock_bot_info
            
            bot_info = await bot.get_me()
            assert bot_info is not None
            assert bot_info.username == "test_bot"
        
        # 3. 注册命令
        async def test_handler(message):
            pass
        
        bot.register_command("test", test_handler)
        assert "test" in bot._command_handlers
        
        # 4. Mock 发送消息
        mock_response = {
            "message_id": 1,
            "from": {"id": 123456, "is_bot": True, "first_name": "TestBot"},
            "chat": {"id": 789012, "type": "private"},
            "date": int(datetime.now().timestamp()),
            "text": "Test message"
        }
        
        with patch.object(bot, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            message = await bot.send_message(
                chat_id=789012,
                text="Test message"
            )
            
            assert message is not None
            assert message.text == "Test message"
        
        # 5. 测试连接
        with patch.object(bot, 'get_me', new_callable=AsyncMock) as mock_get_me:
            mock_get_me.return_value = mock_bot_info
            
            success = await bot.test_connection()
            assert success is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
