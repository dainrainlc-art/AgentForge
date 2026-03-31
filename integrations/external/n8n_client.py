"""
N8N Workflow Integration Client
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
import httpx
from loguru import logger

from agentforge.config import settings


class N8NClient:
    """Client for N8N workflow engine integration"""
    
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None
    ):
        self.host = host or getattr(settings, 'n8n_host', 'localhost')
        self.port = port or getattr(settings, 'n8n_port', 5678)
        self.username = username or getattr(settings, 'n8n_user', 'admin')
        self.password = password or getattr(settings, 'n8n_password', '')
        
        self._base_url = f"http://{self.host}:{self.port}"
        self._webhook_base = f"{self._base_url}/webhook"
    
    async def trigger_workflow(
        self,
        webhook_path: str,
        payload: Dict[str, Any],
        method: str = "POST"
    ) -> Dict[str, Any]:
        """Trigger a workflow via webhook"""
        url = f"{self._webhook_base}/{webhook_path.lstrip('/')}"
        
        logger.info(f"Triggering workflow: {webhook_path}")
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                if method.upper() == "GET":
                    response = await client.get(url, params=payload)
                else:
                    response = await client.post(url, json=payload)
                
                response.raise_for_status()
                
                try:
                    return response.json()
                except:
                    return {"status": "success", "data": response.text}
                    
        except httpx.HTTPStatusError as e:
            logger.error(f"Workflow trigger failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Workflow trigger error: {e}")
            raise
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow status"""
        url = f"{self._base_url}/api/v1/workflows/{workflow_id}"
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    url,
                    auth=(self.username, self.password) if self.password else None
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to get workflow status: {e}")
            raise
    
    async def list_workflows(self) -> List[Dict[str, Any]]:
        """List all workflows"""
        url = f"{self._base_url}/api/v1/workflows"
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    url,
                    auth=(self.username, self.password) if self.password else None
                )
                response.raise_for_status()
                data = response.json()
                return data.get("data", [])
        except Exception as e:
            logger.error(f"Failed to list workflows: {e}")
            raise
    
    async def activate_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Activate a workflow"""
        url = f"{self._base_url}/api/v1/workflows/{workflow_id}/activate"
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    url,
                    auth=(self.username, self.password) if self.password else None
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to activate workflow: {e}")
            raise
    
    async def deactivate_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Deactivate a workflow"""
        url = f"{self._base_url}/api/v1/workflows/{workflow_id}/deactivate"
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    url,
                    auth=(self.username, self.password) if self.password else None
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to deactivate workflow: {e}")
            raise
    
    async def get_execution(self, execution_id: str) -> Dict[str, Any]:
        """Get execution details"""
        url = f"{self._base_url}/api/v1/executions/{execution_id}"
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    url,
                    auth=(self.username, self.password) if self.password else None
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to get execution: {e}")
            raise


class WorkflowManager:
    """Manager for predefined workflows"""
    
    WORKFLOWS = {
        "fiverr_order_notification": {
            "webhook_path": "fiverr/order",
            "description": "Handle Fiverr order notifications"
        },
        "fiverr_message_handler": {
            "webhook_path": "fiverr/message",
            "description": "Handle Fiverr message events"
        },
        "social_media_post": {
            "webhook_path": "social/post",
            "description": "Post to social media platforms"
        },
        "knowledge_sync": {
            "webhook_path": "knowledge/sync",
            "description": "Sync knowledge from external sources"
        },
        "daily_report": {
            "webhook_path": "report/daily",
            "description": "Generate daily report"
        }
    }
    
    def __init__(self, n8n_client: N8NClient):
        self.client = n8n_client
    
    async def trigger_fiverr_order(
        self,
        order_id: str,
        buyer: str,
        status: str,
        details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Trigger Fiverr order workflow"""
        workflow = self.WORKFLOWS["fiverr_order_notification"]
        
        return await self.client.trigger_workflow(
            webhook_path=workflow["webhook_path"],
            payload={
                "order_id": order_id,
                "buyer": buyer,
                "status": status,
                "details": details,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    async def trigger_fiverr_message(
        self,
        message_id: str,
        sender: str,
        content: str,
        conversation_id: str
    ) -> Dict[str, Any]:
        """Trigger Fiverr message workflow"""
        workflow = self.WORKFLOWS["fiverr_message_handler"]
        
        return await self.client.trigger_workflow(
            webhook_path=workflow["webhook_path"],
            payload={
                "message_id": message_id,
                "sender": sender,
                "content": content,
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    async def trigger_social_post(
        self,
        platform: str,
        content: str,
        media_urls: Optional[List[str]] = None,
        schedule_time: Optional[str] = None
    ) -> Dict[str, Any]:
        """Trigger social media post workflow"""
        workflow = self.WORKFLOWS["social_media_post"]
        
        return await self.client.trigger_workflow(
            webhook_path=workflow["webhook_path"],
            payload={
                "platform": platform,
                "content": content,
                "media_urls": media_urls or [],
                "schedule_time": schedule_time,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    async def trigger_knowledge_sync(
        self,
        source: str,
        action: str = "full",
        items: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Trigger knowledge sync workflow"""
        workflow = self.WORKFLOWS["knowledge_sync"]
        
        return await self.client.trigger_workflow(
            webhook_path=workflow["webhook_path"],
            payload={
                "source": source,
                "action": action,
                "items": items or [],
                "timestamp": datetime.now().isoformat()
            }
        )
    
    async def trigger_daily_report(
        self,
        date: Optional[str] = None,
        include_sections: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Trigger daily report workflow"""
        workflow = self.WORKFLOWS["daily_report"]
        
        return await self.client.trigger_workflow(
            webhook_path=workflow["webhook_path"],
            payload={
                "date": date or datetime.now().strftime("%Y-%m-%d"),
                "include_sections": include_sections or ["orders", "messages", "tasks"],
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def list_available_workflows(self) -> Dict[str, Dict[str, str]]:
        """List all available workflows"""
        return self.WORKFLOWS


n8n_client = N8NClient()
workflow_manager = WorkflowManager(n8n_client)
