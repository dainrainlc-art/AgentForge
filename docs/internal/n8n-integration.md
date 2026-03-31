# N8N工作流集成详细方案

## 概述

N8N作为AgentForge项目的核心工作流引擎，负责处理规则明确、可自动化的重复性任务，与GLM-5形成协同：GLM-5处理智能推理，N8N处理流程执行。

## N8N核心定位

### 角色定义
- **跨平台工作流编排引擎**：连接AgentForge与各类外部服务
- **自动化任务执行器**：处理可预测的流程性任务
- **事件驱动处理器**：响应外部事件并触发相应流程

### 与GLM-5的分工
| 维度 | GLM-5 | N8N |
|------|-------|-----|
| 核心能力 | 智能推理、内容生成 | 流程执行、系统集成 |
| 任务类型 | 需要判断的复杂任务 | 规则明确的重复任务 |
| 响应方式 | 生成内容/建议 | 执行操作/调用API |
| 决策权 | 内容质量、策略建议 | 执行时机、流程控制 |

## 核心工作流设计

### 工作流一：Fiverr订单自动化

```
触发器: Fiverr Webhook / 定时轮询
    │
    ▼
[1] 事件分类节点
    │
    ├── 新订单 ──────────────────────────────────┐
    │   │                                         │
    │   ▼                                         │
    │   [订单信息提取]                             │
    │       │                                     │
    │       ├── 客户名称                          │
    │       ├── 需求描述                          │
    │       ├── 预算金额                          │
    │       └── 工期要求                          │
    │       │                                     │
    │       ▼                                     │
    │   [调用GLM-5生成报价建议]                    │
    │       │                                     │
    │       ▼                                     │
    │   [创建Notion任务]                          │
    │       │                                     │
    │       ▼                                     │
    │   [发送桌面通知]                            │
    │                                             │
    ├── 新消息 ──────────────────────────────────┤
    │   │                                         │
    │   ▼                                         │
    │   [消息内容提取]                             │
    │       │                                     │
    │       ▼                                     │
    │   [调用GLM-5生成回复建议]                    │
    │       │                                     │
    │       ▼                                     │
    │   [推送审核队列]                            │
    │                                             │
    ├── 订单完成 ────────────────────────────────┤
    │   │                                         │
    │   ▼                                         │
    │   [调用GLM-5生成交付文档]                    │
    │       │                                     │
    │       ▼                                     │
    │   [打包交付物]                              │
    │       │                                     │
    │       ▼                                     │
    │   [更新订单状态]                            │
    │                                             │
    └── 订单取消 ────────────────────────────────┘
        │
        ▼
    [更新知识库]
        │
        ▼
    [记录操作日志]
```

### 工作流二：社交媒体内容发布

```
触发器: 定时调度 (每日9:00 UTC) / 手动触发
    │
    ▼
[1] 内容规划检查
    │
    └── 查看发布日历，检查今日待发布内容
    │
    ▼
[2] 调用GLM-5生成内容
    │
    ├── 根据主题生成文案
    ├── 平台格式适配
    └── 多语言版本
    │
    ▼
[3] 生成配图建议
    │
    └── 调用GLM-5生成图像描述
    │
    ▼
[4] 创建审核任务
    │
    └── 推送至审核队列
    │
    ▼
[5] 等待人工审核
    │
    ├── 通过 ──► 执行发布
    ├── 修改 ──► 重新生成 ──► 再次审核
    └── 驳回 ──► 记录原因 ──► 流程结束
    │
    ▼
[6] 多平台发布
    │
    ├── YouTube ──► 上传视频/发布Shorts
    ├── Twitter ──► 发布推文/线程
    ├── Facebook ──► 发布帖子
    ├── Instagram ──► 发布图片/Reels
    └── LinkedIn ──► 发布文章
    │
    ▼
[7] 记录发布结果
    │
    ├── 更新发布日志
    ├── 收集互动数据
    └── 更新内容数据库
```

### 工作流三：知识库双向同步

```
触发器: Obsidian文件变更 / 定时同步 (每6小时)
    │
    ▼
[1] 变更检测
    │
    └── 扫描Obsidian vault的文件变更
    │
    ▼
[2] 变更分类
    │
    ├── 新文件 ──► 转换为Notion页面
    ├── 修改文件 ──► 检测冲突 → 同步更新
    └── 删除文件 ──► 软删除Notion对应页面
    │
    ▼
[3] 格式转换
    │
    ├── Markdown → Notion blocks
    ├── 处理嵌入图片
    ├── 处理代码块
    └── 处理表格
    │
    ▼
[4] 同步执行
    │
    └── 调用Notion API执行同步
    │
    ▼
[5] 冲突处理 (如需要)
    │
    └── 如检测到冲突，通知用户手动解决
    │
    ▼
[6] 同步日志记录
    │
    ├── 同步时间
    ├── 变更文件
    └── 成功/失败状态
```

## N8N节点配置

### HTTP Request节点 (调用GLM-5)

```json
{
  "node": "HTTP Request",
  "parameters": {
    "method": "POST",
    "url": "https://qianfan.baidubce.com/v2/coding/chat/completions",
    "authentication": "predefinedCredentialType",
    "nodeCredentialType": "httpHeaderAuth",
    "headers": {
      "Content-Type": "application/json",
      "Authorization": "Bearer {{$credentials.qianfanApiKey}}"
    },
    "body": {
      "model": "glm-5",
      "messages": [
        {
          "role": "system",
          "content": "你是一个专业的Fiverr运营助手..."
        },
        {
          "role": "user",
          "content": "{{$json.userMessage}}"
        }
      ],
      "temperature": 0.5,
      "max_tokens": 4096
    }
  }
}
```

### Webhook节点 (接收外部事件)

```json
{
  "node": "Webhook",
  "parameters": {
    "httpMethod": "POST",
    "path": "fiverr-webhook",
    "responseMode": "onReceived",
    "responseData": "allEntries"
  }
}
```

### Schedule节点 (定时任务)

```json
{
  "node": "Schedule Trigger",
  "parameters": {
    "rule": {
      "interval": [
        {
          "field": "hours",
          "hoursInterval": 6
        }
      ]
    }
  }
}
```

## N8N与AgentForge Core的接口

### 技能调用接口

```python
class N8NSkillInterface:
    """N8N工作流调用接口"""
    
    async def trigger_workflow(
        self, 
        workflow_id: str, 
        data: dict
    ) -> dict:
        """触发N8N工作流"""
        pass
    
    async def get_workflow_status(
        self, 
        execution_id: str
    ) -> dict:
        """获取工作流执行状态"""
        pass
    
    async def call_glm5(
        self, 
        prompt: str, 
        context: dict
    ) -> str:
        """通过N8N调用GLM-5"""
        pass
```

### 事件回调接口

```python
class N8NCallbackHandler:
    """N8N回调处理器"""
    
    async def on_workflow_complete(
        self, 
        workflow_id: str, 
        result: dict
    ):
        """工作流完成回调"""
        pass
    
    async def on_workflow_error(
        self, 
        workflow_id: str, 
        error: str
    ):
        """工作流错误回调"""
        pass
    
    async def on_content_ready(
        self, 
        content: dict
    ):
        """内容准备就绪回调（需人工审核）"""
        pass
```

## 部署配置

### Docker Compose配置

```yaml
n8n:
  image: n8nio/n8n:latest
  container_name: agentforge-n8n
  ports:
    - "5678:5678"
  volumes:
    - ./workflows:/home/node/.n8n
    - ./data/n8n:/data
  environment:
    - N8N_BASIC_AUTH_ACTIVE=true
    - N8N_BASIC_AUTH_USER=${N8N_BASIC_AUTH_USER:-admin}
    - N8N_BASIC_AUTH_PASSWORD=${N8N_BASIC_AUTH_PASSWORD}
    - WEBHOOK_URL=${N8N_WEBHOOK_URL:-http://localhost:5678/webhook/}
    - EXECUTIONS_MODE=regular
    - GENERIC_TIMEZONE=${TZ:-Asia/Shanghai}
  restart: unless-stopped
  networks:
    - agentforge-network
```

### 环境变量

```bash
# N8N配置
N8N_PORT=5678
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=your_secure_password
N8N_WEBHOOK_URL=http://localhost:5678/webhook/

# GLM-5 API配置 (供N8N调用)
QIANFAN_API_KEY=your_qianfan_api_key
GLM5_MODEL=glm-5
GLM5_TEMPERATURE=0.5
GLM5_MAX_TOKENS=4096
```

## 监控与日志

### 工作流执行监控

- 执行次数统计
- 成功/失败率
- 平均执行时间
- 错误类型分布

### 日志记录

- 工作流触发时间
- 输入参数
- 执行步骤
- 输出结果
- 错误信息

## 安全考虑

### 访问控制
- N8N Basic Auth认证
- Webhook签名验证
- API Key加密存储

### 数据安全
- 敏感数据不记录日志
- HTTPS传输
- 本地部署确保数据主权
