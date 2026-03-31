"""AI 技能市场 - 技能管理器测试."""

import json
import tempfile
from pathlib import Path

import pytest

from agentforge.core.schemas.skill_schema import (
    ActionConfig,
    SkillDefinition,
    TriggerConfig,
)
from agentforge.core.skill_manager import SkillLoader, SkillManager


class TestSkillLoader:
    """测试技能加载器."""

    def test_create_loader_default_dir(self):
        """测试创建加载器（默认目录）."""
        loader = SkillLoader()

        assert loader.skills_dir.exists()
        assert loader.skills_dir.is_dir()

    def test_create_loader_custom_dir(self):
        """测试创建加载器（自定义目录）."""
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = SkillLoader(tmpdir)

            assert loader.skills_dir == Path(tmpdir)
            assert loader.skills_dir.exists()

    def test_save_and_load_skill(self):
        """测试保存和加载技能."""
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = SkillLoader(tmpdir)

            skill = SkillDefinition(
                name="测试技能",
                version="1.0.0",
                description="测试技能描述",
                trigger=TriggerConfig(type="manual"),
                actions=[
                    ActionConfig(type="ai_generate", params={"model": "glm-5"}),
                ],
            )

            # 保存技能
            saved_path = loader.save_skill(skill)
            assert saved_path.exists()

            # 加载技能
            loaded_skill = loader.load_skill(saved_path)
            assert loaded_skill.name == skill.name
            assert loaded_skill.version == skill.version
            assert loaded_skill.description == skill.description

    def test_load_all_skills(self):
        """测试加载所有技能."""
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = SkillLoader(tmpdir)

            # 创建多个技能文件
            for i in range(3):
                skill = SkillDefinition(
                    name=f"技能{i}",
                    version="1.0.0",
                    description=f"测试技能{i}",
                    trigger=TriggerConfig(type="manual"),
                    actions=[],
                )
                loader.save_skill(skill)

            # 加载所有技能
            skills = loader.load_all_skills()
            assert len(skills) == 3

    def test_delete_skill(self):
        """测试删除技能."""
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = SkillLoader(tmpdir)

            skill = SkillDefinition(
                name="删除测试",
                version="1.0.0",
                description="测试删除",
                trigger=TriggerConfig(type="manual"),
                actions=[],
            )

            saved_path = loader.save_skill(skill)
            assert saved_path.exists()

            # 删除技能
            success = loader.delete_skill("删除测试")
            assert success is True
            assert not saved_path.exists()

            # 删除不存在的技能
            success = loader.delete_skill("不存在的技能")
            assert success is False


class TestSkillManager:
    """测试技能管理器."""

    @pytest.fixture
    def temp_skills_dir(self):
        """临时技能目录."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_initialize_manager(self, temp_skills_dir):
        """测试初始化管理器."""
        manager = SkillManager(temp_skills_dir)

        assert manager._loader is not None
        assert manager._engine is not None
        assert len(manager._skills) == 0

    @pytest.mark.asyncio
    async def test_load_skills(self, temp_skills_dir):
        """测试加载技能."""
        manager = SkillManager(temp_skills_dir)

        # 创建测试技能文件
        skill = SkillDefinition(
            name="测试技能",
            version="1.0.0",
            description="测试",
            trigger=TriggerConfig(type="manual"),
            actions=[],
        )
        manager._loader.save_skill(skill)

        # 加载技能
        await manager.load_skills()
        assert len(manager._skills) == 1
        assert "测试技能" in manager._skills

    @pytest.mark.asyncio
    async def test_register_skill(self, temp_skills_dir):
        """测试注册技能."""
        manager = SkillManager(temp_skills_dir)
        await manager.initialize()

        skill = SkillDefinition(
            name="新技能",
            version="1.0.0",
            description="新技能描述",
            trigger=TriggerConfig(type="manual"),
            actions=[],
        )

        manager.register_skill(skill, save=True)

        assert len(manager._skills) == 1
        assert manager.get_skill("新技能") == skill

    @pytest.mark.asyncio
    async def test_unregister_skill(self, temp_skills_dir):
        """测试注销技能."""
        manager = SkillManager(temp_skills_dir)

        skill = SkillDefinition(
            name="临时技能",
            version="1.0.0",
            description="临时技能",
            trigger=TriggerConfig(type="manual"),
            actions=[],
        )
        manager._loader.save_skill(skill)
        await manager.initialize()

        # 注销技能
        success = manager.unregister_skill("临时技能", delete=False)
        assert success is True
        assert manager.get_skill("临时技能") is None

    @pytest.mark.asyncio
    async def test_list_skills(self, temp_skills_dir):
        """测试获取技能列表."""
        manager = SkillManager(temp_skills_dir)

        # 创建多个技能
        for i in range(3):
            skill = SkillDefinition(
                name=f"技能{i}",
                version="1.0.0",
                description=f"测试{i}",
                trigger=TriggerConfig(type="manual"),
                actions=[],
                tags=["test"] if i % 2 == 0 else [],
                enabled=i % 2 == 0,
            )
            manager._loader.save_skill(skill)

        await manager.initialize()

        # 获取所有技能
        all_skills = manager.list_skills()
        assert len(all_skills) == 3

        # 按标签筛选
        tagged_skills = manager.list_skills(tag="test")
        assert len(tagged_skills) == 2

        # 按启用状态筛选
        enabled_skills = manager.list_skills(enabled=True)
        assert len(enabled_skills) == 2

    @pytest.mark.asyncio
    async def test_trigger_event(self, temp_skills_dir):
        """测试触发事件."""
        manager = SkillManager(temp_skills_dir)

        # 创建事件触发技能
        skill = SkillDefinition(
            name="事件技能",
            version="1.0.0",
            description="事件技能",
            trigger=TriggerConfig(type="event", event_type="test_event"),
            actions=[
                ActionConfig(type="create_task", params={"title": "测试任务"}),
            ],
            enabled=True,
        )
        manager._loader.save_skill(skill)

        await manager.initialize()

        # 触发事件
        results = await manager.trigger_event("test_event", {"data": "test"})
        assert len(results) == 1
        assert results[0]["skill"] == "事件技能"

    @pytest.mark.asyncio
    async def test_get_event_types(self, temp_skills_dir):
        """测试获取事件类型."""
        manager = SkillManager(temp_skills_dir)

        # 创建不同事件的技能
        skill1 = SkillDefinition(
            name="技能 1",
            version="1.0.0",
            description="技能 1",
            trigger=TriggerConfig(type="event", event_type="event_a"),
            actions=[],
        )
        skill2 = SkillDefinition(
            name="技能 2",
            version="1.0.0",
            description="技能 2",
            trigger=TriggerConfig(type="event", event_type="event_b"),
            actions=[],
        )
        manager._loader.save_skill(skill1)
        manager._loader.save_skill(skill2)

        await manager.initialize()

        event_types = manager.get_event_types()
        assert len(event_types) == 2
        assert "event_a" in event_types
        assert "event_b" in event_types

    @pytest.mark.asyncio
    async def test_get_skills_by_event(self, temp_skills_dir):
        """测试按事件获取技能."""
        manager = SkillManager(temp_skills_dir)

        skill1 = SkillDefinition(
            name="技能 1",
            version="1.0.0",
            description="技能 1",
            trigger=TriggerConfig(type="event", event_type="test_event"),
            actions=[],
        )
        skill2 = SkillDefinition(
            name="技能 2",
            version="1.0.0",
            description="技能 2",
            trigger=TriggerConfig(type="event", event_type="test_event"),
            actions=[],
        )
        manager._loader.save_skill(skill1)
        manager._loader.save_skill(skill2)

        await manager.initialize()

        skills = manager.get_skills_by_event("test_event")
        assert len(skills) == 2
