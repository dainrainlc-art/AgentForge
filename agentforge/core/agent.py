"""
AgentForge Core Agent Module
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from loguru import logger
from agentforge.config import settings
from agentforge.memory.memory_store import MemoryStore
from agentforge.llm.qianfan_client import QianfanClient


class AgentCore:
    """Core Agent implementation for AgentForge"""
    
    def __init__(
        self,
        agent_id: str,
        name: str = "AgentForge",
        memory_store: Optional[MemoryStore] = None,
        llm_client: Optional[QianfanClient] = None
    ):
        self.agent_id = agent_id
        self.name = name
        self.memory_store = memory_store or MemoryStore()
        self.llm_client = llm_client or QianfanClient()
        self.created_at = datetime.now()
        self.conversation_history: List[Dict[str, Any]] = []
        
        logger.info(f"AgentCore initialized: {self.agent_id}")
    
    async def process_message(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Process incoming message and generate response"""
        logger.info(f"Processing message for agent {self.agent_id}")
        
        self.conversation_history.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        
        relevant_memories = await self.memory_store.search_memories(
            query=message,
            limit=5
        )
        
        response = await self.llm_client.chat(
            message=message,
            context=context,
            memories=relevant_memories,
            history=self.conversation_history[-10:]
        )
        
        self.conversation_history.append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().isoformat()
        })
        
        await self.memory_store.store_memory(
            content=f"User: {message}\nAssistant: {response}",
            memory_type="conversation"
        )
        
        return response
    
    async def execute_skill(
        self,
        skill_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a skill by name"""
        logger.info(f"Executing skill: {skill_name}")
        
        return {
            "skill": skill_name,
            "status": "executed",
            "parameters": parameters,
            "result": "Skill execution placeholder"
        }
    
    async def learn(self, experience: str, feedback: Optional[str] = None) -> None:
        """Store learning experience for self-evolution"""
        logger.info(f"Agent {self.agent_id} learning from experience")
        
        await self.memory_store.store_memory(
            content=experience,
            memory_type="learning",
            metadata={"feedback": feedback} if feedback else None
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "conversation_count": len(self.conversation_history),
            "status": "active"
        }
