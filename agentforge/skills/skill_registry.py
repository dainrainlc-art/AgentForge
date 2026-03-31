"""
AgentForge Skill Registry System
"""
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from pydantic import BaseModel, Field
from loguru import logger
from abc import ABC, abstractmethod
import asyncio


class SkillParameter(BaseModel):
    """Skill parameter definition"""
    name: str
    type: str
    description: str
    required: bool = True
    default: Optional[Any] = None


class SkillMetadata(BaseModel):
    """Skill metadata"""
    name: str
    description: str
    category: str
    version: str = "1.0.0"
    author: str = "AgentForge"
    tags: List[str] = Field(default_factory=list)
    parameters: List[SkillParameter] = Field(default_factory=list)


class SkillResult(BaseModel):
    """Skill execution result"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class Skill(ABC):
    """Base class for all skills"""
    
    def __init__(self, metadata: SkillMetadata):
        self.metadata = metadata
        self._enabled = True
    
    @abstractmethod
    async def execute(self, **kwargs) -> SkillResult:
        """Execute the skill"""
        pass
    
    def validate_parameters(self, kwargs: Dict[str, Any]) -> bool:
        """Validate input parameters"""
        for param in self.metadata.parameters:
            if param.required and param.name not in kwargs:
                raise ValueError(f"Missing required parameter: {param.name}")
        return True
    
    def enable(self) -> None:
        """Enable the skill"""
        self._enabled = True
    
    def disable(self) -> None:
        """Disable the skill"""
        self._enabled = False
    
    @property
    def is_enabled(self) -> bool:
        return self._enabled


class FiverrOrderSkill(Skill):
    """Skill for managing Fiverr orders"""
    
    def __init__(self):
        metadata = SkillMetadata(
            name="fiverr_order_manager",
            description="Manage Fiverr orders and communications",
            category="business",
            tags=["fiverr", "orders", "freelance"],
            parameters=[
                SkillParameter(name="action", type="str", description="Action to perform", required=True),
                SkillParameter(name="order_id", type="str", description="Order ID", required=False),
                SkillParameter(name="message", type="str", description="Message content", required=False)
            ]
        )
        super().__init__(metadata)
    
    async def execute(self, **kwargs) -> SkillResult:
        start_time = datetime.now()
        try:
            self.validate_parameters(kwargs)
            action = kwargs.get("action")
            
            if action == "list":
                result_data = {"orders": [], "total": 0, "message": "Order list retrieved"}
            elif action == "get":
                result_data = {"order": {}, "message": "Order details retrieved"}
            elif action == "message":
                result_data = {"message_sent": True, "message": "Message sent successfully"}
            else:
                result_data = {"action": action, "message": "Action executed"}
            
            return SkillResult(
                success=True,
                data=result_data,
                execution_time=(datetime.now() - start_time).total_seconds()
            )
        except Exception as e:
            logger.error(f"FiverrOrderSkill error: {e}")
            return SkillResult(
                success=False,
                error=str(e),
                execution_time=(datetime.now() - start_time).total_seconds()
            )


class SocialMediaSkill(Skill):
    """Skill for social media management"""
    
    def __init__(self):
        metadata = SkillMetadata(
            name="social_media_publisher",
            description="Publish content to social media platforms",
            category="marketing",
            tags=["social", "twitter", "linkedin", "youtube"],
            parameters=[
                SkillParameter(name="platform", type="str", description="Target platform", required=True),
                SkillParameter(name="content", type="str", description="Content to publish", required=True),
                SkillParameter(name="schedule_time", type="str", description="Schedule time", required=False)
            ]
        )
        super().__init__(metadata)
    
    async def execute(self, **kwargs) -> SkillResult:
        start_time = datetime.now()
        try:
            self.validate_parameters(kwargs)
            platform = kwargs.get("platform")
            content = kwargs.get("content")
            
            result_data = {
                "platform": platform,
                "content": content[:100] + "..." if len(content) > 100 else content,
                "status": "published",
                "published_at": datetime.now().isoformat()
            }
            
            return SkillResult(
                success=True,
                data=result_data,
                execution_time=(datetime.now() - start_time).total_seconds()
            )
        except Exception as e:
            logger.error(f"SocialMediaSkill error: {e}")
            return SkillResult(
                success=False,
                error=str(e),
                execution_time=(datetime.now() - start_time).total_seconds()
            )


class KnowledgeManagementSkill(Skill):
    """Skill for knowledge base management"""
    
    def __init__(self):
        metadata = SkillMetadata(
            name="knowledge_manager",
            description="Manage knowledge base and documentation",
            category="knowledge",
            tags=["knowledge", "documentation", "notion", "obsidian"],
            parameters=[
                SkillParameter(name="action", type="str", description="Action to perform", required=True),
                SkillParameter(name="title", type="str", description="Document title", required=False),
                SkillParameter(name="content", type="str", description="Document content", required=False),
                SkillParameter(name="source", type="str", description="Knowledge source", required=False)
            ]
        )
        super().__init__(metadata)
    
    async def execute(self, **kwargs) -> SkillResult:
        start_time = datetime.now()
        try:
            self.validate_parameters(kwargs)
            action = kwargs.get("action")
            
            if action == "create":
                result_data = {"created": True, "message": "Document created"}
            elif action == "search":
                result_data = {"results": [], "total": 0}
            elif action == "sync":
                result_data = {"synced": True, "message": "Knowledge base synced"}
            else:
                result_data = {"action": action, "message": "Action executed"}
            
            return SkillResult(
                success=True,
                data=result_data,
                execution_time=(datetime.now() - start_time).total_seconds()
            )
        except Exception as e:
            logger.error(f"KnowledgeManagementSkill error: {e}")
            return SkillResult(
                success=False,
                error=str(e),
                execution_time=(datetime.now() - start_time).total_seconds()
            )


class ContentCreationSkill(Skill):
    """Skill for content creation"""
    
    def __init__(self):
        metadata = SkillMetadata(
            name="content_creator",
            description="Create content for various purposes",
            category="creative",
            tags=["content", "writing", "creative"],
            parameters=[
                SkillParameter(name="type", type="str", description="Content type", required=True),
                SkillParameter(name="topic", type="str", description="Content topic", required=True),
                SkillParameter(name="style", type="str", description="Writing style", required=False, default="professional"),
                SkillParameter(name="length", type="int", description="Content length", required=False, default=500)
            ]
        )
        super().__init__(metadata)
    
    async def execute(self, **kwargs) -> SkillResult:
        start_time = datetime.now()
        try:
            self.validate_parameters(kwargs)
            
            # 使用参数默认值
            style = kwargs.get("style")
            if style is None:
                # 查找默认值
                for param in self.metadata.parameters:
                    if param.name == "style":
                        style = param.default
                        break
            
            length = kwargs.get("length")
            if length is None:
                for param in self.metadata.parameters:
                    if param.name == "length":
                        length = param.default
                        break
            
            result_data = {
                "content": f"Generated content for {kwargs.get('topic')}",
                "type": kwargs.get("type"),
                "style": style,
                "word_count": length or 500
            }
            
            return SkillResult(
                success=True,
                data=result_data,
                execution_time=(datetime.now() - start_time).total_seconds()
            )
        except Exception as e:
            logger.error(f"ContentCreationSkill error: {e}")
            return SkillResult(
                success=False,
                error=str(e),
                execution_time=(datetime.now() - start_time).total_seconds()
            )


class SkillRegistry:
    """Registry for managing skills"""
    
    def __init__(self):
        self._skills: Dict[str, Skill] = {}
        self._categories: Dict[str, List[str]] = {}
        self._initialize_default_skills()
    
    def _initialize_default_skills(self) -> None:
        """Initialize default skills"""
        self.register(FiverrOrderSkill())
        self.register(SocialMediaSkill())
        self.register(KnowledgeManagementSkill())
        self.register(ContentCreationSkill())
        logger.info(f"Initialized {len(self._skills)} default skills")
    
    def register(self, skill: Skill) -> None:
        """Register a skill"""
        name = skill.metadata.name
        if name in self._skills:
            logger.warning(f"Skill {name} already registered, overwriting")
        
        self._skills[name] = skill
        
        category = skill.metadata.category
        if category not in self._categories:
            self._categories[category] = []
        if name not in self._categories[category]:
            self._categories[category].append(name)
        
        logger.info(f"Registered skill: {name} (category: {category})")
    
    def unregister(self, name: str) -> bool:
        """Unregister a skill"""
        if name not in self._skills:
            return False
        
        skill = self._skills[name]
        category = skill.metadata.category
        
        if category in self._categories and name in self._categories[category]:
            self._categories[category].remove(name)
        
        del self._skills[name]
        logger.info(f"Unregistered skill: {name}")
        return True
    
    def get(self, name: str) -> Optional[Skill]:
        """Get a skill by name"""
        return self._skills.get(name)
    
    def list_skills(self, category: Optional[str] = None) -> List[str]:
        """List all skills or skills in a category"""
        if category:
            return self._categories.get(category, [])
        return list(self._skills.keys())
    
    def list_categories(self) -> List[str]:
        """List all categories"""
        return list(self._categories.keys())
    
    async def execute(self, name: str, **kwargs) -> SkillResult:
        """Execute a skill by name"""
        skill = self.get(name)
        if not skill:
            return SkillResult(
                success=False,
                error=f"Skill not found: {name}"
            )
        
        if not skill.is_enabled:
            return SkillResult(
                success=False,
                error=f"Skill is disabled: {name}"
            )
        
        logger.info(f"Executing skill: {name}")
        return await skill.execute(**kwargs)
    
    def enable_skill(self, name: str) -> bool:
        """Enable a skill"""
        skill = self.get(name)
        if skill:
            skill.enable()
            return True
        return False
    
    def disable_skill(self, name: str) -> bool:
        """Disable a skill"""
        skill = self.get(name)
        if skill:
            skill.disable()
            return True
        return False
    
    def get_skill_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get skill information"""
        skill = self.get(name)
        if not skill:
            return None
        
        return {
            "name": skill.metadata.name,
            "description": skill.metadata.description,
            "category": skill.metadata.category,
            "version": skill.metadata.version,
            "tags": skill.metadata.tags,
            "parameters": [p.model_dump() for p in skill.metadata.parameters],
            "enabled": skill.is_enabled
        }
