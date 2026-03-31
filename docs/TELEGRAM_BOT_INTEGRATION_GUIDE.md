# AgentForge Telegram Bot 集成使用指南

**创建日期**: 2026-03-29  
**版本**: 1.0.0  
**状态**: ✅ 已完成

---

## 📋 概述

AgentForge 现已集成 Telegram Bot，支持以下功能：

- ✅ 系统通知推送
- ✅ 任务状态更新
- ✅ 错误警报
- ✅ 命令交互
- ✅ 订阅管理
- ✅ 广播消息

---

## 🔧 配置

### 1. 创建 Telegram Bot

1. 在 Telegram 中搜索 `@BotFather`
2. 发送 `/newbot` 命令
3. 按提示输入：
   - **Bot 名称**: AgentForge Assistant
   - **Bot 用户名**: agentforge_bot（必须以 bot 结尾）
4. 获取 Token（格式：`123456789:ABCdefGHIjklMNOpqrsTUVwxyz`）

### 2. 配置环境变量

编辑 `.env` 文件，添加：

```bash
# Telegram Bot 配置
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

### 3. 设置 Webhook（可选）

**使用 ngrok 本地开发**:

```bash
# 安装 ngrok
# 访问 https://ngrok.com/ 下载

# 启动 ngrok
ngrok http 8000
```

获取 ngrok URL（如：`https://abc123.ngrok.io`），然后设置 Webhook：

```bash
curl -X POST "http://localhost:8000/api/telegram/webhook/set?url=https://abc123.ngrok.io/api/telegram/webhook"
```

**生产环境**:

```bash
curl -X POST "https://your-domain.com/api/telegram/webhook/set?url=https://your-domain.com/api/telegram/webhook"
```

---

## 🚀 快速开始

### 1. 启动 Bot

Bot 会在 FastAPI 应用启动时自动初始化。

查看日志确认：
```
2026-03-29 11:00:00 - Connected to Telegram Bot: @agentforge_bot
2026-03-29 11:00:00 - Telegram Bot Manager initialized
```

### 2. 与 Bot 交互

在 Telegram 中搜索你的 Bot 用户名，发送 `/start` 开始对话。

**可用命令**:
- `/start` - 启动机器人
- `/help` - 查看帮助
- `/status` - 查看系统状态
- `/subscribe` - 订阅通知
- `/unsubscribe` - 取消订阅

---

## 📖 API 使用示例

### 获取机器人信息

```bash
curl -X GET http://localhost:8000/api/telegram/info
```

响应：
```json
{
  "success": true,
  "bot": {
    "id": 123456789,
    "is_bot": true,
    "first_name": "AgentForge Assistant",
    "username": "agentforge_bot",
    "can_join_groups": true,
    "can_read_all_group_messages": false,
    "supports_inline_queries": false
  }
}
```

### 发送文本消息

```bash
curl -X POST http://localhost:8000/api/telegram/send-message \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": 123456789,
    "text": "Hello from AgentForge!",
    "parse_mode": "HTML"
  }'
```

### 发送通知

```bash
curl -X POST http://localhost:8000/api/telegram/send-notification \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": 123456789,
    "notification_type": "system_status",
    "title": "系统状态",
    "message": "所有服务运行正常",
    "data": {
      "service": "AgentForge",
      "status": "运行中",
      "timestamp": "2026-03-29T11:00:00"
    }
  }'
```

### 订阅通知

```bash
curl -X POST "http://localhost:8000/api/telegram/subscribe?user_id=123456789&chat_id=123456789&first_name=John"
```

### 取消订阅

```bash
curl -X POST "http://localhost:8000/api/telegram/unsubscribe?user_id=123456789"
```

### 获取订阅者列表

```bash
curl -X GET http://localhost:8000/api/telegram/subscribers
```

响应：
```json
{
  "success": true,
  "subscribers": [
    {
      "user_id": 123456789,
      "chat_id": 123456789,
      "username": "johndoe",
      "first_name": "John",
      "subscribed_types": ["system_status", "task_created", "task_completed"],
      "enabled": true,
      "subscribed_at": "2026-03-29T11:00:00"
    }
  ],
  "total": 1
}
```

### 广播通知

```bash
curl -X POST http://localhost:8000/api/telegram/broadcast \
  -H "Content-Type: application/json" \
  -d '{
    "notification_type": "system_status",
    "title": "系统更新",
    "message": "系统将于今晚 23:00 进行维护",
    "data": {
      "maintenance_time": "23:00",
      "expected_duration": "30 分钟"
    }
  }'
```

响应：
```json
{
  "success": true,
  "stats": {
    "sent": 5,
    "failed": 0
  }
}
```

### 设置 Webhook

```bash
curl -X POST "http://localhost:8000/api/telegram/webhook/set?url=https://your-domain.com/api/telegram/webhook"
```

### 删除 Webhook

```bash
curl -X POST http://localhost:8000/api/telegram/webhook/delete
```

### 获取 Webhook 信息

```bash
curl -X GET http://localhost:8000/api/telegram/webhook/info
```

### 测试连接

```bash
curl -X GET http://localhost:8000/api/telegram/test
```

---

## 💻 Python SDK 使用

### 初始化 Bot

```python
from integrations.external.telegram_bot import TelegramBot, TelegramBotManager

# 创建 Bot
bot = TelegramBot(token="your_bot_token")

# 创建管理器
manager = TelegramBotManager(bot)
```

### 发送消息

```python
import asyncio

async def send_message():
    # 发送文本消息
    await bot.send_message(
        chat_id=123456789,
        text="Hello from AgentForge!",
        parse_mode="HTML"
    )
    
    # 发送照片
    await bot.send_photo(
        chat_id=123456789,
        photo="https://example.com/image.jpg",
        caption="Check this out!"
    )
    
    # 发送文档
    await bot.send_document(
        chat_id=123456789,
        document="https://example.com/report.pdf",
        caption="Monthly report"
    )

asyncio.run(send_message())
```

### 发送通知

```python
from integrations.external.telegram_models import Notification, NotificationType

async def send_notification():
    notification = Notification(
        id="notif_123",
        type=NotificationType.TASK_COMPLETED,
        title="任务完成",
        message="任务已成功完成",
        chat_id=123456789,
        data={
            "task_id": "task_456",
            "task_type": "fiverr_order",
            "result": "success"
        }
    )
    
    success = await bot.send_notification(notification)
    print(f"Notification sent: {success}")

asyncio.run(send_notification())
```

### 广播通知

```python
async def broadcast():
    notification = Notification(
        id="notif_broadcast",
        type=NotificationType.SYSTEM_STATUS,
        title="系统维护",
        message="系统将于今晚维护",
        chat_id=0,  # 广播
        data={
            "time": "23:00",
            "duration": "30 分钟"
        }
    )
    
    # 获取订阅者
    subscribers = manager._subscribers
    
    # 广播
    stats = await bot.broadcast_notification(notification, subscribers)
    print(f"Sent: {stats['sent']}, Failed: {stats['failed']}")

asyncio.run(broadcast())
```

### 订阅管理

```python
from integrations.external.telegram_models import Subscriber, NotificationType

async def manage_subscribers():
    # 添加订阅者
    subscriber = Subscriber(
        user_id=123456789,
        chat_id=123456789,
        username="johndoe",
        first_name="John",
        subscribed_types=[
            NotificationType.SYSTEM_STATUS,
            NotificationType.TASK_COMPLETED
        ]
    )
    
    manager._subscribers.append(subscriber)
    
    # 移除订阅者
    manager._subscribers = [
        s for s in manager._subscribers 
        if s.user_id != 123456789
    ]
    
    # 获取所有订阅者
    print(f"Total subscribers: {len(manager._subscribers)}")

asyncio.run(manage_subscribers())
```

### 通知系统集成

```python
async def notify_system_events():
    # 通知任务创建
    await manager.notify_task_created(
        task_id="task_123",
        task_type="fiverr_order",
        description="New order received"
    )
    
    # 通知任务完成
    await manager.notify_task_completed(
        task_id="task_123",
        task_type="fiverr_order",
        result="Order delivered successfully"
    )
    
    # 通知错误
    await manager.notify_error(
        error="Database connection failed",
        level="CRITICAL"
    )

asyncio.run(notify_system_events())
```

### 启动轮询

```python
async def start_bot():
    # 初始化
    await manager.initialize()
    
    # 启动轮询
    await bot.start_polling(interval=1)

# 运行
asyncio.run(start_bot())
```

---

## 🧪 测试

### 运行单元测试

```bash
# 运行所有 Telegram 测试
venv/bin/python -m pytest tests/integration/test_telegram.py -v

# 运行特定测试
venv/bin/python -m pytest tests/integration/test_telegram.py::TestTelegramBot::test_send_message -v

# 运行带覆盖率的测试
venv/bin/python -m pytest tests/integration/test_telegram.py --cov=integrations.external.telegram_bot --cov-report=html
```

### 测试结果

```
======================== 28 passed, 1 warning in 0.80s =========================

测试覆盖:
- 数据模型测试：5/5 通过 ✅
- Bot 客户端测试：14/14 通过 ✅
- Bot 管理器测试：7/7 通过 ✅
- 集成测试：1/1 通过 ✅
- 命令处理测试：5/5 通过 ✅
```

---

## 📊 API 端点列表

| 端点 | 方法 | 说明 | 需要认证 |
|------|------|------|---------|
| `/api/telegram/info` | GET | 获取机器人信息 | ❌ |
| `/api/telegram/webhook` | POST | Webhook 端点 | ❌ |
| `/api/telegram/send-message` | POST | 发送文本消息 | ✅ |
| `/api/telegram/send-notification` | POST | 发送通知 | ✅ |
| `/api/telegram/broadcast` | POST | 广播通知 | ✅ |
| `/api/telegram/subscribe` | POST | 订阅通知 | ✅ |
| `/api/telegram/unsubscribe` | POST | 取消订阅 | ✅ |
| `/api/telegram/subscribers` | GET | 获取订阅者 | ✅ |
| `/api/telegram/webhook/set` | POST | 设置 Webhook | ✅ |
| `/api/telegram/webhook/delete` | POST | 删除 Webhook | ✅ |
| `/api/telegram/webhook/info` | GET | 获取 Webhook 信息 | ✅ |
| `/api/telegram/test` | GET | 测试连接 | ❌ |

---

## 🔔 通知类型

| 类型 | 说明 | 模板 |
|------|------|------|
| `system_status` | 系统状态 | 🤖 系统状态 |
| `task_created` | 任务创建 | 📋 新任务创建 |
| `task_completed` | 任务完成 | ✅ 任务完成 |
| `task_failed` | 任务失败 | ❌ 任务失败 |
| `error_alert` | 错误警报 | ⚠️ 错误警报 |
| `self_evolution` | 自进化系统 | 🔄 自进化系统 |
| `custom` | 自定义通知 | - |

---

## 🔒 安全最佳实践

### 1. Token 管理

- 不要将 Token 提交到版本控制
- 使用环境变量存储 Token
- 定期更换 Token（通过 @BotFather）

### 2. Webhook 安全

- 生产环境必须使用 HTTPS
- 验证 Webhook 请求来源
- 实现 IP 白名单

### 3. 用户隐私

- 仅在用户订阅后发送通知
- 提供简单的取消订阅方式
- 不存储不必要的用户数据

### 4. 速率限制

Telegram API 有限制：
- 每秒最多 30 条消息
- 群组消息有额外限制

实现限流：

```python
import asyncio
from asyncio import Semaphore

class RateLimiter:
    def __init__(self, rate=30):
        self.semaphore = Semaphore(rate)
    
    async def send_message(self, chat_id, text):
        async with self.semaphore:
            return await bot.send_message(chat_id, text)
```

---

## ⚠️ 常见问题

### Q1: Bot 无法接收消息

**原因**: Webhook 未正确设置

**解决**:
1. 检查 Webhook URL 是否正确
2. 确保服务器可公开访问
3. 使用 `getWebhookInfo` 检查状态

### Q2: 消息发送失败

**原因**: Chat ID 无效或 Bot 被拉黑

**解决**:
1. 验证 Chat ID 是否正确
2. 确认用户未屏蔽 Bot
3. 检查 Bot 权限

### Q3: 无法订阅

**原因**: 用户数据不完整

**解决**:
1. 确保提供 user_id 和 chat_id
2. 检查 first_name 是否填写
3. 验证通知类型列表

### Q4: 广播失败

**原因**: 订阅者列表为空

**解决**:
1. 先让用户订阅通知
2. 检查订阅者 enabled 状态
3. 验证通知类型匹配

---

## 📝 最佳实践

### 1. 通知策略

- **系统状态**: 每小时一次
- **任务创建**: 实时
- **任务完成**: 实时
- **错误警报**: 立即（但避免轰炸）

### 2. 消息格式

```python
# 使用 HTML 格式
text = """
<b>任务完成</b>

任务 ID: task_123
类型：fiverr_order
结果：成功
"""

await bot.send_message(chat_id=123, text=text, parse_mode="HTML")
```

### 3. 错误处理

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
async def send_with_retry(chat_id, text):
    return await bot.send_message(chat_id, text)
```

### 4. 日志记录

```python
from loguru import logger

async def send_notification(notification):
    logger.info(f"Sending notification {notification.id} to chat {notification.chat_id}")
    success = await bot.send_notification(notification)
    if success:
        logger.info(f"Notification {notification.id} sent successfully")
    else:
        logger.error(f"Failed to send notification {notification.id}")
```

---

## 🔗 相关资源

- [Telegram Bot API 文档](https://core.telegram.org/bots/api)
- [Telegram Bot 父亲](https://t.me/BotFather)
- [Telegram Bot 示例](https://github.com/python-telegram-bot/python-telegram-bot)
- [AgentForge 项目文档](docs/README.md)

---

## 📈 更新日志

### v1.0.0 (2026-03-29)

- ✅ 初始版本
- ✅ 消息发送（文本、照片、文档）
- ✅ 命令处理
- ✅ 通知系统
- ✅ 订阅管理
- ✅ Webhook 支持
- ✅ 完整测试覆盖（28 个测试）

---

**最后更新**: 2026-03-29  
**维护者**: AgentForge Team  
**状态**: ✅ 生产就绪
