"""AI 技能市场 - 技能定义 JSON Schema."""

from typing import Any, Optional
from pydantic import BaseModel, Field


class ActionConfig(BaseModel):
    """动作配置."""

    type: str = Field(..., description="动作类型")
    params: dict[str, Any] = Field(default_factory=dict, description="动作参数")
    timeout: int = Field(default=30, description="超时时间（秒）")
    retry: int = Field(default=3, description="重试次数")


class TriggerCondition(BaseModel):
    """触发器条件."""

    field: str = Field(..., description="字段名")
    operator: str = Field(..., description="操作符：eq, ne, gt, lt, contains")
    value: Any = Field(..., description="比较值")


class TriggerConfig(BaseModel):
    """触发器配置."""

    type: str = Field(..., description="触发器类型：timer, manual, event")
    cron: Optional[str] = Field(default=None, description="Cron 表达式（timer 类型）")
    event_type: Optional[str] = Field(default=None, description="事件类型（event 类型）")
    conditions: list[TriggerCondition] = Field(default_factory=list, description="触发条件")


class SkillDefinition(BaseModel):
    """技能定义."""

    name: str = Field(..., description="技能名称")
    version: str = Field(..., description="版本号")
    description: str = Field(..., description="技能描述")
    trigger: TriggerConfig = Field(..., description="触发器配置")
    actions: list[ActionConfig] = Field(..., description="动作列表")
    enabled: bool = Field(default=True, description="是否启用")
    tags: list[str] = Field(default_factory=list, description="标签")
    author: str = Field(default="System", description="作者")
    variables: dict[str, Any] = Field(default_factory=dict, description="变量定义")

    class Config:
        """Pydantic 配置."""

        json_schema_extra = {
            "example": {
                "name": "邮件自动回复",
                "version": "1.0.0",
                "description": "自动回复客户邮件",
                "trigger": {
                    "type": "event",
                    "event_type": "new_email",
                    "conditions": [
                        {"field": "sender", "operator": "contains", "value": "@customer.com"}
                    ],
                },
                "actions": [
                    {
                        "type": "ai_generate",
                        "params": {
                            "model": "glm-5",
                            "prompt": "请回复这封邮件：{{email_content}}",
                        },
                        "timeout": 60,
                    },
                    {
                        "type": "send_email",
                        "params": {"to": "{{sender}}", "subject": "Re: {{email_subject}}"},
                    },
                ],
                "enabled": True,
                "tags": ["email", "auto-reply"],
                "author": "System",
            }
        }
