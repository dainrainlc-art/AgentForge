"""
AgentForge 技能基类
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional
from enum import Enum


class SkillStatus(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PENDING = "pending"
    NEEDS_REVIEW = "needs_review"


@dataclass
class SkillResult:
    status: SkillStatus
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    error: Optional[str] = None
    requires_action: Optional[str] = None


class BaseSkill(ABC):
    name: str
    description: str
    version: str = "1.0.0"
    required_permissions: list[str] = []
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._validate_config()
    
    def _validate_config(self) -> None:
        pass
    
    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> SkillResult:
        pass
    
    def validate_input(self, context: Dict[str, Any]) -> bool:
        return True
    
    def get_metadata(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "required_permissions": self.required_permissions,
        }
