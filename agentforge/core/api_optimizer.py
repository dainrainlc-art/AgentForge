"""
AgentForge API Response Optimization Module
API 响应优化模块
"""
from typing import Optional, Any, Dict, List
from fastapi import Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
import gzip
import json
import asyncio
from datetime import datetime
from loguru import logger


class ResponseOptimizer:
    """响应优化器"""
    
    def __init__(self):
        self._min_size = 1024  # 最小压缩大小（1KB）
        self._compression_level = 6  # Gzip 压缩级别（1-9）
    
    def compress_response(self, content: bytes) -> bytes:
        """压缩响应内容"""
        if len(content) < self._min_size:
            return content
        
        try:
            compressed = gzip.compress(
                content,
                compresslevel=self._compression_level
            )
            return compressed
        except Exception as e:
            logger.error(f"Compression error: {e}")
            return content
    
    def create_optimized_response(
        self,
        content: Any,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        use_gzip: bool = True
    ) -> Response:
        """
        创建优化的响应
        
        Args:
            content: 响应内容
            status_code: 状态码
            headers: 响应头
            use_gzip: 是否使用 Gzip 压缩
            
        Returns:
            优化的响应
        """
        # 使用 JSONResponse 进行 JSON 序列化
        if isinstance(content, dict) or isinstance(content, list):
            response = JSONResponse(
                content=content,
                status_code=status_code,
                headers=headers
            )
        else:
            response = Response(
                content=str(content),
                status_code=status_code,
                headers=headers,
                media_type="text/plain"
            )
        
        # Gzip 压缩
        if use_gzip and isinstance(content, (dict, list)):
            content_bytes = json.dumps(content).encode()
            if len(content_bytes) >= self._min_size:
                compressed = self.compress_response(content_bytes)
                if len(compressed) < len(content_bytes):
                    response = Response(
                        content=compressed,
                        status_code=status_code,
                        headers={
                            **(headers or {}),
                            "Content-Encoding": "gzip",
                            "Content-Type": "application/json"
                        }
                    )
        
        return response


class PaginationOptimizer:
    """分页优化器"""
    
    @staticmethod
    def paginate(
        items: List[Any],
        page: int = 1,
        page_size: int = 20,
        total: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        分页响应
        
        Args:
            items: 数据项
            page: 页码
            page_size: 每页数量
            total: 总数
            
        Returns:
            分页响应
        """
        if total is None:
            total = len(items)
        
        start = (page - 1) * page_size
        end = start + page_size
        
        paginated_items = items[start:end]
        
        return {
            "items": paginated_items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "has_next": end < total,
            "has_prev": page > 1
        }


class BatchQueryOptimizer:
    """批量查询优化器"""
    
    @staticmethod
    async def batch_query(
        query_func,
        items: List[Any],
        batch_size: int = 10,
        max_concurrency: int = 5
    ) -> List[Any]:
        """
        批量查询优化
        
        Args:
            query_func: 查询函数
            items: 查询项
            batch_size: 批量大小
            max_concurrency: 最大并发数
            
        Returns:
            查询结果
        """
        results = []
        
        # 分批处理
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            
            # 并发执行
            semaphore = asyncio.Semaphore(max_concurrency)
            
            async def limited_query(item):
                async with semaphore:
                    return await query_func(item)
            
            batch_results = await asyncio.gather(*[limited_query(item) for item in batch])
            results.extend(batch_results)
        
        return results


class StreamingOptimizer:
    """流式响应优化器"""
    
    @staticmethod
    async def stream_generator(
        data_source,
        chunk_size: int = 100
    ):
        """
        流式生成器
        
        Args:
            data_source: 数据源
            chunk_size: 块大小
            
        Yields:
            数据块
        """
        buffer = []
        
        async for item in data_source:
            buffer.append(item)
            
            if len(buffer) >= chunk_size:
                yield json.dumps(buffer).encode()
                buffer = []
        
        if buffer:
            yield json.dumps(buffer).encode()
    
    @staticmethod
    def create_streaming_response(
        data_source,
        media_type: str = "application/json"
    ) -> StreamingResponse:
        """
        创建流式响应
        
        Args:
            data_source: 数据源
            media_type: 媒体类型
            
        Returns:
            流式响应
        """
        return StreamingResponse(
            StreamingOptimizer.stream_generator(data_source),
            media_type=media_type
        )


# 中间件

async def gzip_middleware(request: Request, call_next):
    """
    Gzip 压缩中间件
    
    Args:
        request: 请求
        call_next: 下一个处理函数
        
    Returns:
        响应
    """
    response = await call_next(request)
    
    # 检查是否支持 Gzip
    accept_encoding = request.headers.get("accept-encoding", "")
    
    if "gzip" in accept_encoding.lower():
        # 获取响应体
        body = b""
        async for chunk in response.body_iterator:
            body += chunk
        
        # 压缩
        if len(body) >= 1024:
            compressed_body = gzip.compress(body)
            
            # 创建新响应
            return Response(
                content=compressed_body,
                status_code=response.status_code,
                headers={
                    **dict(response.headers),
                    "Content-Encoding": "gzip",
                    "Content-Length": str(len(compressed_body))
                }
            )
    
    return response


# 工具函数

def optimize_response(
    data: Any,
    use_pagination: bool = False,
    page: int = 1,
    page_size: int = 20,
    total: Optional[int] = None
) -> Dict[str, Any]:
    """
    优化响应数据
    
    Args:
        data: 数据
        use_pagination: 是否分页
        page: 页码
        page_size: 每页数量
        total: 总数
        
    Returns:
        优化的响应数据
    """
    if use_pagination and isinstance(data, list):
        return PaginationOptimizer.paginate(data, page, page_size, total)
    
    return {
        "data": data,
        "timestamp": datetime.now().isoformat(),
        "success": True
    }


async def cache_control_middleware(request: Request, call_next):
    """
    缓存控制中间件
    
    Args:
        request: 请求
        call_next: 下一个处理函数
        
    Returns:
        响应
    """
    response = await call_next(request)
    
    # 添加缓存控制头
    if request.method == "GET":
        # 根据路径设置不同的缓存策略
        if "/api/" in request.url.path:
            # API 响应：短时间缓存
            response.headers["Cache-Control"] = "public, max-age=60"
        elif "/static/" in request.url.path:
            # 静态资源：长时间缓存
            response.headers["Cache-Control"] = "public, max-age=31536000"
    
    return response
