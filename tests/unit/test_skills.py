"""
AgentForge Skill Registry Unit Tests
"""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock

from agentforge.skills.skill_registry import (
    Skill,
    SkillParameter,
    SkillMetadata,
    SkillResult,
    SkillRegistry,
    FiverrOrderSkill,
    SocialMediaSkill,
    KnowledgeManagementSkill,
    ContentCreationSkill,
)


class TestSkillParameter:
    def test_skill_parameter_creation(self):
        param = SkillParameter(
            name="test_param",
            type="str",
            description="Test parameter",
            required=True
        )
        assert param.name == "test_param"
        assert param.type == "str"
        assert param.description == "Test parameter"
        assert param.required is True
        assert param.default is None

    def test_skill_parameter_with_default(self):
        param = SkillParameter(
            name="optional_param",
            type="int",
            description="Optional parameter",
            required=False,
            default=10
        )
        assert param.required is False
        assert param.default == 10


class TestSkillMetadata:
    def test_skill_metadata_creation(self):
        metadata = SkillMetadata(
            name="test_skill",
            description="Test skill description",
            category="test",
            version="1.0.0",
            author="TestAuthor",
            tags=["test", "unit"]
        )
        assert metadata.name == "test_skill"
        assert metadata.description == "Test skill description"
        assert metadata.category == "test"
        assert metadata.version == "1.0.0"
        assert metadata.author == "TestAuthor"
        assert metadata.tags == ["test", "unit"]

    def test_skill_metadata_default_values(self):
        metadata = SkillMetadata(
            name="test_skill",
            description="Test description",
            category="test"
        )
        assert metadata.version == "1.0.0"
        assert metadata.author == "AgentForge"
        assert metadata.tags == []
        assert metadata.parameters == []


class TestSkillResult:
    def test_success_result(self):
        result = SkillResult(
            success=True,
            data={"key": "value"},
            execution_time=0.5
        )
        assert result.success is True
        assert result.data == {"key": "value"}
        assert result.error is None
        assert result.execution_time == 0.5

    def test_error_result(self):
        result = SkillResult(
            success=False,
            error="Something went wrong"
        )
        assert result.success is False
        assert result.data is None
        assert result.error == "Something went wrong"

    def test_timestamp_auto_generated(self):
        result = SkillResult(success=True)
        assert result.timestamp is not None
        datetime.fromisoformat(result.timestamp)


class MockSkill(Skill):
    def __init__(self, metadata=None):
        if metadata is None:
            metadata = SkillMetadata(
                name="mock_skill",
                description="Mock skill for testing",
                category="test",
                parameters=[
                    SkillParameter(name="required_param", type="str", description="Required", required=True),
                    SkillParameter(name="optional_param", type="int", description="Optional", required=False, default=5)
                ]
            )
        super().__init__(metadata)

    async def execute(self, **kwargs):
        return SkillResult(success=True, data=kwargs)


class TestSkill:
    @pytest.fixture
    def skill(self):
        return MockSkill()

    def test_skill_initialization(self, skill):
        assert skill.metadata.name == "mock_skill"
        assert skill.is_enabled is True

    def test_enable_disable(self, skill):
        skill.disable()
        assert skill.is_enabled is False
        
        skill.enable()
        assert skill.is_enabled is True

    def test_validate_parameters_success(self, skill):
        result = skill.validate_parameters({"required_param": "value"})
        assert result is True

    def test_validate_parameters_missing_required(self, skill):
        with pytest.raises(ValueError, match="Missing required parameter"):
            skill.validate_parameters({"optional_param": 10})

    def test_validate_parameters_with_optional_only(self, skill):
        with pytest.raises(ValueError, match="Missing required parameter: required_param"):
            skill.validate_parameters({"optional_param": 10})

    @pytest.mark.asyncio
    async def test_execute(self, skill):
        result = await skill.execute(required_param="test", optional_param=20)
        assert result.success is True
        assert result.data["required_param"] == "test"
        assert result.data["optional_param"] == 20


class TestFiverrOrderSkill:
    @pytest.fixture
    def skill(self):
        return FiverrOrderSkill()

    def test_skill_metadata(self, skill):
        assert skill.metadata.name == "fiverr_order_manager"
        assert skill.metadata.category == "business"
        assert "fiverr" in skill.metadata.tags

    @pytest.mark.asyncio
    async def test_list_orders(self, skill):
        result = await skill.execute(action="list")
        assert result.success is True
        assert "orders" in result.data
        assert "total" in result.data

    @pytest.mark.asyncio
    async def test_get_order(self, skill):
        result = await skill.execute(action="get", order_id="12345")
        assert result.success is True
        assert "order" in result.data

    @pytest.mark.asyncio
    async def test_send_message(self, skill):
        result = await skill.execute(action="message", order_id="12345", message="Hello!")
        assert result.success is True
        assert result.data["message_sent"] is True

    @pytest.mark.asyncio
    async def test_unknown_action(self, skill):
        result = await skill.execute(action="unknown_action")
        assert result.success is True
        assert result.data["action"] == "unknown_action"

    @pytest.mark.asyncio
    async def test_missing_required_parameter(self, skill):
        result = await skill.execute(order_id="12345")
        assert result.success is False
        assert "Missing required parameter: action" in result.error


class TestSocialMediaSkill:
    @pytest.fixture
    def skill(self):
        return SocialMediaSkill()

    def test_skill_metadata(self, skill):
        assert skill.metadata.name == "social_media_publisher"
        assert skill.metadata.category == "marketing"
        assert "twitter" in skill.metadata.tags

    @pytest.mark.asyncio
    async def test_publish_to_twitter(self, skill):
        result = await skill.execute(platform="twitter", content="Hello Twitter!")
        assert result.success is True
        assert result.data["platform"] == "twitter"
        assert result.data["status"] == "published"

    @pytest.mark.asyncio
    async def test_publish_to_linkedin(self, skill):
        result = await skill.execute(platform="linkedin", content="Hello LinkedIn!")
        assert result.success is True
        assert result.data["platform"] == "linkedin"

    @pytest.mark.asyncio
    async def test_publish_with_schedule(self, skill):
        result = await skill.execute(
            platform="twitter",
            content="Scheduled post",
            schedule_time="2024-12-31T12:00:00"
        )
        assert result.success is True

    @pytest.mark.asyncio
    async def test_long_content_truncation(self, skill):
        long_content = "x" * 200
        result = await skill.execute(platform="twitter", content=long_content)
        assert result.success is True
        assert len(result.data["content"]) < len(long_content)

    @pytest.mark.asyncio
    async def test_missing_platform(self, skill):
        result = await skill.execute(content="Hello")
        assert result.success is False
        assert "Missing required parameter: platform" in result.error


class TestKnowledgeManagementSkill:
    @pytest.fixture
    def skill(self):
        return KnowledgeManagementSkill()

    def test_skill_metadata(self, skill):
        assert skill.metadata.name == "knowledge_manager"
        assert skill.metadata.category == "knowledge"
        assert "notion" in skill.metadata.tags

    @pytest.mark.asyncio
    async def test_create_document(self, skill):
        result = await skill.execute(
            action="create",
            title="Test Document",
            content="Test content"
        )
        assert result.success is True
        assert result.data["created"] is True

    @pytest.mark.asyncio
    async def test_search_documents(self, skill):
        result = await skill.execute(action="search", title="test")
        assert result.success is True
        assert "results" in result.data
        assert "total" in result.data

    @pytest.mark.asyncio
    async def test_sync_knowledge_base(self, skill):
        result = await skill.execute(action="sync", source="notion")
        assert result.success is True
        assert result.data["synced"] is True

    @pytest.mark.asyncio
    async def test_unknown_action(self, skill):
        result = await skill.execute(action="delete", title="test")
        assert result.success is True


class TestContentCreationSkill:
    @pytest.fixture
    def skill(self):
        return ContentCreationSkill()

    def test_skill_metadata(self, skill):
        assert skill.metadata.name == "content_creator"
        assert skill.metadata.category == "creative"
        assert "writing" in skill.metadata.tags

    @pytest.mark.asyncio
    async def test_create_blog_post(self, skill):
        result = await skill.execute(
            type="blog",
            topic="AI Technology",
            style="professional",
            length=1000
        )
        assert result.success is True
        assert result.data["type"] == "blog"
        assert result.data["style"] == "professional"
        assert result.data["word_count"] == 1000

    @pytest.mark.asyncio
    async def test_create_with_defaults(self, skill):
        result = await skill.execute(type="article", topic="Test Topic")
        assert result.success is True
        assert result.data["style"] == "professional"
        assert result.data["word_count"] == 500

    @pytest.mark.asyncio
    async def test_missing_required_parameters(self, skill):
        result = await skill.execute(type="blog")
        assert result.success is False
        assert "Missing required parameter: topic" in result.error


class TestSkillRegistry:
    @pytest.fixture
    def registry(self):
        return SkillRegistry()

    def test_initialization(self, registry):
        assert len(registry.list_skills()) == 4
        assert "fiverr_order_manager" in registry.list_skills()
        assert "social_media_publisher" in registry.list_skills()
        assert "knowledge_manager" in registry.list_skills()
        assert "content_creator" in registry.list_skills()

    def test_list_categories(self, registry):
        categories = registry.list_categories()
        assert "business" in categories
        assert "marketing" in categories
        assert "knowledge" in categories
        assert "creative" in categories

    def test_list_skills_by_category(self, registry):
        business_skills = registry.list_skills(category="business")
        assert "fiverr_order_manager" in business_skills

        marketing_skills = registry.list_skills(category="marketing")
        assert "social_media_publisher" in marketing_skills

    def test_get_skill(self, registry):
        skill = registry.get("fiverr_order_manager")
        assert skill is not None
        assert skill.metadata.name == "fiverr_order_manager"

    def test_get_nonexistent_skill(self, registry):
        skill = registry.get("nonexistent_skill")
        assert skill is None

    def test_register_new_skill(self, registry):
        new_skill = MockSkill()
        registry.register(new_skill)
        
        assert "mock_skill" in registry.list_skills()
        assert registry.get("mock_skill") is not None

    def test_register_duplicate_skill(self, registry):
        skill1 = MockSkill()
        skill2 = MockSkill()
        
        registry.register(skill1)
        registry.register(skill2)
        
        assert registry.get("mock_skill") is not None

    def test_unregister_skill(self, registry):
        new_skill = MockSkill()
        registry.register(new_skill)
        
        result = registry.unregister("mock_skill")
        assert result is True
        assert registry.get("mock_skill") is None

    def test_unregister_nonexistent_skill(self, registry):
        result = registry.unregister("nonexistent_skill")
        assert result is False

    @pytest.mark.asyncio
    async def test_execute_skill(self, registry):
        result = await registry.execute(
            "fiverr_order_manager",
            action="list"
        )
        assert result.success is True
        assert "orders" in result.data

    @pytest.mark.asyncio
    async def test_execute_nonexistent_skill(self, registry):
        result = await registry.execute("nonexistent_skill")
        assert result.success is False
        assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_disabled_skill(self, registry):
        registry.disable_skill("fiverr_order_manager")
        result = await registry.execute("fiverr_order_manager", action="list")
        assert result.success is False
        assert "disabled" in result.error.lower()
        
        registry.enable_skill("fiverr_order_manager")

    def test_enable_skill(self, registry):
        registry.disable_skill("fiverr_order_manager")
        assert registry.get("fiverr_order_manager").is_enabled is False
        
        result = registry.enable_skill("fiverr_order_manager")
        assert result is True
        assert registry.get("fiverr_order_manager").is_enabled is True

    def test_disable_skill(self, registry):
        result = registry.disable_skill("fiverr_order_manager")
        assert result is True
        assert registry.get("fiverr_order_manager").is_enabled is False
        
        registry.enable_skill("fiverr_order_manager")

    def test_enable_nonexistent_skill(self, registry):
        result = registry.enable_skill("nonexistent_skill")
        assert result is False

    def test_disable_nonexistent_skill(self, registry):
        result = registry.disable_skill("nonexistent_skill")
        assert result is False

    def test_get_skill_info(self, registry):
        info = registry.get_skill_info("fiverr_order_manager")
        assert info is not None
        assert info["name"] == "fiverr_order_manager"
        assert info["category"] == "business"
        assert info["enabled"] is True
        assert len(info["parameters"]) > 0

    def test_get_skill_info_nonexistent(self, registry):
        info = registry.get_skill_info("nonexistent_skill")
        assert info is None


class TestSkillResultExecutionTime:
    @pytest.mark.asyncio
    async def test_execution_time_recorded(self):
        skill = FiverrOrderSkill()
        result = await skill.execute(action="list")
        assert result.execution_time >= 0

    @pytest.mark.asyncio
    async def test_execution_time_on_error(self):
        skill = MockSkill()
        try:
            await skill.execute()
        except ValueError:
            pass


class TestSkillRegistryIntegration:
    @pytest.fixture
    def registry(self):
        return SkillRegistry()

    @pytest.mark.asyncio
    async def test_full_skill_lifecycle(self, registry):
        custom_skill = MockSkill()
        
        registry.register(custom_skill)
        assert "mock_skill" in registry.list_skills()
        
        result = await registry.execute("mock_skill", required_param="test")
        assert result.success is True
        
        registry.disable_skill("mock_skill")
        result = await registry.execute("mock_skill", required_param="test")
        assert result.success is False
        
        registry.enable_skill("mock_skill")
        
        registry.unregister("mock_skill")
        assert "mock_skill" not in registry.list_skills()

    @pytest.mark.asyncio
    async def test_multiple_skills_execution(self, registry):
        results = await asyncio.gather(
            registry.execute("fiverr_order_manager", action="list"),
            registry.execute("social_media_publisher", platform="twitter", content="Test"),
            registry.execute("knowledge_manager", action="search"),
            registry.execute("content_creator", type="blog", topic="Test")
        )
        
        assert all(r.success for r in results)


class TestSkillParameterValidation:
    def test_parameter_model_dump(self):
        param = SkillParameter(
            name="test",
            type="str",
            description="Test param",
            required=True
        )
        dump = param.model_dump()
        assert dump["name"] == "test"
        assert dump["type"] == "str"
        assert dump["required"] is True


class TestSkillMetadataParameters:
    def test_parameters_in_metadata(self):
        params = [
            SkillParameter(name="p1", type="str", description="P1", required=True),
            SkillParameter(name="p2", type="int", description="P2", required=False)
        ]
        metadata = SkillMetadata(
            name="test",
            description="Test",
            category="test",
            parameters=params
        )
        assert len(metadata.parameters) == 2
        assert metadata.parameters[0].name == "p1"
        assert metadata.parameters[1].name == "p2"
