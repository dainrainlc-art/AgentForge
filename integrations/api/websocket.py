"""
WebSocket API for real-time chat
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
from loguru import logger
import json
import asyncio

from agentforge.core import AgentCore
from agentforge.memory import MemoryStore
from agentforge.llm import QianfanClient


router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.agents: Dict[str, AgentCore] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"WebSocket connected: {user_id}")
    
    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.agents:
            del self.agents[user_id]
        logger.info(f"WebSocket disconnected: {user_id}")
    
    async def get_agent(self, user_id: str) -> AgentCore:
        if user_id not in self.agents:
            memory_store = MemoryStore()
            await memory_store.initialize()
            
            llm_client = QianfanClient()
            
            self.agents[user_id] = AgentCore(
                agent_id=f"ws_agent_{user_id}",
                name=f"AgentForge-WS-{user_id}",
                memory_store=memory_store,
                llm_client=llm_client
            )
        
        return self.agents[user_id]
    
    async def send_message(self, user_id: str, message: dict):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(message)
    
    async def broadcast(self, message: dict):
        for user_id in self.active_connections:
            await self.send_message(user_id, message)


manager = ConnectionManager()


@router.websocket("/ws/chat/{user_id}")
async def websocket_chat(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    
    try:
        await manager.send_message(user_id, {
            "type": "connected",
            "user_id": user_id,
            "message": "WebSocket connected successfully"
        })
        
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                await manager.send_message(user_id, {
                    "type": "error",
                    "message": "Invalid JSON format"
                })
                continue
            
            msg_type = message.get("type", "chat")
            
            if msg_type == "chat":
                content = message.get("content", "")
                
                if not content:
                    await manager.send_message(user_id, {
                        "type": "error",
                        "message": "Empty message content"
                    })
                    continue
                
                await manager.send_message(user_id, {
                    "type": "typing",
                    "status": True
                })
                
                try:
                    agent = await manager.get_agent(user_id)
                    response = await agent.process_message(content)
                    
                    await manager.send_message(user_id, {
                        "type": "chat",
                        "role": "assistant",
                        "content": response,
                        "agent_id": agent.agent_id
                    })
                except Exception as e:
                    logger.error(f"Chat error: {e}")
                    await manager.send_message(user_id, {
                        "type": "error",
                        "message": str(e)
                    })
                finally:
                    await manager.send_message(user_id, {
                        "type": "typing",
                        "status": False
                    })
            
            elif msg_type == "ping":
                await manager.send_message(user_id, {
                    "type": "pong",
                    "timestamp": asyncio.get_event_loop().time()
                })
            
            elif msg_type == "clear":
                if user_id in manager.agents:
                    manager.agents[user_id].conversation_history = []
                
                await manager.send_message(user_id, {
                    "type": "cleared",
                    "message": "Conversation history cleared"
                })
    
    except WebSocketDisconnect:
        manager.disconnect(user_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(user_id)


@router.websocket("/ws/events/{user_id}")
async def websocket_events(websocket: WebSocket, user_id: str):
    await websocket.accept()
    logger.info(f"Event WebSocket connected: {user_id}")
    
    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                event = json.loads(data)
                event_type = event.get("type", "unknown")
                
                if event_type == "subscribe":
                    channels = event.get("channels", [])
                    await websocket.send_json({
                        "type": "subscribed",
                        "channels": channels
                    })
                
                elif event_type == "ping":
                    await websocket.send_json({
                        "type": "pong"
                    })
            
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON"
                })
    
    except WebSocketDisconnect:
        logger.info(f"Event WebSocket disconnected: {user_id}")
