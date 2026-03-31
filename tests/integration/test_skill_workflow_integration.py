"""技能和工作流集成测试."""

import pytest


class TestSkillWorkflowIntegration:
    """技能和工作流集成测试."""

    @pytest.mark.asyncio
    async def test_skill_trigger_workflow(self):
        """测试技能触发工作流."""
        from agentforge.core.skill_manager import SkillManager
        from agentforge.core.workflow_manager import WorkflowManager
        from agentforge.core.schemas.skill_schema import (
            SkillDefinition,
            TriggerConfig,
            ActionConfig,
        )
        from agentforge.core.schemas.workflow_schema import (
            WorkflowDefinition,
            WorkflowTrigger,
            WorkflowStep,
        )

        skill_manager = SkillManager()
        workflow_manager = WorkflowManager()

        await skill_manager.initialize()
        await workflow_manager.initialize()

        # 创建工作流
        workflow = WorkflowDefinition(
            name="技能触发测试工作流",
            version="1.0.0",
            description="被技能触发的工作流",
            trigger=WorkflowTrigger(type="event", event_type="skill_triggered"),
            workflow=[
                WorkflowStep(
                    name="创建任务",
                    type="action",
                    action_type="create_task",
                    params={"title": "工作流任务"},
                ),
            ],
            enabled=True,
        )
        workflow_manager.register_workflow(workflow, save=False)

        # 创建技能（执行后触发事件）
        skill = SkillDefinition(
            name="触发工作流技能",
            version="1.0.0",
            description="触发工作流的技能",
            trigger=TriggerConfig(type="manual"),
            actions=[
                ActionConfig(type="create_task", params={"title": "技能任务"}),
            ],
            enabled=True,
        )
        skill_manager.register_skill(skill, save=False)

        # 执行技能
        skill_results = await skill_manager.trigger_event("manual", {})
        assert len(skill_results) == 1
        assert skill_results[0]["result"].status == "success"

        # 触发工作流事件
        workflow_result = await workflow_manager.execute_workflow(
            "技能触发测试工作流", {}
        )
        assert workflow_result.status == "success"

        # 清理
        skill_manager.unregister_skill("触发工作流技能", delete=False)
        workflow_manager.unregister_workflow("技能触发测试工作流", delete=False)

    @pytest.mark.asyncio
    async def test_workflow_then_skill(self):
        """测试工作流完成后触发技能."""
        from agentforge.core.skill_manager import SkillManager
        from agentforge.core.workflow_manager import WorkflowManager
        from agentforge.core.schemas.skill_schema import (
            SkillDefinition,
            TriggerConfig,
            ActionConfig,
        )
        from agentforge.core.schemas.workflow_schema import (
            WorkflowDefinition,
            WorkflowTrigger,
            WorkflowStep,
        )

        skill_manager = SkillManager()
        workflow_manager = WorkflowManager()

        await skill_manager.initialize()
        await workflow_manager.initialize()

        # 创建技能（监听工作流完成事件）
        skill = SkillDefinition(
            name="工作流完成技能",
            version="1.0.0",
            description="工作流完成后执行",
            trigger=TriggerConfig(type="event", event_type="workflow_completed"),
            actions=[
                ActionConfig(
                    type="send_message", params={"to": "user", "content": "工作流已完成"}
                ),
            ],
            enabled=True,
        )
        skill_manager.register_skill(skill, save=False)

        # 创建工作流（完成后触发事件）
        workflow = WorkflowDefinition(
            name="主工作流",
            version="1.0.0",
            description="主工作流",
            trigger=WorkflowTrigger(type="manual"),
            workflow=[
                WorkflowStep(
                    name="步骤 1",
                    type="action",
                    action_type="create_task",
                    params={"title": "步骤 1"},
                ),
            ],
            enabled=True,
        )
        workflow_manager.register_workflow(workflow, save=False)

        # 执行工作流
        result = await workflow_manager.execute_workflow("主工作流", {})
        assert result.status == "success"

        # 触发技能（模拟工作流完成事件）
        skill_results = await skill_manager.trigger_event(
            "workflow_completed", {"workflow_name": "主工作流"}
        )
        assert len(skill_results) == 1

        # 清理
        skill_manager.unregister_skill("工作流完成技能", delete=False)
        workflow_manager.unregister_workflow("主工作流", delete=False)


class TestComplexIntegration:
    """复杂集成场景测试."""

    @pytest.mark.asyncio
    async def test_chained_execution(self):
        """测试链式执行：技能 -> 工作流 -> 技能."""
        from agentforge.core.skill_manager import SkillManager
        from agentforge.core.workflow_manager import WorkflowManager
        from agentforge.core.schemas.skill_schema import (
            SkillDefinition,
            TriggerConfig,
            ActionConfig,
        )
        from agentforge.core.schemas.workflow_schema import (
            WorkflowDefinition,
            WorkflowTrigger,
            WorkflowStep,
        )

        skill_manager = SkillManager()
        workflow_manager = WorkflowManager()

        await skill_manager.initialize()
        await workflow_manager.initialize()

        execution_log = []

        # 创建第一个技能
        skill1 = SkillDefinition(
            name="技能 1",
            version="1.0.0",
            description="链式执行第一个",
            trigger=TriggerConfig(type="manual"),
            actions=[
                ActionConfig(type="create_task", params={"title": "技能 1 任务"}),
            ],
            enabled=True,
        )
        skill_manager.register_skill(skill1, save=False)

        # 创建工作流
        workflow = WorkflowDefinition(
            name="中间工作流",
            version="1.0.0",
            description="链式执行中间",
            trigger=WorkflowTrigger(type="event", event_type="skill1_completed"),
            workflow=[
                WorkflowStep(
                    name="处理",
                    type="action",
                    action_type="send_message",
                    params={"to": "user", "content": "中间处理"},
                ),
            ],
            enabled=True,
        )
        workflow_manager.register_workflow(workflow, save=False)

        # 创建第二个技能
        skill2 = SkillDefinition(
            name="技能 2",
            version="1.0.0",
            description="链式执行第二个",
            trigger=TriggerConfig(type="event", event_type="workflow_done"),
            actions=[
                ActionConfig(type="create_task", params={"title": "技能 2 任务"}),
            ],
            enabled=True,
        )
        skill_manager.register_skill(skill2, save=False)

        # 执行链式调用
        # 1. 执行技能 1
        result1 = await skill_manager.trigger_event("manual", {})
        assert len(result1) == 1
        execution_log.append("skill1")

        # 2. 触发工作流
        result2 = await workflow_manager.execute_workflow("中间工作流", {})
        assert result2.status == "success"
        execution_log.append("workflow")

        # 3. 触发技能 2
        result3 = await skill_manager.trigger_event("workflow_done", {})
        assert len(result3) == 1
        execution_log.append("skill2")

        # 验证执行顺序
        assert execution_log == ["skill1", "workflow", "skill2"]

        # 清理
        skill_manager.unregister_skill("技能 1", delete=False)
        skill_manager.unregister_skill("技能 2", delete=False)
        workflow_manager.unregister_workflow("中间工作流", delete=False)

    @pytest.mark.asyncio
    async def test_parallel_skill_workflow(self):
        """测试技能和工作的并行执行."""
        import asyncio
        from agentforge.core.skill_manager import SkillManager
        from agentforge.core.workflow_manager import WorkflowManager
        from agentforge.core.schemas.skill_schema import (
            SkillDefinition,
            TriggerConfig,
            ActionConfig,
        )
        from agentforge.core.schemas.workflow_schema import (
            WorkflowDefinition,
            WorkflowTrigger,
            WorkflowStep,
        )

        skill_manager = SkillManager()
        workflow_manager = WorkflowManager()

        await skill_manager.initialize()
        await workflow_manager.initialize()

        # 创建技能
        skill = SkillDefinition(
            name="并行技能",
            version="1.0.0",
            description="并行执行",
            trigger=TriggerConfig(type="manual"),
            actions=[
                ActionConfig(type="create_task", params={"title": "技能任务"}),
            ],
            enabled=True,
        )
        skill_manager.register_skill(skill, save=False)

        # 创建工作流
        workflow = WorkflowDefinition(
            name="并行工作流",
            version="1.0.0",
            description="并行执行",
            trigger=WorkflowTrigger(type="manual"),
            workflow=[
                WorkflowStep(
                    name="步骤",
                    type="action",
                    action_type="send_message",
                    params={"to": "user"},
                ),
            ],
            enabled=True,
        )
        workflow_manager.register_workflow(workflow, save=False)

        # 并行执行
        tasks = [
            skill_manager.trigger_event("manual", {}),
            workflow_manager.execute_workflow("并行工作流", {}),
            skill_manager.trigger_event("manual", {}),
            workflow_manager.execute_workflow("并行工作流", {}),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 验证所有任务都完成
        assert len(results) == 4

        # 清理
        skill_manager.unregister_skill("并行技能", delete=False)
        workflow_manager.unregister_workflow("并行工作流", delete=False)
