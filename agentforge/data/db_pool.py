"""
Database Connection Pool Manager
"""
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager
import asyncpg
from loguru import logger

from agentforge.config import settings


class DatabasePool:
    """PostgreSQL connection pool manager"""
    
    _instance: Optional['DatabasePool'] = None
    _pool: Optional[asyncpg.Pool] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def initialize(
        self,
        min_size: int = 5,
        max_size: int = 20,
        max_queries: int = 50000,
        max_inactive_connection_lifetime: float = 300.0
    ):
        """Initialize connection pool"""
        if self._pool is not None:
            return
        
        try:
            self._pool = await asyncpg.create_pool(
                host=settings.postgres_host,
                port=settings.postgres_port,
                database=settings.postgres_db,
                user=settings.postgres_user,
                password=settings.postgres_password,
                min_size=min_size,
                max_size=max_size,
                max_queries=max_queries,
                max_inactive_connection_lifetime=max_inactive_connection_lifetime,
                command_timeout=60.0
            )
            logger.info(f"Database pool initialized (min={min_size}, max={max_size})")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise
    
    async def close(self):
        """Close connection pool"""
        if self._pool is not None:
            await self._pool.close()
            self._pool = None
            logger.info("Database pool closed")
    
    @asynccontextmanager
    async def acquire(self) -> AsyncGenerator[asyncpg.Connection, None]:
        """Acquire a connection from the pool"""
        if self._pool is None:
            await self.initialize()
        
        async with self._pool.acquire() as connection:
            try:
                yield connection
            except Exception as e:
                logger.error(f"Database error: {e}")
                raise
    
    async def execute(self, query: str, *args) -> str:
        """Execute a query"""
        async with self.acquire() as conn:
            return await conn.execute(query, *args)
    
    async def fetch(self, query: str, *args) -> list:
        """Fetch multiple rows"""
        async with self.acquire() as conn:
            return await conn.fetch(query, *args)
    
    async def fetchrow(self, query: str, *args) -> Optional[asyncpg.Record]:
        """Fetch a single row"""
        async with self.acquire() as conn:
            return await conn.fetchrow(query, *args)
    
    async def fetchval(self, query: str, *args):
        """Fetch a single value"""
        async with self.acquire() as conn:
            return await conn.fetchval(query, *args)
    
    async def execute_many(self, query: str, args_list: list) -> None:
        """Execute multiple queries in a transaction"""
        async with self.acquire() as conn:
            async with conn.transaction():
                await conn.executemany(query, args_list)
    
    @property
    def pool_size(self) -> int:
        """Get current pool size"""
        if self._pool is None:
            return 0
        return self._pool.get_size()
    
    @property
    def idle_connections(self) -> int:
        """Get number of idle connections"""
        if self._pool is None:
            return 0
        return self._pool.get_idle_size()


db_pool = DatabasePool()
