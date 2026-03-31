# AgentForge 第三阶段开发 - 产品需求文档

## Overview
- **Summary**: AgentForge 第三阶段开发计划，旨在完善系统的测试覆盖、API 接口、用户界面和部署优化，将系统从原型阶段推进到生产就绪状态。
- **Purpose**: 在已完成的核心基础架构和业务引擎基础上，添加测试体系、完善 API 接口、开发用户界面、优化部署流程，确保系统可以安全、稳定地投入生产使用。
- **Target Users**: Fiverr 自由职业者、内容创作者、知识工作者

## Goals
- 建立完整的测试体系（单元测试、集成测试、E2E 测试）
- 完善 API 接口，暴露所有业务引擎功能
- 开发 Web 前端界面，提供友好的用户交互体验
- 实现用户认证与授权系统
- 优化部署流程，支持生产环境部署
- 添加监控与日志系统

## Non-Goals (Out of Scope)
- 移动端应用开发（iOS/Android）
- 多租户支持
- 国际化多语言支持（除已有的 AI 翻译功能外）
- 高级数据分析与 BI 报表
- 插件系统开发

## Background & Context
- 第一阶段：核心基础架构已完成（数据库、AI 能力、API 框架）
- 第二阶段：业务引擎已完成（Fiverr、社交媒体、知识管理、客户沟通）
- 当前状态：系统具备核心功能，但缺乏测试、UI 和生产级部署能力
- 技术栈：FastAPI、SQLAlchemy 2.0、PostgreSQL、Redis、Qdrant、N8N、GLM-5

## Functional Requirements
- **FR-1**: 系统应提供完整的单元测试覆盖，覆盖所有核心模块
- **FR-2**: 系统应提供集成测试，验证各模块间的协作
- **FR-3**: 系统应提供 E2E 测试，验证完整的用户流程
- **FR-4**: API 应暴露所有业务引擎的功能端点
- **FR-5**: 系统应提供用户注册、登录功能
- **FR-6**: 系统应使用 JWT Token 进行认证
- **FR-7**: 系统应提供 Web 前端界面
- **FR-8**: 前端应支持对话交互、订单管理、内容创作等功能
- **FR-9**: 系统应提供健康检查和监控端点
- **FR-10**: 系统应支持 Docker Compose 一键部署

## Non-Functional Requirements
- **NFR-1**: 单元测试覆盖率应达到 70% 以上
- **NFR-2**: API 响应时间应在 200ms 以内（P95）
- **NFR-3**: 系统应支持至少 100 并发用户
- **NFR-4**: 所有敏感数据应加密存储
- **NFR-5**: 系统应提供完整的日志记录
- **NFR-6**: 前端首屏加载时间应在 3s 以内

## Constraints
- **Technical**: Python 3.12+、FastAPI、React/Vue、PostgreSQL、Docker
- **Business**: 开发周期 2-3 个月，预算有限（使用开源技术栈）
- **Dependencies**: 百度千帆 API 可用性、N8N 服务稳定性

## Assumptions
- 用户具备基本的计算机操作能力
- 用户已有 Fiverr 账户和社交媒体账户
- 用户愿意提供必要的 API 密钥和配置
- 部署环境为 Linux 服务器

## Acceptance Criteria

### AC-1: 测试体系建立
- **Given**: 项目代码库已存在
- **When**: 开发人员运行测试命令
- **Then**: 所有测试通过，覆盖率报告显示 ≥70% 覆盖率
- **Verification**: `programmatic`
- **Notes**: 使用 pytest 和 pytest-cov

### AC-2: API 接口完善
- **Given**: 业务引擎已实现
- **When**: 客户端调用 API 端点
- **Then**: 返回正确的响应数据，状态码符合预期
- **Verification**: `programmatic`

### AC-3: 用户认证功能
- **Given**: 用户访问系统
- **When**: 用户注册或登录
- **Then**: 系统返回有效的 JWT Token
- **Verification**: `programmatic`

### AC-4: Web 前端可用
- **Given**: 用户访问前端 URL
- **When**: 页面加载完成
- **Then**: 用户可以看到主要功能界面并进行操作
- **Verification**: `human-judgment`

### AC-5: 部署流程简化
- **Given**: 服务器已安装 Docker 和 Docker Compose
- **When**: 执行部署脚本
- **Then**: 所有服务正常启动，系统可访问
- **Verification**: `programmatic`

### AC-6: 监控与日志
- **Given**: 系统运行中
- **When**: 发生错误或异常
- **Then**: 日志被正确记录，监控指标可查询
- **Verification**: `programmatic`

## Open Questions
- [ ] 前端框架选择：React 还是 Vue？
- [ ] 是否需要支持 OAuth 第三方登录？
- [ ] 生产环境是否需要 Kubernetes 部署？
- [ ] 是否需要实时通知功能（WebSocket）？
