"""
AgentForge Memory Store - Short-term (Redis) and Long-term (Qdrant) Memory
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import redis.asyncio as redis
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from loguru import logger
from agentforge.config import settings


class MemoryStore:
    """Memory store with Redis for short-term and Qdrant for long-term storage"""
    
    COLLECTION_NAME = "agentforge_memories"
    
    def __init__(
        self,
        redis_url: Optional[str] = None,
        qdrant_url: Optional[str] = None
    ):
        self.redis_url = redis_url or settings.redis_url
        self.qdrant_url = qdrant_url or settings.qdrant_url
        
        self._redis: Optional[redis.Redis] = None
        self._qdrant: Optional[QdrantClient] = None
        
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize connections to Redis and Qdrant"""
        if self._initialized:
            return
        
        try:
            self._redis = redis.from_url(self.redis_url, decode_responses=True)
            await self._redis.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            self._redis = None
        
        try:
            self._qdrant = QdrantClient(url=self.qdrant_url)
            collections = self._qdrant.get_collections()
            
            if self.COLLECTION_NAME not in [c.name for c in collections.collections]:
                self._qdrant.create_collection(
                    collection_name=self.COLLECTION_NAME,
                    vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
                )
                logger.info(f"Created Qdrant collection: {self.COLLECTION_NAME}")
            
            logger.info("Qdrant connection established")
        except Exception as e:
            logger.warning(f"Qdrant connection failed: {e}")
            self._qdrant = None
        
        self._initialized = True
    
    async def store_memory(
        self,
        content: str,
        memory_type: str = "general",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store memory in both short-term and long-term storage"""
        await self.initialize()
        
        memory_id = f"{memory_type}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        memory_data = {
            "id": memory_id,
            "content": content,
            "type": memory_type,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        if self._redis:
            try:
                key = f"memory:{memory_id}"
                await self._redis.setex(
                    key,
                    86400,
                    json.dumps(memory_data, ensure_ascii=False)
                )
                await self._redis.lpush("memory:recent", memory_id)
                await self._redis.ltrim("memory:recent", 0, 99)
                logger.debug(f"Stored short-term memory: {memory_id}")
            except Exception as e:
                logger.error(f"Failed to store in Redis: {e}")
        
        if self._qdrant:
            try:
                point = PointStruct(
                    id=hash(memory_id) % (2**63),
                    vector=[0.0] * 1536,
                    payload=memory_data
                )
                self._qdrant.upsert(
                    collection_name=self.COLLECTION_NAME,
                    points=[point]
                )
                logger.debug(f"Stored long-term memory: {memory_id}")
            except Exception as e:
                logger.error(f"Failed to store in Qdrant: {e}")
        
        return memory_id
    
    async def search_memories(
        self,
        query: str,
        limit: int = 5,
        memory_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search memories from storage"""
        await self.initialize()
        
        memories = []
        
        if self._redis:
            try:
                memory_ids = await self._redis.lrange("memory:recent", 0, limit - 1)
                for mid in memory_ids:
                    data = await self._redis.get(f"memory:{mid}")
                    if data:
                        memory = json.loads(data)
                        if memory_type is None or memory.get("type") == memory_type:
                            memories.append(memory)
            except Exception as e:
                logger.error(f"Failed to search Redis: {e}")
        
        return memories[:limit]
    
    async def consolidate_memories(self) -> int:
        """Consolidate short-term memories into long-term storage"""
        await self.initialize()
        
        consolidated = 0
        
        if self._redis:
            try:
                memory_ids = await self._redis.lrange("memory:recent", 0, -1)
                for mid in memory_ids:
                    data = await self._redis.get(f"memory:{mid}")
                    if data:
                        memory = json.loads(data)
                        if self._qdrant:
                            point = PointStruct(
                                id=hash(mid) % (2**63),
                                vector=[0.0] * 1536,
                                payload=memory
                            )
                            self._qdrant.upsert(
                                collection_name=self.COLLECTION_NAME,
                                points=[point]
                            )
                        consolidated += 1
                
                logger.info(f"Consolidated {consolidated} memories")
            except Exception as e:
                logger.error(f"Memory consolidation failed: {e}")
        
        return consolidated
    
    async def clear_short_term(self) -> None:
        """Clear short-term memory cache"""
        if self._redis:
            try:
                memory_ids = await self._redis.lrange("memory:recent", 0, -1)
                for mid in memory_ids:
                    await self._redis.delete(f"memory:{mid}")
                await self._redis.delete("memory:recent")
                logger.info("Cleared short-term memory cache")
            except Exception as e:
                logger.error(f"Failed to clear short-term memory: {e}")
