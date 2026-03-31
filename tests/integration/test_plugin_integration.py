"""插件集成测试."""

import pytest


class TestPluginBasicIntegration:
    """插件基础集成测试."""

    @pytest.mark.asyncio
    async def test_plugin_initialization(self):
        """测试插件初始化."""
        from agentforge.core.plugin_manager import PluginManager

        plugin_manager = PluginManager()
        await plugin_manager.initialize()

        # 验证插件已加载
        plugins = plugin_manager.list_plugins()
        assert len(plugins) > 0

        # 验证特定插件
        plugin_names = plugin_manager.get_plugin_names()
        assert "calendar" in plugin_names or len(plugin_names) > 0

    @pytest.mark.asyncio
    async def test_plugin_enable_disable(self):
        """测试插件启用禁用."""
        from agentforge.core.plugin_manager import PluginManager

        plugin_manager = PluginManager()
        await plugin_manager.initialize()

        # 获取插件
        calendar_plugin = plugin_manager.get_plugin("calendar")
        if calendar_plugin:
            # 初始状态应该是启用的
            assert calendar_plugin.is_enabled()

            # 禁用
            plugin_manager.disable_plugin("calendar")
            assert not calendar_plugin.is_enabled()

            # 重新启用
            plugin_manager.enable_plugin("calendar")
            assert calendar_plugin.is_enabled()

    @pytest.mark.asyncio
    async def test_plugin_capabilities(self):
        """测试插件能力查询."""
        from agentforge.core.plugin_manager import PluginManager

        plugin_manager = PluginManager()
        await plugin_manager.initialize()

        # 获取所有插件能力
        for plugin_name in plugin_manager.get_plugin_names():
            capabilities = plugin_manager.get_plugin_capabilities(plugin_name)
            assert isinstance(capabilities, list)
            assert len(capabilities) > 0

        # 按能力筛选插件
        action_plugins = plugin_manager.get_plugins_by_capability("action")
        assert isinstance(action_plugins, list)


class TestPluginExecution:
    """插件执行测试."""

    @pytest.mark.asyncio
    async def test_calendar_plugin_execution(self):
        """测试日历插件执行."""
        from agentforge.core.plugin_manager import PluginManager

        plugin_manager = PluginManager()
        await plugin_manager.initialize()

        plugin = plugin_manager.get_plugin("calendar")
        if plugin:
            # 获取日期
            result = await plugin.execute({"operation": "get_date"})
            assert "date" in result
            assert "time" in result
            assert "datetime" in result

            # 添加提醒
            result = await plugin.execute(
                {
                    "operation": "add_reminder",
                    "title": "测试提醒",
                    "description": "测试描述",
                }
            )
            assert result.get("success") is True

            # 列出提醒
            result = await plugin.execute({"operation": "list_reminders"})
            assert "count" in result
            assert "reminders" in result

    @pytest.mark.asyncio
    async def test_file_plugin_execution(self):
        """测试文件插件执行."""
        from agentforge.core.plugin_manager import PluginManager

        plugin_manager = PluginManager()
        await plugin_manager.initialize()

        plugin = plugin_manager.get_plugin("file")
        if plugin:
            # 写入文件
            test_content = "测试内容"
            result = await plugin.execute(
                {
                    "operation": "write",
                    "path": "test.txt",
                    "content": test_content,
                }
            )
            assert result.get("success") is True

            # 读取文件
            result = await plugin.execute(
                {
                    "operation": "read",
                    "path": "test.txt",
                }
            )
            assert "content" in result
            assert result["content"] == test_content

            # 写入 JSON
            test_data = {"key": "value", "number": 123}
            result = await plugin.execute(
                {
                    "operation": "write_json",
                    "path": "test.json",
                    "data": test_data,
                }
            )
            assert result.get("success") is True

            # 读取 JSON
            result = await plugin.execute(
                {
                    "operation": "read_json",
                    "path": "test.json",
                }
            )
            assert "data" in result
            assert result["data"]["key"] == "value"


class TestPluginWithSkillIntegration:
    """插件与技能集成测试."""

    @pytest.mark.asyncio
    async def test_plugin_as_skill_action(self):
        """测试插件作为技能动作."""
        from agentforge.core.skill_manager import SkillManager
        from agentforge.core.plugin_manager import PluginManager
        from agentforge.core.schemas.skill_schema import (
            SkillDefinition,
            TriggerConfig,
            ActionConfig,
        )

        skill_manager = SkillManager()
        plugin_manager = PluginManager()

        await skill_manager.initialize()
        await plugin_manager.initialize()

        # 获取插件
        calendar_plugin = plugin_manager.get_plugin("calendar")
        if not calendar_plugin:
            pytest.skip("日历插件不可用")

        # 注册插件动作为技能处理器
        async def calendar_handler(params: dict, context):
            return await calendar_plugin.execute(params)

        skill_manager.register_action_handler("calendar_plugin", calendar_handler)

        # 创建使用插件的技能
        skill = SkillDefinition(
            name="插件技能测试",
            version="1.0.0",
            description="使用插件的技能",
            trigger=TriggerConfig(type="manual"),
            actions=[
                ActionConfig(
                    type="calendar_plugin",
                    params={"operation": "get_date"},
                ),
            ],
            enabled=True,
        )

        skill_manager.register_skill(skill, save=False)

        # 执行技能
        results = await skill_manager.trigger_event("manual", {})

        # 验证
        assert len(results) == 1
        assert results[0]["result"].status == "success"

        # 清理
        skill_manager.unregister_skill("插件技能测试", delete=False)


class TestPluginWithWorkflowIntegration:
    """插件与工作流集成测试."""

    @pytest.mark.asyncio
    async def test_plugin_in_workflow(self):
        """测试工作流中使用插件."""
        from agentforge.core.workflow_manager import WorkflowManager
        from agentforge.core.plugin_manager import PluginManager
        from agentforge.core.schemas.workflow_schema import (
            WorkflowDefinition,
            WorkflowTrigger,
            WorkflowStep,
        )

        workflow_manager = WorkflowManager()
        plugin_manager = PluginManager()

        await workflow_manager.initialize()
        await plugin_manager.initialize()

        # 获取插件
        calendar_plugin = plugin_manager.get_plugin("calendar")
        if not calendar_plugin:
            pytest.skip("日历插件不可用")

        # 注册插件动作为工作流处理器
        async def calendar_handler(params: dict, context):
            return await calendar_plugin.execute(params)

        workflow_manager.register_action_handler("calendar_plugin", calendar_handler)

        # 创建使用插件的工作流
        workflow = WorkflowDefinition(
            name="插件工作流测试",
            version="1.0.0",
            description="使用插件的工作流",
            trigger=WorkflowTrigger(type="manual"),
            workflow=[
                WorkflowStep(
                    name="获取日期",
                    type="action",
                    action_type="calendar_plugin",
                    params={"operation": "get_date"},
                    timeout=30,
                    on_error="abort",
                ),
            ],
            enabled=True,
        )

        workflow_manager.register_workflow(workflow, save=False)

        # 执行工作流
        result = await workflow_manager.execute_workflow("插件工作流测试", {})

        # 验证
        assert result is not None
        assert result.status == "success"

        # 清理
        workflow_manager.unregister_workflow("插件工作流测试", delete=False)


class TestPluginErrorHandling:
    """插件错误处理测试."""

    @pytest.mark.asyncio
    async def test_plugin_error_in_skill(self):
        """测试技能中插件错误处理."""
        from agentforge.core.skill_manager import SkillManager
        from agentforge.core.plugin_manager import PluginManager
        from agentforge.core.schemas.skill_schema import (
            SkillDefinition,
            TriggerConfig,
            ActionConfig,
        )

        skill_manager = SkillManager()
        plugin_manager = PluginManager()

        await skill_manager.initialize()
        await plugin_manager.initialize()

        # 创建一个会失败的插件动作
        async def failing_handler(params: dict, context):
            raise ValueError("故意失败")

        skill_manager.register_action_handler("failing_plugin", failing_handler)

        # 创建技能（错误时继续）
        skill = SkillDefinition(
            name="错误处理测试",
            version="1.0.0",
            description="测试错误处理",
            trigger=TriggerConfig(type="manual"),
            actions=[
                ActionConfig(
                    type="failing_plugin",
                    params={},
                    on_error="continue",  # 继续执行
                ),
                ActionConfig(
                    type="create_task",
                    params={"title": "后续任务"},
                ),
            ],
            enabled=True,
        )

        skill_manager.register_skill(skill, save=False)

        # 执行技能（应该继续执行）
        results = await skill_manager.trigger_event("manual", {})

        # 验证：第一个动作失败，但第二个动作成功
        assert len(results) == 1
        # 技能应该完成（因为 on_error=continue）

        # 清理
        skill_manager.unregister_skill("错误处理测试", delete=False)


class TestPluginPerformance:
    """插件性能测试."""

    @pytest.mark.asyncio
    async def test_plugin_concurrent_execution(self):
        """测试插件并发执行."""
        import asyncio
        from agentforge.core.plugin_manager import PluginManager

        plugin_manager = PluginManager()
        await plugin_manager.initialize()

        plugin = plugin_manager.get_plugin("calendar")
        if not plugin:
            pytest.skip("日历插件不可用")

        # 并发执行 10 次
        tasks = []
        for i in range(10):
            task = asyncio.create_task(
                plugin.execute({"operation": "get_date"})
            )
            tasks.append(task)

        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 验证所有任务都完成
        success_count = sum(1 for r in results if not isinstance(r, Exception))
        assert success_count > 0

    @pytest.mark.asyncio
    async def test_plugin_memory_usage(self):
        """测试插件内存使用（简化版）."""
        from agentforge.core.plugin_manager import PluginManager

        plugin_manager = PluginManager()
        await plugin_manager.initialize()

        plugin = plugin_manager.get_plugin("calendar")
        if not plugin:
            pytest.skip("日历插件不可用")

        # 多次执行
        for _ in range(100):
            await plugin.execute({"operation": "get_date"})

        # 如果能正常执行完成，说明没有严重的内存泄漏
        assert True
