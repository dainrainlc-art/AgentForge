"""插件系统 - 文件处理插件."""

import aiofiles
import json
import csv
import io
from pathlib import Path
from typing import Any

from loguru import logger

from agentforge.core.plugin_base import ActionPlugin


class FilePlugin(ActionPlugin):
    """文件处理插件."""

    name = "file"
    version = "1.0.0"
    description = "文件读写和处理"
    author = "System"

    def __init__(self, config: dict | None = None):
        super().__init__(config)
        import tempfile
        base_dir = self.get_config("base_dir")
        self.base_dir = Path(base_dir) if base_dir else Path(tempfile.mkdtemp(prefix="file_plugin_"))
        self.max_file_size = self.get_config("max_file_size", 10 * 1024 * 1024)  # 10MB

    async def initialize(self):
        """初始化插件."""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.enable()
        logger.info(f"文件处理插件已初始化，基础目录：{self.base_dir}")

    async def shutdown(self):
        """关闭插件."""
        self.disable()
        logger.info("文件处理插件已关闭")

    def get_capabilities(self) -> list[str]:
        """返回插件能力."""
        return ["action", "file_operation"]

    async def execute(self, params: dict, context=None) -> dict:
        """执行文件操作."""
        operation = params.get("operation", "read")
        file_path = params.get("path", "")

        if not file_path:
            raise ValueError("必须指定文件路径")

        if operation == "read":
            return await self.read_file(file_path)
        elif operation == "write":
            content = params.get("content", "")
            return await self.write_file(file_path, content)
        elif operation == "read_json":
            return await self.read_json(file_path)
        elif operation == "write_json":
            data = params.get("data", {})
            return await self.write_json(file_path, data)
        elif operation == "read_csv":
            return await self.read_csv(file_path)
        else:
            raise ValueError(f"不支持的操作：{operation}")

    async def read_file(self, file_path: str) -> dict:
        """读取文件."""
        try:
            full_path = self._get_full_path(file_path)

            if not full_path.exists():
                return {"error": "文件不存在"}

            # 检查文件大小
            if full_path.stat().st_size > self.max_file_size:
                return {"error": "文件过大"}

            async with aiofiles.open(full_path, "r", encoding="utf-8") as f:
                content = await f.read()

            return {
                "path": str(full_path),
                "content": content,
                "size": full_path.stat().st_size,
            }

        except Exception as e:
            logger.error(f"读取文件失败：{str(e)}")
            return {"error": str(e)}

    async def write_file(self, file_path: str, content: str) -> dict:
        """写入文件."""
        try:
            full_path = self._get_full_path(file_path)
            full_path.parent.mkdir(parents=True, exist_ok=True)

            async with aiofiles.open(full_path, "w", encoding="utf-8") as f:
                await f.write(content)

            return {
                "path": str(full_path),
                "success": True,
                "size": len(content.encode("utf-8")),
            }

        except Exception as e:
            logger.error(f"写入文件失败：{str(e)}")
            return {"error": str(e)}

    async def read_json(self, file_path: str) -> dict:
        """读取 JSON 文件."""
        try:
            result = await self.read_file(file_path)

            if "error" in result:
                return result

            data = json.loads(result["content"])
            return {"path": result["path"], "data": data}

        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败：{str(e)}")
            return {"error": f"JSON 格式错误：{str(e)}"}
        except Exception as e:
            logger.error(f"读取 JSON 失败：{str(e)}")
            return {"error": str(e)}

    async def write_json(self, file_path: str, data: Any) -> dict:
        """写入 JSON 文件."""
        try:
            content = json.dumps(data, ensure_ascii=False, indent=2)
            return await self.write_file(file_path, content)

        except Exception as e:
            logger.error(f"写入 JSON 失败：{str(e)}")
            return {"error": str(e)}

    async def read_csv(self, file_path: str) -> dict:
        """读取 CSV 文件."""
        try:
            result = await self.read_file(file_path)

            if "error" in result:
                return result

            # 解析 CSV
            reader = csv.DictReader(io.StringIO(result["content"]))
            rows = list(reader)

            return {
                "path": result["path"],
                "data": rows,
                "row_count": len(rows),
            }

        except Exception as e:
            logger.error(f"读取 CSV 失败：{str(e)}")
            return {"error": str(e)}

    def _get_full_path(self, file_path: str) -> Path:
        """获取完整路径（防止目录遍历攻击）."""
        # 如果是绝对路径，转换为相对路径
        if Path(file_path).is_absolute():
            file_path = file_path.lstrip("/")

        full_path = self.base_dir / file_path

        # 确保路径在 base_dir 内
        try:
            full_path.resolve().relative_to(self.base_dir.resolve())
        except ValueError:
            raise ValueError("文件路径必须在基础目录内")

        return full_path

    def validate_config(self) -> bool:
        """验证配置."""
        try:
            self.base_dir.mkdir(parents=True, exist_ok=True)
            return True
        except Exception:
            return False
