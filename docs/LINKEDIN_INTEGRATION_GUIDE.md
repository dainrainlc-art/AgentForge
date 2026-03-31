# AgentForge LinkedIn 集成使用指南

**创建日期**: 2026-03-29  
**版本**: 1.0.0  
**状态**: ✅ 已完成

---

## 📋 概述

AgentForge 现已集成 LinkedIn API，支持以下功能：

- ✅ 个人资料同步
- ✅ 人脉网络管理
- ✅ 动态发布与管理
- ✅ 数据分析
- ✅ 自动化发布

---

## 🔧 配置

### 1. 创建 LinkedIn 应用

1. 访问 [LinkedIn Developer Portal](https://www.linkedin.com/developers/)
2. 点击 "Create app"
3. 选择关联的 LinkedIn 公司主页
4. 填写应用信息：
   - **App Name**: AgentForge
   - **App Description**: AI 驱动的 Fiverr 运营自动化智能助理
   - **Privacy Policy URL**: 你的隐私政策 URL
   - **User Agreement URL**: 你的用户协议 URL
   - **Website URL**: https://your-domain.com
   - **Redirect URL**: http://localhost:8000/callback (开发环境)

5. 接受条款并创建应用

### 2. 获取凭证

创建应用后，在 "Auth" 标签页获取：
- **Client ID**
- **Client Secret**

### 3. 配置环境变量

编辑 `.env` 文件，添加：

```bash
# LinkedIn API 配置
LINKEDIN_CLIENT_ID=your_client_id_here
LINKEDIN_CLIENT_SECRET=your_client_secret_here
LINKEDIN_REDIRECT_URI=http://localhost:8000/callback
```

### 4. 权限申请

在 "Auth" 标签页申请以下权限：
- `r_liteprofile` - 基本个人资料
- `r_emailaddress` - 邮箱地址
- `w_member_social` - 发布动态
- `r_basicprofile` - 详细个人资料
- `r_1st_connections` - 一度人脉
- `r_organization_social` - 公司主页数据
- `w_organization_social` - 管理公司主页

---

## 🚀 快速开始

### 1. OAuth 2.0 授权流程

#### 步骤 1: 获取授权 URL

```bash
curl -X GET http://localhost:8000/api/linkedin/auth/url
```

响应：
```json
{
  "authorization_url": "https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id=xxx&redirect_uri=http://localhost:8000/callback&state=xyz&scope=r_liteprofile...",
  "state": "xyz123"
}
```

#### 步骤 2: 用户授权

在浏览器中打开 `authorization_url`，用户登录并授权应用。

#### 步骤 3: 获取授权码

授权后，LinkedIn 会重定向到：
```
http://localhost:8000/callback?code=AQXXX...&state=xyz123
```

#### 步骤 4: 换取访问令牌

```bash
curl -X POST http://localhost:8000/api/linkedin/auth/token \
  -H "Content-Type: application/json" \
  -d '{"code": "AQXXX...", "state": "xyz123"}'
```

响应：
```json
{
  "access_token": "AQXXX...",
  "expires_in": 3600,
  "token_type": "Bearer"
}
```

---

## 📖 API 使用示例

### 获取个人资料

```bash
curl -X GET http://localhost:8000/api/linkedin/profile
```

响应：
```json
{
  "profile": {
    "id": "xxx",
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "headline": "Software Engineer",
    "summary": "Experienced developer...",
    "location": "San Francisco, CA",
    "follower_count": 1000,
    "connection_count": 500
  },
  "success": true
}
```

### 获取人脉列表

```bash
curl -X GET "http://localhost:8000/api/linkedin/connections?start=0&count=10"
```

响应：
```json
{
  "connections": [
    {
      "id": "conn1",
      "full_name": "Jane Smith",
      "headline": "Product Manager",
      "location": "New York, NY",
      "connection_degree": "1st"
    }
  ],
  "total": 2,
  "start": 0,
  "count": 10
}
```

### 发布动态

```bash
curl -X POST http://localhost:8000/api/linkedin/post \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello LinkedIn! This is my first post from AgentForge.",
    "visibility": "public",
    "hashtags": ["hello", "linkedin", "agentforge"]
  }'
```

响应：
```json
{
  "id": "post123",
  "text": "Hello LinkedIn! This is my first post from AgentForge.",
  "visibility": "public",
  "created_at": "2026-03-29T10:00:00Z",
  "success": true
}
```

### 获取动态列表

```bash
curl -X GET "http://localhost:8000/api/linkedin/posts?start=0&count=10"
```

### 删除动态

```bash
curl -X DELETE http://localhost:8000/api/linkedin/post/post123
```

### 获取分析数据

```bash
curl -X GET "http://localhost:8000/api/linkedin/analytics?period=last_7_days"
```

响应：
```json
{
  "analytics": {
    "profile_views": 150,
    "post_impressions": 5000,
    "search_appearances": 200,
    "connection_requests": 25,
    "period": "last_7_days"
  },
  "success": true
}
```

### 自动发布动态

```bash
curl -X POST "http://localhost:8000/api/linkedin/auto-post?content=Auto-posted%20from%20AgentForge&hashtags=automation,ai"
```

### 获取人脉网络摘要

```bash
curl -X GET http://localhost:8000/api/linkedin/network/summary
```

响应：
```json
{
  "success": true,
  "summary": {
    "total_connections": 500,
    "top_industries": {
      "Technology": 150,
      "Finance": 80,
      "Marketing": 60
    },
    "recent_connections": [
      {
        "name": "Jane Smith",
        "headline": "Software Engineer at Tech Company",
        "location": "San Francisco"
      }
    ]
  }
}
```

### 测试连接

```bash
curl -X GET http://localhost:8000/api/linkedin/test
```

---

## 💻 Python SDK 使用

### 初始化客户端

```python
from integrations.external.linkedin_client import LinkedInClient, LinkedInManager

# 创建客户端
client = LinkedInClient(
    client_id="your_client_id",
    client_secret="your_client_secret",
    redirect_uri="http://localhost:8000/callback"
)

# 创建管理器
manager = LinkedInManager(client)
```

### 获取个人资料

```python
import asyncio

async def get_profile():
    profile = await client.get_profile()
    print(f"Name: {profile.full_name}")
    print(f"Heading: {profile.headline}")
    print(f"Followers: {profile.follower_count}")

asyncio.run(get_profile())
```

### 发布动态

```python
async def create_post():
    post = await client.create_post(
        text="Hello from AgentForge!",
        visibility="public",
        hashtags=["automation", "ai"]
    )
    print(f"Post created: {post.id}")

asyncio.run(create_post())
```

### 自动发布

```python
async def auto_post():
    success = await manager.auto_post(
        "Auto-posted content",
        hashtags=["automation"]
    )
    print(f"Post success: {success}")

asyncio.run(auto_post())
```

### 获取人脉网络摘要

```python
async def get_network_summary():
    summary = await manager.get_network_summary()
    print(f"Total connections: {summary['total_connections']}")
    print(f"Top industries: {summary['top_industries']}")

asyncio.run(get_network_summary())
```

---

## 🧪 测试

### 运行单元测试

```bash
# 运行所有 LinkedIn 测试
venv/bin/python -m pytest tests/integration/test_linkedin.py -v

# 运行特定测试
venv/bin/python -m pytest tests/integration/test_linkedin.py::TestLinkedInModels::test_profile_creation -v

# 运行带覆盖率的测试
venv/bin/python -m pytest tests/integration/test_linkedin.py --cov=integrations.external.linkedin_client --cov-report=html
```

### 测试结果

```
======================== 17 passed, 1 warning in 0.89s =========================
```

**测试覆盖率**:
- 数据模型测试：3/3 通过
- 客户端测试：10/10 通过
- 管理器测试：3/3 通过
- 集成测试：1/1 通过

---

## 📊 API 端点列表

| 端点 | 方法 | 说明 | 需要认证 |
|------|------|------|---------|
| `/api/linkedin/auth/url` | GET | 获取授权 URL | ❌ |
| `/api/linkedin/auth/token` | POST | 换取访问令牌 | ❌ |
| `/api/linkedin/profile` | GET | 获取个人资料 | ✅ |
| `/api/linkedin/connections` | GET | 获取人脉列表 | ✅ |
| `/api/linkedin/post` | POST | 创建动态 | ✅ |
| `/api/linkedin/posts` | GET | 获取动态列表 | ✅ |
| `/api/linkedin/post/{id}` | DELETE | 删除动态 | ✅ |
| `/api/linkedin/analytics` | GET | 获取分析数据 | ✅ |
| `/api/linkedin/test` | GET | 测试连接 | ✅ |
| `/api/linkedin/sync` | POST | 同步个人资料 | ✅ |
| `/api/linkedin/auto-post` | POST | 自动发布 | ✅ |
| `/api/linkedin/network/summary` | GET | 网络摘要 | ✅ |

---

## 🔒 安全最佳实践

### 1. 令牌管理

- 访问令牌有效期为 1 小时
- 实现令牌刷新机制
- 不要将令牌提交到版本控制
- 使用环境变量存储敏感信息

### 2. OAuth 2.0 安全

- 始终使用 `state` 参数防止 CSRF 攻击
- 使用 HTTPS（生产环境）
- 验证重定向 URI

### 3. 速率限制

LinkedIn API 有速率限制：
- 个人资料 API: 500 次/天
- 动态 API: 250 次/天
- 人脉 API: 250 次/天

实现重试机制：

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def call_linkedin_api():
    # API 调用
    pass
```

---

## ⚠️ 常见问题

### Q1: 获取授权时出现 "Permission Denied"

**原因**: 应用权限未审批

**解决**:
1. 在 LinkedIn Developer Portal 检查权限状态
2. 提交权限申请
3. 等待审批（通常 1-3 个工作日）

### Q2: API 返回 401 错误

**原因**: 令牌过期或无效

**解决**:
1. 检查令牌是否过期
2. 使用刷新令牌刷新访问令牌
3. 重新进行授权流程

### Q3: 动态发布失败

**原因**: 缺少 `w_member_social` 权限

**解决**:
1. 在 Developer Portal 申请权限
2. 等待审批
3. 重新授权

### Q4: 无法获取人脉列表

**原因**: 缺少 `r_1st_connections` 权限

**解决**:
1. 申请相应权限
2. 注意：只能获取一度人脉

---

## 📝 最佳实践

### 1. 自动化发布

使用定时任务自动发布内容：

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('cron', hour=9, minute=0)
async def scheduled_post():
    content = generate_content()
    await manager.auto_post(content, hashtags=["automation"])

scheduler.start()
```

### 2. 内容策略

- 发布时间：工作日 9:00-11:00
- 频率：每天 1-2 条
- 内容：技术分享、项目更新、行业洞察
- 标签：3-5 个相关标签

### 3. 人脉管理

定期同步人脉数据：

```python
async def sync_connections():
    connections = await client.get_connections()
    # 分析行业分布
    # 识别关键人脉
    # 更新 CRM 系统
```

### 4. 数据分析

每周生成分析报告：

```python
async def weekly_analytics():
    analytics = await client.get_analytics("last_7_days")
    report = generate_report(analytics)
    save_report(report)
```

---

## 🔗 相关资源

- [LinkedIn API 文档](https://docs.microsoft.com/en-us/linkedin/)
- [OAuth 2.0 规范](https://datatracker.ietf.org/doc/html/rfc6749)
- [LinkedIn Developer Portal](https://www.linkedin.com/developers/)
- [AgentForge 项目文档](docs/README.md)

---

## 📈 更新日志

### v1.0.0 (2026-03-29)

- ✅ 初始版本
- ✅ 个人资料管理
- ✅ 人脉管理
- ✅ 动态发布
- ✅ 数据分析
- ✅ 自动化发布
- ✅ 完整测试覆盖

---

**最后更新**: 2026-03-29  
**维护者**: AgentForge Team  
**状态**: ✅ 生产就绪
