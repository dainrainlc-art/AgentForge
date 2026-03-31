"""
Orders API Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from loguru import logger

from integrations.api.auth import verify_token_dependency
from integrations.external.fiverr_client import FiverrClient, FiverrOrder


router = APIRouter()


class OrderResponse(BaseModel):
    id: str
    buyer_username: str
    seller_username: str
    status: str
    price: float
    currency: str
    description: str
    created_at: str
    updated_at: str


class OrderListResponse(BaseModel):
    orders: List[OrderResponse]
    total: int


class OrderStatsResponse(BaseModel):
    total: int
    active: int
    pending: int
    completed: int
    revenue: float


fiverr_client: Optional[FiverrClient] = None


def get_fiverr_client() -> FiverrClient:
    global fiverr_client
    if fiverr_client is None:
        fiverr_client = FiverrClient()
    return fiverr_client


@router.get("", response_model=OrderListResponse)
async def list_orders(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100),
    payload: dict = Depends(verify_token_dependency)
):
    """List all orders"""
    client = get_fiverr_client()
    
    orders = await client.get_orders(status=status, limit=limit)
    
    return OrderListResponse(
        orders=[
            OrderResponse(
                id=o.id,
                buyer_username=o.buyer_username,
                seller_username=o.seller_username,
                status=o.status,
                price=o.price,
                currency=o.currency,
                description=o.description,
                created_at=o.created_at.isoformat(),
                updated_at=o.updated_at.isoformat()
            )
            for o in orders
        ],
        total=len(orders)
    )


@router.get("/stats", response_model=OrderStatsResponse)
async def get_order_stats(payload: dict = Depends(verify_token_dependency)):
    """Get order statistics"""
    client = get_fiverr_client()
    
    orders = await client.get_orders()
    
    total = len(orders)
    active = sum(1 for o in orders if o.status == "active")
    pending = sum(1 for o in orders if o.status == "pending")
    completed = sum(1 for o in orders if o.status == "completed")
    revenue = sum(o.price for o in orders if o.status in ["completed", "delivered"])
    
    return OrderStatsResponse(
        total=total,
        active=active,
        pending=pending,
        completed=completed,
        revenue=revenue
    )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    payload: dict = Depends(verify_token_dependency)
):
    """Get specific order"""
    client = get_fiverr_client()
    
    order = await client.get_order(order_id)
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return OrderResponse(
        id=order.id,
        buyer_username=order.buyer_username,
        seller_username=order.seller_username,
        status=order.status,
        price=order.price,
        currency=order.currency,
        description=order.description,
        created_at=order.created_at.isoformat(),
        updated_at=order.updated_at.isoformat()
    )


@router.post("/{order_id}/message")
async def send_order_message(
    order_id: str,
    message: str,
    payload: dict = Depends(verify_token_dependency)
):
    """Send message to order"""
    client = get_fiverr_client()
    
    success = await client.send_message(order_id, message)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send message")
    
    return {"status": "sent", "order_id": order_id}
