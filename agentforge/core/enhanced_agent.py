"""
Enhanced Agent Core with Self-Evolution
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from loguru import logger

from agentforge.memory import MemoryStore
from agentforge.llm import QianfanClient, model_router
from agentforge.core.self_evolution import SelfEvolutionEngine
from agentforge.skills import SkillRegistry


class EnhancedAgentCore:
    """Enhanced Agent with self-evolution capabilities"""
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        memory_store: MemoryStore,
        llm_client: QianfanClient,
        skills: Optional[List[str]] = None
    ):
        self.agent_id = agent_id
        self.name = name
        self.memory_store = memory_store
        self.llm_client = llm_client
        
        self.skills = skills or []
        self.skill_registry = SkillRegistry()
        
        self.conversation_history: List[Dict[str, Any]] = []
        self.created_at = datetime.now()
        
        self._evolution_engine = SelfEvolutionEngine(memory_store, llm_client)
        
        self._model_preference: Optional[str] = None
        
        logger.info(f"EnhancedAgentCore initialized: {self.agent_id}")
    
    async def process_message(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        task_type: str = "default"
    ) -> str:
        """Process message with intelligent model routing"""
        start_time = datetime.now()
        
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
        
        try:
            response = await model_router.chat_with_failover(
                message=message,
                task_type=task_type,
                context=context,
                memories=relevant_memories,
                history=self.conversation_history,
                prefer_model=self._model_preference
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
            
            self._record_task(
                task_type=task_type,
                description=message[:100],
                result=response[:100],
                success=True
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            
            self._evolution_engine.log_error(e, {
                "message": message[:100],
                "context": context
            })
            
            self._record_task(
                task_type=task_type,
                description=message[:100],
                result=str(e)[:100],
                success=False
            )
            
            raise
    
    async def execute_skill(
        self,
        skill_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a registered skill"""
        skill = self.skill_registry.get_skill(skill_name)
        
        if not skill:
            raise ValueError(f"Skill not found: {skill_name}")
        
        logger.info(f"Executing skill: {skill_name}")
        
        try:
            result = await skill.execute(
                agent=self,
                parameters=parameters
            )
            
            self._record_task(
                task_type="skill",
                description=f"Skill: {skill_name}",
                result=str(result)[:100],
                success=True
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Skill execution failed: {e}")
            
            self._record_task(
                task_type="skill",
                description=f"Skill: {skill_name}",
                result=str(e)[:100],
                success=False
            )
            
            raise
    
    def set_model_preference(self, model: str) -> None:
        """Set preferred model for this agent"""
        self._model_preference = model
        logger.info(f"Model preference set to: {model}")
    
    async def start_evolution(self) -> None:
        """Start the self-evolution engine"""
        await self._evolution_engine.start()
    
    async def stop_evolution(self) -> None:
        """Stop the self-evolution engine"""
        await self._evolution_engine.stop()
    
    async def run_evolution_cycle(self) -> Dict[str, Any]:
        """Run a complete evolution cycle manually"""
        return await self._evolution_engine.run_all()
    
    def _record_task(
        self,
        task_type: str,
        description: str,
        result: str,
        success: bool
    ) -> None:
        """Record task for evolution review"""
        self._evolution_engine.task_reviewer.record_task_completion(
            task_id=f"{self.agent_id}_{datetime.now().timestamp()}",
            task_type=task_type,
            description=description,
            result=result,
            success=success
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "conversation_count": len(self.conversation_history),
            "skills": self.skills,
            "model_preference": self._model_preference,
            "evolution_running": self._evolution_engine._running,
            "status": "active"
        }
    
    def clear_history(self) -> None:
        """Clear conversation history"""
        self.conversation_history = []
        logger.info(f"Conversation history cleared for {self.agent_id}")
