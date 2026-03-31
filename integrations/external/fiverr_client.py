"""
AgentForge Fiverr API Client - Complete Integration
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import httpx
from loguru import logger
from enum import Enum

from agentforge.config import settings


class OrderStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    LATE = "late"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DISPUTED = "disputed"


class DeliveryStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    REVISION = "revision"


class FiverrOrder(BaseModel):
    """Fiverr order model"""
    id: str
    buyer_username: str
    seller_username: str
    status: str
    price: float
    currency: str = "USD"
    description: str = ""
    title: str = ""
    package_id: Optional[str] = None
    delivery_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FiverrMessage(BaseModel):
    """Fiverr message model"""
    id: str
    order_id: str
    sender_username: str
    receiver_username: Optional[str] = None
    content: str
    is_read: bool = False
    attachments: List[str] = Field(default_factory=list)
    created_at: datetime


class FiverrDelivery(BaseModel):
    """Fiverr delivery model"""
    id: str
    order_id: str
    status: DeliveryStatus
    message: str
    attachments: List[str] = Field(default_factory=list)
    created_at: datetime
    revision_count: int = 0


class FiverrReview(BaseModel):
    """Fiverr review model"""
    id: str
    order_id: str
    buyer_username: str
    rating: int
    comment: str
    created_at: datetime


class FiverrWebhookEvent(BaseModel):
    """Fiverr webhook event model"""
    event_type: str
    event_id: str
    timestamp: datetime
    data: Dict[str, Any]
    signature: Optional[str] = None


class FiverrClient:
    """Complete Fiverr API client"""
    
    BASE_URL = "https://api.fiverr.com/v2"
    SANDBOX_URL = "https://api-sandbox.fiverr.com/v2"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        sandbox: bool = False
    ):
        self.api_key = api_key or getattr(settings, 'fiverr_api_key', None)
        self.sandbox = sandbox
        self.base_url = self.SANDBOX_URL if sandbox else self.BASE_URL
        
        if not self.api_key:
            logger.warning("Fiverr API key not configured")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get API headers"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None
    ) -> Optional[Dict]:
        """Make API request"""
        if not self.api_key:
            return None
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.request(
                    method=method,
                    url=f"{self.base_url}{endpoint}",
                    headers=self._get_headers(),
                    params=params,
                    json=data
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 401:
                    logger.error("Fiverr API authentication failed")
                    return None
                elif response.status_code == 429:
                    logger.warning("Fiverr API rate limit exceeded")
                    return None
                else:
                    logger.error(f"Fiverr API error: {response.status_code}")
                    return None
                    
        except httpx.TimeoutException:
            logger.error("Fiverr API request timed out")
            return None
        except Exception as e:
            logger.error(f"Fiverr API request failed: {e}")
            return None
    
    async def get_orders(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[FiverrOrder]:
        """Get orders from Fiverr"""
        params = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        
        data = await self._request("GET", "/orders", params=params)
        
        if not data:
            return []
        
        return [
            FiverrOrder(
                id=o["id"],
                buyer_username=o.get("buyer_username", ""),
                seller_username=o.get("seller_username", ""),
                status=o.get("status", ""),
                price=o.get("price", 0),
                currency=o.get("currency", "USD"),
                description=o.get("description", ""),
                title=o.get("title", ""),
                package_id=o.get("package_id"),
                delivery_date=datetime.fromisoformat(o["delivery_date"]) if o.get("delivery_date") else None,
                created_at=datetime.fromisoformat(o["created_at"]),
                updated_at=datetime.fromisoformat(o["updated_at"]),
                metadata=o.get("metadata", {})
            )
            for o in data.get("orders", [])
        ]
    
    async def get_order(self, order_id: str) -> Optional[FiverrOrder]:
        """Get specific order"""
        data = await self._request("GET", f"/orders/{order_id}")
        
        if not data:
            return None
        
        return FiverrOrder(
            id=data["id"],
            buyer_username=data.get("buyer_username", ""),
            seller_username=data.get("seller_username", ""),
            status=data.get("status", ""),
            price=data.get("price", 0),
            currency=data.get("currency", "USD"),
            description=data.get("description", ""),
            title=data.get("title", ""),
            package_id=data.get("package_id"),
            delivery_date=datetime.fromisoformat(data["delivery_date"]) if data.get("delivery_date") else None,
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            metadata=data.get("metadata", {})
        )
    
    async def update_order_status(
        self,
        order_id: str,
        status: str,
        notes: Optional[str] = None
    ) -> bool:
        """Update order status"""
        data = {"status": status}
        if notes:
            data["notes"] = notes
        
        result = await self._request("PUT", f"/orders/{order_id}/status", data=data)
        return result is not None
    
    async def accept_order(self, order_id: str) -> bool:
        """Accept an order"""
        result = await self._request("POST", f"/orders/{order_id}/accept")
        return result is not None
    
    async def decline_order(self, order_id: str, reason: str) -> bool:
        """Decline an order"""
        result = await self._request("POST", f"/orders/{order_id}/decline", data={"reason": reason})
        return result is not None
    
    async def request_cancellation(
        self,
        order_id: str,
        reason: str,
        mutual: bool = True
    ) -> bool:
        """Request order cancellation"""
        data = {
            "reason": reason,
            "mutual": mutual
        }
        result = await self._request("POST", f"/orders/{order_id}/cancel", data=data)
        return result is not None
    
    async def extend_delivery(
        self,
        order_id: str,
        new_delivery_date: datetime,
        reason: str
    ) -> bool:
        """Request delivery extension"""
        data = {
            "new_delivery_date": new_delivery_date.isoformat(),
            "reason": reason
        }
        result = await self._request("POST", f"/orders/{order_id}/extend", data=data)
        return result is not None
    
    async def get_messages(
        self,
        order_id: str,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[FiverrMessage]:
        """Get messages for an order"""
        params = {"limit": limit, "unread_only": unread_only}
        data = await self._request("GET", f"/orders/{order_id}/messages", params=params)
        
        if not data:
            return []
        
        return [
            FiverrMessage(
                id=m["id"],
                order_id=m.get("order_id", ""),
                sender_username=m.get("sender_username", ""),
                receiver_username=m.get("receiver_username"),
                content=m.get("content", ""),
                is_read=m.get("is_read", False),
                attachments=m.get("attachments", []),
                created_at=datetime.fromisoformat(m["created_at"])
            )
            for m in data.get("messages", [])
        ]
    
    async def send_message(
        self,
        order_id: str,
        message: str,
        attachments: Optional[List[str]] = None
    ) -> Optional[str]:
        """Send message to order, returns message ID"""
        data = {"message": message}
        if attachments:
            data["attachments"] = attachments
        
        result = await self._request("POST", f"/orders/{order_id}/messages", data=data)
        
        if result and "message_id" in result:
            logger.info(f"Message sent to order {order_id}")
            return result["message_id"]
        return None
    
    async def mark_message_read(self, order_id: str, message_id: str) -> bool:
        """Mark message as read"""
        result = await self._request("PUT", f"/orders/{order_id}/messages/{message_id}/read")
        return result is not None
    
    async def get_unread_count(self) -> Dict[str, int]:
        """Get unread message counts"""
        data = await self._request("GET", "/messages/unread/count")
        
        if not data:
            return {"total": 0, "orders": {}}
        
        return {
            "total": data.get("total", 0),
            "orders": data.get("orders", {})
        }
    
    async def submit_delivery(
        self,
        order_id: str,
        message: str,
        attachments: List[str],
        source_files: Optional[List[str]] = None
    ) -> Optional[str]:
        """Submit delivery for order"""
        data = {
            "message": message,
            "attachments": attachments
        }
        if source_files:
            data["source_files"] = source_files
        
        result = await self._request("POST", f"/orders/{order_id}/deliver", data=data)
        
        if result and "delivery_id" in result:
            logger.info(f"Delivery submitted for order {order_id}")
            return result["delivery_id"]
        return None
    
    async def get_delivery(self, order_id: str) -> Optional[FiverrDelivery]:
        """Get delivery details"""
        data = await self._request("GET", f"/orders/{order_id}/delivery")
        
        if not data:
            return None
        
        return FiverrDelivery(
            id=data["id"],
            order_id=data.get("order_id", ""),
            status=DeliveryStatus(data.get("status", "pending")),
            message=data.get("message", ""),
            attachments=data.get("attachments", []),
            created_at=datetime.fromisoformat(data["created_at"]),
            revision_count=data.get("revision_count", 0)
        )
    
    async def request_revision(
        self,
        order_id: str,
        message: str
    ) -> bool:
        """Request revision on delivery"""
        result = await self._request("POST", f"/orders/{order_id}/revision", data={"message": message})
        return result is not None
    
    async def submit_quote(
        self,
        buyer_username: str,
        title: str,
        description: str,
        price: float,
        delivery_days: int,
        revisions: int = 2
    ) -> Optional[str]:
        """Submit custom quote to buyer"""
        data = {
            "buyer_username": buyer_username,
            "title": title,
            "description": description,
            "price": price,
            "delivery_days": delivery_days,
            "revisions": revisions
        }
        
        result = await self._request("POST", "/quotes", data=data)
        
        if result and "quote_id" in result:
            logger.info(f"Quote submitted: {result['quote_id']}")
            return result["quote_id"]
        return None
    
    async def get_quote(self, quote_id: str) -> Optional[Dict[str, Any]]:
        """Get quote details"""
        return await self._request("GET", f"/quotes/{quote_id}")
    
    async def get_review(self, order_id: str) -> Optional[FiverrReview]:
        """Get order review"""
        data = await self._request("GET", f"/orders/{order_id}/review")
        
        if not data:
            return None
        
        return FiverrReview(
            id=data["id"],
            order_id=data.get("order_id", ""),
            buyer_username=data.get("buyer_username", ""),
            rating=data.get("rating", 0),
            comment=data.get("comment", ""),
            created_at=datetime.fromisoformat(data["created_at"])
        )
    
    async def respond_to_review(
        self,
        order_id: str,
        response: str
    ) -> bool:
        """Respond to buyer review"""
        result = await self._request("POST", f"/orders/{order_id}/review/respond", data={"response": response})
        return result is not None
    
    async def get_earnings(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get earnings summary"""
        params = {}
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()
        
        data = await self._request("GET", "/earnings", params=params)
        return data or {"total": 0, "pending": 0, "cleared": 0, "withdrawn": 0}
    
    async def get_analytics(
        self,
        period: str = "30d"
    ) -> Dict[str, Any]:
        """Get seller analytics"""
        params = {"period": period}
        data = await self._request("GET", "/analytics", params=params)
        return data or {
            "impressions": 0,
            "clicks": 0,
            "orders": 0,
            "cancellations": 0,
            "average_rating": 0
        }
    
    async def setup_webhook(
        self,
        callback_url: str,
        events: List[str],
        secret: Optional[str] = None
    ) -> Optional[str]:
        """Setup webhook for events"""
        data = {
            "callback_url": callback_url,
            "events": events
        }
        if secret:
            data["secret"] = secret
        
        result = await self._request("POST", "/webhooks", data=data)
        
        if result and "webhook_id" in result:
            logger.info(f"Webhook created: {result['webhook_id']}")
            return result["webhook_id"]
        return None
    
    async def delete_webhook(self, webhook_id: str) -> bool:
        """Delete webhook"""
        result = await self._request("DELETE", f"/webhooks/{webhook_id}")
        return result is not None
    
    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        secret: str
    ) -> bool:
        """Verify webhook signature"""
        import hmac
        import hashlib
        
        expected = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected)
    
    async def health_check(self) -> bool:
        """Check if Fiverr API is accessible"""
        data = await self._request("GET", "/user")
        return data is not None
    
    async def get_user_info(self) -> Optional[Dict[str, Any]]:
        """Get current user info"""
        return await self._request("GET", "/user")


fiverr_client = FiverrClient()
