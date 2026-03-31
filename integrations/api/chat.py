"""
Chat API Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from loguru import logger

from agentforge.core import AgentCore
from agentforge.memory import MemoryStore
from agentforge.llm import QianfanClient
from integrations.api.auth import verify_token_dependency


router = APIRouter()
security = HTTPBearer()


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    agent: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    agent: str
    model: str


class ConversationHistory(BaseModel):
    messages: List[Dict[str, Any]]
    total: int


agents: Dict[str, AgentCore] = {}
conversations: Dict[str, List[Dict[str, Any]]] = {}
conversation_counter = 0


def generate_conversation_id() -> str:
    global conversation_counter
    conversation_counter += 1
    return f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{conversation_counter:04d}"


async def get_or_create_agent(user_id: str, agent_type: str = "default") -> AgentCore:
    """Get or create agent for user"""
    agent_key = f"{user_id}_{agent_type}"
    
    if agent_key not in agents:
        memory_store = MemoryStore()
        await memory_store.initialize()
        
        llm_client = QianfanClient()
        
        agents[agent_key] = AgentCore(
            agent_id=f"agent_{agent_key}",
            name=f"AgentForge-{agent_type}",
            memory_store=memory_store,
            llm_client=llm_client
        )
        logger.info(f"Created new agent: {agent_key}")
    
    return agents[agent_key]


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    payload: dict = Depends(verify_token_dependency)
):
    """Send message and get response"""
    user_id = payload.get("user_id")
    
    agent_type = request.agent or "default"
    agent = await get_or_create_agent(user_id, agent_type)
    
    conversation_id = request.conversation_id or generate_conversation_id()
    
    if conversation_id not in conversations:
        conversations[conversation_id] = []
    
    conversations[conversation_id].append({
        "role": "user",
        "content": request.message,
        "timestamp": datetime.now().isoformat()
    })
    
    try:
        response = await agent.process_message(
            message=request.message,
            context=request.context
        )
        
        conversations[conversation_id].append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().isoformat()
        })
        
        return ChatResponse(
            response=response,
            conversation_id=conversation_id,
            agent=agent_type,
            model="glm-5"
        )
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/message", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    payload: dict = Depends(verify_token_dependency)
):
    """Send message to agent and get response (alias for /chat)"""
    return await chat(request, payload)


@router.get("/history", response_model=ConversationHistory)
async def get_history(
    conversation_id: Optional[str] = None,
    payload: dict = Depends(verify_token_dependency)
):
    """Get conversation history"""
    if conversation_id and conversation_id in conversations:
        return ConversationHistory(
            messages=conversations[conversation_id],
            total=len(conversations[conversation_id])
        )
    
    user_id = payload.get("user_id")
    agent_key = f"{user_id}_default"
    
    if agent_key not in agents:
        return ConversationHistory(messages=[], total=0)
    
    agent = agents[agent_key]
    
    return ConversationHistory(
        messages=agent.conversation_history,
        total=len(agent.conversation_history)
    )


@router.delete("/history")
async def clear_history(
    conversation_id: Optional[str] = None,
    payload: dict = Depends(verify_token_dependency)
):
    """Clear conversation history"""
    if conversation_id and conversation_id in conversations:
        del conversations[conversation_id]
        logger.info(f"Cleared conversation: {conversation_id}")
        return {"status": "cleared", "conversation_id": conversation_id}
    
    user_id = payload.get("user_id")
    
    for key in list(agents.keys()):
        if key.startswith(user_id):
            agents[key].conversation_history = []
    
    logger.info(f"Cleared history for user: {user_id}")
    
    return {"status": "cleared"}


@router.get("/status")
async def get_agent_status(payload: dict = Depends(verify_token_dependency)):
    """Get agent status"""
    user_id = payload.get("user_id")
    
    user_agents = {k: v for k, v in agents.items() if k.startswith(user_id)}
    
    if not user_agents:
        return {"status": "not_initialized", "agents": []}
    
    return {
        "status": "active",
        "agents": [
            {
                "agent_id": agent.agent_id,
                "name": agent.name,
                "conversation_length": len(agent.conversation_history)
            }
            for agent in user_agents.values()
        ]
    }
