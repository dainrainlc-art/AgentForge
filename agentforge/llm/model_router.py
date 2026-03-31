"""
Multi-Model Router - Intelligent model selection and failover
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
import httpx
from loguru import logger

from agentforge.config import settings


class ModelType(Enum):
    DEFAULT = "default"
    CODE = "code"
    LONG_CONTEXT = "long_context"
    CREATIVE = "creative"
    ANALYSIS = "analysis"


@dataclass
class ModelConfig:
    """Configuration for a specific model"""
    model_id: str
    model_type: ModelType
    max_tokens: int = 4096
    temperature: float = 0.7
    priority: int = 1
    enabled: bool = True
    daily_quota: Optional[int] = None
    used_today: int = 0


AVAILABLE_MODELS: Dict[str, ModelConfig] = {
    "glm-5": ModelConfig(
        model_id="glm-5",
        model_type=ModelType.DEFAULT,
        max_tokens=4096,
        temperature=0.7,
        priority=1,
        enabled=True,
        daily_quota=100000
    ),
    "kimi-k2.5": ModelConfig(
        model_id="kimi-k2.5",
        model_type=ModelType.LONG_CONTEXT,
        max_tokens=8192,
        temperature=0.7,
        priority=2,
        enabled=True,
        daily_quota=50000
    ),
    "deepseek-v3.2": ModelConfig(
        model_id="deepseek-v3.2",
        model_type=ModelType.CODE,
        max_tokens=4096,
        temperature=0.5,
        priority=3,
        enabled=True,
        daily_quota=50000
    ),
    "minimax-m2.5": ModelConfig(
        model_id="minimax-m2.5",
        model_type=ModelType.CREATIVE,
        max_tokens=4096,
        temperature=0.9,
        priority=4,
        enabled=True,
        daily_quota=30000
    ),
}


class ModelRouter:
    """Intelligent model routing with failover"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        self.api_key = api_key or settings.qianfan_api_key
        self.base_url = base_url or getattr(settings, 'qianfan_base_url', 'https://qianfan.baidubce.com/v2/coding')
        
        self._model_usage: Dict[str, int] = {m: 0 for m in AVAILABLE_MODELS}
        self._model_errors: Dict[str, List[datetime]] = {m: [] for m in AVAILABLE_MODELS}
        self._quota_exceeded: set = set()
    
    def select_model(
        self,
        task_type: str = "default",
        context_length: int = 0,
        prefer_model: Optional[str] = None
    ) -> str:
        """Select the best model for the task"""
        
        if prefer_model and prefer_model in AVAILABLE_MODELS:
            if self._is_model_available(prefer_model):
                return prefer_model
        
        candidates = []
        
        for model_id, config in AVAILABLE_MODELS.items():
            if not config.enabled:
                continue
            if not self._is_model_available(model_id):
                continue
            
            if config.model_type.value == task_type:
                candidates.append((config.priority, model_id))
            else:
                candidates.append((config.priority + 10, model_id))
        
        if not candidates:
            return "glm-5"
        
        candidates.sort(key=lambda x: x[0])
        return candidates[0][1]
    
    def _is_model_available(self, model_id: str) -> bool:
        """Check if model is available for use"""
        config = AVAILABLE_MODELS.get(model_id)
        if not config:
            return False
        
        if model_id in self._quota_exceeded:
            return False
        
        if config.daily_quota:
            if self._model_usage.get(model_id, 0) >= config.daily_quota:
                return False
        
        if model_id in self._model_errors:
            recent_errors = [
                e for e in self._model_errors[model_id]
                if (datetime.now() - e).total_seconds() < 300
            ]
            if len(recent_errors) >= 3:
                return False
        
        return True
    
    async def chat_with_failover(
        self,
        message: str,
        task_type: str = "default",
        context: Optional[Dict[str, Any]] = None,
        memories: Optional[List[Dict[str, Any]]] = None,
        history: Optional[List[Dict[str, Any]]] = None,
        prefer_model: Optional[str] = None
    ) -> str:
        """Execute chat with automatic failover"""
        
        selected_model = self.select_model(task_type, 0, prefer_model)
        
        models_to_try = [selected_model]
        for model_id in AVAILABLE_MODELS:
            if model_id != selected_model and self._is_model_available(model_id):
                models_to_try.append(model_id)
        
        last_error = None
        
        for model_id in models_to_try:
            try:
                config = AVAILABLE_MODELS[model_id]
                
                response = await self._execute_chat(
                    model_id=model_id,
                    message=message,
                    context=context,
                    memories=memories,
                    history=history,
                    temperature=config.temperature,
                    max_tokens=config.max_tokens
                )
                
                self._model_usage[model_id] = self._model_usage.get(model_id, 0) + 1
                
                return response
                
            except Exception as e:
                logger.warning(f"Model {model_id} failed: {e}")
                self._model_errors.setdefault(model_id, []).append(datetime.now())
                last_error = e
                continue
        
        raise Exception(f"All models failed. Last error: {last_error}")
    
    async def _execute_chat(
        self,
        model_id: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        memories: Optional[List[Dict[str, Any]]] = None,
        history: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> str:
        """Execute chat request"""
        
        if not self.api_key:
            raise ValueError("API key not configured")
        
        messages = []
        
        if memories:
            memory_context = "\n".join([m.get("content", "") for m in memories[:3]])
            if memory_context:
                messages.append({
                    "role": "system",
                    "content": f"Relevant context from memory:\n{memory_context}"
                })
        
        if context:
            messages.append({
                "role": "system",
                "content": f"Context: {context}"
            })
        
        if history:
            for h in history[-5:]:
                role = h.get("role", "user")
                content = h.get("content", "")
                if role in ["user", "assistant"]:
                    messages.append({"role": role, "content": content})
        
        messages.append({"role": "user", "content": message})
        
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model_id,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            data = response.json()
            
            if "error" in data:
                raise Exception(f"API error: {data}")
            
            choices = data.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "")
            
            return ""
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get model usage statistics"""
        return {
            "usage": dict(self._model_usage),
            "quota_exceeded": list(self._quota_exceeded),
            "model_errors": {
                k: len(v) for k, v in self._model_errors.items()
            }
        }
    
    def reset_daily_stats(self) -> None:
        """Reset daily usage statistics"""
        self._model_usage = {m: 0 for m in AVAILABLE_MODELS}
        self._quota_exceeded.clear()
        logger.info("Daily model usage statistics reset")


model_router = ModelRouter()
