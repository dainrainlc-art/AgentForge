import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Search, Download, Star, Package, Zap, TrendingUp, Clock } from 'lucide-react';

interface Plugin {
  id: string;
  name: string;
  description: string;
  type: string;
  version: string;
  author: string;
  tags: string[];
  downloads?: number;
  rating?: number;
  status?: string;
  enabled?: boolean;
}

export function PluginMarketplace() {
  const [plugins, setPlugins] = useState<Plugin[]>([]);
  const [marketplacePlugins, setMarketplacePlugins] = useState<Plugin[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState('marketplace');
  const [selectedPlugin, setSelectedPlugin] = useState<Plugin | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPlugins();
    fetchMarketplacePlugins();
  }, []);

  const fetchPlugins = async () => {
    try {
      const response = await fetch('/api/plugins/list');
      if (response.ok) {
        const data = await response.json();
        setPlugins(data);
      }
    } catch (error) {
      console.error('Failed to fetch plugins:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchMarketplacePlugins = async () => {
    try {
      const response = await fetch('/api/plugins/marketplace');
      if (response.ok) {
        const data = await response.json();
        setMarketplacePlugins(data);
      }
    } catch (error) {
      console.error('Failed to fetch marketplace plugins:', error);
    }
  };

  const handleInstall = async (pluginId: string) => {
    try {
      const response = await fetch(`/api/plugins/install/${pluginId}`, {
        method: 'POST',
      });
      if (response.ok) {
        alert('Plugin installed successfully!');
        fetchPlugins();
        fetchMarketplacePlugins();
      }
    } catch (error) {
      console.error('Failed to install plugin:', error);
      alert('Failed to install plugin');
    }
  };

  const handleEnable = async (pluginId: string) => {
    try {
      const response = await fetch(`/api/plugins/${pluginId}/enable`, {
        method: 'POST',
      });
      if (response.ok) {
        fetchPlugins();
      }
    } catch (error) {
      console.error('Failed to enable plugin:', error);
    }
  };

  const handleDisable = async (pluginId: string) => {
    try {
      const response = await fetch(`/api/plugins/${pluginId}/disable`, {
        method: 'POST',
      });
      if (response.ok) {
        fetchPlugins();
      }
    } catch (error) {
      console.error('Failed to disable plugin:', error);
    }
  };

  const handleUninstall = async (pluginId: string) => {
    if (!confirm('Are you sure you want to uninstall this plugin?')) return;
    
    try {
      const response = await fetch(`/api/plugins/${pluginId}/uninstall`, {
        method: 'POST',
      });
      if (response.ok) {
        fetchPlugins();
      }
    } catch (error) {
      console.error('Failed to uninstall plugin:', error);
    }
  };

  const filteredPlugins = (pluginList: Plugin[]) => {
    if (!searchQuery) return pluginList;
    
    const query = searchQuery.toLowerCase();
    return pluginList.filter(plugin =>
      plugin.name.toLowerCase().includes(query) ||
      plugin.description.toLowerCase().includes(query) ||
      plugin.tags.some(tag => tag.toLowerCase().includes(query))
    );
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'automation':
        return <Zap className="w-4 h-4" />;
      case 'skill':
        return <Package className="w-4 h-4" />;
      case 'analytics':
        return <TrendingUp className="w-4 h-4" />;
      default:
        return <Package className="w-4 h-4" />;
    }
  };

  const renderPluginCard = (plugin: Plugin, isMarketplace: boolean) => (
    <Card key={plugin.id} className="hover:shadow-lg transition-shadow">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-lg bg-blue-100 dark:bg-blue-900/20 flex items-center justify-center">
              {getTypeIcon(plugin.type)}
            </div>
            <div>
              <CardTitle className="text-lg">{plugin.name}</CardTitle>
              <CardDescription className="text-sm">
                by {plugin.author} • v{plugin.version}
              </CardDescription>
            </div>
          </div>
          {plugin.rating && (
            <div className="flex items-center gap-1 text-yellow-500">
              <Star className="w-4 h-4 fill-current" />
              <span className="text-sm font-medium">{plugin.rating}</span>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
          {plugin.description}
        </p>
        
        <div className="flex flex-wrap gap-2 mb-4">
          {plugin.tags.map((tag) => (
            <Badge key={tag} variant="secondary" className="text-xs">
              {tag}
            </Badge>
          ))}
        </div>

        {plugin.downloads && (
          <div className="flex items-center gap-4 text-sm text-gray-500 mb-4">
            <div className="flex items-center gap-1">
              <Download className="w-4 h-4" />
              <span>{plugin.downloads.toLocaleString()} downloads</span>
            </div>
          </div>
        )}

        <div className="flex gap-2">
          {isMarketplace ? (
            <Button
              onClick={() => handleInstall(plugin.id)}
              className="flex-1"
              size="sm"
            >
              <Download className="w-4 h-4 mr-2" />
              Install
            </Button>
          ) : (
            <>
              {plugin.enabled ? (
                <Button
                  onClick={() => handleDisable(plugin.id)}
                  variant="outline"
                  size="sm"
                >
                  Disable
                </Button>
              ) : (
                <Button
                  onClick={() => handleEnable(plugin.id)}
                  size="sm"
                >
                  Enable
                </Button>
              )}
              <Button
                onClick={() => handleUninstall(plugin.id)}
                variant="destructive"
                size="sm"
              >
                Uninstall
              </Button>
            </>
          )}
          
          <Dialog>
            <DialogTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSelectedPlugin(plugin)}
              >
                Details
              </Button>
            </DialogTrigger>
          </Dialog>
        </div>

        {plugin.status && (
          <Badge className="mt-2" variant={
            plugin.status === 'active' ? 'default' :
            plugin.status === 'error' ? 'destructive' : 'secondary'
          }>
            {plugin.status}
          </Badge>
        )}
      </CardContent>
    </Card>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <Package className="w-12 h-12 animate-spin mx-auto mb-4 text-blue-500" />
          <p className="text-gray-600">Loading plugins...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Plugin Marketplace</h1>
        <div className="flex items-center gap-4">
          <div className="relative w-64">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              placeholder="Search plugins..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="marketplace">
            <Download className="w-4 h-4 mr-2" />
            Marketplace ({marketplacePlugins.length})
          </TabsTrigger>
          <TabsTrigger value="installed">
            <Package className="w-4 h-4 mr-2" />
            Installed ({plugins.length})
          </TabsTrigger>
          <TabsTrigger value="popular">
            <Star className="w-4 h-4 mr-2" />
            Popular
          </TabsTrigger>
        </TabsList>

        <TabsContent value="marketplace" className="mt-6">
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {filteredPlugins(marketplacePlugins).map((plugin) =>
              renderPluginCard(plugin, true)
            )}
          </div>
          {filteredPlugins(marketplacePlugins).length === 0 && (
            <div className="text-center py-12 text-gray-500">
              No plugins found
            </div>
          )}
        </TabsContent>

        <TabsContent value="installed" className="mt-6">
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {filteredPlugins(plugins).map((plugin) =>
              renderPluginCard(plugin, false)
            )}
          </div>
          {filteredPlugins(plugins).length === 0 && (
            <div className="text-center py-12 text-gray-500">
              No installed plugins
            </div>
          )}
        </TabsContent>

        <TabsContent value="popular" className="mt-6">
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {filteredPlugins(
              [...marketplacePlugins].sort((a, b) => 
                (b.downloads || 0) - (a.downloads || 0)
              )
            ).map((plugin) =>
              renderPluginCard(plugin, true)
            )}
          </div>
        </TabsContent>
      </Tabs>

      {/* Plugin Details Dialog */}
      {selectedPlugin && (
        <Dialog open={!!selectedPlugin} onOpenChange={() => setSelectedPlugin(null)}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle className="text-2xl">{selectedPlugin.name}</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 rounded-lg bg-blue-100 dark:bg-blue-900/20 flex items-center justify-center">
                  {getTypeIcon(selectedPlugin.type)}
                </div>
                <div>
                  <p className="text-lg font-semibold">v{selectedPlugin.version}</p>
                  <p className="text-sm text-gray-500">by {selectedPlugin.author}</p>
                </div>
              </div>
              
              <div>
                <h3 className="font-semibold mb-2">Description</h3>
                <p className="text-gray-600 dark:text-gray-400">
                  {selectedPlugin.description}
                </p>
              </div>

              {selectedPlugin.downloads && (
                <div>
                  <h3 className="font-semibold mb-2">Statistics</h3>
                  <div className="flex gap-4 text-sm">
                    <div className="flex items-center gap-1">
                      <Download className="w-4 h-4" />
                      <span>{selectedPlugin.downloads.toLocaleString()} downloads</span>
                    </div>
                    {selectedPlugin.rating && (
                      <div className="flex items-center gap-1">
                        <Star className="w-4 h-4 fill-current text-yellow-500" />
                        <span>{selectedPlugin.rating} rating</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              <div>
                <h3 className="font-semibold mb-2">Tags</h3>
                <div className="flex flex-wrap gap-2">
                  {selectedPlugin.tags.map((tag) => (
                    <Badge key={tag} variant="secondary">
                      {tag}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}

export default PluginMarketplace;
