"""
Memory 模块单元测试

测试 AgentForge Memory 存储功能，包括：
- MemoryStore: 内存存储（Redis + Qdrant）
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any
import json

from agentforge.memory.memory_store import MemoryStore


@pytest.fixture
def mock_redis():
    """Mock Redis 客户端"""
    redis_mock = MagicMock()
    redis_mock.setex = AsyncMock(return_value=True)
    redis_mock.lpush = AsyncMock(return_value=1)
    redis_mock.ltrim = AsyncMock(return_value=True)
    redis_mock.lrange = AsyncMock(return_value=["memory_001", "memory_002"])
    redis_mock.get = AsyncMock(return_value=json.dumps({
        "id": "memory_001",
        "content": "Test memory content",
        "type": "conversation",
        "timestamp": datetime.now().isoformat()
    }))
    redis_mock.delete = AsyncMock(return_value=1)
    redis_mock.ping = AsyncMock(return_value=True)
    return redis_mock


@pytest.fixture
def mock_qdrant():
    """Mock Qdrant 客户端"""
    qdrant_mock = MagicMock()
    qdrant_mock.get_collections = MagicMock(return_value=MagicMock(collections=[]))
    qdrant_mock.create_collection = MagicMock(return_value=True)
    qdrant_mock.upsert = MagicMock(return_value=True)
    return qdrant_mock


@pytest.fixture
def memory_store_config():
    """MemoryStore 测试配置"""
    return {
        "redis_url": "redis://localhost:6379",
        "qdrant_url": "http://localhost:6333"
    }


class TestMemoryStore:
    """MemoryStore 测试"""
    
    @pytest.mark.asyncio
    async def test_store_initialization(self, memory_store_config):
        """测试存储初始化"""
        store = MemoryStore(
            redis_url=memory_store_config["redis_url"],
            qdrant_url=memory_store_config["qdrant_url"]
        )
        
        assert store.redis_url == "redis://localhost:6379"
        assert store.qdrant_url == "http://localhost:6333"
        assert store._initialized is False
        assert store._redis is None
        assert store._qdrant is None
    
    @pytest.mark.asyncio
    async def test_initialize_success(
        self,
        memory_store_config,
        mock_redis,
        mock_qdrant
    ):
        """测试初始化成功"""
        with patch("agentforge.memory.memory_store.redis.from_url", return_value=mock_redis):
            with patch("agentforge.memory.memory_store.QdrantClient", return_value=mock_qdrant):
                store = MemoryStore(**memory_store_config)
                await store.initialize()
                
                assert store._initialized is True
                assert store._redis is not None
                assert store._qdrant is not None
    
    @pytest.mark.asyncio
    async def test_initialize_redis_failure(
        self,
        memory_store_config,
        mock_qdrant
    ):
        """测试 Redis 初始化失败"""
        with patch("agentforge.memory.memory_store.redis.from_url", side_effect=Exception("Redis connection failed")):
            with patch("agentforge.memory.memory_store.QdrantClient", return_value=mock_qdrant):
                store = MemoryStore(**memory_store_config)
                await store.initialize()
                
                assert store._initialized is True
                assert store._redis is None
                assert store._qdrant is not None
    
    @pytest.mark.asyncio
    async def test_initialize_qdrant_failure(
        self,
        memory_store_config,
        mock_redis
    ):
        """测试 Qdrant 初始化失败"""
        with patch("agentforge.memory.memory_store.redis.from_url", return_value=mock_redis):
            with patch("agentforge.memory.memory_store.QdrantClient", side_effect=Exception("Qdrant connection failed")):
                store = MemoryStore(**memory_store_config)
                await store.initialize()
                
                assert store._initialized is True
                assert store._redis is not None
                assert store._qdrant is None
    
    @pytest.mark.asyncio
    async def test_initialize_already_initialized(
        self,
        memory_store_config,
        mock_redis,
        mock_qdrant
    ):
        """测试重复初始化"""
        with patch("agentforge.memory.memory_store.redis.from_url", return_value=mock_redis):
            with patch("agentforge.memory.memory_store.QdrantClient", return_value=mock_qdrant):
                store = MemoryStore(**memory_store_config)
                await store.initialize()
                
                call_count_before = mock_redis.ping.call_count
                await store.initialize()
                call_count_after = mock_redis.ping.call_count
                
                assert call_count_before == call_count_after
    
    @pytest.mark.asyncio
    async def test_store_memory_success(
        self,
        memory_store_config,
        mock_redis,
        mock_qdrant
    ):
        """测试存储记忆成功"""
        with patch("agentforge.memory.memory_store.redis.from_url", return_value=mock_redis):
            with patch("agentforge.memory.memory_store.QdrantClient", return_value=mock_qdrant):
                store = MemoryStore(**memory_store_config)
                await store.initialize()
                
                memory_id = await store.store_memory(
                    content="Test memory content",
                    memory_type="conversation",
                    metadata={"user_id": "123", "session": "test"}
                )
                
                assert memory_id.startswith("conversation_")
                mock_redis.setex.assert_called_once()
                mock_redis.lpush.assert_called_once()
                mock_redis.ltrim.assert_called_once()
                mock_qdrant.upsert.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_store_memory_redis_only(
        self,
        memory_store_config,
        mock_redis
    ):
        """测试仅 Redis 存储（Qdrant 不可用）"""
        with patch("agentforge.memory.memory_store.redis.from_url", return_value=mock_redis):
            with patch("agentforge.memory.memory_store.QdrantClient", side_effect=Exception("Qdrant failed")):
                store = MemoryStore(**memory_store_config)
                await store.initialize()
                
                memory_id = await store.store_memory(
                    content="Redis only memory",
                    memory_type="general"
                )
                
                assert memory_id.startswith("general_")
                mock_redis.setex.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_store_memory_qdrant_only(
        self,
        memory_store_config,
        mock_qdrant
    ):
        """测试仅 Qdrant 存储（Redis 不可用）"""
        with patch("agentforge.memory.memory_store.redis.from_url", side_effect=Exception("Redis failed")):
            with patch("agentforge.memory.memory_store.QdrantClient", return_value=mock_qdrant):
                store = MemoryStore(**memory_store_config)
                await store.initialize()
                
                memory_id = await store.store_memory(
                    content="Qdrant only memory",
                    memory_type="learning"
                )
                
                assert memory_id.startswith("learning_")
                mock_qdrant.upsert.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_store_memory_with_default_type(
        self,
        memory_store_config,
        mock_redis,
        mock_qdrant
    ):
        """测试使用默认类型存储记忆"""
        with patch("agentforge.memory.memory_store.redis.from_url", return_value=mock_redis):
            with patch("agentforge.memory.memory_store.QdrantClient", return_value=mock_qdrant):
                store = MemoryStore(**memory_store_config)
                await store.initialize()
                
                memory_id = await store.store_memory(content="Default type memory")
                
                assert memory_id.startswith("general_")
    
    @pytest.mark.asyncio
    async def test_store_memory_with_empty_metadata(
        self,
        memory_store_config,
        mock_redis,
        mock_qdrant
    ):
        """测试使用空元数据存储记忆"""
        with patch("agentforge.memory.memory_store.redis.from_url", return_value=mock_redis):
            with patch("agentforge.memory.memory_store.QdrantClient", return_value=mock_qdrant):
                store = MemoryStore(**memory_store_config)
                await store.initialize()
                
                memory_id = await store.store_memory(
                    content="Empty metadata memory",
                    metadata={}
                )
                
                assert memory_id is not None
    
    @pytest.mark.asyncio
    async def test_search_memories_success(
        self,
        memory_store_config,
        mock_redis,
        mock_qdrant
    ):
        """测试搜索记忆成功"""
        with patch("agentforge.memory.memory_store.redis.from_url", return_value=mock_redis):
            with patch("agentforge.memory.memory_store.QdrantClient", return_value=mock_qdrant):
                store = MemoryStore(**memory_store_config)
                await store.initialize()
                
                memories = await store.search_memories(
                    query="test query",
                    limit=5
                )
                
                assert len(memories) <= 5
                mock_redis.lrange.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_memories_with_type_filter(
        self,
        memory_store_config,
        mock_redis
    ):
        """测试按类型过滤搜索记忆"""
        mock_redis.get = AsyncMock(return_value=json.dumps({
            "id": "memory_001",
            "content": "Test",
            "type": "conversation",
            "timestamp": datetime.now().isoformat()
        }))
        
        with patch("agentforge.memory.memory_store.redis.from_url", return_value=mock_redis):
            store = MemoryStore(**memory_store_config)
            await store.initialize()
            
            memories = await store.search_memories(
                query="test",
                limit=5,
                memory_type="conversation"
            )
            
            for memory in memories:
                assert memory.get("type") == "conversation"
    
    @pytest.mark.asyncio
    async def test_search_memories_redis_failure(
        self,
        memory_store_config,
        mock_qdrant
    ):
        """测试 Redis 失败时的搜索"""
        with patch("agentforge.memory.memory_store.redis.from_url", side_effect=Exception("Redis failed")):
            with patch("agentforge.memory.memory_store.QdrantClient", return_value=mock_qdrant):
                store = MemoryStore(**memory_store_config)
                await store.initialize()
                
                memories = await store.search_memories(query="test")
                
                assert memories == []
    
    @pytest.mark.asyncio
    async def test_search_memories_empty_result(
        self,
        memory_store_config,
        mock_redis
    ):
        """测试空搜索结果"""
        mock_redis.lrange = AsyncMock(return_value=[])
        
        with patch("agentforge.memory.memory_store.redis.from_url", return_value=mock_redis):
            store = MemoryStore(**memory_store_config)
            await store.initialize()
            
            memories = await store.search_memories(query="nonexistent")
            
            assert memories == []
    
    @pytest.mark.asyncio
    async def test_consolidate_memories_success(
        self,
        memory_store_config,
        mock_redis,
        mock_qdrant
    ):
        """测试记忆巩固成功"""
        mock_redis.lrange = AsyncMock(return_value=["memory_001", "memory_002"])
        mock_redis.get = AsyncMock(return_value=json.dumps({
            "id": "memory_001",
            "content": "Test memory",
            "type": "conversation"
        }))
        
        with patch("agentforge.memory.memory_store.redis.from_url", return_value=mock_redis):
            with patch("agentforge.memory.memory_store.QdrantClient", return_value=mock_qdrant):
                store = MemoryStore(**memory_store_config)
                await store.initialize()
                
                count = await store.consolidate_memories()
                
                assert count >= 0
                mock_redis.lrange.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_consolidate_memories_empty(
        self,
        memory_store_config,
        mock_redis
    ):
        """测试空记忆巩固"""
        mock_redis.lrange = AsyncMock(return_value=[])
        
        with patch("agentforge.memory.memory_store.redis.from_url", return_value=mock_redis):
            store = MemoryStore(**memory_store_config)
            await store.initialize()
            
            count = await store.consolidate_memories()
            
            assert count == 0
    
    @pytest.mark.asyncio
    async def test_consolidate_memories_redis_failure(
        self,
        memory_store_config
    ):
        """测试 Redis 失败时的记忆巩固"""
        with patch("agentforge.memory.memory_store.redis.from_url", side_effect=Exception("Redis failed")):
            store = MemoryStore(**memory_store_config)
            await store.initialize()
            
            count = await store.consolidate_memories()
            
            assert count == 0
    
    @pytest.mark.asyncio
    async def test_clear_short_term_success(
        self,
        memory_store_config,
        mock_redis
    ):
        """测试清除短期记忆成功"""
        mock_redis.lrange = AsyncMock(return_value=["memory_001", "memory_002"])
        
        with patch("agentforge.memory.memory_store.redis.from_url", return_value=mock_redis):
            store = MemoryStore(**memory_store_config)
            await store.initialize()
            
            await store.clear_short_term()
            
            mock_redis.delete.assert_called()
    
    @pytest.mark.asyncio
    async def test_clear_short_term_empty(
        self,
        memory_store_config,
        mock_redis
    ):
        """测试清除空短期记忆"""
        mock_redis.lrange = AsyncMock(return_value=[])
        
        with patch("agentforge.memory.memory_store.redis.from_url", return_value=mock_redis):
            store = MemoryStore(**memory_store_config)
            await store.initialize()
            
            await store.clear_short_term()
            
            mock_redis.delete.assert_called()
    
    @pytest.mark.asyncio
    async def test_clear_short_term_failure(
        self,
        memory_store_config,
        mock_redis
    ):
        """测试清除短期记忆失败"""
        mock_redis.lrange = AsyncMock(side_effect=Exception("Redis error"))
        
        with patch("agentforge.memory.memory_store.redis.from_url", return_value=mock_redis):
            store = MemoryStore(**memory_store_config)
            await store.initialize()
            
            await store.clear_short_term()
    
    @pytest.mark.asyncio
    async def test_store_memory_redis_error_handling(
        self,
        memory_store_config,
        mock_redis,
        mock_qdrant
    ):
        """测试 Redis 错误处理"""
        mock_redis.setex = AsyncMock(side_effect=Exception("Redis storage failed"))
        
        with patch("agentforge.memory.memory_store.redis.from_url", return_value=mock_redis):
            with patch("agentforge.memory.memory_store.QdrantClient", return_value=mock_qdrant):
                store = MemoryStore(**memory_store_config)
                await store.initialize()
                
                memory_id = await store.store_memory(content="Test")
                
                assert memory_id is not None
    
    @pytest.mark.asyncio
    async def test_store_memory_qdrant_error_handling(
        self,
        memory_store_config,
        mock_redis,
        mock_qdrant
    ):
        """测试 Qdrant 错误处理"""
        mock_qdrant.upsert = MagicMock(side_effect=Exception("Qdrant storage failed"))
        
        with patch("agentforge.memory.memory_store.redis.from_url", return_value=mock_redis):
            with patch("agentforge.memory.memory_store.QdrantClient", return_value=mock_qdrant):
                store = MemoryStore(**memory_store_config)
                await store.initialize()
                
                memory_id = await store.store_memory(content="Test")
                
                assert memory_id is not None
    
    @pytest.mark.asyncio
    async def test_search_memories_json_decode_error(
        self,
        memory_store_config,
        mock_redis
    ):
        """测试 JSON 解码错误处理"""
        mock_redis.get = AsyncMock(return_value="invalid json")
        
        with patch("agentforge.memory.memory_store.redis.from_url", return_value=mock_redis):
            store = MemoryStore(**memory_store_config)
            await store.initialize()
            
            memories = await store.search_memories(query="test")
            
            assert memories == [] or len(memories) == 0
