"""
数据库集成测试
测试 PostgreSQL、Redis 和 Qdrant 的集成和数据流转

测试场景：
1. PostgreSQL - 用户、订单、知识文档的 CRUD 操作
2. Redis - 缓存、会话管理、速率限制
3. Qdrant - 向量存储和相似度搜索
4. 多数据库协同操作
"""
import pytest
import asyncio
from typing import List, Dict, Any
from datetime import datetime
from uuid import uuid4

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, text

# 测试数据库连接配置
TEST_DATABASE_URL = "postgresql+asyncpg://agentforge:test_password@localhost:5432/agentforge_test"


# ============================================================================
# 数据库连接夹具
# ============================================================================


@pytest.fixture(scope="session")
def db_engine():
    """创建数据库引擎"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=True,  # 输出 SQL 日志
        pool_pre_ping=True,
    )
    yield engine
    asyncio.run(engine.dispose())


@pytest.fixture(scope="function")
async def db_session(db_engine):
    """创建数据库会话（每个测试函数独立）"""
    async_session = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False, autocommit=False
    )

    session = async_session()

    try:
        yield session
        await session.rollback()  # 回滚所有更改
    finally:
        await session.close()


@pytest.fixture(scope="session")
def redis_client():
    """创建 Redis 客户端"""
    import redis.asyncio as redis

    client = redis.Redis(
        host="localhost",
        port=6379,
        db=1,  # 使用不同的 DB 避免冲突
        decode_responses=True,
    )
    yield client
    asyncio.run(client.aclose())


@pytest.fixture(scope="session")
def qdrant_client():
    """创建 Qdrant 客户端"""
    from qdrant_client import AsyncQdrantClient

    client = AsyncQdrantClient(
        host="localhost",
        port=6333,
    )
    yield client
    asyncio.run(client.close())


# ============================================================================
# PostgreSQL 集成测试
# ============================================================================


class TestPostgreSQLIntegration:
    """PostgreSQL 数据库集成测试"""

    @pytest.mark.asyncio
    async def test_database_connection(self, db_engine):
        """测试数据库连接是否成功"""
        async with db_engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            row = result.fetchone()
            assert row[0] == 1, "数据库连接失败"

    @pytest.mark.asyncio
    async def test_user_crud_operations(self, db_session):
        """测试用户的 CRUD 操作"""
        from agentforge.security.password_handler import PasswordHandler

        # Create
        user_id = uuid4()
        password_hash = PasswordHandler.hash_password("Test@123456")

        await db_session.execute(
            text(
                """
                INSERT INTO users (id, email, password_hash, name, is_active)
                VALUES (:id, :email, :password_hash, :name, :is_active)
            """
            ),
            {
                "id": user_id,
                "email": f"test_{uuid4()}@example.com",
                "password_hash": password_hash,
                "name": "测试用户",
                "is_active": True,
            },
        )
        await db_session.commit()

        # Read
        result = await db_session.execute(
            text("SELECT * FROM users WHERE id = :id"), {"id": user_id}
        )
        user = result.fetchone()
        assert user is not None
        assert user.email == f"test_{uuid4()}@example.com" or user.email.endswith("@example.com")

        # Update
        await db_session.execute(
            text("UPDATE users SET name = :name WHERE id = :id"),
            {"name": "更新后的名字", "id": user_id},
        )
        await db_session.commit()

        result = await db_session.execute(
            text("SELECT name FROM users WHERE id = :id"), {"id": user_id}
        )
        updated_user = result.fetchone()
        assert updated_user.name == "更新后的名字"

        # Delete
        await db_session.execute(text("DELETE FROM users WHERE id = :id"), {"id": user_id})
        await db_session.commit()

        result = await db_session.execute(
            text("SELECT * FROM users WHERE id = :id"), {"id": user_id}
        )
        deleted_user = result.fetchone()
        assert deleted_user is None

    @pytest.mark.asyncio
    async def test_order_with_user_relationship(self, db_session):
        """测试订单与用户的关联关系"""
        from agentforge.security.password_handler import PasswordHandler

        # 创建测试用户
        user_id = uuid4()
        password_hash = PasswordHandler.hash_password("Test@123456")

        await db_session.execute(
            text(
                """
                INSERT INTO users (id, email, password_hash, name, is_active)
                VALUES (:id, :email, :password_hash, :name, :is_active)
            """
            ),
            {
                "id": user_id,
                "email": f"order_test_{uuid4()}@example.com",
                "password_hash": password_hash,
                "name": "订单测试用户",
                "is_active": True,
            },
        )
        await db_session.commit()

        # 创建测试订单
        order_id = uuid4()
        await db_session.execute(
            text(
                """
                INSERT INTO orders (id, user_id, fiverr_order_id, status, amount, currency, description, metadata)
                VALUES (:id, :user_id, :fiverr_order_id, :status, :amount, :currency, :description, :metadata)
            """
            ),
            {
                "id": order_id,
                "user_id": user_id,
                "fiverr_order_id": "FO_TEST_123",
                "status": "active",
                "amount": 150.00,
                "currency": "USD",
                "description": "测试订单",
                "metadata": '{"buyer": "test_buyer", "delivery_days": 7}',
            },
        )
        await db_session.commit()

        # 查询订单及其关联用户
        result = await db_session.execute(
            text(
                """
                SELECT o.*, u.email as user_email
                FROM orders o
                JOIN users u ON o.user_id = u.id
                WHERE o.id = :id
            """
            ),
            {"id": order_id},
        )
        order_with_user = result.fetchone()

        assert order_with_user is not None
        assert order_with_user.fiverr_order_id == "FO_TEST_123"
        assert order_with_user.user_email.endswith("@example.com")

        # 清理数据
        await db_session.execute(text("DELETE FROM orders WHERE id = :id"), {"id": order_id})
        await db_session.execute(text("DELETE FROM users WHERE id = :id"), {"id": user_id})
        await db_session.commit()

    @pytest.mark.asyncio
    async def test_knowledge_document_with_tags(self, db_session):
        """测试知识文档和标签的存储"""
        doc_id = uuid4()

        # 插入知识文档
        await db_session.execute(
            text(
                """
                INSERT INTO knowledge_docs (id, title, content, source, doc_type, tags)
                VALUES (:id, :title, :content, :source, :doc_type, :tags)
            """
            ),
            {
                "id": doc_id,
                "title": "测试知识文档",
                "content": "这是测试内容",
                "source": "test_source",
                "doc_type": "integration_test",
                "tags": ["测试", "集成", "PostgreSQL"],
            },
        )
        await db_session.commit()

        # 查询并验证标签
        result = await db_session.execute(
            text("SELECT tags FROM knowledge_docs WHERE id = :id"), {"id": doc_id}
        )
        doc = result.fetchone()
        assert doc is not None
        assert "测试" in doc.tags
        assert "集成" in doc.tags

        # 清理
        await db_session.execute(text("DELETE FROM knowledge_docs WHERE id = :id"), {"id": doc_id})
        await db_session.commit()

    @pytest.mark.asyncio
    async def test_transaction_rollback(self, db_session):
        """测试事务回滚功能"""
        try:
            # 开始事务
            async with db_session.begin():
                user_id = uuid4()
                from agentforge.security.password_handler import PasswordHandler

                password_hash = PasswordHandler.hash_password("Test@123456")

                await db_session.execute(
                    text(
                        """
                        INSERT INTO users (id, email, password_hash, name, is_active)
                        VALUES (:id, :email, :password_hash, :name, :is_active)
                    """
                    ),
                    {
                        "id": user_id,
                        "email": f"rollback_test_{uuid4()}@example.com",
                        "password_hash": password_hash,
                        "name": "回滚测试",
                        "is_active": True,
                    },
                )

                # 模拟错误
                raise ValueError("模拟错误，触发回滚")

        except ValueError:
            # 预期中的错误
            pass

        # 验证数据已回滚
        result = await db_session.execute(
            text("SELECT * FROM users WHERE name = :name"), {"name": "回滚测试"}
        )
        users = result.fetchall()
        assert len(users) == 0, "事务回滚失败"


# ============================================================================
# Redis 集成测试
# ============================================================================


class TestRedisIntegration:
    """Redis 缓存集成测试"""

    @pytest.mark.asyncio
    async def test_redis_connection(self, redis_client):
        """测试 Redis 连接"""
        pong = await redis_client.ping()
        assert pong is True, "Redis 连接失败"

    @pytest.mark.asyncio
    async def test_cache_operations(self, redis_client):
        """测试缓存的增删改查操作"""
        # Set
        await redis_client.set("test_key", "test_value")
        value = await redis_client.get("test_key")
        assert value == "test_value"

        # Set with expiration
        await redis_client.setex("temp_key", 1, "temp_value")  # 1 秒过期
        assert await redis_client.exists("temp_key")

        # Delete
        await redis_client.delete("test_key")
        assert not await redis_client.exists("test_key")

    @pytest.mark.asyncio
    async def test_hash_operations(self, redis_client):
        """测试 Hash 操作"""
        user_data = {
            "name": "测试用户",
            "email": "test@example.com",
            "age": "25",
        }

        # HSET
        await redis_client.hset("user:1001", mapping=user_data)

        # HGET
        name = await redis_client.hget("user:1001", "name")
        assert name == "测试用户"

        # HGETALL
        all_data = await redis_client.hgetall("user:1001")
        assert all_data == user_data

        # HDEL
        await redis_client.hdel("user:1001", "age")
        age = await redis_client.hget("user:1001", "age")
        assert age is None

        # 清理
        await redis_client.delete("user:1001")

    @pytest.mark.asyncio
    async def test_list_operations(self, redis_client):
        """测试列表操作（用于队列）"""
        queue_name = "test_queue"

        # LPUSH
        await redis_client.lpush(queue_name, "task3", "task2", "task1")

        # LLEN
        length = await redis_client.llen(queue_name)
        assert length == 3

        # RPOP (FIFO)
        task = await redis_client.rpop(queue_name)
        assert task == "task1"

        # 清理
        await redis_client.delete(queue_name)

    @pytest.mark.asyncio
    async def test_rate_limiting(self, redis_client):
        """测试速率限制功能"""
        user_id = "test_user"
        limit = 5
        window = 60  # 秒

        key = f"rate_limit:{user_id}"

        # 模拟请求
        for i in range(limit):
            count = await redis_client.incr(key)
            if count == 1:
                await redis_client.expire(key, window)
            assert count <= limit

        # 超出限制
        count = await redis_client.incr(key)
        assert count > limit

        # 清理
        await redis_client.delete(key)

    @pytest.mark.asyncio
    async def test_session_management(self, redis_client):
        """测试会话管理"""
        session_id = "session_test_123"
        session_data = {
            "user_id": "123",
            "username": "testuser",
            "login_time": datetime.now().isoformat(),
        }

        # 存储会话
        await redis_client.hset(f"session:{session_id}", mapping=session_data)
        await redis_client.expire(f"session:{session_id}", 3600)  # 1 小时过期

        # 读取会话
        stored_data = await redis_client.hgetall(f"session:{session_id}")
        assert stored_data["username"] == "testuser"

        # 删除会话（登出）
        await redis_client.delete(f"session:{session_id}")
        assert not await redis_client.exists(f"session:{session_id}")


# ============================================================================
# Qdrant 向量数据库集成测试
# ============================================================================


class TestQdrantIntegration:
    """Qdrant 向量数据库集成测试"""

    @pytest.mark.asyncio
    async def test_qdrant_connection(self, qdrant_client):
        """测试 Qdrant 连接"""
        try:
            await qdrant_client.get_collections()
            assert True
        except Exception as e:
            pytest.fail(f"Qdrant 连接失败：{e}")

    @pytest.mark.asyncio
    async def test_vector_collection_operations(self, qdrant_client):
        """测试向量集合操作"""
        collection_name = "test_collection"

        try:
            # 删除已存在的集合
            await qdrant_client.delete_collection(collection_name)
        except Exception:
            pass

        # 创建集合
        from qdrant_client.http import models

        await qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(size=4, distance=models.Distance.COSINE),
        )

        # 验证集合存在
        collections = await qdrant_client.get_collections()
        collection_names = [c.name for c in collections.collections]
        assert collection_name in collection_names

        # 清理
        await qdrant_client.delete_collection(collection_name)

    @pytest.mark.asyncio
    async def test_vector_similarity_search(self, qdrant_client):
        """测试向量相似度搜索"""
        collection_name = "test_similarity"

        try:
            await qdrant_client.delete_collection(collection_name)
        except Exception:
            pass

        from qdrant_client.http import models

        # 创建集合
        await qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(size=4, distance=models.Distance.COSINE),
        )

        # 插入向量
        await qdrant_client.upsert(
            collection_name=collection_name,
            points=[
                models.PointStruct(
                    id=1,
                    vector=[0.1, 0.2, 0.3, 0.4],
                    payload={"text": "文档 1", "category": "A"},
                ),
                models.PointStruct(
                    id=2,
                    vector=[0.9, 0.8, 0.7, 0.6],
                    payload={"text": "文档 2", "category": "B"},
                ),
                models.PointStruct(
                    id=3,
                    vector=[0.15, 0.25, 0.35, 0.45],
                    payload={"text": "文档 3", "category": "A"},
                ),
            ],
        )

        # 相似度搜索
        search_results = await qdrant_client.search(
            collection_name=collection_name,
            query_vector=[0.1, 0.2, 0.3, 0.4],
            limit=2,
        )

        assert len(search_results) >= 1
        assert search_results[0].id == 1  # 最相似的应该是 ID 为 1 的向量

        # 带过滤的搜索
        filtered_results = await qdrant_client.search(
            collection_name=collection_name,
            query_vector=[0.1, 0.2, 0.3, 0.4],
            limit=2,
            filter=models.Filter(
                must=[models.FieldCondition(key="category", match=models.MatchValue(value="A"))]
            ),
        )

        assert len(filtered_results) >= 1
        assert all(
            filtered_results[i].payload.get("category") == "A" for i in range(len(filtered_results))
        )

        # 清理
        await qdrant_client.delete_collection(collection_name)

    @pytest.mark.asyncio
    async def test_vector_payload_operations(self, qdrant_client):
        """测试向量负载操作"""
        collection_name = "test_payload"

        try:
            await qdrant_client.delete_collection(collection_name)
        except Exception:
            pass

        from qdrant_client.http import models

        await qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(size=4, distance=models.Distance.COSINE),
        )

        # 插入带负载的向量
        await qdrant_client.upsert(
            collection_name=collection_name,
            points=[
                models.PointStruct(
                    id=1,
                    vector=[0.1, 0.2, 0.3, 0.4],
                    payload={
                        "title": "测试文档",
                        "content": "这是测试内容",
                        "tags": ["测试", "集成"],
                        "score": 0.95,
                    },
                )
            ],
        )

        # 检索负载
        retrieved = await qdrant_client.retrieve(
            collection_name=collection_name,
            ids=[1],
        )

        assert len(retrieved) == 1
        assert retrieved[0].payload["title"] == "测试文档"
        assert "测试" in retrieved[0].payload["tags"]
        assert retrieved[0].payload["score"] == 0.95

        # 更新负载
        await qdrant_client.set_payload(
            collection_name=collection_name,
            payload={"updated": True},
            points=[1],
        )

        updated = await qdrant_client.retrieve(
            collection_name=collection_name,
            ids=[1],
        )
        assert updated[0].payload.get("updated") is True

        # 清理
        await qdrant_client.delete_collection(collection_name)


# ============================================================================
# 多数据库协同测试
# ============================================================================


class TestMultiDatabaseCollaboration:
    """多数据库协同操作测试"""

    @pytest.mark.asyncio
    async def test_postgres_redis_collaboration(self, db_session, redis_client):
        """测试 PostgreSQL 和 Redis 协同工作"""
        from agentforge.security.password_handler import PasswordHandler

        user_id = str(uuid4())
        email = f"collab_test_{uuid4()}@example.com"

        # 1. 在 PostgreSQL 中创建用户
        password_hash = PasswordHandler.hash_password("Test@123456")
        await db_session.execute(
            text(
                """
                INSERT INTO users (id, email, password_hash, name, is_active)
                VALUES (:id, :email, :password_hash, :name, :is_active)
            """
            ),
            {
                "id": user_id,
                "email": email,
                "password_hash": password_hash,
                "name": "协同测试用户",
                "is_active": True,
            },
        )
        await db_session.commit()

        # 2. 在 Redis 中缓存用户数据
        await redis_client.hset(
            f"user:cache:{user_id}",
            mapping={"email": email, "name": "协同测试用户", "cached_at": datetime.now().isoformat()},
        )
        await redis_client.expire(f"user:cache:{user_id}", 3600)

        # 3. 从 Redis 读取缓存
        cached_user = await redis_client.hgetall(f"user:cache:{user_id}")
        assert cached_user["email"] == email

        # 4. 验证 PostgreSQL 中的数据
        result = await db_session.execute(
            text("SELECT email, name FROM users WHERE id = :id"), {"id": user_id}
        )
        db_user = result.fetchone()
        assert db_user.email == email

        # 5. 清理
        await db_session.execute(text("DELETE FROM users WHERE id = :id"), {"id": user_id})
        await db_session.commit()
        await redis_client.delete(f"user:cache:{user_id}")

    @pytest.mark.asyncio
    async def test_knowledge_base_workflow(self, db_session, qdrant_client):
        """测试知识库工作流程（PostgreSQL + Qdrant）"""
        import numpy as np

        doc_id = str(uuid4())
        collection_name = "knowledge_docs_test"

        try:
            # 1. 在 Qdrant 中创建集合
            from qdrant_client.http import models

            try:
                await qdrant_client.delete_collection(collection_name)
            except Exception:
                pass

            await qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(size=4, distance=models.Distance.COSINE),
            )

            # 2. 在 PostgreSQL 中创建知识文档
            await db_session.execute(
                text(
                    """
                    INSERT INTO knowledge_docs (id, title, content, source, doc_type, tags)
                    VALUES (:id, :title, :content, :source, :doc_type, :tags)
                """
                ),
                {
                    "id": doc_id,
                    "title": "测试知识文档",
                    "content": "这是测试内容，用于验证知识库工作流程。",
                    "source": "test",
                    "doc_type": "integration",
                    "tags": ["测试", "知识库"],
                },
            )
            await db_session.commit()

            # 3. 生成模拟向量并存储到 Qdrant
            mock_embedding = np.random.rand(4).tolist()
            await qdrant_client.upsert(
                collection_name=collection_name,
                points=[
                    models.PointStruct(
                        id=1,
                        vector=mock_embedding,
                        payload={"doc_id": doc_id, "title": "测试知识文档"},
                    )
                ],
            )

            # 4. 验证数据一致性
            result = await db_session.execute(
                text("SELECT title FROM knowledge_docs WHERE id = :id"), {"id": doc_id}
            )
            db_doc = result.fetchone()
            assert db_doc.title == "测试知识文档"

            # 5. 清理
            await db_session.execute(text("DELETE FROM knowledge_docs WHERE id = :id"), {"id": doc_id})
            await db_session.commit()
            await qdrant_client.delete_collection(collection_name)

        except Exception as e:
            # 确保清理
            try:
                await qdrant_client.delete_collection(collection_name)
            except Exception:
                pass
            raise e


# ============================================================================
# 数据库连接池测试
# ============================================================================


class TestDatabaseConnectionPool:
    """数据库连接池测试"""

    @pytest.mark.asyncio
    async def test_concurrent_database_operations(self, db_engine):
        """测试并发数据库操作"""
        async_session = async_sessionmaker(
            db_engine, class_=AsyncSession, expire_on_commit=False
        )

        async def create_test_user(session_id: int):
            """创建测试用户的辅助函数"""
            async with async_session() as session:
                user_id = uuid4()
                from agentforge.security.password_handler import PasswordHandler

                password_hash = PasswordHandler.hash_password("Test@123456")
                await session.execute(
                    text(
                        """
                        INSERT INTO users (id, email, password_hash, name, is_active)
                        VALUES (:id, :email, :password_hash, :name, :is_active)
                    """
                    ),
                    {
                        "id": user_id,
                        "email": f"concurrent_test_{session_id}_{uuid4()}@example.com",
                        "password_hash": password_hash,
                        "name": f"并发测试用户{session_id}",
                        "is_active": True,
                    },
                )
                await session.commit()
                return user_id

        # 并发创建 10 个用户
        tasks = [create_test_user(i) for i in range(10)]
        user_ids = await asyncio.gather(*tasks)

        assert len(user_ids) == 10

        # 清理
        async with async_session() as session:
            for user_id in user_ids:
                await session.execute(
                    text("DELETE FROM users WHERE id = :id"), {"id": str(user_id)}
                )
            await session.commit()
