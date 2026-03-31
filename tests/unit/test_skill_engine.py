"""AI 技能市场 - 技能引擎测试."""

import pytest

from agentforge.core.schemas.skill_schema import (
    ActionConfig,
    SkillDefinition,
    TriggerConfig,
)
from agentforge.core.skill_engine import ActionExecutor, SkillContext, SkillEngine


class TestSkillDefinition:
    """测试技能定义."""

    def test_create_skill_definition(self):
        """测试创建技能定义."""
        skill = SkillDefinition(
            name="测试技能",
            version="1.0.0",
            description="测试技能描述",
            trigger=TriggerConfig(type="manual"),
            actions=[
                ActionConfig(type="ai_generate", params={"model": "glm-5"}),
            ],
        )

        assert skill.name == "测试技能"
        assert skill.version == "1.0.0"
        assert skill.enabled is True
        assert len(skill.actions) == 1

    def test_skill_with_trigger_conditions(self):
        """测试带条件的技能."""
        skill = SkillDefinition(
            name="条件技能",
            version="1.0.0",
            description="带条件的技能",
            trigger=TriggerConfig(
                type="event",
                event_type="new_order",
                conditions=[
                    {
                        "field": "order_value",
                        "operator": "gt",
                        "value": 100,
                    }
                ],
            ),
            actions=[
                ActionConfig(type="send_message", params={"to": "customer"}),
            ],
        )

        assert skill.trigger.type == "event"
        assert len(skill.trigger.conditions) == 1


class TestSkillContext:
    """测试技能上下文."""

    def test_create_context(self):
        """测试创建上下文."""
        skill = SkillDefinition(
            name="测试",
            version="1.0.0",
            description="测试",
            trigger=TriggerConfig(type="manual"),
            actions=[],
        )

        context = SkillContext(skill)

        assert context.skill == skill
        assert context.status == "pending"
        assert context.start_time is None

    def test_context_variables(self):
        """测试上下文变量."""
        skill = SkillDefinition(
            name="测试",
            version="1.0.0",
            description="测试",
            trigger=TriggerConfig(type="manual"),
            actions=[],
        )

        context = SkillContext(skill, {"key1": "value1"})

        assert context.get_variable("key1") == "value1"
        assert context.get_variable("key2", "default") == "default"

        context.set_variable("key2", "value2")
        assert context.get_variable("key2") == "value2"


class TestActionExecutor:
    """测试动作执行器."""

    def test_register_handler(self):
        """测试注册处理器."""
        executor = ActionExecutor()

        async def dummy_handler(params, context):
            return {"result": "ok"}

        executor.register_handler("test_action", dummy_handler)

        assert "test_action" in executor._handlers

    def test_replace_variables(self):
        """测试变量替换."""
        executor = ActionExecutor()
        skill = SkillDefinition(
            name="测试",
            version="1.0.0",
            description="测试",
            trigger=TriggerConfig(type="manual"),
            actions=[],
        )
        context = SkillContext(skill, {"name": "张三", "age": 25})

        params = {
            "message": "你好，{{name}}",
            "info": "年龄：{{age}}",
        }

        result = executor._replace_variables(params, context)

        assert result["message"] == "你好，张三"
        assert result["info"] == "年龄：25"

    def test_replace_nested_variables(self):
        """测试嵌套变量替换."""
        executor = ActionExecutor()
        skill = SkillDefinition(
            name="测试",
            version="1.0.0",
            description="测试",
            trigger=TriggerConfig(type="manual"),
            actions=[],
        )
        context = SkillContext(skill, {"user": "李四"})

        params = {
            "data": {
                "title": "{{user}} 的报告",
                "items": ["项目 1", "{{user}} 的项目 2"],
            }
        }

        result = executor._replace_variables(params, context)

        assert result["data"]["title"] == "李四 的报告"
        assert result["data"]["items"][0] == "项目 1"
        assert result["data"]["items"][1] == "李四 的项目 2"


class TestSkillEngine:
    """测试技能引擎."""

    def test_create_engine(self):
        """测试创建技能引擎."""
        engine = SkillEngine()

        assert engine._executor is not None
        assert engine._evaluator is not None

    @pytest.mark.asyncio
    async def test_execute_skill_success(self):
        """测试成功执行技能."""
        engine = SkillEngine()

        skill = SkillDefinition(
            name="测试技能",
            version="1.0.0",
            description="测试技能",
            trigger=TriggerConfig(type="manual"),
            actions=[
                ActionConfig(type="create_task", params={"title": "测试任务"}),
            ],
        )

        context = await engine.execute_skill(skill)

        assert context.status == "success"
        assert len(context.results) == 1
        assert context.start_time is not None
        assert context.end_time is not None

    @pytest.mark.asyncio
    async def test_execute_skill_with_trigger_condition(self):
        """测试带条件的技能执行."""
        engine = SkillEngine()

        skill = SkillDefinition(
            name="条件技能",
            version="1.0.0",
            description="条件技能",
            trigger=TriggerConfig(
                type="event",
                event_type="new_order",
                conditions=[
                    {
                        "field": "order_value",
                        "operator": "gt",
                        "value": 100,
                    }
                ],
            ),
            actions=[
                ActionConfig(type="send_message", params={}),
            ],
        )

        # 条件满足
        context = await engine.execute_skill(skill, {"order_value": 150})
        assert context.status == "success"

        # 条件不满足
        context = await engine.execute_skill(skill, {"order_value": 50})
        assert context.status == "skipped"

    @pytest.mark.asyncio
    async def test_execute_skill_with_variables(self):
        """测试带变量的技能执行."""
        engine = SkillEngine()

        skill = SkillDefinition(
            name="变量技能",
            version="1.0.0",
            description="变量技能",
            trigger=TriggerConfig(type="manual"),
            actions=[
                ActionConfig(
                    type="send_message",
                    params={"to": "{{customer}}", "content": "你好，{{customer}}"},
                ),
            ],
        )

        context = await engine.execute_skill(skill, {"customer": "王五"})

        assert context.status == "success"
        assert context.results[0]["to"] == "王五"

    def test_get_running_skills(self):
        """测试获取运行中的技能（简化测试）."""
        engine = SkillEngine()

        skills = engine.get_running_skills()
        assert isinstance(skills, list)
        assert len(skills) == 0
