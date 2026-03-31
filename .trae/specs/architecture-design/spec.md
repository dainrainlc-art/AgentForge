# AgentForge 系统架构设计规范

## Why

开发准备工作已完成，项目需要进入架构设计阶段。AgentForge是一个复杂的AI驱动个人助理系统，涉及Fiverr运营自动化、社交媒体营销、知识管理、多Agent协作等多个子系统。需要设计清晰的系统架构，确保各模块职责明确、接口规范、可扩展性强。核心技术栈已确定为GLM-5作为核心AI模型，N8N作为工作流引擎。

## What Changes

- 设计AgentForge整体系统架构（六层架构）
- 定义核心模块及其职责边界
- 设计模块间的接口规范与通信协议
- 设计GLM-5与N8N的协同架构
- 设计数据流与存储架构
- 设计安全架构与访问控制
- 设计部署架构与运维方案

## Impact

- Affected specs: 项目整体架构、模块设计、接口规范
- Affected code: src/ 目录下的所有代码结构

## ADDED Requirements

### Requirement: 系统六层架构设计

系统SHALL采用六层架构设计，从底层到顶层依次为：

1. **基础设施层 (Infrastructure Layer)**
   - Docker容器化部署
   - 本地存储与网络配置
   - 资源监控与管理

2. **数据存储层 (Data Storage Layer)**
   - PostgreSQL: 结构化业务数据
   - Redis: 缓存与会话管理
   - Qdrant: 向量检索与语义搜索
   - Obsidian: 本地知识库
   - Notion: 云端协作空间

3. **AI能力层 (AI Capabilities Layer)**
   - GLM-5核心模型集成
   - 多模型路由与故障转移
   - Prompt管理与优化
   - 记忆系统与自进化机制

4. **业务逻辑层 (Business Logic Layer)**
   - Fiverr运营自动化引擎
   - 社交媒体营销引擎
   - 知识管理引擎
   - 客户沟通引擎
   - 项目管理引擎

5. **集成接口层 (Integration Layer)**
   - Fiverr API集成
   - 社交媒体API集成
   - GitHub API集成
   - Notion/Obsidian集成

6. **用户交互层 (User Interface Layer)**
   - 桌面客户端 (Tauri)
   - Web界面
   - CLI命令行
   - 通知推送系统

#### Scenario: 架构层次调用
- **WHEN** 用户发起业务请求
- **THEN** 请求从用户交互层向下传递，经过各层处理后返回结果

### Requirement: 核心模块设计

系统SHALL包含以下核心模块：

**AgentForge Core (核心调度模块)**
- 意图识别与任务路由
- 多Agent协调与调度
- 记忆管理与自进化
- 配置管理与监控

**GLM-5 Integration (AI能力模块)**
- API调用封装
- Prompt模板管理
- 响应解析与验证
- 配额监控与限流

**N8N Workflow Engine (工作流引擎)**
- 工作流定义与执行
- 事件监听与触发
- 定时任务调度
- 错误处理与重试

**Fiverr Automation (Fiverr自动化模块)**
- 订单监控与处理
- 客户消息管理
- 交付物打包
- 评价收集

**Social Media Manager (社交媒体管理模块)**
- 多平台内容发布
- 内容适配与格式化
- 互动监控
- 效果分析

**Knowledge Manager (知识管理模块)**
- Obsidian本地库管理
- Notion云端同步
- 文档检索与索引
- 版本控制

#### Scenario: 模块间通信
- **WHEN** 一个模块需要调用另一个模块
- **THEN** 通过标准化的接口进行通信，确保松耦合

### Requirement: GLM-5与N8N协同架构

系统SHALL实现GLM-5与N8N的紧密协同：

**协同模式一：内容生成与发布**
- GLM-5生成内容 → 人工审核 → N8N执行发布

**协同模式二：事件监控与响应**
- N8N监控事件 → GLM-5分析处理 → N8N执行响应

**协同模式三：定时任务与报告**
- N8N定时触发 → GLM-5生成报告 → N8N分发通知

#### Scenario: 内容发布流程
- **WHEN** 需要发布社交媒体内容
- **THEN** GLM-5生成内容，人工审核后，N8N执行多平台发布

### Requirement: 数据流设计

系统SHALL定义清晰的数据流：

**订单数据流**
```
Fiverr API → N8N Webhook → 订单处理器 → PostgreSQL → 通知推送
```

**内容数据流**
```
用户请求 → GLM-5生成 → 审核队列 → N8N发布 → 社交平台
```

**知识数据流**
```
Obsidian变更 → N8N同步 → Notion更新 → 版本记录
```

#### Scenario: 数据一致性保证
- **WHEN** 数据在多个存储间同步
- **THEN** 系统确保数据一致性，处理冲突

### Requirement: 接口规范设计

系统SHALL定义标准化的接口规范：

**内部API规范**
- RESTful风格
- JSON数据格式
- 版本控制 (v1)
- 统一错误处理
- 请求/响应日志

**Agent间通信协议**
- 消息队列模式
- 异步通信为主
- 超时与重试机制
- 状态追踪

**外部API集成规范**
- OAuth 2.0认证
- 速率限制处理
- 错误重试策略
- Webhook签名验证

#### Scenario: API调用
- **WHEN** 模块调用内部API
- **THEN** 遵循统一的接口规范，返回标准化响应

### Requirement: 安全架构设计

系统SHALL实现多层次安全防护：

**数据安全**
- 敏感数据加密存储 (AES-256)
- 传输加密 (TLS 1.3)
- 密钥管理 (环境变量)

**访问控制**
- API Key认证
- 最小权限原则
- 操作审计日志

**隐私保护**
- 数据分类分级
- 客户信息隔离
- GDPR合规考虑

#### Scenario: 敏感数据访问
- **WHEN** 访问敏感数据
- **THEN** 系统验证权限，记录审计日志

### Requirement: 部署架构设计

系统SHALL支持本地Docker部署：

**容器编排**
- AgentForge Core容器
- N8N容器
- PostgreSQL容器
- Redis容器
- Qdrant容器

**资源规划**
- CPU: 建议4核以上
- 内存: 建议8GB以上
- 存储: 建议50GB以上

**运维监控**
- 日志聚合
- 性能监控
- 告警通知
- 备份策略

#### Scenario: 服务启动
- **WHEN** 执行docker-compose up
- **THEN** 所有服务按依赖顺序启动，健康检查通过

## MODIFIED Requirements

无修改的需求。

## REMOVED Requirements

无移除的需求。
