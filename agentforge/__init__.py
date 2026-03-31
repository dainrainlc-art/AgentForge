"""
AgentForge Package
"""
from agentforge.config import settings
from agentforge.core import AgentCore, EnhancedAgentCore, TaskPlanner, SelfEvolutionEngine
from agentforge.llm import QianfanClient
from agentforge.memory import MemoryStore
from agentforge.skills import SkillRegistry, Skill

__version__ = "1.0.0"

__all__ = [
    "settings",
    "AgentCore",
    "EnhancedAgentCore",
    "TaskPlanner",
    "SelfEvolutionEngine",
    "QianfanClient",
    "MemoryStore",
    "SkillRegistry",
    "Skill"
]
