"""
AgentForge Plugin System
技能插件市场框架
"""
from typing import Dict, Any, List, Optional, Callable, Type
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import importlib
import inspect
import json
from pathlib import Path
from loguru import logger


class PluginType(str, Enum):
    SKILL = "skill"
    INTEGRATION = "integration"
    ANALYTICS = "analytics"
    AUTOMATION = "automation"
    UI_COMPONENT = "ui_component"


class PluginStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISABLED = "disabled"
    ERROR = "error"


class PluginMetadata(BaseModel):
    id: str
    name: str
    description: str
    version: str
    author: str
    type: PluginType
    status: PluginStatus = PluginStatus.INACTIVE
    tags: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    icon: Optional[str] = None
    website: Optional[str] = None
    license: str = "MIT"


class PluginConfig(BaseModel):
    enabled: bool = True
    settings: Dict[str, Any] = Field(default_factory=dict)
    api_keys: Dict[str, str] = Field(default_factory=dict)
    thresholds: Dict[str, float] = Field(default_factory=dict)


class PluginContext(BaseModel):
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PluginResult(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BasePlugin:
    """Base class for all plugins"""
    
    metadata: PluginMetadata
    config: PluginConfig
    
    def __init__(self, config: Optional[PluginConfig] = None):
        self.config = config or PluginConfig()
        self._initialized = False
    
    async def initialize(self) -> bool:
        """Initialize plugin"""
        try:
            await self.on_init()
            self._initialized = True
            logger.info(f"Plugin {self.metadata.name} initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize plugin {self.metadata.name}: {e}")
            self.metadata.status = PluginStatus.ERROR
            return False
    
    async def shutdown(self) -> bool:
        """Shutdown plugin"""
        try:
            await self.on_shutdown()
            self._initialized = False
            logger.info(f"Plugin {self.metadata.name} shutdown")
            return True
        except Exception as e:
            logger.error(f"Failed to shutdown plugin {self.metadata.name}: {e}")
            return False
    
    async def execute(
        self,
        input_data: Any,
        context: Optional[PluginContext] = None
    ) -> PluginResult:
        """Execute plugin logic"""
        if not self._initialized:
            return PluginResult(
                success=False,
                error="Plugin not initialized"
            )
        
        if not self.config.enabled:
            return PluginResult(
                success=False,
                error="Plugin is disabled"
            )
        
        try:
            result = await self.on_execute(input_data, context or PluginContext())
            return PluginResult(
                success=True,
                data=result,
                message=f"Plugin {self.metadata.name} executed successfully"
            )
        except Exception as e:
            logger.error(f"Plugin execution error: {e}")
            return PluginResult(
                success=False,
                error=str(e)
            )
    
    async def on_init(self):
        """Override this method for initialization logic"""
        pass
    
    async def on_shutdown(self):
        """Override this method for cleanup logic"""
        pass
    
    async def on_execute(
        self,
        input_data: Any,
        context: PluginContext
    ) -> Any:
        """Override this method for plugin logic"""
        raise NotImplementedError("Subclasses must implement on_execute")
    
    def validate_input(self, input_data: Any) -> bool:
        """Validate input data"""
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """Get plugin status"""
        return {
            "id": self.metadata.id,
            "name": self.metadata.name,
            "status": self.metadata.status.value,
            "initialized": self._initialized,
            "enabled": self.config.enabled
        }


class PluginRegistry:
    """Plugin registry and marketplace"""
    
    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = Path(plugins_dir)
        self.plugins: Dict[str, BasePlugin] = {}
        self.plugin_classes: Dict[str, Type[BasePlugin]] = {}
        self._load_plugins_from_dir()
    
    def _load_plugins_from_dir(self):
        """Load plugins from directory"""
        if not self.plugins_dir.exists():
            self.plugins_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created plugins directory at {self.plugins_dir}")
            return
        
        for plugin_dir in self.plugins_dir.iterdir():
            if plugin_dir.is_dir():
                try:
                    self._load_plugin_from_directory(plugin_dir)
                except Exception as e:
                    logger.error(f"Failed to load plugin from {plugin_dir}: {e}")
    
    def _load_plugin_from_directory(self, plugin_dir: Path):
        """Load a single plugin from directory"""
        metadata_file = plugin_dir / "metadata.json"
        if not metadata_file.exists():
            return
        
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata_dict = json.load(f)
        
        metadata = PluginMetadata(**metadata_dict)
        
        plugin_file = plugin_dir / "plugin.py"
        if plugin_file.exists():
            spec = importlib.util.spec_from_file_location(
                f"plugins.{metadata.id}",
                plugin_file
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                if hasattr(module, 'Plugin'):
                    plugin_class = getattr(module, 'Plugin')
                    self.plugin_classes[metadata.id] = plugin_class
                    logger.info(f"Loaded plugin: {metadata.name}")
    
    def register(
        self,
        plugin_class: Type[BasePlugin],
        config: Optional[PluginConfig] = None
    ) -> bool:
        """Register a plugin"""
        try:
            metadata = plugin_class.metadata
            plugin = plugin_class(config=config)
            self.plugins[metadata.id] = plugin
            self.plugin_classes[metadata.id] = plugin_class
            
            logger.info(f"Registered plugin: {metadata.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to register plugin: {e}")
            return False
    
    def unregister(self, plugin_id: str) -> bool:
        """Unregister a plugin"""
        if plugin_id not in self.plugins:
            return False
        
        plugin = self.plugins[plugin_id]
        plugin.metadata.status = PluginStatus.INACTIVE
        
        del self.plugins[plugin_id]
        logger.info(f"Unregistered plugin: {plugin_id}")
        return True
    
    async def enable_plugin(self, plugin_id: str) -> PluginResult:
        """Enable a plugin"""
        if plugin_id not in self.plugins:
            return PluginResult(
                success=False,
                error=f"Plugin {plugin_id} not found"
            )
        
        plugin = self.plugins[plugin_id]
        
        if plugin.metadata.status == PluginStatus.ACTIVE:
            return PluginResult(
                success=True,
                message="Plugin already enabled"
            )
        
        success = await plugin.initialize()
        
        if success:
            plugin.metadata.status = PluginStatus.ACTIVE
            plugin.config.enabled = True
            return PluginResult(
                success=True,
                message=f"Plugin {plugin.metadata.name} enabled"
            )
        else:
            return PluginResult(
                success=False,
                error="Failed to initialize plugin"
            )
    
    async def disable_plugin(self, plugin_id: str) -> PluginResult:
        """Disable a plugin"""
        if plugin_id not in self.plugins:
            return PluginResult(
                success=False,
                error=f"Plugin {plugin_id} not found"
            )
        
        plugin = self.plugins[plugin_id]
        
        if plugin.metadata.status == PluginStatus.INACTIVE:
            return PluginResult(
                success=True,
                message="Plugin already disabled"
            )
        
        await plugin.shutdown()
        plugin.metadata.status = PluginStatus.INACTIVE
        plugin.config.enabled = False
        
        return PluginResult(
            success=True,
            message=f"Plugin {plugin.metadata.name} disabled"
        )
    
    async def execute_plugin(
        self,
        plugin_id: str,
        input_data: Any,
        context: Optional[PluginContext] = None
    ) -> PluginResult:
        """Execute a plugin"""
        if plugin_id not in self.plugins:
            return PluginResult(
                success=False,
                error=f"Plugin {plugin_id} not found"
            )
        
        plugin = self.plugins[plugin_id]
        return await plugin.execute(input_data, context)
    
    def get_plugin(self, plugin_id: str) -> Optional[BasePlugin]:
        """Get a plugin by ID"""
        return self.plugins.get(plugin_id)
    
    def list_plugins(
        self,
        plugin_type: Optional[PluginType] = None,
        status: Optional[PluginStatus] = None
    ) -> List[Dict[str, Any]]:
        """List all registered plugins"""
        result = []
        
        for plugin in self.plugins.values():
            if plugin_type and plugin.metadata.type != plugin_type:
                continue
            if status and plugin.metadata.status != status:
                continue
            
            result.append({
                "id": plugin.metadata.id,
                "name": plugin.metadata.name,
                "description": plugin.metadata.description,
                "type": plugin.metadata.type.value,
                "status": plugin.metadata.status.value,
                "version": plugin.metadata.version,
                "author": plugin.metadata.author,
                "tags": plugin.metadata.tags,
                "enabled": plugin.config.enabled
            })
        
        return result
    
    def get_plugin_info(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed plugin information"""
        if plugin_id not in self.plugins:
            return None
        
        plugin = self.plugins[plugin_id]
        return {
            **plugin.metadata.dict(),
            "status_info": plugin.get_status()
        }
    
    def search_plugins(self, query: str) -> List[Dict[str, Any]]:
        """Search plugins by name, description, or tags"""
        query_lower = query.lower()
        results = []
        
        for plugin in self.plugins.values():
            if (query_lower in plugin.metadata.name.lower() or
                query_lower in plugin.metadata.description.lower() or
                any(query_lower in tag.lower() for tag in plugin.metadata.tags)):
                results.append({
                    "id": plugin.metadata.id,
                    "name": plugin.metadata.name,
                    "description": plugin.metadata.description,
                    "type": plugin.metadata.type.value,
                    "tags": plugin.metadata.tags
                })
        
        return results
    
    def install_plugin(self, plugin_package: Dict[str, Any]) -> bool:
        """Install a new plugin"""
        try:
            plugin_dir = self.plugins_dir / plugin_package["id"]
            plugin_dir.mkdir(parents=True, exist_ok=True)
            
            metadata_file = plugin_dir / "metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(plugin_package["metadata"], f, indent=2)
            
            plugin_file = plugin_dir / "plugin.py"
            with open(plugin_file, 'w', encoding='utf-8') as f:
                f.write(plugin_package["code"])
            
            self._load_plugin_from_directory(plugin_dir)
            
            logger.info(f"Installed plugin: {plugin_package['metadata']['name']}")
            return True
        except Exception as e:
            logger.error(f"Failed to install plugin: {e}")
            return False
    
    def uninstall_plugin(self, plugin_id: str) -> bool:
        """Uninstall a plugin"""
        if plugin_id not in self.plugins:
            return False
        
        plugin_dir = self.plugins_dir / plugin_id
        if plugin_dir.exists():
            import shutil
            shutil.rmtree(plugin_dir)
        
        self.unregister(plugin_id)
        logger.info(f"Uninstalled plugin: {plugin_id}")
        return True


class PluginMarketplace:
    """Plugin marketplace for browsing and installing plugins"""
    
    def __init__(self, registry: PluginRegistry):
        self.registry = registry
        self._available_plugins: List[Dict[str, Any]] = []
    
    def fetch_available_plugins(self) -> List[Dict[str, Any]]:
        """Fetch available plugins from marketplace"""
        # In a real implementation, this would fetch from a remote marketplace
        self._available_plugins = [
            {
                "id": "twitter-auto-post",
                "name": "Twitter Auto Poster",
                "description": "Automatically post content to Twitter",
                "type": PluginType.AUTOMATION.value,
                "version": "1.0.0",
                "author": "AgentForge Team",
                "tags": ["twitter", "social", "automation"],
                "downloads": 1250,
                "rating": 4.5
            },
            {
                "id": "sentiment-analyzer",
                "name": "Sentiment Analyzer",
                "description": "Analyze sentiment of text content",
                "type": PluginType.SKILL.value,
                "version": "2.1.0",
                "author": "AI Labs",
                "tags": ["ai", "nlp", "sentiment"],
                "downloads": 3420,
                "rating": 4.8
            },
            {
                "id": "pdf-processor",
                "name": "PDF Processor",
                "description": "Extract and process PDF documents",
                "type": PluginType.SKILL.value,
                "version": "1.2.0",
                "author": "DocTools",
                "tags": ["pdf", "document", "extraction"],
                "downloads": 890,
                "rating": 4.2
            }
        ]
        
        return self._available_plugins
    
    def get_plugin_details(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """Get details for a specific plugin"""
        for plugin in self._available_plugins:
            if plugin["id"] == plugin_id:
                return plugin
        return None
    
    def install_plugin(self, plugin_id: str) -> bool:
        """Install a plugin from marketplace"""
        plugin_data = self.get_plugin_details(plugin_id)
        if not plugin_data:
            return False
        
        # In a real implementation, this would download the plugin package
        return self.registry.install_plugin({
            "id": plugin_id,
            "metadata": plugin_data,
            "code": "# Plugin code would be downloaded here"
        })
    
    def search_marketplace(self, query: str) -> List[Dict[str, Any]]:
        """Search marketplace"""
        query_lower = query.lower()
        return [
            plugin for plugin in self._available_plugins
            if (query_lower in plugin["name"].lower() or
                query_lower in plugin["description"].lower() or
                any(query_lower in tag.lower() for tag in plugin["tags"]))
        ]
    
    def get_popular_plugins(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get popular plugins"""
        return sorted(
            self._available_plugins,
            key=lambda x: (x.get("downloads", 0), x.get("rating", 0)),
            reverse=True
        )[:limit]
    
    def get_recent_plugins(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recently added plugins"""
        return sorted(
            self._available_plugins,
            key=lambda x: x.get("version", "0.0.0"),
            reverse=True
        )[:limit]


# Global registry instance
plugin_registry = PluginRegistry()
plugin_marketplace = PluginMarketplace(plugin_registry)


def register_plugin(plugin_class: Type[BasePlugin]):
    """Decorator to register a plugin"""
    plugin_registry.register(plugin_class)
    return plugin_class


def create_plugin_metadata(
    id: str,
    name: str,
    description: str,
    type: PluginType,
    version: str = "1.0.0",
    author: str = "Unknown",
    tags: Optional[List[str]] = None
) -> PluginMetadata:
    """Helper to create plugin metadata"""
    return PluginMetadata(
        id=id,
        name=name,
        description=description,
        version=version,
        author=author,
        type=type,
        tags=tags or []
    )
