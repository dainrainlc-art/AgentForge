"""
AgentForge Event Store - Redis Streams Implementation
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import redis.asyncio as redis
from loguru import logger

from agentforge.config import settings
from integrations.events.event_bus import Event


class EventStore:
    """Event store using Redis Streams"""
    
    STREAM_KEY = "agentforge:events"
    MAX_STREAM_LENGTH = 10000
    
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or settings.redis_url
        self._redis: Optional[redis.Redis] = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize Redis connection"""
        if self._initialized:
            return
        
        try:
            self._redis = redis.from_url(self.redis_url, decode_responses=True)
            await self._redis.ping()
            self._initialized = True
            logger.info("EventStore initialized with Redis")
        except Exception as e:
            logger.warning(f"EventStore initialization failed: {e}")
            self._redis = None
    
    async def store_event(self, event: Event) -> str:
        """Store event in Redis Stream"""
        if not self._redis:
            await self.initialize()
        
        if not self._redis:
            logger.warning("Redis not available, event not stored")
            return ""
        
        try:
            event_data = {
                "id": event.id,
                "type": event.type,
                "source": event.source,
                "data": json.dumps(event.data, ensure_ascii=False),
                "timestamp": event.timestamp,
                "metadata": json.dumps(event.metadata, ensure_ascii=False)
            }
            
            entry_id = await self._redis.xadd(
                self.STREAM_KEY,
                event_data,
                maxlen=self.MAX_STREAM_LENGTH
            )
            
            logger.debug(f"Stored event {event.id} in stream: {entry_id}")
            return entry_id
            
        except Exception as e:
            logger.error(f"Failed to store event: {e}")
            return ""
    
    async def get_events(
        self,
        count: int = 100,
        event_type: Optional[str] = None
    ) -> List[Event]:
        """Get events from stream"""
        if not self._redis:
            await self.initialize()
        
        if not self._redis:
            return []
        
        try:
            events = await self._redis.xrange(
                self.STREAM_KEY,
                count=count
            )
            
            result = []
            for entry_id, data in events:
                try:
                    event = Event(
                        id=data.get("id", ""),
                        type=data.get("type", ""),
                        source=data.get("source", ""),
                        data=json.loads(data.get("data", "{}")),
                        timestamp=data.get("timestamp", ""),
                        metadata=json.loads(data.get("metadata", "{}"))
                    )
                    
                    if event_type is None or event.type == event_type:
                        result.append(event)
                        
                except Exception as e:
                    logger.error(f"Failed to parse event: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get events: {e}")
            return []
    
    async def get_events_since(
        self,
        since_id: str,
        count: int = 100
    ) -> List[Event]:
        """Get events since a specific ID"""
        if not self._redis:
            await self.initialize()
        
        if not self._redis:
            return []
        
        try:
            events = await self._redis.xrange(
                self.STREAM_KEY,
                min=since_id,
                count=count
            )
            
            result = []
            for entry_id, data in events:
                try:
                    event = Event(
                        id=data.get("id", ""),
                        type=data.get("type", ""),
                        source=data.get("source", ""),
                        data=json.loads(data.get("data", "{}")),
                        timestamp=data.get("timestamp", ""),
                        metadata=json.loads(data.get("metadata", "{}"))
                    )
                    result.append(event)
                except Exception as e:
                    logger.error(f"Failed to parse event: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get events since {since_id}: {e}")
            return []
    
    async def replay_events(self, since_id: str = "0-0") -> int:
        """Replay events from a specific ID"""
        events = await self.get_events_since(since_id)
        
        from integrations.events.event_bus import event_bus
        
        replayed = 0
        for event in events:
            await event_bus.publish(
                event_type=event.type,
                source=event.source,
                data=event.data,
                metadata=event.metadata
            )
            replayed += 1
        
        logger.info(f"Replayed {replayed} events")
        return replayed
    
    async def clear_events(self) -> None:
        """Clear all events from stream"""
        if not self._redis:
            await self.initialize()
        
        if not self._redis:
            return
        
        try:
            await self._redis.delete(self.STREAM_KEY)
            logger.info("Cleared all events from stream")
        except Exception as e:
            logger.error(f"Failed to clear events: {e}")
    
    async def get_stream_length(self) -> int:
        """Get stream length"""
        if not self._redis:
            await self.initialize()
        
        if not self._redis:
            return 0
        
        try:
            return await self._redis.xlen(self.STREAM_KEY)
        except Exception as e:
            logger.error(f"Failed to get stream length: {e}")
            return 0
