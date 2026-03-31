"""
Fiverr Order Tracker - Automatic order status tracking and notifications
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from loguru import logger
from enum import Enum
import asyncio

from integrations.external.fiverr_client import FiverrClient, FiverrOrder
from integrations.events.event_bus import event_bus
from integrations.events.notification import notification_service


class OrderStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    LATE = "late"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DISPUTED = "disputed"


class TrackingEvent(BaseModel):
    """Order tracking event"""
    order_id: str
    event_type: str
    old_status: Optional[str] = None
    new_status: str
    timestamp: datetime = Field(default_factory=datetime.now)
    notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class OrderTrackerConfig(BaseModel):
    """Order tracker configuration"""
    check_interval_seconds: int = 300
    late_threshold_hours: int = 24
    reminder_before_due_hours: int = 12
    enable_notifications: bool = True
    track_status_changes: bool = True


class TrackedOrder(BaseModel):
    """Tracked order with additional metadata"""
    order: FiverrOrder
    last_checked: datetime
    status_history: List[TrackingEvent] = Field(default_factory=list)
    due_date: Optional[datetime] = None
    reminder_sent: bool = False
    late_notification_sent: bool = False


class OrderTracker:
    """Automatic order status tracker"""
    
    def __init__(
        self,
        fiverr_client: Optional[FiverrClient] = None,
        config: Optional[OrderTrackerConfig] = None
    ):
        self.fiverr_client = fiverr_client or FiverrClient()
        self.config = config or OrderTrackerConfig()
        
        self._tracked_orders: Dict[str, TrackedOrder] = {}
        self._running = False
        self._tracker_task: Optional[asyncio.Task] = None
    
    async def start_tracking(self) -> None:
        """Start the order tracking loop"""
        if self._running:
            logger.warning("Order tracker already running")
            return
        
        self._running = True
        self._tracker_task = asyncio.create_task(self._tracking_loop())
        logger.info("Order tracker started")
    
    async def stop_tracking(self) -> None:
        """Stop the order tracking loop"""
        self._running = False
        
        if self._tracker_task:
            self._tracker_task.cancel()
            try:
                await self._tracker_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Order tracker stopped")
    
    async def _tracking_loop(self) -> None:
        """Main tracking loop"""
        while self._running:
            try:
                await self._check_all_orders()
                await asyncio.sleep(self.config.check_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Tracking loop error: {e}")
                await asyncio.sleep(60)
    
    async def _check_all_orders(self) -> None:
        """Check all tracked orders"""
        orders = await self.fiverr_client.get_orders()
        
        for order in orders:
            await self._process_order(order)
    
    async def _process_order(self, order: FiverrOrder) -> None:
        """Process a single order"""
        order_id = order.id
        
        if order_id in self._tracked_orders:
            tracked = self._tracked_orders[order_id]
            old_status = tracked.order.status
            
            if old_status != order.status:
                await self._handle_status_change(tracked, old_status, order.status)
            
            tracked.order = order
            tracked.last_checked = datetime.now()
        else:
            tracked = TrackedOrder(
                order=order,
                last_checked=datetime.now(),
                due_date=self._estimate_due_date(order)
            )
            self._tracked_orders[order_id] = tracked
            logger.info(f"Started tracking order: {order_id}")
        
        await self._check_order_alerts(tracked)
    
    def _estimate_due_date(self, order: FiverrOrder) -> Optional[datetime]:
        """Estimate order due date"""
        if order.status in [OrderStatus.COMPLETED, OrderStatus.CANCELLED]:
            return None
        
        delivery_days = 7
        
        if order.status == OrderStatus.ACTIVE:
            return order.created_at + timedelta(days=delivery_days)
        
        return None
    
    async def _handle_status_change(
        self,
        tracked: TrackedOrder,
        old_status: str,
        new_status: str
    ) -> None:
        """Handle order status change"""
        event = TrackingEvent(
            order_id=tracked.order.id,
            event_type="status_change",
            old_status=old_status,
            new_status=new_status,
            timestamp=datetime.now()
        )
        
        tracked.status_history.append(event)
        
        logger.info(f"Order {tracked.order.id} status changed: {old_status} -> {new_status}")
        
        if self.config.track_status_changes:
            await event_bus.publish(
                event_type=f"order.{new_status}",
                source="order_tracker",
                data={
                    "order_id": tracked.order.id,
                    "old_status": old_status,
                    "new_status": new_status,
                    "buyer_username": tracked.order.buyer_username,
                    "price": tracked.order.price
                }
            )
        
        if self.config.enable_notifications:
            await self._send_status_notification(tracked, old_status, new_status)
    
    async def _send_status_notification(
        self,
        tracked: TrackedOrder,
        old_status: str,
        new_status: str
    ) -> None:
        """Send notification for status change"""
        priority_map = {
            OrderStatus.COMPLETED: "high",
            OrderStatus.DELIVERED: "high",
            OrderStatus.CANCELLED: "urgent",
            OrderStatus.LATE: "urgent",
            OrderStatus.ACTIVE: "normal",
        }
        
        priority = priority_map.get(new_status, "normal")
        
        await notification_service.send_notification(
            type="order",
            title=f"Order {new_status.title()}",
            message=f"Order #{tracked.order.id} from {tracked.order.buyer_username} is now {new_status}",
            priority=priority,
            channels=["desktop", "telegram"]
        )
    
    async def _check_order_alerts(self, tracked: TrackedOrder) -> None:
        """Check for order alerts (late, due soon)"""
        if not tracked.due_date:
            return
        
        now = datetime.now()
        
        if tracked.order.status == OrderStatus.ACTIVE:
            if now > tracked.due_date and not tracked.late_notification_sent:
                await self._handle_late_order(tracked)
                tracked.late_notification_sent = True
            
            elif not tracked.reminder_sent:
                time_until_due = tracked.due_date - now
                if time_until_due <= timedelta(hours=self.config.reminder_before_due_hours):
                    await self._handle_due_soon(tracked)
                    tracked.reminder_sent = True
    
    async def _handle_late_order(self, tracked: TrackedOrder) -> None:
        """Handle late order"""
        logger.warning(f"Order {tracked.order.id} is late!")
        
        event = TrackingEvent(
            order_id=tracked.order.id,
            event_type="late_alert",
            new_status=tracked.order.status,
            notes=f"Order is overdue. Due date: {tracked.due_date}"
        )
        
        tracked.status_history.append(event)
        
        await event_bus.publish(
            event_type="order.late",
            source="order_tracker",
            data={
                "order_id": tracked.order.id,
                "due_date": tracked.due_date.isoformat(),
                "buyer_username": tracked.order.buyer_username
            }
        )
        
        if self.config.enable_notifications:
            await notification_service.send_notification(
                type="alert",
                title="Late Order Alert!",
                message=f"Order #{tracked.order.id} is overdue. Contact buyer immediately.",
                priority="urgent",
                channels=["desktop", "telegram"]
            )
    
    async def _handle_due_soon(self, tracked: TrackedOrder) -> None:
        """Handle order due soon"""
        logger.info(f"Order {tracked.order.id} is due soon")
        
        event = TrackingEvent(
            order_id=tracked.order.id,
            event_type="due_soon_reminder",
            new_status=tracked.order.status,
            notes=f"Order due in {self.config.reminder_before_due_hours} hours"
        )
        
        tracked.status_history.append(event)
        
        if self.config.enable_notifications:
            await notification_service.send_notification(
                type="reminder",
                title="Order Due Soon",
                message=f"Order #{tracked.order.id} is due in {self.config.reminder_before_due_hours} hours",
                priority="high",
                channels=["desktop"]
            )
    
    def add_order_to_track(self, order: FiverrOrder) -> None:
        """Manually add an order to track"""
        if order.id not in self._tracked_orders:
            tracked = TrackedOrder(
                order=order,
                last_checked=datetime.now(),
                due_date=self._estimate_due_date(order)
            )
            self._tracked_orders[order.id] = tracked
            logger.info(f"Added order to tracking: {order.id}")
    
    def remove_order_from_track(self, order_id: str) -> bool:
        """Remove an order from tracking"""
        if order_id in self._tracked_orders:
            del self._tracked_orders[order_id]
            logger.info(f"Removed order from tracking: {order_id}")
            return True
        return False
    
    def get_tracked_order(self, order_id: str) -> Optional[TrackedOrder]:
        """Get a tracked order"""
        return self._tracked_orders.get(order_id)
    
    def get_all_tracked_orders(self) -> List[TrackedOrder]:
        """Get all tracked orders"""
        return list(self._tracked_orders.values())
    
    def get_orders_by_status(self, status: OrderStatus) -> List[TrackedOrder]:
        """Get orders by status"""
        return [
            t for t in self._tracked_orders.values()
            if t.order.status == status.value
        ]
    
    def get_late_orders(self) -> List[TrackedOrder]:
        """Get all late orders"""
        now = datetime.now()
        return [
            t for t in self._tracked_orders.values()
            if t.due_date and now > t.due_date and t.order.status == OrderStatus.ACTIVE.value
        ]
    
    def get_order_history(self, order_id: str) -> List[TrackingEvent]:
        """Get order tracking history"""
        tracked = self._tracked_orders.get(order_id)
        return tracked.status_history if tracked else []
    
    def get_tracking_stats(self) -> Dict[str, Any]:
        """Get tracking statistics"""
        orders = list(self._tracked_orders.values())
        
        return {
            "total_tracked": len(orders),
            "by_status": {
                status.value: len([o for o in orders if o.order.status == status.value])
                for status in OrderStatus
            },
            "late_orders": len(self.get_late_orders()),
            "running": self._running
        }


order_tracker = OrderTracker()
