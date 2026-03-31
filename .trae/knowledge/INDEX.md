# AgentForge 项目知识库索引

**创建日期**: 2026-03-28  
**维护者**: AgentForge 开发团队  
**版本**: V1.0

---

## 知识库概述

本知识库是 AgentForge 项目的核心知识管理中枢，旨在系统化地记录和管理项目开发过程中的关键知识、技术决策、架构演进和开发日志。

### 知识库目标

1. **知识沉淀**: 将项目开发过程中的隐性知识显性化，形成可复用的知识资产
2. **决策追溯**: 完整记录技术决策的背景、理由和影响，便于后续回顾和调整
3. **经验传承**: 为团队成员和未来维护者提供完整的项目上下文
4. **持续演进**: 支持项目知识的持续更新和迭代

### 知识库范围

| 类别 | 内容 | 存储位置 |
|------|------|----------|
| **核心知识** | 项目背景、架构设计、技术选型 | `core/` |
| **决策记录** | 架构决策记录 (ADR) | `decisions/` |
| **开发日志** | 开发过程记录、里程碑 | `logs/` |

---

## 知识分类索引

### 1. 核心知识 (Core Knowledge)

| 文档 | 描述 | 更新日期 |
|------|------|----------|
| [project_overview.md](./core/project_overview.md) | 项目概述、背景目标、技术架构 | 2026-03-28 |

### 2. 决策记录 (Architecture Decision Records)

| 编号 | 标题 | 状态 | 日期 |
|------|------|------|------|
| [ADR-001](./decisions/ADR-001-architecture-reconstruction.md) | 架构重建决策 | 已接受 | 2026-03-28 |

### 3. 开发日志 (Development Logs)

| 日期 | 标题 | 类型 |
|------|------|------|
| [2026-03-28](./logs/2026-03-28-reconstruction.md) | 项目重建启动 | 里程碑 |

---

## 知识库结构

```
.trae/knowledge/
├── INDEX.md                              # 知识库索引（本文件）
├── core/                                 # 核心知识目录
│   └── project_overview.md               # 项目概述
├── decisions/                            # 决策记录目录
│   └── ADR-001-architecture-reconstruction.md  # 架构重建决策
└── logs/                                 # 开发日志目录
    └── 2026-03-28-reconstruction.md      # 重建启动日志
```

---

## 文档更新记录

| 日期 | 版本 | 更新内容 | 更新人 |
|------|------|----------|--------|
| 2026-03-28 | V1.0 | 知识库初始化，创建基础结构 | AgentForge Team |

---

## 知识库使用指南

### 新成员入门

1. 首先阅读 [project_overview.md](./core/project_overview.md) 了解项目全貌
2. 浏览 `decisions/` 目录了解关键技术决策
3. 查看 `logs/` 目录了解项目演进历程

### 决策记录规范

- 使用 ADR (Architecture Decision Record) 格式
- 编号规则: ADR-NNN (三位数字递增)
- 状态: 提议 → 已接受 → 已废弃/已替代

### 开发日志规范

- 文件命名: `YYYY-MM-DD-topic.md`
- 记录关键节点、问题解决、经验教训
- 保持简洁、突出重点

---

## 相关资源

- [项目架构文档](../../docs/architecture/overview.md)
- [开发指南](../../docs/guides/development.md)
- [ADR 模板](../rules/adr_template.md)
- [项目规则](../rules/project_rules.md)

---

*本知识库遵循渐进式演进原则，将随项目发展持续更新和完善。*
