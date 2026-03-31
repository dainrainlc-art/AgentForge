"""工作流模板市场 - 工作流管理器测试."""

import tempfile
from pathlib import Path

import pytest

from agentforge.core.schemas.workflow_schema import (
    WorkflowDefinition,
    WorkflowStep,
    WorkflowTrigger,
)
from agentforge.core.workflow_manager import WorkflowLoader, WorkflowManager


class TestWorkflowLoader:
    """测试工作流加载器."""

    def test_create_loader_default_dir(self):
        """测试创建加载器（默认目录）."""
        loader = WorkflowLoader()

        assert loader.workflows_dir.exists()
        assert loader.workflows_dir.is_dir()

    def test_create_loader_custom_dir(self):
        """测试创建加载器（自定义目录）."""
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = WorkflowLoader(tmpdir)

            assert loader.workflows_dir == Path(tmpdir)
            assert loader.workflows_dir.exists()

    def test_save_and_load_workflow(self):
        """测试保存和加载工作流."""
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = WorkflowLoader(tmpdir)

            workflow = WorkflowDefinition(
                name="测试工作流",
                version="1.0.0",
                description="测试工作流描述",
                trigger=WorkflowTrigger(type="manual"),
                workflow=[
                    WorkflowStep(name="步骤 1", type="action", action_type="send_message"),
                ],
            )

            # 保存工作流
            saved_path = loader.save_workflow(workflow)
            assert saved_path.exists()

            # 加载工作流
            loaded_workflow = loader.load_workflow(saved_path)
            assert loaded_workflow.name == workflow.name
            assert loaded_workflow.version == workflow.version
            assert loaded_workflow.description == workflow.description

    def test_load_all_workflows(self):
        """测试加载所有工作流."""
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = WorkflowLoader(tmpdir)

            # 创建多个工作流文件
            for i in range(3):
                workflow = WorkflowDefinition(
                    name=f"工作流{i}",
                    version="1.0.0",
                    description=f"测试工作流{i}",
                    trigger=WorkflowTrigger(type="manual"),
                    workflow=[],
                )
                loader.save_workflow(workflow)

            # 加载所有工作流
            workflows = loader.load_all_workflows()
            assert len(workflows) == 3

    def test_delete_workflow(self):
        """测试删除工作流."""
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = WorkflowLoader(tmpdir)

            workflow = WorkflowDefinition(
                name="删除测试",
                version="1.0.0",
                description="测试删除",
                trigger=WorkflowTrigger(type="manual"),
                workflow=[],
            )

            saved_path = loader.save_workflow(workflow)
            assert saved_path.exists()

            # 删除工作流
            success = loader.delete_workflow("删除测试")
            assert success is True
            assert not saved_path.exists()

            # 删除不存在的工作流
            success = loader.delete_workflow("不存在的工作流")
            assert success is False


class TestWorkflowManager:
    """测试工作流管理器."""

    @pytest.fixture
    def temp_workflows_dir(self):
        """临时工作流目录."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_initialize_manager(self, temp_workflows_dir):
        """测试初始化管理器."""
        manager = WorkflowManager(temp_workflows_dir)

        assert manager._loader is not None
        assert manager._engine is not None
        assert len(manager._workflows) == 0

    @pytest.mark.asyncio
    async def test_load_workflows(self, temp_workflows_dir):
        """测试加载工作流."""
        manager = WorkflowManager(temp_workflows_dir)

        # 创建工作流文件
        workflow = WorkflowDefinition(
            name="测试工作流",
            version="1.0.0",
            description="测试",
            trigger=WorkflowTrigger(type="manual"),
            workflow=[],
        )
        manager._loader.save_workflow(workflow)

        # 加载工作流
        await manager.load_workflows()
        assert len(manager._workflows) == 1
        assert "测试工作流" in manager._workflows

    @pytest.mark.asyncio
    async def test_register_workflow(self, temp_workflows_dir):
        """测试注册工作流."""
        manager = WorkflowManager(temp_workflows_dir)
        await manager.initialize()

        workflow = WorkflowDefinition(
            name="新工作流",
            version="1.0.0",
            description="新工作流描述",
            trigger=WorkflowTrigger(type="manual"),
            workflow=[],
        )

        manager.register_workflow(workflow, save=True)

        assert len(manager._workflows) == 1
        assert manager.get_workflow("新工作流") == workflow

    @pytest.mark.asyncio
    async def test_unregister_workflow(self, temp_workflows_dir):
        """测试注销工作流."""
        manager = WorkflowManager(temp_workflows_dir)

        workflow = WorkflowDefinition(
            name="临时工作流",
            version="1.0.0",
            description="临时工作流",
            trigger=WorkflowTrigger(type="manual"),
            workflow=[],
        )
        manager._loader.save_workflow(workflow)
        await manager.initialize()

        # 注销工作流
        success = manager.unregister_workflow("临时工作流", delete=False)
        assert success is True
        assert manager.get_workflow("临时工作流") is None

    @pytest.mark.asyncio
    async def test_list_workflows(self, temp_workflows_dir):
        """测试获取工作流列表."""
        manager = WorkflowManager(temp_workflows_dir)

        # 创建多个工作流
        for i in range(3):
            workflow = WorkflowDefinition(
                name=f"工作流{i}",
                version="1.0.0",
                description=f"测试{i}",
                trigger=WorkflowTrigger(type="manual"),
                workflow=[],
                tags=["test"] if i % 2 == 0 else [],
                enabled=i % 2 == 0,
            )
            manager._loader.save_workflow(workflow)

        await manager.initialize()

        # 获取所有工作流
        all_workflows = manager.list_workflows()
        assert len(all_workflows) == 3

        # 按标签筛选
        tagged_workflows = manager.list_workflows(tag="test")
        assert len(tagged_workflows) == 2

        # 按启用状态筛选
        enabled_workflows = manager.list_workflows(enabled=True)
        assert len(enabled_workflows) == 2

    @pytest.mark.asyncio
    async def test_execute_workflow(self, temp_workflows_dir):
        """测试执行工作流."""
        manager = WorkflowManager(temp_workflows_dir)

        # 创建工作流
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
            enabled=True,
        )
        manager._loader.save_workflow(workflow)
        await manager.initialize()

        # 执行工作流
        result = await manager.execute_workflow("测试工作流")
        assert result is not None
        assert result.status == "success"
