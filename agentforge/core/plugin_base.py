"""插件系统 - 插件基类和接口定义."""

from abc import ABC, abstractmethod
from typing import Any


class Plugin(ABC):
    """插件基类."""

    # 插件元数据
    name: str = "my_plugin"
    version: str = "1.0.0"
    description: str = "我的插件"
    author: str = "Unknown"

    def __init__(self, config: dict[str, Any] | None = None):
        """初始化插件."""
        self.config = config or {}
        self._enabled = False

    @abstractmethod
    async def initialize(self):
        """初始化插件."""
        pass

    @abstractmethod
    async def shutdown(self):
        """关闭插件."""
        pass

    def get_capabilities(self) -> list[str]:
        """返回插件能力列表."""
        return []

    def is_enabled(self) -> bool:
        """检查插件是否启用."""
        return self._enabled

    def enable(self):
        """启用插件."""
        self._enabled = True

    def disable(self):
        """禁用插件."""
        self._enabled = False

    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置项."""
        return self.config.get(key, default)

    def validate_config(self) -> bool:
        """验证配置."""
        return True


class ActionPlugin(Plugin):
    """动作插件基类."""

    @abstractmethod
    async def execute(self, params: dict[str, Any], context: Any) -> Any:
        """执行动作."""
        pass

    def get_capabilities(self) -> list[str]:
        """返回支持的动作类型."""
        return ["action"]


class TriggerPlugin(Plugin):
    """触发器插件基类."""

    @abstractmethod
    async def check_trigger(self, event_data: dict[str, Any]) -> bool:
        """检查是否触发."""
        pass

    def get_capabilities(self) -> list[str]:
        """返回支持的触发器类型."""
        return ["trigger"]


class DataPlugin(Plugin):
    """数据源插件基类."""

    @abstractmethod
    async def query(self, query_params: dict[str, Any]) -> Any:
        """查询数据."""
        pass

    def get_capabilities(self) -> list[str]:
        """返回支持的数据类型."""
        return ["data_source"]


class AIPlugin(Plugin):
    """AI 能力插件基类."""

    @abstractmethod
    async def generate(self, prompt: str, options: dict[str, Any]) -> str:
        """生成内容."""
        pass

    def get_capabilities(self) -> list[str]:
        """返回支持的 AI 能力."""
        return ["ai_capability"]
