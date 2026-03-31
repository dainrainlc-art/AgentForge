"""
AgentForge n8n Integration Module
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
import httpx
from loguru import logger

from agentforge.config import settings


class WorkflowDefinition(BaseModel):
    """n8n workflow definition"""
    id: Optional[str] = None
    name: str
    description: str = ""
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    connections: Dict[str, Any] = Field(default_factory=dict)
    active: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class WorkflowExecution(BaseModel):
    """n8n workflow execution result"""
    execution_id: str
    workflow_id: str
    status: str
    started_at: str
    finished_at: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class N8NClient:
    """Client for n8n workflow engine integration"""
    
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None
    ):
        self.host = host or settings.n8n_host
        self.port = port or settings.n8n_port
        self.base_url = f"http://{self.host}:{self.port}"
        self.username = username or getattr(settings, 'n8n_basic_auth_user', 'admin')
        self.password = password or getattr(settings, 'n8n_basic_auth_password', 'admin')
        self._initialized = False
    
    async def initialize(self) -> bool:
        """Initialize connection to n8n"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/healthz",
                    auth=(self.username, self.password)
                )
                if response.status_code == 200:
                    self._initialized = True
                    logger.info(f"Connected to n8n at {self.base_url}")
                    return True
        except Exception as e:
            logger.warning(f"Failed to connect to n8n: {e}")
        return False
    
    async def list_workflows(self) -> List[Dict[str, Any]]:
        """List all workflows"""
        if not self._initialized:
            await self.initialize()
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/workflows",
                    auth=(self.username, self.password)
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("data", [])
        except Exception as e:
            logger.error(f"Failed to list workflows: {e}")
        return []
    
    async def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow by ID"""
        if not self._initialized:
            await self.initialize()
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/workflows/{workflow_id}",
                    auth=(self.username, self.password)
                )
                if response.status_code == 200:
                    return response.json().get("data")
        except Exception as e:
            logger.error(f"Failed to get workflow {workflow_id}: {e}")
        return None
    
    async def create_workflow(self, workflow: WorkflowDefinition) -> Optional[str]:
        """Create a new workflow"""
        if not self._initialized:
            await self.initialize()
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/workflows",
                    auth=(self.username, self.password),
                    json={
                        "name": workflow.name,
                        "nodes": workflow.nodes,
                        "connections": workflow.connections,
                        "settings": {},
                        "staticData": None
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    workflow_id = data.get("data", {}).get("id")
                    logger.info(f"Created workflow: {workflow_id}")
                    return workflow_id
        except Exception as e:
            logger.error(f"Failed to create workflow: {e}")
        return None
    
    async def execute_workflow(
        self,
        workflow_id: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Optional[WorkflowExecution]:
        """Execute a workflow"""
        if not self._initialized:
            await self.initialize()
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/workflows/{workflow_id}/execute",
                    auth=(self.username, self.password),
                    json={"data": data or {}}
                )
                if response.status_code == 200:
                    result = response.json()
                    return WorkflowExecution(
                        execution_id=result.get("executionId", ""),
                        workflow_id=workflow_id,
                        status="running",
                        started_at=datetime.now().isoformat()
                    )
        except Exception as e:
            logger.error(f"Failed to execute workflow {workflow_id}: {e}")
        return None
    
    async def activate_workflow(self, workflow_id: str) -> bool:
        """Activate a workflow"""
        if not self._initialized:
            await self.initialize()
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.patch(
                    f"{self.base_url}/api/v1/workflows/{workflow_id}",
                    auth=(self.username, self.password),
                    json={"active": True}
                )
                if response.status_code == 200:
                    logger.info(f"Activated workflow: {workflow_id}")
                    return True
        except Exception as e:
            logger.error(f"Failed to activate workflow {workflow_id}: {e}")
        return False
    
    async def deactivate_workflow(self, workflow_id: str) -> bool:
        """Deactivate a workflow"""
        if not self._initialized:
            await self.initialize()
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.patch(
                    f"{self.base_url}/api/v1/workflows/{workflow_id}",
                    auth=(self.username, self.password),
                    json={"active": False}
                )
                if response.status_code == 200:
                    logger.info(f"Deactivated workflow: {workflow_id}")
                    return True
        except Exception as e:
            logger.error(f"Failed to deactivate workflow {workflow_id}: {e}")
        return False
    
    async def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow"""
        if not self._initialized:
            await self.initialize()
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.delete(
                    f"{self.base_url}/api/v1/workflows/{workflow_id}",
                    auth=(self.username, self.password)
                )
                if response.status_code == 200:
                    logger.info(f"Deleted workflow: {workflow_id}")
                    return True
        except Exception as e:
            logger.error(f"Failed to delete workflow {workflow_id}: {e}")
        return False
    
    async def get_execution(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get execution details"""
        if not self._initialized:
            await self.initialize()
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/executions/{execution_id}",
                    auth=(self.username, self.password)
                )
                if response.status_code == 200:
                    return response.json().get("data")
        except Exception as e:
            logger.error(f"Failed to get execution {execution_id}: {e}")
        return None
    
    def create_fiverr_order_workflow(self) -> WorkflowDefinition:
        """Create Fiverr order monitoring workflow"""
        return WorkflowDefinition(
            name="Fiverr Order Monitor",
            description="Monitor and process Fiverr orders",
            nodes=[
                {
                    "name": "Schedule Trigger",
                    "type": "n8n-nodes-base.scheduleTrigger",
                    "position": [250, 300],
                    "parameters": {
                        "rule": {"interval": [{"field": "hours", "hoursInterval": 1}]}
                    }
                },
                {
                    "name": "HTTP Request",
                    "type": "n8n-nodes-base.httpRequest",
                    "position": [450, 300],
                    "parameters": {
                        "url": "http://agentforge-core:8080/api/fiverr/orders",
                        "method": "GET"
                    }
                },
                {
                    "name": "AgentForge Process",
                    "type": "n8n-nodes-base.httpRequest",
                    "position": [650, 300],
                    "parameters": {
                        "url": "http://agentforge-core:8080/api/chat/message",
                        "method": "POST",
                        "jsonParameters": True,
                        "bodyParametersJson": "={\"message\": \"Process new Fiverr orders\"}"
                    }
                }
            ],
            connections={
                "Schedule Trigger": {"main": [[{"node": "HTTP Request", "type": "main", "index": 0}]]},
                "HTTP Request": {"main": [[{"node": "AgentForge Process", "type": "main", "index": 0}]]}
            }
        )
    
    def create_social_media_workflow(self) -> WorkflowDefinition:
        """Create social media publishing workflow"""
        return WorkflowDefinition(
            name="Social Media Publisher",
            description="Publish content to social media platforms",
            nodes=[
                {
                    "name": "Webhook",
                    "type": "n8n-nodes-base.webhook",
                    "position": [250, 300],
                    "parameters": {
                        "httpMethod": "POST",
                        "path": "social-publish"
                    }
                },
                {
                    "name": "AgentForge Content",
                    "type": "n8n-nodes-base.httpRequest",
                    "position": [450, 300],
                    "parameters": {
                        "url": "http://agentforge-core:8080/api/skills/execute",
                        "method": "POST",
                        "jsonParameters": True,
                        "bodyParametersJson": "={\"skill\": \"social_media_publisher\", \"params\": $json}"
                    }
                }
            ],
            connections={
                "Webhook": {"main": [[{"node": "AgentForge Content", "type": "main", "index": 0}]]}
            }
        )
    
    def create_knowledge_sync_workflow(self) -> WorkflowDefinition:
        """Create knowledge base sync workflow"""
        return WorkflowDefinition(
            name="Knowledge Sync",
            description="Sync knowledge base with external sources",
            nodes=[
                {
                    "name": "Schedule Trigger",
                    "type": "n8n-nodes-base.scheduleTrigger",
                    "position": [250, 300],
                    "parameters": {
                        "rule": {"interval": [{"field": "hours", "hoursInterval": 6}]}
                    }
                },
                {
                    "name": "AgentForge Sync",
                    "type": "n8n-nodes-base.httpRequest",
                    "position": [450, 300],
                    "parameters": {
                        "url": "http://agentforge-core:8080/api/knowledge/sync",
                        "method": "POST"
                    }
                }
            ],
            connections={
                "Schedule Trigger": {"main": [[{"node": "AgentForge Sync", "type": "main", "index": 0}]]}
            }
        )
