/**
 * 插件管理界面 - 完整的插件管理功能
 * 支持筛选、搜索、启用/禁用、配置、查看详情等功能
 */

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { 
  Search, 
  Filter, 
  Package, 
  Zap, 
  TrendingUp, 
  Settings, 
  CheckCircle, 
  XCircle,
  RefreshCw,
  Download,
  Star,
  Trash2,
  Save,
  AlertCircle
} from "lucide-react";

interface PluginConfig {
  key: string;
  type: "string" | "number" | "boolean" | "json";
  label: string;
  description?: string;
  default?: unknown;
  required?: boolean;
}

interface Plugin {
  id: string;
  name: string;
  description: string;
  type: "automation" | "skill" | "analytics" | "integration" | "utility";
  version: string;
  author: string;
  tags: string[];
  downloads?: number;
  rating?: number;
  status: "active" | "inactive" | "error" | "pending";
  enabled: boolean;
  config_schema?: PluginConfig[];
  config_values?: Record<string, unknown>;
  capabilities?: string[];
  installed_at?: string;
  updated_at?: string;
}

export const PluginManagement: React.FC = () => {
  const [plugins, setPlugins] = useState<Plugin[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedType, setSelectedType] = useState<string | null>(null);
  const [selectedStatus, setSelectedStatus] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("all");
  const [selectedPlugin, setSelectedPlugin] = useState<Plugin | null>(null);
  const [configDialogOpen, setConfigDialogOpen] = useState(false);
  const [configValues, setConfigValues] = useState<Record<string, unknown>>({});
  const [savingConfig, setSavingConfig] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchPlugins();
  }, []);

  const fetchPlugins = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/plugins/list");
      if (response.ok) {
        const data = await response.json();
        setPlugins(data);
      }
    } catch (error) {
      console.error("获取插件列表失败:", error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleEnable = async (pluginId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/plugins/${pluginId}/enable`, {
        method: "POST",
      });
      if (response.ok) {
        fetchPlugins();
        alert("插件已启用");
      } else {
        const error = await response.json();
        alert(`启用失败：${error.detail}`);
      }
    } catch (error) {
      console.error("启用插件失败:", error);
      alert("启用失败");
    }
  };

  const handleDisable = async (pluginId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/plugins/${pluginId}/disable`, {
        method: "POST",
      });
      if (response.ok) {
        fetchPlugins();
        alert("插件已禁用");
      } else {
        const error = await response.json();
        alert(`禁用失败：${error.detail}`);
      }
    } catch (error) {
      console.error("禁用插件失败:", error);
      alert("禁用失败");
    }
  };

  const handleUninstall = async (pluginId: string) => {
    if (!confirm(`确定要卸载插件 "${pluginId}" 吗？此操作不可恢复。`)) {
      return;
    }
    try {
      const response = await fetch(`http://localhost:8000/api/plugins/${pluginId}/uninstall`, {
        method: "POST",
      });
      if (response.ok) {
        fetchPlugins();
        alert("插件已卸载");
      } else {
        const error = await response.json();
        alert(`卸载失败：${error.detail}`);
      }
    } catch (error) {
      console.error("卸载插件失败:", error);
      alert("卸载失败");
    }
  };

  const handleOpenConfig = (plugin: Plugin) => {
    setSelectedPlugin(plugin);
    setConfigValues(plugin.config_values || {});
    setConfigDialogOpen(true);
  };

  const handleSaveConfig = async () => {
    if (!selectedPlugin) return;
    
    setSavingConfig(true);
    try {
      const response = await fetch(`http://localhost:8000/api/plugins/${selectedPlugin.id}/config`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ config: configValues }),
      });
      
      if (response.ok) {
        alert("配置保存成功");
        setConfigDialogOpen(false);
        fetchPlugins();
      } else {
        const error = await response.json();
        alert(`保存失败：${error.detail}`);
      }
    } catch (error) {
      console.error("保存配置失败:", error);
      alert("保存失败");
    } finally {
      setSavingConfig(false);
    }
  };

  const handleRefresh = () => {
    setRefreshing(true);
    fetchPlugins();
  };

  const getFilteredPlugins = () => {
    let filtered = plugins;

    // 按类型筛选
    if (selectedType) {
      filtered = filtered.filter((p) => p.type === selectedType);
    }

    // 按状态筛选
    if (selectedStatus) {
      if (selectedStatus === "enabled") {
        filtered = filtered.filter((p) => p.enabled);
      } else if (selectedStatus === "disabled") {
        filtered = filtered.filter((p) => !p.enabled);
      } else if (selectedStatus === "active") {
        filtered = filtered.filter((p) => p.status === "active");
      } else if (selectedStatus === "error") {
        filtered = filtered.filter((p) => p.status === "error");
      }
    }

    // 按搜索词筛选
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (p) =>
          p.name.toLowerCase().includes(query) ||
          p.description.toLowerCase().includes(query) ||
          p.tags.some((tag) => tag.toLowerCase().includes(query)) ||
          p.capabilities?.some((cap) => cap.toLowerCase().includes(query)),
      );
    }

    // 按标签页筛选
    if (activeTab === "automation") {
      filtered = filtered.filter((p) => p.type === "automation");
    } else if (activeTab === "skill") {
      filtered = filtered.filter((p) => p.type === "skill");
    } else if (activeTab === "analytics") {
      filtered = filtered.filter((p) => p.type === "analytics");
    } else if (activeTab === "integration") {
      filtered = filtered.filter((p) => p.type === "integration");
    } else if (activeTab === "utility") {
      filtered = filtered.filter((p) => p.type === "utility");
    }

    return filtered;
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case "automation":
        return <Zap className="w-4 h-4" />;
      case "skill":
        return <Package className="w-4 h-4" />;
      case "analytics":
        return <TrendingUp className="w-4 h-4" />;
      case "integration":
        return <Settings className="w-4 h-4" />;
      default:
        return <Package className="w-4 h-4" />;
    }
  };

  const getStatusBadge = (plugin: Plugin) => {
    if (plugin.status === "error") {
      return (
        <Badge variant="destructive">
          <XCircle className="w-3 h-3 mr-1" />
          错误
        </Badge>
      );
    } else if (plugin.status === "active") {
      return (
        <Badge className="bg-green-500">
          <CheckCircle className="w-3 h-3 mr-1" />
          运行中
        </Badge>
      );
    } else if (plugin.status === "pending") {
      return (
        <Badge variant="secondary">
          <RefreshCw className="w-3 h-3 mr-1 animate-spin" />
          加载中
        </Badge>
      );
    } else {
      return (
        <Badge variant="secondary">
          <XCircle className="w-3 h-3 mr-1" />
          未激活
        </Badge>
      );
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <RefreshCw className="w-12 h-12 animate-spin mx-auto mb-4 text-blue-500" />
          <p className="text-gray-600">加载插件列表...</p>
        </div>
      </div>
    );
  }

  const filteredPlugins = getFilteredPlugins();

  return (
    <div className="container mx-auto p-6">
      {/* 头部 */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold mb-2">插件管理</h1>
          <p className="text-gray-600">管理和配置系统插件</p>
        </div>
        <div className="flex items-center gap-4">
          <Button
            onClick={handleRefresh}
            variant="outline"
            size="sm"
            disabled={refreshing}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? "animate-spin" : ""}`} />
            刷新
          </Button>
        </div>
      </div>

      {/* 筛选和搜索 */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="flex gap-4 items-center">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <Input
                placeholder="搜索插件名称、描述、标签或能力..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-gray-500" />
              <select
                value={selectedType || ""}
                onChange={(e) => setSelectedType(e.target.value || null)}
                className="p-2 border rounded"
              >
                <option value="">所有类型</option>
                <option value="automation">自动化</option>
                <option value="skill">技能</option>
                <option value="analytics">分析</option>
                <option value="integration">集成</option>
                <option value="utility">工具</option>
              </select>
              
              <select
                value={selectedStatus || ""}
                onChange={(e) => setSelectedStatus(e.target.value || null)}
                className="p-2 border rounded"
              >
                <option value="">所有状态</option>
                <option value="enabled">已启用</option>
                <option value="disabled">已禁用</option>
                <option value="active">运行中</option>
                <option value="error">错误</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 标签页 */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="mb-4">
          <TabsTrigger value="all">全部 ({plugins.length})</TabsTrigger>
          <TabsTrigger value="automation">
            <Zap className="w-4 h-4 mr-2" />
            自动化
          </TabsTrigger>
          <TabsTrigger value="skill">
            <Package className="w-4 h-4 mr-2" />
            技能
          </TabsTrigger>
          <TabsTrigger value="analytics">
            <TrendingUp className="w-4 h-4 mr-2" />
            分析
          </TabsTrigger>
          <TabsTrigger value="integration">
            <Settings className="w-4 h-4 mr-2" />
            集成
          </TabsTrigger>
          <TabsTrigger value="utility">
            <Package className="w-4 h-4 mr-2" />
            工具
          </TabsTrigger>
        </TabsList>

        <TabsContent value="all" className="mt-0">
          <PluginGrid
            plugins={filteredPlugins}
            getStatusBadge={getStatusBadge}
            getTypeIcon={getTypeIcon}
            handleEnable={handleEnable}
            handleDisable={handleDisable}
            handleUninstall={handleUninstall}
            handleOpenConfig={handleOpenConfig}
            setSelectedPlugin={setSelectedPlugin}
          />
        </TabsContent>

        <TabsContent value="automation" className="mt-0">
          <PluginGrid
            plugins={filteredPlugins}
            getStatusBadge={getStatusBadge}
            getTypeIcon={getTypeIcon}
            handleEnable={handleEnable}
            handleDisable={handleDisable}
            handleUninstall={handleUninstall}
            handleOpenConfig={handleOpenConfig}
            setSelectedPlugin={setSelectedPlugin}
          />
        </TabsContent>

        <TabsContent value="skill" className="mt-0">
          <PluginGrid
            plugins={filteredPlugins}
            getStatusBadge={getStatusBadge}
            getTypeIcon={getTypeIcon}
            handleEnable={handleEnable}
            handleDisable={handleDisable}
            handleUninstall={handleUninstall}
            handleOpenConfig={handleOpenConfig}
            setSelectedPlugin={setSelectedPlugin}
          />
        </TabsContent>

        <TabsContent value="analytics" className="mt-0">
          <PluginGrid
            plugins={filteredPlugins}
            getStatusBadge={getStatusBadge}
            getTypeIcon={getTypeIcon}
            handleEnable={handleEnable}
            handleDisable={handleDisable}
            handleUninstall={handleUninstall}
            handleOpenConfig={handleOpenConfig}
            setSelectedPlugin={setSelectedPlugin}
          />
        </TabsContent>

        <TabsContent value="integration" className="mt-0">
          <PluginGrid
            plugins={filteredPlugins}
            getStatusBadge={getStatusBadge}
            getTypeIcon={getTypeIcon}
            handleEnable={handleEnable}
            handleDisable={handleDisable}
            handleUninstall={handleUninstall}
            handleOpenConfig={handleOpenConfig}
            setSelectedPlugin={setSelectedPlugin}
          />
        </TabsContent>

        <TabsContent value="utility" className="mt-0">
          <PluginGrid
            plugins={filteredPlugins}
            getStatusBadge={getStatusBadge}
            getTypeIcon={getTypeIcon}
            handleEnable={handleEnable}
            handleDisable={handleDisable}
            handleUninstall={handleUninstall}
            handleOpenConfig={handleOpenConfig}
            setSelectedPlugin={setSelectedPlugin}
          />
        </TabsContent>
      </Tabs>

      {/* 插件详情对话框 */}
      {selectedPlugin && !configDialogOpen && (
        <PluginDetailDialog
          plugin={selectedPlugin}
          open={!!selectedPlugin && !configDialogOpen}
          onOpenChange={() => setSelectedPlugin(null)}
          onConfigure={() => handleOpenConfig(selectedPlugin)}
        />
      )}

      {/* 配置对话框 */}
      {selectedPlugin && configDialogOpen && (
        <ConfigDialog
          plugin={selectedPlugin}
          open={configDialogOpen}
          onOpenChange={setConfigDialogOpen}
          configValues={configValues}
          setConfigValues={setConfigValues}
          onSave={handleSaveConfig}
          saving={savingConfig}
        />
      )}
    </div>
  );
};

interface PluginGridProps {
  plugins: Plugin[];
  getStatusBadge: (plugin: Plugin) => React.ReactNode;
  getTypeIcon: (type: string) => React.ReactNode;
  handleEnable: (id: string) => void;
  handleDisable: (id: string) => void;
  handleUninstall: (id: string) => void;
  handleOpenConfig: (plugin: Plugin) => void;
  setSelectedPlugin: (plugin: Plugin) => void;
}

const PluginGrid: React.FC<PluginGridProps> = ({
  plugins,
  getStatusBadge,
  getTypeIcon,
  handleEnable,
  handleDisable,
  handleUninstall,
  handleOpenConfig,
  setSelectedPlugin,
}) => {
  if (plugins.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <Package className="w-12 h-12 mx-auto mb-4 opacity-50" />
        <p>暂无插件</p>
        <p className="text-sm">从插件市场安装更多插件</p>
      </div>
    );
  }

  return (
    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
      {plugins.map((plugin) => (
        <Card key={plugin.id} className="hover:shadow-lg transition-shadow">
          <CardHeader>
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3 flex-1">
                <div className="w-12 h-12 rounded-lg bg-blue-100 dark:bg-blue-900/20 flex items-center justify-center">
                  {getTypeIcon(plugin.type)}
                </div>
                <div className="flex-1">
                  <CardTitle className="text-lg">{plugin.name}</CardTitle>
                  <CardDescription className="text-sm">
                    v{plugin.version} • by {plugin.author}
                  </CardDescription>
                </div>
              </div>
              {getStatusBadge(plugin)}
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {/* 描述 */}
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {plugin.description}
              </p>

              {/* 标签 */}
              {plugin.tags && plugin.tags.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {plugin.tags.map((tag) => (
                    <Badge key={tag} variant="secondary" className="text-xs">
                      {tag}
                    </Badge>
                  ))}
                </div>
              )}

              {/* 能力 */}
              {plugin.capabilities && plugin.capabilities.length > 0 && (
                <div className="text-xs text-gray-500">
                  <strong>能力：</strong>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {plugin.capabilities.map((cap) => (
                      <Badge key={cap} variant="outline" className="text-xs">
                        {cap}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {/* 下载和评分 */}
              <div className="flex items-center gap-4 text-sm text-gray-500">
                {plugin.downloads && (
                  <div className="flex items-center gap-1">
                    <Download className="w-4 h-4" />
                    <span>{plugin.downloads.toLocaleString()}</span>
                  </div>
                )}
                {plugin.rating && (
                  <div className="flex items-center gap-1 text-yellow-500">
                    <Star className="w-4 h-4 fill-current" />
                    <span>{plugin.rating}</span>
                  </div>
                )}
              </div>

              {/* 操作按钮 */}
              <div className="flex gap-2 pt-2 border-t">
                {plugin.enabled ? (
                  <Button
                    onClick={() => handleDisable(plugin.id)}
                    variant="outline"
                    size="sm"
                    className="flex-1"
                  >
                    <XCircle className="w-4 h-4 mr-1" />
                    禁用
                  </Button>
                ) : (
                  <Button
                    onClick={() => handleEnable(plugin.id)}
                    size="sm"
                    className="flex-1"
                  >
                    <CheckCircle className="w-4 h-4 mr-1" />
                    启用
                  </Button>
                )}

                <Button
                  onClick={() => handleOpenConfig(plugin)}
                  disabled={!plugin.config_schema || plugin.config_schema.length === 0}
                  variant="outline"
                  size="sm"
                >
                  <Settings className="w-4 h-4" />
                </Button>

                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSelectedPlugin(plugin)}
                >
                  <Package className="w-4 h-4" />
                </Button>

                <Button
                  onClick={() => handleUninstall(plugin.id)}
                  variant="destructive"
                  size="sm"
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};

interface PluginDetailDialogProps {
  plugin: Plugin;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfigure: () => void;
}

const PluginDetailDialog: React.FC<PluginDetailDialogProps> = ({
  plugin,
  open,
  onOpenChange,
  onConfigure,
}) => {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl">{plugin.name}</DialogTitle>
        </DialogHeader>
        <div className="space-y-6 mt-4">
          {/* 基本信息 */}
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-lg bg-blue-100 dark:bg-blue-900/20 flex items-center justify-center">
              {plugin.type === "automation" && <Zap className="w-8 h-8" />}
              {plugin.type === "skill" && <Package className="w-8 h-8" />}
              {plugin.type === "analytics" && <TrendingUp className="w-8 h-8" />}
              {plugin.type === "integration" && <Settings className="w-8 h-8" />}
              {plugin.type === "utility" && <Package className="w-8 h-8" />}
            </div>
            <div>
              <div className="text-lg font-semibold">v{plugin.version}</div>
              <div className="text-sm text-gray-500">by {plugin.author}</div>
              <div className="text-sm text-gray-500">
                类型：<Badge variant="outline">{plugin.type}</Badge>
              </div>
            </div>
          </div>

          {/* 状态 */}
          <div>
            <h3 className="font-semibold mb-2">状态</h3>
            <div className="flex gap-4">
              <div>
                <span className="text-gray-500">启用状态：</span>
                <Badge variant={plugin.enabled ? "default" : "secondary"}>
                  {plugin.enabled ? "已启用" : "已禁用"}
                </Badge>
              </div>
              <div>
                <span className="text-gray-500">运行状态：</span>
                <Badge variant={
                  plugin.status === "active" ? "default" :
                  plugin.status === "error" ? "destructive" : "secondary"
                }>
                  {plugin.status}
                </Badge>
              </div>
            </div>
          </div>

          {/* 描述 */}
          <div>
            <h3 className="font-semibold mb-2">描述</h3>
            <p className="text-gray-600">{plugin.description}</p>
          </div>

          {/* 标签 */}
          {plugin.tags && plugin.tags.length > 0 && (
            <div>
              <h3 className="font-semibold mb-2">标签</h3>
              <div className="flex flex-wrap gap-2">
                {plugin.tags.map((tag) => (
                  <Badge key={tag} variant="secondary">
                    {tag}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* 能力 */}
          {plugin.capabilities && plugin.capabilities.length > 0 && (
            <div>
              <h3 className="font-semibold mb-2">能力</h3>
              <div className="flex flex-wrap gap-2">
                {plugin.capabilities.map((cap) => (
                  <Badge key={cap} variant="outline">
                    {cap}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* 统计信息 */}
          <div className="grid grid-cols-2 gap-4">
            {plugin.downloads && (
              <div>
                <h3 className="font-semibold mb-2">下载量</h3>
                <div className="text-2xl font-bold">{plugin.downloads.toLocaleString()}</div>
              </div>
            )}
            {plugin.rating && (
              <div>
                <h3 className="font-semibold mb-2">评分</h3>
                <div className="flex items-center gap-2">
                  <span className="text-2xl font-bold">{plugin.rating}</span>
                  <Star className="w-6 h-6 fill-current text-yellow-500" />
                </div>
              </div>
            )}
          </div>

          {/* 安装信息 */}
          <div className="text-sm text-gray-500">
            {plugin.installed_at && (
              <div className="mb-1">
                安装时间：{new Date(plugin.installed_at).toLocaleString("zh-CN")}
              </div>
            )}
            {plugin.updated_at && (
              <div className="mb-1">
                更新时间：{new Date(plugin.updated_at).toLocaleString("zh-CN")}
              </div>
            )}
          </div>

          {/* 操作按钮 */}
          <div className="flex gap-2 pt-4 border-t">
            {plugin.config_schema && plugin.config_schema.length > 0 && (
              <Button onClick={onConfigure} className="flex-1">
                <Settings className="w-4 h-4 mr-2" />
                配置插件
              </Button>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

interface ConfigDialogProps {
  plugin: Plugin;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  configValues: Record<string, unknown>;
  setConfigValues: (values: Record<string, unknown>) => void;
  onSave: () => void;
  saving: boolean;
}

const ConfigDialog: React.FC<ConfigDialogProps> = ({
  plugin,
  open,
  onOpenChange,
  configValues,
  setConfigValues,
  onSave,
  saving,
}) => {
  const handleConfigChange = (key: string, value: unknown) => {
    setConfigValues({
      ...configValues,
      [key]: value,
    });
  };

  const renderConfigField = (config: PluginConfig) => {
    const value = configValues[config.key] ?? config.default;

    if (config.type === "boolean") {
      return (
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <Label>{config.label}</Label>
            {config.description && (
              <p className="text-sm text-gray-500">{config.description}</p>
            )}
          </div>
          <Switch
            checked={value as boolean}
            onCheckedChange={(checked) => handleConfigChange(config.key, checked)}
          />
        </div>
      );
    }

    if (config.type === "number") {
      return (
        <div>
          <Label>{config.label}</Label>
          {config.description && (
            <p className="text-sm text-gray-500 mb-2">{config.description}</p>
          )}
          <Input
            type="number"
            value={value as number}
            onChange={(e) => handleConfigChange(config.key, parseFloat(e.target.value))}
          />
        </div>
      );
    }

    if (config.type === "json") {
      return (
        <div>
          <Label>{config.label}</Label>
          {config.description && (
            <p className="text-sm text-gray-500 mb-2">{config.description}</p>
          )}
          <Textarea
            value={typeof value === "string" ? value : JSON.stringify(value, null, 2)}
            onChange={(e) => {
              try {
                const parsed = JSON.parse(e.target.value);
                handleConfigChange(config.key, parsed);
              } catch {
                handleConfigChange(config.key, e.target.value);
              }
            }}
            className="font-mono text-sm"
            rows={6}
          />
        </div>
      );
    }

    // string 类型
    return (
      <div>
        <Label>{config.label}</Label>
        {config.description && (
          <p className="text-sm text-gray-500 mb-2">{config.description}</p>
        )}
        <Input
          type="text"
          value={value as string}
          onChange={(e) => handleConfigChange(config.key, e.target.value)}
        />
      </div>
    );
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl">配置插件：{plugin.name}</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 mt-4">
          {plugin.config_schema?.map((config) => (
            <div key={config.key}>
              {renderConfigField(config)}
            </div>
          ))}

          {(!plugin.config_schema || plugin.config_schema.length === 0) && (
            <div className="text-center py-8 text-gray-500">
              <AlertCircle className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>该插件没有可配置项</p>
            </div>
          )}

          <div className="flex gap-2 pt-4 border-t">
            <Button
              onClick={onSave}
              disabled={saving || !plugin.config_schema || plugin.config_schema.length === 0}
              className="flex-1"
            >
              <Save className="w-4 h-4 mr-2" />
              {saving ? "保存中..." : "保存配置"}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default PluginManagement;
