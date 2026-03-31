"""工作流模板市场 - 工作流引擎测试."""

import pytest

from agentforge.core.schemas.workflow_schema import (
    WorkflowDefinition,
    WorkflowStep,
    WorkflowTrigger,
)
from agentforge.core.workflow_engine import WorkflowContext, WorkflowEngine, WorkflowExecutor


class TestWorkflowDefinition:
    """测试工作流定义."""

    def test_create_workflow_definition(self):
        """测试创建工作流定义."""
        workflow = WorkflowDefinition(
            name="测试工作流",
            version="1.0.0",
            description="测试工作流描述",
            trigger=WorkflowTrigger(type="manual"),
            workflow=[
                WorkflowStep(name="步骤 1", type="action", action_type="send_message"),
            ],
        )

        assert workflow.name == "测试工作流"
        assert workflow.version == "1.0.0"
        assert workflow.enabled is True
        assert len(workflow.workflow) == 1

    def test_workflow_with_condition_step(self):
        """测试带条件步骤的工作流."""
        workflow = WorkflowDefinition(
            name="条件工作流",
            version="1.0.0",
            description="带条件的工作流",
            trigger=WorkflowTrigger(type="event", event_type="test"),
            workflow=[
                WorkflowStep(
                    name="条件判断",
                    type="condition",
                    conditions=[
                        {"field": "value", "operator": "gt", "value": 10}
                    ],
                ),
            ],
        )

        assert workflow.workflow[0].type == "condition"
        assert len(workflow.workflow[0].conditions) == 1

    def test_workflow_with_parallel_step(self):
        """测试带并行步骤的工作流."""
        workflow = WorkflowDefinition(
            name="并行工作流",
            version="1.0.0",
            description="带并行的工作流",
            trigger=WorkflowTrigger(type="manual"),
            workflow=[
                WorkflowStep(
                    name="并行执行",
                    type="parallel",
                    steps=[
                        WorkflowStep(name="子步骤 1", type="action", action_type="task1"),
                        WorkflowStep(name="子步骤 2", type="action", action_type="task2"),
                    ],
                ),
            ],
        )

        assert workflow.workflow[0].type == "parallel"
        assert len(workflow.workflow[0].steps) == 2


class TestWorkflowContext:
    """测试工作流上下文."""

    def test_create_context(self):
        """测试创建上下文."""
        workflow = WorkflowDefinition(
            name="测试",
            version="1.0.0",
            description="测试",
            trigger=WorkflowTrigger(type="manual"),
            workflow=[],
        )

        context = WorkflowContext(workflow)

        assert context.workflow == workflow
        assert context.status == "pending"
        assert context.start_time is None

    def test_context_variables(self):
        """测试上下文变量."""
        workflow = WorkflowDefinition(
            name="测试",
            version="1.0.0",
            description="测试",
            trigger=WorkflowTrigger(type="manual"),
            workflow=[],
        )

        context = WorkflowContext(workflow, {"key1": "value1"})

        assert context.get_variable("key1") == "value1"
        assert context.get_variable("key2", "default") == "default"

        context.set_variable("key2", "value2")
        assert context.get_variable("key2") == "value2"

    def test_record_step(self):
        """测试记录步骤."""
        workflow = WorkflowDefinition(
            name="测试",
            version="1.0.0",
            description="测试",
            trigger=WorkflowTrigger(type="manual"),
            workflow=[],
        )

        context = WorkflowContext(workflow)
        context.record_step("步骤 1", "success", result={"data": "ok"})

        assert len(context.history) == 1
        assert context.history[0]["step"] == "步骤 1"
        assert context.history[0]["status"] == "success"


class TestWorkflowExecutor:
    """测试工作流执行器."""

    def test_register_handler(self):
        """测试注册处理器."""
        executor = WorkflowExecutor()

        async def dummy_handler(params, context):
            return {"result": "ok"}

        executor.register_handler("test_action", dummy_handler)

        assert "test_action" in executor._handlers

    def test_evaluate_condition(self):
        """测试条件评估."""
        executor = WorkflowExecutor()

        # 测试等于操作符
        assert executor._evaluate_condition(5, "eq", 5) is True
        assert executor._evaluate_condition(5, "eq", 10) is False

        # 测试大于操作符
        assert executor._evaluate_condition(10, "gt", 5) is True
        assert executor._evaluate_condition(5, "gt", 10) is False

        # 测试存在操作符
        assert executor._evaluate_condition("value", "exists", True) is True
        assert executor._evaluate_condition(None, "exists", True) is False

    def test_replace_variables(self):
        """测试变量替换."""
        executor = WorkflowExecutor()
        workflow = WorkflowDefinition(
            name="测试",
            version="1.0.0",
            description="测试",
            trigger=WorkflowTrigger(type="manual"),
            workflow=[],
        )
        context = WorkflowContext(workflow, {"name": "张三", "age": 25})

        params = {
            "message": "你好，{{name}}",
            "info": "年龄：{{age}}",
        }

        result = executor._replace_variables(params, context)

        assert result["message"] == "你好，张三"
        assert result["info"] == "年龄：25"


class TestWorkflowEngine:
    """测试工作流引擎."""

    def test_create_engine(self):
        """测试创建工作流引擎."""
        engine = WorkflowEngine()

        assert engine._executor is not None

    @pytest.mark.asyncio
    async def test_execute_workflow_success(self):
        """测试成功执行工作流."""
        engine = WorkflowEngine()

        workflow = WorkflowDefinition(
            name="测试工作流",
            version="1.0.0",
            description="测试工作流",
            trigger=WorkflowTrigger(type="manual"),
            workflow=[
                WorkflowStep(
                    name="创建任务",
                    type="action",
                    action_type="create_task",
                    params={"title": "测试任务"},
                ),
            ],
        )

        context = await engine.execute_workflow(workflow)

        assert context.status == "success"
        # 每个步骤会记录 2 次（started 和 success）
        assert len(context.history) >= 1
        assert context.start_time is not None
        assert context.end_time is not None

    @pytest.mark.asyncio
    async def test_execute_workflow_with_error(self):
        """测试工作流执行失败."""
        engine = WorkflowEngine()

        workflow = WorkflowDefinition(
            name="错误工作流",
            version="1.0.0",
            description="错误工作流",
            trigger=WorkflowTrigger(type="manual"),
            workflow=[
                WorkflowStep(
                    name="未知动作",
                    type="action",
                    action_type="unknown_action",
                    params={},
                    on_error="abort",
                ),
            ],
        )

        context = await engine.execute_workflow(workflow)

        assert context.status == "failed"
        assert context.error is not None

    def test_get_running_workflows(self):
        """测试获取运行中的工作流."""
        engine = WorkflowEngine()

        workflows = engine.get_running_workflows()
        assert isinstance(workflows, list)
        assert len(workflows) == 0
