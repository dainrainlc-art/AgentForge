"""插件系统 - 插件管理器."""

import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Any, Type

from loguru import logger

from agentforge.core.plugin_base import Plugin


class PluginManager:
    """插件管理器."""

    def __init__(self, plugins_dir: str | None = None):
        if plugins_dir is None:
            plugins_dir = Path(__file__).parent.parent / "plugins"

        self.plugins_dir = Path(plugins_dir)
        self.plugins_dir.mkdir(parents=True, exist_ok=True)

        self._plugins: dict[str, Plugin] = {}
        self._plugin_classes: dict[str, Type[Plugin]] = {}

    async def initialize(self):
        """初始化插件管理器."""
        await self.load_plugins()

    async def load_plugins(self):
        """加载所有插件."""
        if not self.plugins_dir.exists():
            logger.warning(f"插件目录不存在：{self.plugins_dir}")
            return

        # 加载内置插件
        await self._load_builtin_plugins()

        # 加载外部插件
        await self._load_external_plugins()

        logger.info(f"加载了 {len(self._plugins)} 个插件")

    async def _load_builtin_plugins(self):
        """加载内置插件."""
        # 导入预定义的插件
        builtin_plugins = [
            "agentforge.plugins.weather_plugin.WeatherPlugin",
            "agentforge.plugins.currency_plugin.CurrencyPlugin",
            "agentforge.plugins.translation_plugin.TranslationPlugin",
        ]

        for plugin_path in builtin_plugins:
            try:
                module_path, class_name = plugin_path.rsplit(".", 1)
                module = importlib.import_module(module_path)
                plugin_class = getattr(module, class_name)
                await self.register_plugin_class(plugin_class)
            except Exception as e:
                logger.warning(f"加载内置插件失败 {plugin_path}: {str(e)}")

    async def _load_external_plugins(self):
        """加载外部插件."""
        for plugin_file in self.plugins_dir.glob("*.py"):
            if plugin_file.name.startswith("_"):
                continue

            try:
                spec = importlib.util.spec_from_file_location(
                    plugin_file.stem, plugin_file
                )
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[plugin_file.stem] = module
                    spec.loader.exec_module(module)

                    # 查找插件类
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (
                            isinstance(attr, type)
                            and issubclass(attr, Plugin)
                            and attr is not Plugin
                        ):
                            await self.register_plugin_class(attr)

                logger.info(f"加载外部插件：{plugin_file.name}")
            except Exception as e:
                logger.error(f"加载外部插件失败 {plugin_file.name}: {str(e)}")

    async def register_plugin_class(self, plugin_class: Type[Plugin], config: dict | None = None):
        """注册插件类."""
        try:
            # 创建插件实例
            plugin = plugin_class(config)

            # 验证配置
            if not plugin.validate_config():
                logger.error(f"插件配置验证失败：{plugin.name}")
                return

            # 初始化插件
            await plugin.initialize()

            # 注册插件
            self._plugins[plugin.name] = plugin
            self._plugin_classes[plugin.name] = plugin_class

            logger.info(f"注册插件：{plugin.name} v{plugin.version}")
        except Exception as e:
            logger.error(f"注册插件失败 {plugin_class.__name__}: {str(e)}")

    def unregister_plugin(self, plugin_name: str):
        """注销插件."""
        if plugin_name in self._plugins:
            plugin = self._plugins[plugin_name]
            try:
                import asyncio
                asyncio.get_event_loop().run_until_complete(plugin.shutdown())
            except Exception as e:
                logger.error(f"关闭插件失败 {plugin_name}: {str(e)}")

            del self._plugins[plugin_name]
            logger.info(f"注销插件：{plugin_name}")

    def get_plugin(self, plugin_name: str) -> Plugin | None:
        """获取插件实例."""
        return self._plugins.get(plugin_name)

    def list_plugins(self) -> list[Plugin]:
        """获取所有插件列表."""
        return list(self._plugins.values())

    def get_plugin_names(self) -> list[str]:
        """获取所有插件名称."""
        return list(self._plugins.keys())

    def enable_plugin(self, plugin_name: str) -> bool:
        """启用插件."""
        plugin = self.get_plugin(plugin_name)
        if plugin:
            plugin.enable()
            logger.info(f"启用插件：{plugin_name}")
            return True
        return False

    def disable_plugin(self, plugin_name: str) -> bool:
        """禁用插件."""
        plugin = self.get_plugin(plugin_name)
        if plugin:
            plugin.disable()
            logger.info(f"禁用插件：{plugin_name}")
            return True
        return False

    def get_plugin_capabilities(self, plugin_name: str) -> list[str]:
        """获取插件能力列表."""
        plugin = self.get_plugin(plugin_name)
        if plugin:
            return plugin.get_capabilities()
        return []

    def get_plugins_by_capability(self, capability: str) -> list[Plugin]:
        """根据能力获取插件列表."""
        result = []
        for plugin in self._plugins.values():
            if capability in plugin.get_capabilities():
                result.append(plugin)
        return result

    async def reload_plugin(self, plugin_name: str, config: dict | None = None) -> bool:
        """重新加载插件."""
        if plugin_name not in self._plugin_classes:
            logger.error(f"插件不存在：{plugin_name}")
            return False

        # 注销旧插件
        self.unregister_plugin(plugin_name)

        # 重新加载新插件
        plugin_class = self._plugin_classes[plugin_name]
        await self.register_plugin_class(plugin_class, config)

        return True
