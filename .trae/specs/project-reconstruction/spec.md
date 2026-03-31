# AgentForge 项目系统性重建 Spec

## Why

当前 AgentForge 项目的实际开发状态与《AgentForge 个人助理系统架构规划方案》文档存在严重偏离，核心问题包括：

1. **核心框架偏离**：规划使用 OpenAkita 自进化AI助手框架，实际为自研核心，失去了自进化能力和生态系统支持
2. **架构层级缺失**：规划的六层架构未完整实现，缺少事件驱动模式和自进化机制
3. **关键集成缺失**：n8n工作流引擎、Obsidian/Notion知识库、Fiverr/LinkedIn/社交媒体API等均未实现
4. **部署方式偏离**：规划 Docker 容器化部署，实际为直接运行

这些问题已无法通过局部调整解决，需要执行系统性重建工作。

## What Changes

### **BREAKING** 项目环境重置
- 删除原有项目文件（保留架构规划文档和必要的配置文件）
- 重新构建符合规划的项目结构

### **BREAKING** 多Agent团队配置
- 配置企业级多Agent开发团队，包括：
  - 架构师（负责系统架构设计与技术选型）
  - 资深软件工程师（负责核心功能开发）
  - 测试工程师（负责测试策略与自动化测试）
  - 安全工程师（负责安全架构与漏洞防护）
  - 验收工程师（负责需求验证与用户体验评估）
  - DevOps工程师（负责CI/CD流程与部署自动化）
  - 产品经理（负责需求分析与产品路线规划）
  - UI/UX设计师（负责用户界面与交互体验设计）
  - 数据工程师（负责数据架构设计与数据处理流程）

### Trae系统配置优化
- 更新项目规则和技巧配置
- 创建项目文档集
- 配置所需MCP servers
- 完成开发环境配置

### 项目启动与知识传递
- 将架构规划文档分发给所有Agent
- 制定详细的项目落地方案拆分清单

### 项目管理与持续性保障
- 建立项目知识库
- 实施阶段性总结机制
- 配置开发状态自动记录功能

## Impact

### Affected specs
- 所有现有 spec 文件将被归档
- 新建完整的系统重建 spec

### Affected code
- 所有现有源代码将被删除
- 重新构建符合规划的项目结构

## ADDED Requirements

### Requirement: 项目评估与重建规划
系统 SHALL 提供完整的项目评估与重建规划能力。

#### Scenario: 项目评估完成
- **WHEN** 执行项目评估
- **THEN** 生成详细的偏离程度分析报告
- **AND** 确认是否需要系统性重建

#### Scenario: 重建计划制定
- **WHEN** 确认需要重建
- **THEN** 制定完整的重建计划
- **AND** 包含数据迁移策略、功能优先级、进度安排、质量保障措施

### Requirement: 项目环境重置
系统 SHALL 支持项目环境的完整重置与重建。

#### Scenario: 环境清理
- **WHEN** 执行环境重置
- **THEN** 删除原有项目文件
- **AND** 保留必要的配置和文档

#### Scenario: 多Agent团队配置
- **WHEN** 配置多Agent团队
- **THEN** 创建所有必需的Agent配置文件
- **AND** 为各Agent配置匹配其职责的专业大模型

### Requirement: Trae系统配置优化
系统 SHALL 支持Trae系统配置的完整优化。

#### Scenario: 规则和技巧更新
- **WHEN** 更新Trae配置
- **THEN** 创建针对AgentForge项目的专项规则
- **AND** 配置项目所需的技能要求

#### Scenario: MCP Servers配置
- **WHEN** 配置MCP servers
- **THEN** 配置所有项目所需的免费MCP servers
- **AND** 确保开发环境资源充足

### Requirement: 项目启动与知识传递
系统 SHALL 支持项目启动和知识传递流程。

#### Scenario: 文档分发
- **WHEN** 启动项目
- **THEN** 将架构规划文档分发给所有Agent
- **AND** 确认所有Agent已完成文档阅读

#### Scenario: 落地方案制定
- **WHEN** 知识传递完成
- **THEN** 制定详细的项目落地方案拆分清单
- **AND** 存储于项目文档集作为长期记忆

### Requirement: 项目管理与持续性保障
系统 SHALL 提供项目管理和持续性保障机制。

#### Scenario: 知识库建立
- **WHEN** 项目启动
- **THEN** 建立项目知识库
- **AND** 定期更新开发文档与决策记录

#### Scenario: 阶段性总结
- **WHEN** 完成阶段性任务
- **THEN** 执行阶段性总结
- **AND** 确保关键信息得到持续强化

## MODIFIED Requirements

### Requirement: 项目结构
原有项目结构 SHALL 被完全重建，符合《AgentForge 个人助理系统架构规划方案》的六层架构设计。

## REMOVED Requirements

### Requirement: 自研核心框架
**Reason**: 规划要求使用 OpenAkita 框架，自研核心不符合规划要求
**Migration**: 需要重新基于 OpenAkita 框架构建系统核心

### Requirement: 简化的三层架构
**Reason**: 规划要求六层架构，当前简化架构不符合规划
**Migration**: 需要按照六层架构重新设计系统结构
