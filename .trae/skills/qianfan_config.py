"""
百度千帆LLM配置
核心模型：GLM-5
工作流引擎：N8N
"""
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum


class ModelType(Enum):
    GLM_5 = "glm-5"
    KIMI_K25 = "kimi-k2.5"
    DEEPSEEK_V32 = "deepseek-v3.2"
    MINIMAX_M25 = "minimax-m2.5"


@dataclass
class ModelConfig:
    name: str
    context_window: int
    specialty: str
    max_tokens: int = 4096
    temperature: float = 0.7
    is_core: bool = False


CORE_MODEL_RATIONALE = """
GLM-5作为核心AI模型的技术选型理由：

1. 多语言处理能力
   - 优秀的英文/中文双语能力
   - 适合国际化Fiverr业务的客户沟通
   - 支持多语言内容创作和翻译

2. 内容创作能力
   - 社交媒体文案生成质量高
   - 营销内容创意性强
   - 符合不同平台的内容风格

3. 客户沟通场景
   - 专业且友好的沟通风格
   - 理解客户需求的准确度高
   - 回复内容自然流畅

4. 响应效率
   - 响应速度与质量平衡
   - 适合日常运营自动化场景
   - 配额消耗合理

5. 技术生态
   - 百度千帆Coding Plan Pro支持
   - API稳定可靠
   - 与N8N工作流集成便捷
"""


@dataclass
class QianfanConfig:
    api_key: str
    base_url_openai: str = "https://qianfan.baidubce.com/v2/coding"
    base_url_anthropic: str = "https://qianfan.baidubce.com/anthropic/coding"
    
    core_model: str = ModelType.GLM_5.value
    models: Dict[str, ModelConfig] = None
    rate_limits: Dict[str, int] = None
    
    def __post_init__(self):
        if self.models is None:
            self.models = {
                ModelType.GLM_5.value: ModelConfig(
                    name="glm-5",
                    context_window=64000,
                    specialty="多语言处理、内容创作、客户沟通",
                    max_tokens=4096,
                    temperature=0.5,
                    is_core=True,
                ),
                ModelType.KIMI_K25.value: ModelConfig(
                    name="kimi-k2.5",
                    context_window=128000,
                    specialty="长上下文理解、多轮对话、复杂推理",
                    max_tokens=8192,
                    temperature=0.3,
                    is_core=False,
                ),
                ModelType.DEEPSEEK_V32.value: ModelConfig(
                    name="deepseek-v3.2",
                    context_window=64000,
                    specialty="代码生成、技术写作、调试分析",
                    max_tokens=4096,
                    temperature=0.4,
                    is_core=False,
                ),
                ModelType.MINIMAX_M25.value: ModelConfig(
                    name="minimax-m2.5",
                    context_window=32000,
                    specialty="快速响应、实时交互、简单任务",
                    max_tokens=2048,
                    temperature=0.7,
                    is_core=False,
                ),
            }
        
        if self.rate_limits is None:
            self.rate_limits = {
                "per_5_hours": 6000,
                "per_week": 45000,
                "per_month": 90000,
                "web_search_per_month": 2000,
            }


@dataclass
class RoutingRule:
    task_type: str
    primary_model: str
    fallback_models: List[str]
    description: str
    use_core_model: bool = False


ROUTING_RULES: List[RoutingRule] = [
    RoutingRule(
        task_type="core_business",
        primary_model=ModelType.GLM_5.value,
        fallback_models=[ModelType.KIMI_K25.value, ModelType.DEEPSEEK_V32.value],
        description="核心业务：Fiverr运营、客户沟通、内容创作",
        use_core_model=True,
    ),
    RoutingRule(
        task_type="customer_communication",
        primary_model=ModelType.GLM_5.value,
        fallback_models=[ModelType.KIMI_K25.value],
        description="客户沟通：消息回复、需求确认、项目更新",
        use_core_model=True,
    ),
    RoutingRule(
        task_type="content_creation",
        primary_model=ModelType.GLM_5.value,
        fallback_models=[ModelType.KIMI_K25.value],
        description="内容创作：社交媒体文案、营销内容、博客文章",
        use_core_model=True,
    ),
    RoutingRule(
        task_type="multilingual",
        primary_model=ModelType.GLM_5.value,
        fallback_models=[ModelType.KIMI_K25.value],
        description="多语言处理：翻译、本地化、跨文化沟通",
        use_core_model=True,
    ),
    RoutingRule(
        task_type="code_generation",
        primary_model=ModelType.DEEPSEEK_V32.value,
        fallback_models=[ModelType.GLM_5.value, ModelType.KIMI_K25.value],
        description="代码生成：固件开发、脚本编写、代码审查",
        use_core_model=False,
    ),
    RoutingRule(
        task_type="architecture_design",
        primary_model=ModelType.GLM_5.value,
        fallback_models=[ModelType.KIMI_K25.value, ModelType.DEEPSEEK_V32.value],
        description="架构设计：系统设计、技术方案、模块规划",
        use_core_model=True,
    ),
    RoutingRule(
        task_type="quick_response",
        primary_model=ModelType.MINIMAX_M25.value,
        fallback_models=[ModelType.GLM_5.value],
        description="快速响应：即时回复、简单确认、状态更新",
        use_core_model=False,
    ),
    RoutingRule(
        task_type="long_document",
        primary_model=ModelType.KIMI_K25.value,
        fallback_models=[ModelType.GLM_5.value, ModelType.DEEPSEEK_V32.value],
        description="长文档处理：技术文档、项目报告、需求分析",
        use_core_model=False,
    ),
    RoutingRule(
        task_type="technical_writing",
        primary_model=ModelType.GLM_5.value,
        fallback_models=[ModelType.DEEPSEEK_V32.value, ModelType.KIMI_K25.value],
        description="技术写作：API文档、用户手册、技术博客",
        use_core_model=True,
    ),
]


def get_model_for_task(task_type: str) -> RoutingRule:
    for rule in ROUTING_RULES:
        if rule.task_type == task_type:
            return rule
    return ROUTING_RULES[0]


def get_core_model() -> str:
    return ModelType.GLM_5.value


def is_core_model_task(task_type: str) -> bool:
    rule = get_model_for_task(task_type)
    return rule.use_core_model


N8N_WORKFLOW_INTEGRATION = """
N8N工作流集成架构：

1. 核心角色定位
   - N8N作为跨平台工作流编排引擎
   - 处理规则明确、可自动化的重复性任务
   - 与GLM-5协同：GLM-5处理智能推理，N8N处理流程执行

2. 主要应用场景
   - Fiverr订单监控与自动处理
   - 社交媒体内容定时发布
   - Obsidian-Notion知识库同步
   - GitHub项目自动备份
   - 客户消息通知推送

3. 与GLM-5的协同模式
   - GLM-5生成内容 → N8N执行发布流程
   - N8N监控事件 → GLM-5分析处理 → N8N执行响应
   - N8N定时触发 → GLM-5生成报告 → N8N分发通知

4. 技术集成点
   - Webhook接收外部事件
   - HTTP Request调用GLM-5 API
   - 数据库操作（PostgreSQL/Redis）
   - 文件系统操作
   - 第三方API集成
"""
