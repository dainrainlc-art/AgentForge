"""AI 技能市场 - 技能执行引擎."""

import asyncio
import re
from datetime import datetime
from typing import Any, Callable

from loguru import logger

from agentforge.core.schemas.skill_schema import ActionConfig, SkillDefinition, TriggerCondition


class SkillContext:
    """技能执行上下文."""

    def __init__(self, skill: SkillDefinition, variables: dict[str, Any] | None = None):
        self.skill = skill
        self.variables = variables or {}
        self.start_time: datetime | None = None
        self.end_time: datetime | None = None
        self.status: str = "pending"  # pending, running, success, failed
        self.results: list[Any] = []
        self.error: str | None = None

    def set_variable(self, key: str, value: Any):
        """设置变量."""
        self.variables[key] = value

    def get_variable(self, key: str, default: Any = None) -> Any:
        """获取变量."""
        return self.variables.get(key, default)


class ActionExecutor:
    """动作执行器."""

    def __init__(self, action_handlers: dict[str, Callable] | None = None):
        self._handlers = action_handlers or {}

    def register_handler(self, action_type: str, handler: Callable):
        """注册动作处理器."""
        self._handlers[action_type] = handler
        logger.info(f"注册动作处理器：{action_type}")

    async def execute(
        self, action: ActionConfig, context: SkillContext
    ) -> Any:
        """执行动作."""
        action_type = action.type

        if action_type not in self._handlers:
            raise ValueError(f"未知的动作类型：{action_type}")

        handler = self._handlers[action_type]

        # 替换变量
        params = self._replace_variables(action.params, context)

        # 执行动作
        try:
            if asyncio.iscoroutinefunction(handler):
                result = await handler(params, context)
            else:
                result = handler(params, context)

            logger.info(f"动作执行成功：{action_type}")
            return result

        except Exception as e:
            logger.error(f"动作执行失败：{action_type}, 错误：{str(e)}")
            raise

    def _replace_variables(self, params: dict, context: SkillContext) -> dict:
        """替换参数中的变量."""
        result = {}

        for key, value in params.items():
            if isinstance(value, str):
                # 替换 {{variable}} 格式的变量
                result[key] = self._replace_string_variables(value, context)
            elif isinstance(value, dict):
                result[key] = self._replace_variables(value, context)
            elif isinstance(value, list):
                result[key] = [
                    self._replace_string_variables(item, context)
                    if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                result[key] = value

        return result

    def _replace_string_variables(self, text: str, context: SkillContext) -> str:
        """替换字符串中的变量."""
        pattern = r"\{\{(\w+)\}\}"

        def replacer(match):
            var_name = match.group(1)
            value = context.get_variable(var_name)
            return str(value) if value is not None else match.group(0)

        return re.sub(pattern, replacer, text)


class TriggerEvaluator:
    """触发器评估器."""

    def __init__(self):
        self._operators = {
            "eq": lambda a, b: a == b,
            "ne": lambda a, b: a != b,
            "gt": lambda a, b: a > b,
            "lt": lambda a, b: a < b,
            "contains": lambda a, b: b in a if isinstance(a, str) else b in list(a),
        }

    def evaluate(self, skill: SkillDefinition, event_data: dict[str, Any]) -> bool:
        """评估触发器条件."""
        trigger = skill.trigger
        conditions = trigger.conditions

        if not conditions:
            return True

        for condition in conditions:
            field_value = self._get_nested_field(event_data, condition.field)

            if condition.operator not in self._operators:
                logger.warning(f"未知的操作符：{condition.operator}")
                continue

            if not self._operators[condition.operator](field_value, condition.value):
                return False

        return True

    def _get_nested_field(self, data: dict, field: str) -> Any:
        """获取嵌套字段值."""
        keys = field.split(".")
        value = data

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None

        return value


class SkillEngine:
    """技能引擎."""

    def __init__(self):
        self._executor = ActionExecutor()
        self._evaluator = TriggerEvaluator()
        self._running_skills: dict[str, SkillContext] = {}
        self._register_default_handlers()

    def _register_default_handlers(self):
        """注册默认动作处理器."""
        # AI 生成
        self._executor.register_handler("ai_generate", self._handle_ai_generate)
        # HTTP 请求
        self._executor.register_handler("http_request", self._handle_http_request)
        # 发送消息
        self._executor.register_handler("send_message", self._handle_send_message)
        # 创建任务
        self._executor.register_handler("create_task", self._handle_create_task)
        # 数据查询
        self._executor.register_handler("query_data", self._handle_query_data)

    async def execute_skill(
        self, skill: SkillDefinition, event_data: dict[str, Any] | None = None
    ) -> SkillContext:
        """执行技能."""
        context = SkillContext(skill, event_data or {})

        # 评估触发器
        if event_data and not self._evaluator.evaluate(skill, event_data):
            logger.info(f"技能 {skill.name} 触发器条件不满足，跳过执行")
            context.status = "skipped"
            return context

        self._running_skills[skill.name] = context
        context.start_time = datetime.now()
        context.status = "running"

        try:
            for action in skill.actions:
                result = await self._executor.execute(action, context)
                context.results.append(result)

                # 如果动作返回数据，更新上下文变量
                if isinstance(result, dict):
                    for key, value in result.items():
                        context.set_variable(key, value)

            context.status = "success"
            logger.info(f"技能执行成功：{skill.name}")

        except Exception as e:
            context.status = "failed"
            context.error = str(e)
            logger.error(f"技能执行失败：{skill.name}, 错误：{str(e)}")

        finally:
            context.end_time = datetime.now()
            if skill.name in self._running_skills:
                del self._running_skills[skill.name]

        return context

    def register_action_handler(self, action_type: str, handler: Callable):
        """注册自定义动作处理器."""
        self._executor.register_handler(action_type, handler)

    def get_running_skills(self) -> list[str]:
        """获取正在运行的技能列表."""
        return list(self._running_skills.keys())

    # 默认动作处理器实现

    async def _handle_ai_generate(
        self, params: dict, context: SkillContext
    ) -> dict:
        """AI 生成处理器."""
        from agentforge.services.ai_service import AIService

        ai_service = AIService()
        model = params.get("model", "glm-5")
        prompt = params.get("prompt", "")

        response = await ai_service.generate(
            model=model,
            prompt=prompt,
            system_prompt=context.skill.description,
        )

        return {"ai_result": response}

    async def _handle_http_request(
        self, params: dict, context: SkillContext
    ) -> dict:
        """HTTP 请求处理器."""
        import httpx

        url = params.get("url")
        method = params.get("method", "GET")
        headers = params.get("headers", {})
        body = params.get("body")

        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                json=body,
                timeout=params.get("timeout", 30),
            )
            response.raise_for_status()

        return {"http_response": response.json()}

    async def _handle_send_message(
        self, params: dict, context: SkillContext
    ) -> dict:
        """发送消息处理器（简化版，实际应集成消息服务）."""
        to = params.get("to", "unknown")
        content = params.get("content", "")
        subject = params.get("subject", "")

        logger.info(f"发送消息到：{to}, 主题：{subject}, 内容：{content}")

        return {"message_sent": True, "to": to}

    async def _handle_create_task(
        self, params: dict, context: SkillContext
    ) -> dict:
        """创建任务处理器."""
        title = params.get("title", "新任务")
        description = params.get("description", "")
        priority = params.get("priority", "medium")

        logger.info(f"创建任务：{title}, 优先级：{priority}")

        return {
            "task_created": True,
            "title": title,
            "priority": priority,
        }

    async def _handle_query_data(
        self, params: dict, context: SkillContext
    ) -> dict:
        """数据查询处理器（简化版）."""
        query_type = params.get("type", "custom")
        query_params = params.get("params", {})

        logger.info(f"查询数据：{query_type}, 参数：{query_params}")

        # 这里应该根据 query_type 调用不同的数据服务
        return {"data": [], "total": 0}
