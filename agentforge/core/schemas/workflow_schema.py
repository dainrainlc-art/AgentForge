"""工作流模板市场 - 工作流定义 YAML Schema."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class WorkflowStep(BaseModel):
    """工作流步骤."""

    name: str = Field(..., description="步骤名称")
    type: str = Field(..., description="步骤类型：action, condition, parallel")
    action_type: Optional[str] = Field(default=None, description="动作类型")
    params: dict[str, Any] = Field(default_factory=dict, description="动作参数")
    conditions: Optional[list[dict[str, Any]]] = Field(
        default=None, description="条件列表（condition 类型）"
    )
    steps: Optional[list["WorkflowStep"]] = Field(
        default=None, description="子步骤（parallel 类型）"
    )
    timeout: int = Field(default=300, description="超时时间（秒）")
    retry: int = Field(default=3, description="重试次数")
    on_error: Optional[str] = Field(
        default=None, description="错误处理：continue, abort, retry"
    )


class WorkflowTrigger(BaseModel):
    """工作流触发器."""

    type: str = Field(..., description="触发器类型：manual, event, timer")
    event_type: Optional[str] = Field(default=None, description="事件类型")
    cron: Optional[str] = Field(default=None, description="Cron 表达式")
    conditions: Optional[list[dict[str, Any]]] = Field(
        default_factory=list, description="触发条件"
    )


class WorkflowDefinition(BaseModel):
    """工作流定义."""

    name: str = Field(..., description="工作流名称")
    version: str = Field(..., description="版本号")
    description: str = Field(..., description="工作流描述")
    trigger: WorkflowTrigger = Field(..., description="触发器配置")
    workflow: list[WorkflowStep] = Field(..., description="工作流步骤")
    variables: dict[str, Any] = Field(default_factory=dict, description="变量定义")
    enabled: bool = Field(default=True, description="是否启用")
    tags: list[str] = Field(default_factory=list, description="标签")
    author: str = Field(default="System", description="作者")

    class Config:
        """Pydantic 配置."""

        json_schema_extra = {
            "example": {
                "name": "Fiverr 订单自动化",
                "version": "1.0.0",
                "description": "自动处理 Fiverr 订单",
                "trigger": {
                    "type": "event",
                    "event_type": "new_order",
                    "conditions": [{"field": "amount", "operator": "gt", "value": 50}],
                },
                "workflow": [
                    {
                        "name": "发送欢迎消息",
                        "type": "action",
                        "action_type": "send_message",
                        "params": {
                            "to": "{{customer_id}}",
                            "template": "welcome",
                        },
                    },
                    {
                        "name": "生成工作计划",
                        "type": "action",
                        "action_type": "ai_generate",
                        "params": {
                            "model": "glm-5",
                            "prompt": "生成订单 #{{order_id}} 的工作计划",
                        },
                    },
                    {
                        "name": "创建任务",
                        "type": "action",
                        "action_type": "create_task",
                        "params": {
                            "title": "完成订单 #{{order_id}}",
                            "description": "{{ai_result}}",
                            "priority": "high",
                        },
                    },
                ],
                "enabled": True,
                "tags": ["fiverr", "order"],
                "author": "System",
            }
        }
