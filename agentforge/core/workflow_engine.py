"""工作流模板市场 - 工作流执行引擎."""

import asyncio
from datetime import datetime
from typing import Any, Callable

from loguru import logger

from agentforge.core.schemas.workflow_schema import (
    WorkflowDefinition,
    WorkflowStep,
)


class WorkflowContext:
    """工作流执行上下文."""

    def __init__(self, workflow: WorkflowDefinition, variables: dict[str, Any] | None = None):
        self.workflow = workflow
        self.variables = variables or {}
        self.start_time: datetime | None = None
        self.end_time: datetime | None = None
        self.status: str = "pending"  # pending, running, success, failed, paused
        self.current_step: str | None = None
        self.step_results: dict[str, Any] = {}
        self.error: str | None = None
        self.history: list[dict] = []

    def set_variable(self, key: str, value: Any):
        """设置变量."""
        self.variables[key] = value

    def get_variable(self, key: str, default: Any = None) -> Any:
        """获取变量."""
        return self.variables.get(key, default)

    def record_step(self, step_name: str, status: str, result: Any = None, error: str = None):
        """记录步骤执行."""
        self.history.append(
            {
                "step": step_name,
                "status": status,
                "result": result,
                "error": error,
                "timestamp": datetime.now().isoformat(),
            }
        )
        self.current_step = step_name


class WorkflowExecutor:
    """工作流执行器."""

    def __init__(self, action_handlers: dict[str, Callable] | None = None):
        self._handlers = action_handlers or {}
        self._register_default_handlers()

    def register_handler(self, action_type: str, handler: Callable):
        """注册动作处理器."""
        self._handlers[action_type] = handler
        logger.info(f"注册工作流动作处理器：{action_type}")

    async def execute_step(
        self, step: WorkflowStep, context: WorkflowContext
    ) -> Any:
        """执行工作流步骤."""
        context.record_step(step.name, "started")

        try:
            if step.type == "condition":
                result = await self._execute_condition(step, context)
            elif step.type == "parallel":
                result = await self._execute_parallel(step, context)
            elif step.type == "action":
                result = await self._execute_action(step, context)
            else:
                raise ValueError(f"未知的步骤类型：{step.type}")

            context.record_step(step.name, "success", result)
            logger.info(f"工作流步骤执行成功：{step.name}")
            return result

        except Exception as e:
            error_msg = str(e)
            context.record_step(step.name, "failed", error=error_msg)
            logger.error(f"工作流步骤执行失败：{step.name}, 错误：{error_msg}")

            # 错误处理
            if step.on_error == "continue":
                context.record_step(step.name, "skipped")
                return None
            elif step.on_error == "retry":
                return await self._retry_step(step, context)
            else:  # abort
                raise

    async def _execute_action(
        self, step: WorkflowStep, context: WorkflowContext
    ) -> Any:
        """执行动作步骤."""
        if not step.action_type:
            raise ValueError("动作步骤缺少 action_type")

        if step.action_type not in self._handlers:
            raise ValueError(f"未知的动作类型：{step.action_type}")

        handler = self._handlers[step.action_type]
        params = self._replace_variables(step.params, context)

        if asyncio.iscoroutinefunction(handler):
            result = await handler(params, context)
        else:
            result = handler(params, context)

        return result

    async def _execute_condition(
        self, step: WorkflowStep, context: WorkflowContext
    ) -> bool:
        """执行条件步骤."""
        if not step.conditions:
            return True

        for condition in step.conditions:
            field = condition.get("field")
            operator = condition.get("operator")
            value = condition.get("value")

            actual_value = context.get_variable(field)

            if not self._evaluate_condition(actual_value, operator, value):
                return False

        return True

    async def _execute_parallel(
        self, step: WorkflowStep, context: WorkflowContext
    ) -> list[Any]:
        """执行并行步骤."""
        if not step.steps:
            return []

        tasks = [self.execute_step(sub_step, context) for sub_step in step.steps]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return results

    async def _retry_step(self, step: WorkflowStep, context: WorkflowContext) -> Any:
        """重试步骤."""
        max_retries = step.retry or 3

        for attempt in range(max_retries):
            try:
                logger.info(f"重试步骤：{step.name}, 尝试 {attempt + 1}/{max_retries}")
                return await self._execute_action(step, context)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # 指数退避

        raise RuntimeError(f"步骤重试失败：{step.name}")

    def _evaluate_condition(self, actual: Any, operator: str, expected: Any) -> bool:
        """评估条件."""
        operators = {
            "eq": lambda a, b: a == b,
            "ne": lambda a, b: a != b,
            "gt": lambda a, b: a > b,
            "lt": lambda a, b: a < b,
            "gte": lambda a, b: a >= b,
            "lte": lambda a, b: a <= b,
            "contains": lambda a, b: b in a if isinstance(a, str) else b in list(a),
            "exists": lambda a, b: a is not None,
        }

        if operator not in operators:
            logger.warning(f"未知的操作符：{operator}")
            return False

        return operators[operator](actual, expected)

    def _replace_variables(self, params: dict, context: WorkflowContext) -> dict:
        """替换参数中的变量."""
        import re

        result = {}

        for key, value in params.items():
            if isinstance(value, str):
                pattern = r"\{\{(\w+)\}\}"

                def replacer(match):
                    var_name = match.group(1)
                    var_value = context.get_variable(var_name)
                    return str(var_value) if var_value is not None else match.group(0)

                result[key] = re.sub(pattern, replacer, value)
            elif isinstance(value, dict):
                result[key] = self._replace_variables(value, context)
            elif isinstance(value, list):
                result[key] = [
                    self._replace_variables(item, context)
                    if isinstance(item, (dict, list))
                    else self._replace_string_variable(item, context)
                    if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                result[key] = value

        return result

    def _replace_string_variable(self, text: str, context: WorkflowContext) -> str:
        """替换字符串中的变量."""
        import re

        pattern = r"\{\{(\w+)\}\}"

        def replacer(match):
            var_name = match.group(1)
            var_value = context.get_variable(var_name)
            return str(var_value) if var_value is not None else match.group(0)

        return re.sub(pattern, replacer, text)

    def _register_default_handlers(self):
        """注册默认动作处理器."""
        # 这些处理器应该复用技能引擎的处理器
        self._handlers.setdefault("ai_generate", self._handle_ai_generate)
        self._handlers.setdefault("send_message", self._handle_send_message)
        self._handlers.setdefault("create_task", self._handle_create_task)
        self._handlers.setdefault("http_request", self._handle_http_request)
        self._handlers.setdefault("query_data", self._handle_query_data)

    # 默认处理器实现（与技能引擎类似）
    async def _handle_ai_generate(self, params: dict, context: WorkflowContext) -> dict:
        """AI 生成处理器."""
        from agentforge.services.ai_service import AIService

        ai_service = AIService()
        model = params.get("model", "glm-5")
        prompt = params.get("prompt", "")

        response = await ai_service.generate(
            model=model,
            prompt=prompt,
            system_prompt=context.workflow.description,
        )

        return {"ai_result": response}

    async def _handle_send_message(self, params: dict, context: WorkflowContext) -> dict:
        """发送消息处理器."""
        to = params.get("to", "unknown")
        content = params.get("content", "")
        subject = params.get("subject", "")

        logger.info(f"发送消息到：{to}, 主题：{subject}, 内容：{content}")
        return {"message_sent": True, "to": to}

    async def _handle_create_task(self, params: dict, context: WorkflowContext) -> dict:
        """创建任务处理器."""
        title = params.get("title", "新任务")
        description = params.get("description", "")
        priority = params.get("priority", "medium")

        logger.info(f"创建任务：{title}, 优先级：{priority}")
        return {"task_created": True, "title": title, "priority": priority}

    async def _handle_http_request(self, params: dict, context: WorkflowContext) -> dict:
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

    async def _handle_query_data(self, params: dict, context: WorkflowContext) -> dict:
        """数据查询处理器."""
        query_type = params.get("type", "custom")
        query_params = params.get("params", {})

        logger.info(f"查询数据：{query_type}, 参数：{query_params}")
        return {"data": [], "total": 0}


class WorkflowEngine:
    """工作流引擎."""

    def __init__(self):
        self._executor = WorkflowExecutor()
        self._running_workflows: dict[str, WorkflowContext] = {}

    async def execute_workflow(
        self, workflow: WorkflowDefinition, variables: dict[str, Any] | None = None
    ) -> WorkflowContext:
        """执行工作流."""
        context = WorkflowContext(workflow, variables)

        self._running_workflows[workflow.name] = context
        context.start_time = datetime.now()
        context.status = "running"

        try:
            for step in workflow.workflow:
                await self._executor.execute_step(step, context)

            context.status = "success"
            logger.info(f"工作流执行成功：{workflow.name}")

        except Exception as e:
            context.status = "failed"
            context.error = str(e)
            logger.error(f"工作流执行失败：{workflow.name}, 错误：{str(e)}")

        finally:
            context.end_time = datetime.now()
            if workflow.name in self._running_workflows:
                del self._running_workflows[workflow.name]

        return context

    def register_action_handler(self, action_type: str, handler: Callable):
        """注册自定义动作处理器."""
        self._executor.register_handler(action_type, handler)

    def get_running_workflows(self) -> list[str]:
        """获取正在运行的工作流列表."""
        return list(self._running_workflows.keys())

    def get_workflow_history(self, context: WorkflowContext) -> list[dict]:
        """获取工作流执行历史."""
        return context.history
