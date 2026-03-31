# AgentForge 项目规则

## 1. 项目概述

AgentForge是一个AI驱动的Fiverr运营自动化智能助理系统，采用六层架构设计，实现松耦合、高内聚的系统结构。核心技术栈为GLM-5（核心AI模型）和N8N（工作流引擎）。

### 1.1 项目目标

- 自动化Fiverr订单管理和客户沟通
- 社交媒体内容生成与发布自动化
- 知识管理与文档同步
- 多Agent协同工作流

### 1.2 技术栈

| 层级 | 技术选型 |
|------|----------|
| 前端 | React + TypeScript + Tailwind CSS + Vite |
| 后端 | Python 3.12+ + FastAPI |
| AI模型 | GLM-5 (核心) + Kimi-K2.5 + DeepSeek + MiniMax |
| 工作流 | N8N |
| 数据库 | PostgreSQL + Redis + Qdrant |
| 部署 | Docker + Docker Compose |

---

## 2. 六层架构开发规范

### 2.1 架构层次

```
用户交互层 (User Interface Layer)
    ↓
集成接口层 (Integration Layer)
    ↓
业务逻辑层 (Business Logic Layer)
    ↓
AI能力层 (AI Capabilities Layer)
    ↓
数据存储层 (Data Storage Layer)
    ↓
基础设施层 (Infrastructure Layer)
```

### 2.2 层间依赖原则

1. **单向依赖**: 上层可依赖下层，下层不可依赖上层
2. **接口隔离**: 同层模块间通过接口通信，避免直接依赖
3. **标准化接口**: 跨层调用必须通过标准化接口

### 2.3 各层职责

| 层级 | 职责 | 禁止行为 |
|------|------|----------|
| 用户交互层 | UI展示、用户输入处理、通知推送 | 包含业务逻辑 |
| 集成接口层 | 外部API封装、认证授权、错误处理 | 包含业务逻辑 |
| 业务逻辑层 | 核心业务功能、业务规则、事务管理 | 直接访问外部API |
| AI能力层 | 模型调用、Prompt管理、记忆系统 | 处理业务逻辑 |
| 数据存储层 | 数据持久化、缓存、向量检索 | 包含业务逻辑 |
| 基础设施层 | 容器编排、存储、网络、监控 | 暴露给上层应用 |

---

## 3. 代码风格标准

### 3.1 Python代码规范 (PEP 8)

#### 命名规范

```python
# 模块名: 小写下划线
my_module.py

# 类名: 大驼峰
class MyClassName:
    pass

# 函数/方法名: 小写下划线
def my_function_name():
    pass

# 常量: 大写下划线
MY_CONSTANT = "value"

# 私有属性/方法: 单下划线前缀
_private_attribute = None
```

#### 类型注解

```python
from typing import Optional, List, Dict

def process_data(
    items: List[str],
    config: Dict[str, any],
    timeout: Optional[int] = None
) -> bool:
    return True
```

#### 文档字符串

```python
def calculate_total(items: List[Order]) -> float:
    """计算订单总金额.

    Args:
        items: 订单项列表

    Returns:
        订单总金额

    Raises:
        ValueError: 当订单项为空时
    """
    if not items:
        raise ValueError("订单项不能为空")
    return sum(item.price for item in items)
```

#### 导入顺序

```python
# 标准库
import os
import sys
from typing import List, Optional

# 第三方库
import fastapi
from fastapi import HTTPException
import pydantic

# 本地模块
from agentforge.core import config
from agentforge.utils import helpers
```

### 3.2 TypeScript代码规范 (ESLint)

#### 命名规范

```typescript
// 文件名: 小写下划线或小写中划线
my_component.tsx
my-component.tsx

// 接口/类型: 大驼峰
interface UserProfile {
  id: string;
  name: string;
}

// 组件: 大驼峰
const MyComponent: React.FC = () => {
  return <div></div>;
};

// 函数: 小驼峰
const handleClick = () => {};

// 常量: 大写下划线
const API_BASE_URL = "http://localhost:8000";
```

#### 组件结构

```typescript
import React from "react";

interface Props {
  title: string;
  onSubmit: (data: FormData) => void;
}

export const MyComponent: React.FC<Props> = ({ title, onSubmit }) => {
  const [state, setState] = React.useState<string>("");

  const handleSubmit = () => {
    onSubmit({ value: state });
  };

  return (
    <div className="container">
      <h1>{title}</h1>
      <button onClick={handleSubmit}>提交</button>
    </div>
  );
};
```

### 3.3 代码格式化工具

#### Python

```bash
# 使用Black格式化
black src/ tests/

# 使用Ruff检查
ruff check src/ tests/

# 使用MyPy类型检查
mypy src/
```

#### TypeScript

```bash
# 使用ESLint检查
npm run lint

# 使用TypeScript编译器检查
npm run build
```

---

## 4. Git提交规范 (Conventional Commits)

### 4.1 提交消息格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### 4.2 提交类型

| 类型 | 说明 | 示例 |
|------|------|------|
| feat | 新功能 | feat(auth): 添加JWT认证 |
| fix | Bug修复 | fix(api): 修复用户登录失败 |
| docs | 文档更新 | docs(readme): 更新安装说明 |
| style | 代码格式 | style: 格式化代码 |
| refactor | 重构 | refactor(core): 重构配置模块 |
| perf | 性能优化 | perf(db): 优化查询性能 |
| test | 测试 | test(auth): 添加认证测试 |
| chore | 构建/工具 | chore(deps): 更新依赖 |
| ci | CI配置 | ci: 添加GitHub Actions |

### 4.3 作用域 (Scope)

```
api       - API相关
auth      - 认证授权
core      - 核心模块
db        - 数据库
frontend  - 前端
workflow  - 工作流
config    - 配置
deps      - 依赖
```

### 4.4 提交示例

```bash
# 新功能
feat(fiverr): 添加订单自动报价功能

# Bug修复
fix(knowledge): 修复文档同步失败问题

# 重构
refactor(social-media): 重构内容发布引擎

# 破坏性变更
feat(api)!: 重构API响应格式

BREAKING CHANGE: API响应格式从v1改为v2
```

---

## 5. 分支管理策略 (Git Flow)

### 5.1 分支类型

| 分支 | 说明 | 命名规则 |
|------|------|----------|
| main | 主分支，生产环境代码 | main |
| develop | 开发分支 | develop |
| feature | 功能分支 | feature/功能名称 |
| release | 发布分支 | release/版本号 |
| hotfix | 热修复分支 | hotfix/问题描述 |
| bugfix | Bug修复分支 | bugfix/问题描述 |

### 5.2 分支工作流

```
main ──────────────────────────────────────●
                    \                     /
develop ─────────────●────●────●────●────●
                    /     \         /
feature/login ─────●───────●
                         \
feature/api ──────────────●────●
                              \
release/v1.0 ─────────────────●────●
                                   \
hotfix/urgent ─────────────────────●
```

### 5.3 分支操作规范

```bash
# 创建功能分支
git checkout develop
git checkout -b feature/new-feature

# 完成功能开发，合并回develop
git checkout develop
git merge --no-ff feature/new-feature
git branch -d feature/new-feature

# 创建发布分支
git checkout -b release/v1.0 develop

# 发布完成后合并到main和develop
git checkout main
git merge --no-ff release/v1.0
git tag -a v1.0 -m "Release v1.0"
git checkout develop
git merge --no-ff release/v1.0
git branch -d release/v1.0

# 创建热修复分支
git checkout -b hotfix/urgent-bug main

# 修复完成后合并到main和develop
git checkout main
git merge --no-ff hotfix/urgent-bug
git tag -a v1.0.1 -m "Hotfix v1.0.1"
git checkout develop
git merge --no-ff hotfix/urgent-bug
git branch -d hotfix/urgent-bug
```

---

## 6. 代码审查流程

### 6.1 Pull Request流程

1. **创建PR**: 功能分支 -> develop
2. **自动检查**: CI运行测试和代码检查
3. **代码审查**: 至少1名审查者批准
4. **合并**: Squash merge或常规merge

### 6.2 PR标题规范

```
<type>(<scope>): <description>

示例:
feat(fiverr): 添加订单自动监控功能
fix(knowledge): 修复文档同步失败问题
refactor(core): 重构配置管理模块
```

### 6.3 PR检查清单

#### 提交者检查

- [ ] 代码遵循项目代码规范
- [ ] 已添加必要的单元测试
- [ ] 所有测试通过
- [ ] 已更新相关文档
- [ ] 无安全漏洞
- [ ] 提交消息符合规范

#### 审查者检查

- [ ] 代码逻辑正确
- [ ] 代码可读性好
- [ ] 无重复代码
- [ ] 错误处理完善
- [ ] 性能可接受
- [ ] 安全性考虑周全

### 6.4 审查意见类型

| 标签 | 含义 |
|------|------|
| MUST | 必须修改 |
| SHOULD | 建议修改 |
| NIT | 小问题，可选修改 |
| QUESTION | 疑问，需要讨论 |
| PRAISE | 做得好 |

---

## 7. 测试覆盖率要求

### 7.1 覆盖率标准

| 指标 | 要求 |
|------|------|
| 总体覆盖率 | ≥ 70% |
| 核心模块覆盖率 | ≥ 80% |
| 新增代码覆盖率 | ≥ 80% |

### 7.2 测试类型

```
tests/
├── unit/           # 单元测试
│   ├── test_config.py
│   ├── test_core.py
│   └── test_workflows.py
├── integration/    # 集成测试
│   └── test_api.py
└── e2e/            # 端到端测试
    └── test_user_flow.py
```

### 7.3 测试命名规范

```python
# 单元测试
class TestOrderEngine:
    def test_calculate_total_with_valid_items(self):
        pass

    def test_calculate_total_with_empty_items_raises_error(self):
        pass

# 集成测试
class TestFiverrIntegration:
    async def test_create_order_success(self):
        pass
```

### 7.4 运行测试

```bash
# 运行所有测试
pytest

# 运行带覆盖率的测试
pytest --cov=src/agentforge --cov-report=html

# 运行特定测试
pytest tests/unit/test_core.py -v

# 运行标记的测试
pytest -m "not slow"
```

---

## 8. 文档编写规范

### 8.1 文档结构

```
docs/
├── architecture/       # 架构文档
│   ├── system-overview.md
│   ├── adr.md
│   └── api-specification.md
├── internal/           # 内部文档
│   └── n8n-integration.md
├── technical/          # 技术文档
│   └── README.md
└── opensource/         # 开源相关
    └── README.md
```

### 8.2 文档格式

#### Markdown规范

```markdown
# 一级标题 (文档标题)

## 二级标题 (章节)

### 三级标题 (小节)

#### 四级标题 (细节)

**粗体文本**
*斜体文本*
`代码`

- 无序列表项1
- 无序列表项2

1. 有序列表项1
2. 有序列表项2

| 表头1 | 表头2 |
|-------|-------|
| 内容1 | 内容2 |

[链接文本](URL)
![图片描述](图片URL)

> 引用文本

```语言
代码块
```
```

### 8.3 代码注释规范

#### Python

```python
def complex_function(data: dict) -> Result:
    """函数简短描述.

    详细描述（可选）。

    Args:
        data: 参数描述

    Returns:
        返回值描述

    Raises:
        ExceptionType: 异常描述

    Example:
        >>> result = complex_function({"key": "value"})
        >>> print(result.status)
        "success"
    """
    pass
```

#### TypeScript

```typescript
/**
 * 函数简短描述
 * 
 * @param data - 参数描述
 * @returns 返回值描述
 * @throws {Error} 异常描述
 * 
 * @example
 * const result = complexFunction({ key: "value" });
 * console.log(result.status); // "success"
 */
function complexFunction(data: Record<string, string>): Result {
  // 实现复杂逻辑
  // 步骤1: 数据验证
  // 步骤2: 处理数据
  // 步骤3: 返回结果
}
```

### 8.4 README模板

```markdown
# 模块名称

简短描述模块功能。

## 功能特性

- 特性1
- 特性2

## 快速开始

### 安装

```bash
pip install module-name
```

### 使用

```python
from module import main
main()
```

## API文档

### 函数名

描述函数功能。

## 配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| key | string | "" | 说明 |

## 许可证

MIT License
```

---

## 9. 开发命令速查

### 9.1 后端开发

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 运行开发服务器
uvicorn agentforge.api.main:app --reload

# 运行测试
pytest

# 代码格式化
black src/ tests/
ruff check src/ tests/

# 类型检查
mypy src/
```

### 9.2 前端开发

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 运行开发服务器
npm run dev

# 构建生产版本
npm run build

# 预览生产版本
npm run preview
```

### 9.3 Docker操作

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看服务日志
docker-compose logs -f

# 停止所有服务
docker-compose down

# 重建服务
docker-compose up -d --build
```

---

## 10. 安全规范

### 10.1 敏感信息处理

- 禁止在代码中硬编码密钥、密码
- 使用环境变量存储敏感配置
- `.env`文件必须添加到`.gitignore`
- 提供`.env.example`作为配置模板

### 10.2 API安全

- 所有API端点需要认证
- 使用JWT进行身份验证
- 实施速率限制
- 输入验证和清理

### 10.3 数据安全

- 敏感数据加密存储
- 数据库访问使用最小权限
- 定期备份数据
- 审计日志记录
