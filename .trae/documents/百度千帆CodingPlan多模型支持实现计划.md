# 百度千帆 Coding Plan Pro 套餐多模型支持实现计划

## 📋 项目概述

基于百度千帆 Coding Plan Pro 套餐，实现多模型支持和动态切换功能，并分析项目的多 Agent 架构支持情况。

## 🎯 目标

1. **配置百度千帆 API**：使用提供的 API KEY 和正确的 Base URL
2. **实现 Model Name 动态配置**：支持在配置文件中指定和切换模型
3. **支持多模型**：kimi-k2.5、deepseek-v3.2、glm-5、minimax-m2.5
4. **分析多 Agent 架构**：评估当前架构并提供改进方案

## 📚 百度千帆 Coding Plan Pro 套餐特性

### 套餐限制
- **价格**: ¥200/月
- **请求限额**: 
  - 每 5 小时：最多约 6,000 次请求
  - 每周：最多约 45,000 次请求
  - 每月：最多约 90,000 次请求
- **并发限制**: 建议使用不超过 2 个终端
- **联网搜索**: 每月最多约 2000 次

### 支持的模型
- kimi-k2.5
- deepseek-v3.2
- glm-5
- minimax-m2.5

### API 配置
- **Base URL**: `https://qianfan.baidubce.com/v2/coding`
- **API Key**: `bce-v3/ALTAKSP-9hcnf5Y5pK5e8rK2IzTXE/21b6ec2afc8223f33cfb8b6309f9d43a00eb0b28`

## 🔧 实现步骤

### 阶段 1: 更新配置和客户端

#### 1.1 更新 `.env` 文件
**文件**: `/home/dainrain4/trae_projects/AgentForge/.env`

**修改内容**:
```env
# 百度千帆配置
QIANFAN_API_KEY=bce-v3/ALTAKSP-9hcnf5Y5pK5e8rK2IzTXE/21b6ec2afc8223f33cfb8b6309f9d43a00eb0b28
QIANFAN_BASE_URL=https://qianfan.baidubce.com/v2/coding
QIANFAN_DEFAULT_MODEL=glm-5
```

#### 1.2 更新 `config.py`
**文件**: `/home/dainrain4/trae_projects/AgentForge/src/agentforge/config.py`

**添加字段**:
```python
QIANFAN_BASE_URL: str = "https://qianfan.baidubce.com/v2/coding"
QIANFAN_DEFAULT_MODEL: str = "glm-5"
```

#### 1.3 重构 `QianfanClient`
**文件**: `/home/dainrain4/trae_projects/AgentForge/src/agentforge/integrations/qianfan/client.py`

**关键修改**:
1. 从配置读取 Base URL
2. 支持动态 Model Name
3. 添加模型验证
4. 优化错误处理和重试机制

**代码示例**:
```python
class QianfanClient:
    def __init__(self):
        self.client = openai.AsyncOpenAI(
            api_key=settings.QIANFAN_API_KEY,
            base_url=settings.QIANFAN_BASE_URL
        )
        self.default_model = settings.QIANFAN_DEFAULT_MODEL
        self.supported_models = [
            "kimi-k2.5",
            "deepseek-v3.2", 
            "glm-5",
            "minimax-m2.5"
        ]
    
    async def generate(self, prompt: str, model: Optional[str] = None, ...):
        # 验证模型
        model_name = model or self.default_model
        if model_name not in self.supported_models:
            raise ValueError(f"不支持的模型：{model_name}")
        
        # 调用 API
        response = await self.client.chat.completions.create(
            model=model_name,
            messages=messages,
            ...
        )
```

### 阶段 2: 实现模型配置功能

#### 2.1 创建模型配置管理
**文件**: `/home/dainrain4/trae_projects/AgentForge/src/agentforge/integrations/qianfan/model_config.py` (新建)

**功能**:
- 模型元数据管理
- 模型性能参数配置
- 模型切换日志

#### 2.2 更新用户 API
**文件**: `/home/dainrain4/trae_projects/AgentForge/src/agentforge/api/routes/chat.py`

**新增接口**:
```python
@router.post("/chat")
async def chat(request: ChatRequest):
    # 支持在请求中指定模型
    model = request.model or settings.QIANFAN_DEFAULT_MODEL
    response = await qianfan_client.chat(
        messages=request.messages,
        model=model
    )
```

### 阶段 3: 前端模型选择器

#### 3.1 更新 Chat 页面
**文件**: `/home/dainrain4/trae_projects/AgentForge/frontend/src/pages/Chat.tsx`

**新增功能**:
- 模型选择下拉框
- 显示当前模型信息
- 模型切换按钮

### 阶段 4: 多 Agent 架构分析

#### 4.1 当前架构分析

**需要检查的文件**:
1. `/home/dainrain4/trae_projects/AgentForge/src/agentforge/api/main.py` - API 入口
2. `/home/dainrain4/trae_projects/AgentForge/src/agentforge/api/routes/chat.py` - 聊天路由
3. `/home/dainrain4/trae_projects/AgentForge/src/agentforge/workflows/` - 工作流引擎
4. 数据库设计 - 用户会话管理

**分析要点**:
- 当前是否使用会话隔离
- Agent 状态管理方式
- 数据库表结构设计
- API 请求处理流程

#### 4.2 多 Agent 实现方案（预估）

**方案 A: 基于用户的 Agent 隔离**（推荐）
- 每个用户拥有独立的 Agent 实例
- 通过用户 ID 隔离上下文
- 数据库存储用户专属配置

**实现难度**: ⭐⭐⭐ (中等)
**影响范围**: 
- 需要修改数据库 schema
- 更新会话管理逻辑
- 添加 Agent 配置管理

**方案 B: 基于会话的 Agent 隔离**
- 每个会话创建临时 Agent
- 会话结束后销毁
- 适合短期任务

**实现难度**: ⭐⭐ (较易)
**影响范围**:
- 会话管理优化
- 临时状态存储

**方案 C: 完全并行的多 Agent 系统**
- 独立的 Agent 服务实例
- 消息队列协调
- 负载均衡

**实现难度**: ⭐⭐⭐⭐⭐ (复杂)
**影响范围**:
- 架构重构
- 引入消息队列
- 分布式协调

#### 4.3 推荐方案

**采用方案 A + B 的混合模式**:
1. 用户级 Agent 配置（长期）
2. 会话级上下文隔离（短期）
3. 支持多个并发会话

**修改流程**:
```
1. 数据库扩展 (2-3 小时)
   - 添加 agent_configs 表
   - 添加 user_sessions 表
   
2. 后端修改 (4-6 小时)
   - 更新认证模块
   - 修改会话管理
   - 添加 Agent 工厂
   
3. 前端修改 (2-3 小时)
   - Agent 配置界面
   - 多会话管理
   
4. 测试验证 (2-3 小时)
```

**总预估时间**: 10-15 小时

**风险评估**:
- ✅ 不会破坏现有功能
- ✅ 渐进式重构
- ⚠️ 需要充分测试
- ⚠️ 数据库迁移需谨慎

## 📝 交付成果

1. ✅ 更新后的配置文件
2. ✅ 重构的 QianfanClient
3. ✅ 模型配置管理模块
4. ✅ 前端模型选择器
5. ✅ 多 Agent 架构分析报告
6. ✅ 实现方案文档

## ️ 注意事项

### 百度千帆套餐限制
1. **并发控制**: Pro 版本建议不超过 2 个终端
2. **速率限制**: 高峰期可能限流，需实现重试机制
3. **用量监控**: 添加用量统计和预警

### 安全考虑
1. API KEY 加密存储
2. 请求频率限制
3. 用户配额管理

### 性能优化
1. 连接池管理
2. 响应缓存
3. 异步并发处理

## 🚀 实施顺序

1. **阶段 1** (优先级：高) - 基础配置更新
2. **阶段 2** (优先级：高) - 模型配置功能
3. **阶段 3** (优先级：中) - 前端 UI 更新
4. **阶段 4** (优先级：低) - 多 Agent 架构（需讨论确认）

## 💬 待讨论问题

1. 多 Agent 的具体需求场景？
2. 是否需要支持用户自定义 Agent 配置？
3. 多 Agent 之间的协作机制？
4. 资源配额如何分配？
