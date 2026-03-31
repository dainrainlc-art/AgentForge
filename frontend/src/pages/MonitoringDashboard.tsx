import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Activity, Server, HardDrive, Network, AlertTriangle, CheckCircle } from 'lucide-react';

interface SystemMetrics {
  cpu: number;
  memory: number;
  disk: number;
  network_sent_mb: number;
  network_recv_mb: number;
}

interface Alert {
  id: string;
  rule: string;
  level: 'info' | 'warning' | 'critical';
  message: string;
  triggered_at: string;
}

interface DashboardData {
  timestamp: string;
  system: SystemMetrics;
  metrics: Record<string, any>;
  requests: {
    endpoints: Array<{
      endpoint: string;
      method: string;
      count: number;
      error_rate: number;
      latency_avg_ms: number;
    }>;
  };
  alerts: Alert[];
}

export function MonitoringDashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval] = useState(5000); // 5 seconds

  useEffect(() => {
    fetchDashboardData();
    
    if (autoRefresh) {
      const interval = setInterval(fetchDashboardData, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const fetchDashboardData = async () => {
    try {
      const response = await fetch('/api/monitoring/dashboard');
      if (response.ok) {
        const result = await response.json();
        setData(result);
      }
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getAlertColor = (level: string) => {
    switch (level) {
      case 'critical':
        return 'bg-red-500';
      case 'warning':
        return 'bg-yellow-500';
      case 'info':
        return 'bg-blue-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getMetricColor = (value: number, warning: number, critical: number) => {
    if (value >= critical) return 'text-red-600';
    if (value >= warning) return 'text-yellow-600';
    return 'text-green-600';
  };

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <Activity className="w-12 h-12 animate-spin mx-auto mb-4 text-blue-500" />
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Performance Monitoring</h1>
        <div className="flex items-center gap-4">
          <Badge variant={autoRefresh ? "default" : "secondary"}>
            {autoRefresh ? 'Auto-refresh ON' : 'Auto-refresh OFF'}
          </Badge>
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className="text-sm text-blue-600 hover:underline"
          >
            Toggle
          </button>
        </div>
      </div>

      {/* Active Alerts */}
      {data && data.alerts.length > 0 && (
        <Card className="mb-6 border-red-200 bg-red-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-red-700">
              <AlertTriangle className="w-5 h-5" />
              Active Alerts ({data.alerts.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {data.alerts.map((alert) => (
                <div key={alert.id} className="flex items-center justify-between p-2 bg-white rounded">
                  <div>
                    <p className="font-medium">{alert.rule}</p>
                    <p className="text-sm text-gray-600">{alert.message}</p>
                  </div>
                  <Badge className={getAlertColor(alert.level)}>
                    {alert.level.toUpperCase()}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* System Metrics */}
      <Tabs defaultValue="overview" className="mb-6">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="requests">Requests</TabsTrigger>
          <TabsTrigger value="metrics">Metrics</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {/* CPU */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">CPU Usage</CardTitle>
                <Server className="w-4 h-4 text-gray-500" />
              </CardHeader>
              <CardContent>
                <div className={`text-2xl font-bold ${getMetricColor(data?.system.cpu || 0, 70, 90)}`}>
                  {data?.system.cpu?.toFixed(1)}%
                </div>
                <Progress value={data?.system.cpu || 0} className="mt-2" />
                <p className="text-xs text-gray-500 mt-1">
                  {data?.system.cpu! > 90 ? 'Critical' : data?.system.cpu! > 70 ? 'Warning' : 'Normal'}
                </p>
              </CardContent>
            </Card>

            {/* Memory */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Memory Usage</CardTitle>
                <HardDrive className="w-4 h-4 text-gray-500" />
              </CardHeader>
              <CardContent>
                <div className={`text-2xl font-bold ${getMetricColor(data?.system.memory || 0, 75, 95)}`}>
                  {data?.system.memory?.toFixed(1)}%
                </div>
                <Progress value={data?.system.memory || 0} className="mt-2" />
                <p className="text-xs text-gray-500 mt-1">
                  {data?.system.memory! > 95 ? 'Critical' : data?.system.memory! > 75 ? 'Warning' : 'Normal'}
                </p>
              </CardContent>
            </Card>

            {/* Disk */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Disk Usage</CardTitle>
                <HardDrive className="w-4 h-4 text-gray-500" />
              </CardHeader>
              <CardContent>
                <div className={`text-2xl font-bold ${getMetricColor(data?.system.disk || 0, 80, 95)}`}>
                  {data?.system.disk?.toFixed(1)}%
                </div>
                <Progress value={data?.system.disk || 0} className="mt-2" />
                <p className="text-xs text-gray-500 mt-1">
                  {data?.system.disk! > 95 ? 'Critical' : data?.system.disk! > 80 ? 'Warning' : 'Normal'}
                </p>
              </CardContent>
            </Card>

            {/* Network */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Network I/O</CardTitle>
                <Network className="w-4 h-4 text-gray-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  ↓ {data?.system.network_recv_mb?.toFixed(1)} MB
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  ↑ {data?.system.network_sent_mb?.toFixed(1)} MB sent
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Request Stats */}
          <div className="grid gap-4 md:grid-cols-2 mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Request Volume by Endpoint</CardTitle>
              </CardHeader>
              <CardContent>
                {data?.requests.endpoints && data.requests.endpoints.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={data.requests.endpoints}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="endpoint" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="count" fill="#3b82f6" name="Requests" />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <p className="text-center text-gray-500 py-12">No request data available</p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Average Latency by Endpoint</CardTitle>
              </CardHeader>
              <CardContent>
                {data?.requests.endpoints && data.requests.endpoints.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={data.requests.endpoints}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="endpoint" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Line type="monotone" dataKey="latency_avg_ms" stroke="#10b981" name="Latency (ms)" />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <p className="text-center text-gray-500 py-12">No latency data available</p>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="requests">
          <Card>
            <CardHeader>
              <CardTitle>Detailed Request Statistics</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-2">Endpoint</th>
                      <th className="text-left p-2">Method</th>
                      <th className="text-right p-2">Count</th>
                      <th className="text-right p-2">Error Rate</th>
                      <th className="text-right p-2">Avg Latency</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data?.requests.endpoints?.map((endpoint, idx) => (
                      <tr key={idx} className="border-b">
                        <td className="p-2">{endpoint.endpoint}</td>
                        <td className="p-2">
                          <Badge variant="outline">{endpoint.method}</Badge>
                        </td>
                        <td className="text-right p-2">{endpoint.count.toLocaleString()}</td>
                        <td className="text-right p-2">
                          <Badge variant={endpoint.error_rate > 0.05 ? 'destructive' : 'secondary'}>
                            {(endpoint.error_rate * 100).toFixed(2)}%
                          </Badge>
                        </td>
                        <td className="text-right p-2">
                          {endpoint.latency_avg_ms.toFixed(2)} ms
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="metrics">
          <Card>
            <CardHeader>
              <CardTitle>All Metrics</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {data && Object.entries(data.metrics).map(([name, metric]: [string, any]) => (
                  <Card key={name}>
                    <CardHeader>
                      <CardTitle className="text-sm">{name}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">
                        {metric.latest?.toFixed(2)} {metric.unit}
                      </div>
                      <div className="text-xs text-gray-500 mt-2">
                        Min: {metric.min?.toFixed(2)} | Max: {metric.max?.toFixed(2)} | Avg: {metric.avg?.toFixed(2)}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Last Updated */}
      <div className="text-center text-sm text-gray-500 mt-6">
        Last updated: {data?.timestamp ? new Date(data.timestamp).toLocaleString() : 'N/A'}
        {autoRefresh && ' • Auto-refreshing every 5s'}
      </div>
    </div>
  );
}

export default MonitoringDashboard;
