"""
Baidu Qianfan Coding Plan Pro LLM Client
Compatible with OpenAI API protocol
"""
from typing import Optional, Dict, Any, List
import httpx
from loguru import logger
from agentforge.config import settings


class QianfanClient:
    """Client for Baidu Qianfan Coding Plan Pro API (OpenAI compatible)"""
    
    MODEL_ROUTING = {
        "default": "glm-5",
        "code": "deepseek-v3.2",
        "long_context": "kimi-k2.5",
        "creative": "minimax-m2.5",
        "analysis": "kimi-k2.5"
    }
    
    AVAILABLE_MODELS = [
        "glm-5",
        "kimi-k2.5",
        "deepseek-v3.2",
        "minimax-m2.5"
    ]
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: Optional[str] = None
    ):
        self.api_key = api_key or settings.qianfan_api_key
        self.base_url = base_url or getattr(settings, 'qianfan_base_url', 'https://qianfan.baidubce.com/v2/coding')
        self.default_model = default_model or getattr(settings, 'qianfan_default_model', 'glm-5')
        
        if not self.api_key:
            logger.warning("Qianfan API key not configured")
    
    async def chat(
        self,
        message: str,
        model: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        memories: Optional[List[Dict[str, Any]]] = None,
        history: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """Send chat message to Qianfan Coding Plan API (OpenAI compatible)"""
        
        if not self.api_key:
            return "Error: Qianfan API key not configured"
        
        model = model or self.default_model
        
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
        
        try:
            url = f"{self.base_url}/chat/completions"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                data = response.json()
                
                if "error" in data:
                    logger.error(f"Qianfan API error: {data}")
                    return f"Error: {data.get('error', {}).get('message', 'Unknown error')}"
                
                choices = data.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "")
                
                return ""
                
        except Exception as e:
            logger.error(f"Qianfan API call failed: {e}")
            return f"Error: {str(e)}"
    
    async def chat_stream(
        self,
        message: str,
        model: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        history: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ):
        """Stream chat response"""
        if not self.api_key:
            yield "Error: Qianfan API key not configured"
            return
        
        model = model or self.default_model
        
        messages = []
        
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
        
        try:
            url = f"{self.base_url}/chat/completions"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": True
            }
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream("POST", url, json=payload, headers=headers) as response:
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str == "[DONE]":
                                break
                            try:
                                import json
                                data = json.loads(data_str)
                                choices = data.get("choices", [])
                                if choices:
                                    delta = choices[0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        yield content
                            except Exception:
                                pass
                                
        except Exception as e:
            logger.error(f"Qianfan streaming API call failed: {e}")
            yield f"Error: {str(e)}"
    
    def route_to_model(self, task_type: str) -> str:
        """Route to appropriate model based on task type"""
        return self.MODEL_ROUTING.get(task_type, self.MODEL_ROUTING["default"])
    
    async def health_check(self) -> bool:
        """Check if Qianfan API is accessible"""
        if not self.api_key:
            return False
        
        try:
            response = await self.chat("Hello", max_tokens=10)
            return not response.startswith("Error")
        except Exception:
            return False
    
    def list_available_models(self) -> List[str]:
        """List available models"""
        return self.AVAILABLE_MODELS
