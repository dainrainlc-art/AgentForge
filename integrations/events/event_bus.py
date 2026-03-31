"""
AgentForge Event Bus - Event-Driven Architecture
"""
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from pydantic import BaseModel, Field
from loguru import logger
import asyncio
import json


class Event(BaseModel):
    """Event definition"""
    id: str
    type: str
    source: str
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EventHandler:
    """Event handler wrapper"""
    
    def __init__(self, callback: Callable, event_types: List[str]):
        self.callback = callback
        self.event_types = event_types


class EventBus:
    """Event bus for publish-subscribe pattern"""
    
    def __init__(self):
        self._handlers: List[EventHandler] = []
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._event_counter = 0
    
    def _generate_event_id(self) -> str:
        self._event_counter += 1
        return f"evt_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self._event_counter:04d}"
    
    def subscribe(self, event_types: List[str]) -> Callable:
        """Decorator to subscribe to events"""
        def decorator(func: Callable) -> Callable:
            handler = EventHandler(callback=func, event_types=event_types)
            self._handlers.append(handler)
            logger.info(f"Subscribed handler {func.__name__} to events: {event_types}")
            return func
        return decorator
    
    def add_handler(self, handler: Callable, event_types: List[str]) -> None:
        """Add event handler programmatically"""
        event_handler = EventHandler(callback=handler, event_types=event_types)
        self._handlers.append(event_handler)
        logger.info(f"Added handler for events: {event_types}")
    
    async def publish(
        self,
        event_type: str,
        source: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Publish an event"""
        event = Event(
            id=self._generate_event_id(),
            type=event_type,
            source=source,
            data=data,
            metadata=metadata or {}
        )
        
        await self._event_queue.put(event)
        logger.debug(f"Published event: {event_type} from {source}")
        
        return event.id
    
    async def publish_sync(
        self,
        event_type: str,
        source: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Any]:
        """Publish event and wait for all handlers to complete"""
        event = Event(
            id=self._generate_event_id(),
            type=event_type,
            source=source,
            data=data,
            metadata=metadata or {}
        )
        
        results = []
        for handler in self._handlers:
            if "*" in handler.event_types or event.type in handler.event_types:
                try:
                    result = await handler.callback(event)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Handler error for event {event.type}: {e}")
                    results.append({"error": str(e)})
        
        logger.debug(f"Processed event {event.id} with {len(results)} handlers")
        return results
    
    async def start_processing(self) -> None:
        """Start event processing loop"""
        self._running = True
        logger.info("Event bus started processing")
        
        while self._running:
            try:
                event = await asyncio.wait_for(
                    self._event_queue.get(),
                    timeout=1.0
                )
                
                for handler in self._handlers:
                    if "*" in handler.event_types or event.type in handler.event_types:
                        try:
                            await handler.callback(event)
                        except Exception as e:
                            logger.error(f"Handler error for event {event.type}: {e}")
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Event processing error: {e}")
    
    def stop_processing(self) -> None:
        """Stop event processing"""
        self._running = False
        logger.info("Event bus stopped processing")
    
    def get_queue_size(self) -> int:
        """Get current queue size"""
        return self._event_queue.qsize()
    
    def list_handlers(self) -> List[Dict[str, Any]]:
        """List all registered handlers"""
        return [
            {
                "callback": h.callback.__name__,
                "event_types": h.event_types
            }
            for h in self._handlers
        ]


event_bus = EventBus()
