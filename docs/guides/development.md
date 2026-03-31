# AgentForge 开发指南

## 1. 开发环境搭建

### 1.1 系统要求

| 项目 | 最低要求 | 推荐配置 |
|------|----------|----------|
| 操作系统 | Windows 10/11, macOS 10.15+, Ubuntu 20.04+ | Windows 11, macOS 13+, Ubuntu 22.04+ |
| Python | 3.12+ | 3.12.x |
| Docker | 24.0+ | 最新稳定版 |
| 内存 | 8GB | 16GB+ |
| 存储 | 50GB可用空间 | 100GB+ SSD |

### 1.2 安装步骤

#### 1.2.1 克隆项目

```bash
git clone https://github.com/your-username/AgentForge.git
cd AgentForge
```

#### 1.2.2 安装Docker

**Windows/macOS**:
```bash
# 下载并安装 Docker Desktop
# https://www.docker.com/products/docker-desktop
```

**Linux (Ubuntu)**:
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

#### 1.2.3 创建Python虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
.\venv\Scripts\activate   # Windows
```

#### 1.2.4 安装依赖

```bash
pip install -r requirements.txt
```

#### 1.2.5 配置环境变量

复制环境变量模板并编辑：

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置必要的环境变量：

```env
# 百度千帆API配置
QIANFAN_API_KEY=your_api_key_here

# 数据库配置
POSTGRES_USER=agentforge
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=agentforge

# N8N配置
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=your_n8n_password

# 安全配置
SECRET_KEY=your_secret_key_here
ENCRYPTION_KEY=your_encryption_key_here

# 时区配置
TZ=Asia/Shanghai
```

### 1.3 启动服务

#### 1.3.1 启动基础服务

```bash
./start-services.sh
```

或手动启动：

```bash
docker-compose up -d postgres redis qdrant n8n
```

#### 1.3.2 启动AgentForge API

```bash
./run.sh
```

或手动启动：

```bash
source venv/bin/activate
python -m uvicorn src.agentforge.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 1.4 验证安装

访问以下地址验证服务状态：

| 服务 | 地址 | 说明 |
|------|------|------|
| AgentForge API | http://localhost:8000 | API服务 |
| API文档 (Swagger) | http://localhost:8000/docs | 交互式API文档 |
| N8N工作流 | http://localhost:5678 | 工作流编辑器 |
| Qdrant控制台 | http://localhost:6333/dashboard | 向量数据库管理 |

## 2. 代码规范

### 2.1 项目结构

```
AgentForge/
├── src/
│   └── agentforge/
│       ├── api/              # FastAPI后端接口
│       │   ├── routes/       # 路由模块
│       │   ├── auth.py       # 认证模块
│       │   └── main.py       # 应用入口
│       ├── core/             # AgentForge Core核心调度
│       ├── models/           # 数据模型
│       ├── integrations/     # 外部服务集成
│       │   ├── postgresql/   # PostgreSQL数据库
│       │   ├── redis/        # Redis缓存
│       │   ├── qdrant/       # Qdrant向量数据库
│       │   ├── qianfan/      # 百度千帆GLM-5
│       │   └── n8n/          # N8N工作流桥接
│       ├── utils/            # 工具函数
│       └── workflows/        # 工作流定义
├── frontend/                 # 前端代码
├── docker/                   # Docker配置
├── docs/                     # 项目文档
├── tests/                    # 测试代码
│   ├── unit/                 # 单元测试
│   ├── integration/          # 集成测试
│   └── e2e/                  # 端到端测试
├── .env                      # 环境配置
├── requirements.txt          # Python依赖
└── pytest.ini                # 测试配置
```

### 2.2 Python代码规范

#### 2.2.1 代码风格

遵循 PEP 8 规范，使用以下工具进行代码质量控制：

```bash
# 代码格式化
black src/

# 代码检查
ruff src/

# 类型检查
mypy src/
```

#### 2.2.2 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 模块 | 小写下划线 | `agent_core.py` |
| 类 | 大驼峰 | `AgentCore` |
| 函数/方法 | 小写下划线 | `process_order()` |
| 常量 | 大写下划线 | `MAX_RETRIES` |
| 私有属性 | 单下划线前缀 | `_internal_state` |

#### 2.2.3 文档字符串

使用 Google 风格的文档字符串：

```python
def process_order(order_id: str, priority: str = "normal") -> OrderResult:
    """处理订单请求.

    Args:
        order_id: 订单唯一标识符
        priority: 订单优先级，可选值为 "high", "normal", "low"

    Returns:
        OrderResult: 包含处理结果的对象

    Raises:
        OrderNotFoundError: 订单不存在时抛出
        ValidationError: 参数验证失败时抛出

    Example:
        >>> result = process_order("order_123", priority="high")
        >>> print(result.status)
        "completed"
    """
    pass
```

#### 2.2.4 类型注解

所有公共函数必须添加类型注解：

```python
from typing import Optional, List, Dict, Any

async def get_orders(
    status: Optional[str] = None,
    limit: int = 10,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """获取订单列表."""
    pass
```

### 2.3 前端代码规范

#### 2.3.1 技术栈

- React 18+
- TypeScript
- Tailwind CSS
- Vite

#### 2.3.2 组件规范

```tsx
import React from 'react';

interface ButtonProps {
  label: string;
  onClick: () => void;
  variant?: 'primary' | 'secondary';
  disabled?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  label,
  onClick,
  variant = 'primary',
  disabled = false,
}) => {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`btn btn-${variant}`}
    >
      {label}
    </button>
  );
};
```

### 2.4 配置管理

#### 2.4.1 环境变量

所有配置通过环境变量管理，禁止硬编码：

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    qianfan_api_key: str
    database_url: str
    redis_url: str
    
    class Config:
        env_file = ".env"

settings = Settings()
```

#### 2.4.2 敏感信息处理

- 禁止将敏感信息提交到代码仓库
- 使用 `.env.example` 提供配置模板
- 生产环境使用加密存储

## 3. 测试规范

### 3.1 测试结构

```
tests/
├── unit/                     # 单元测试
│   ├── test_config.py
│   ├── test_core.py
│   └── test_workflows.py
├── integration/              # 集成测试
│   └── test_api.py
├── e2e/                      # 端到端测试
│   └── test_flows.py
├── conftest.py               # pytest配置和fixtures
└── __init__.py
```

### 3.2 测试命名规范

| 测试类型 | 命名规范 | 示例 |
|----------|----------|------|
| 单元测试 | `test_<module>_<function>` | `test_order_process()` |
| 集成测试 | `test_<feature>_<scenario>` | `test_api_create_order()` |
| 端到端测试 | `test_<flow>_<expected_result>` | `test_order_flow_success()` |

### 3.3 编写测试

#### 3.3.1 单元测试示例

```python
import pytest
from agentforge.core.agentforge_core import AgentForgeCore

class TestAgentForgeCore:
    @pytest.fixture
    def core(self):
        return AgentForgeCore()
    
    def test_intent_recognition_order(self, core):
        """测试订单意图识别."""
        result = core.recognize_intent("帮我处理新订单")
        assert result["intent"] == "order_management"
        assert result["confidence"] > 0.8
    
    def test_intent_recognition_content(self, core):
        """测试内容创作意图识别."""
        result = core.recognize_intent("写一篇技术博客")
        assert result["intent"] == "content_creation"
```

#### 3.3.2 集成测试示例

```python
import pytest
from httpx import AsyncClient
from agentforge.api.main import app

@pytest.mark.asyncio
async def test_api_health_check():
    """测试API健康检查端点."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

### 3.4 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/unit/test_core.py

# 运行特定测试用例
pytest tests/unit/test_core.py::TestAgentForgeCore::test_intent_recognition_order

# 生成覆盖率报告
pytest --cov=src/agentforge --cov-report=html

# 详细输出
pytest -v --tb=short
```

### 3.5 测试覆盖率要求

| 模块类型 | 最低覆盖率 |
|----------|------------|
| 核心模块 | 80% |
| API路由 | 70% |
| 工具函数 | 90% |
| 集成模块 | 60% |

## 4. Git工作流

### 4.1 分支策略

```
main (生产分支)
  │
  ├── develop (开发分支)
  │     │
  │     ├── feature/order-management (功能分支)
  │     ├── feature/content-engine (功能分支)
  │     └── bugfix/api-error (修复分支)
  │
  └── release/v1.0.0 (发布分支)
```

### 4.2 分支命名规范

| 分支类型 | 命名规范 | 示例 |
|----------|----------|------|
| 功能分支 | `feature/<feature-name>` | `feature/order-management` |
| 修复分支 | `bugfix/<bug-name>` | `bugfix/api-timeout` |
| 发布分支 | `release/v<version>` | `release/v1.0.0` |
| 热修复分支 | `hotfix/<issue-name>` | `hotfix/security-patch` |

### 4.3 提交信息规范

使用 Conventional Commits 规范：

```
<type>(<scope>): <subject>

<body>

<footer>
```

#### 4.3.1 提交类型

| 类型 | 说明 | 示例 |
|------|------|------|
| feat | 新功能 | `feat(api): add order management endpoint` |
| fix | 修复bug | `fix(core): resolve memory leak issue` |
| docs | 文档更新 | `docs(readme): update installation guide` |
| style | 代码格式 | `style: format code with black` |
| refactor | 重构 | `refactor(core): optimize intent recognition` |
| test | 测试 | `test(api): add integration tests for orders` |
| chore | 构建/工具 | `chore: update dependencies` |

#### 4.3.2 提交示例

```
feat(api): add customer communication endpoint

- Add POST /api/v1/communication/reply endpoint
- Implement automatic reply generation
- Add message priority sorting

Closes #123
```

### 4.4 Pull Request流程

1. **创建功能分支**
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/new-feature
   ```

2. **开发和提交**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

3. **推送到远程**
   ```bash
   git push origin feature/new-feature
   ```

4. **创建Pull Request**
   - 在GitHub上创建PR
   - 填写PR模板
   - 关联相关Issue

5. **代码审查**
   - 至少需要1个审查者批准
   - 通过所有CI检查
   - 解决所有审查意见

6. **合并**
   - 使用Squash Merge合并到develop
   - 删除功能分支

### 4.5 代码审查清单

- [ ] 代码符合项目规范
- [ ] 添加了必要的测试
- [ ] 测试覆盖率达标
- [ ] 文档已更新
- [ ] 无安全漏洞
- [ ] 无性能问题
- [ ] 提交信息符合规范

## 5. 开发工具

### 5.1 推荐IDE配置

**VS Code扩展**：
- Python
- Pylance
- Black Formatter
- Ruff
- GitLens
- Docker

**settings.json**:
```json
{
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

### 5.2 调试配置

**launch.json**:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "src.agentforge.api.main:app",
        "--reload",
        "--port",
        "8000"
      ],
      "jinja": true,
      "justMyCode": false
    }
  ]
}
```

### 5.3 常用命令

```bash
# 启动开发服务
./run.sh

# 运行测试
pytest

# 代码格式化
black src/ && ruff src/ --fix

# 类型检查
mypy src/

# 查看日志
docker-compose logs -f agentforge-core

# 重建容器
docker-compose up -d --build
```

## 6. 相关文档

- [架构概览](../architecture/overview.md)
- [API文档模板](../api/template.md)
- [部署文档](../deployment/docker.md)
