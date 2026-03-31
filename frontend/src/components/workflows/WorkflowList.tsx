/**
 * 工作流管理列表 - 完整的工作流管理界面
 * 支持筛选、搜索、启用/禁用、执行、查看/编辑、删除等功能
 */

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { 
  Play, 
  Pause, 
  Edit, 
  Trash2, 
  Search, 
  Filter, 
  Eye, 
  Zap, 
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  FileText,
  Settings,
  RefreshCw
} from "lucide-react";

interface WorkflowStep {
  name: string;
  type: "action" | "condition" | "parallel";
  action_type?: string;
  params?: Record<string, unknown>;
  conditions?: Array<{
    field: string;
    operator: string;
    value: unknown;
  }>;
  steps?: WorkflowStep[];
  timeout?: number;
  retry?: number;
  on_error?: "continue" | "abort" | "retry";
}

interface WorkflowExecution {
  id: string;
  workflow_name: string;
  status: "running" | "success" | "failed" | "pending";
  started_at: string;
  completed_at?: string;
  error?: string;
  steps_executed?: number;
}

interface Workflow {
  name: string;
  version: string;
  description: string;
  trigger: {
    type: "manual" | "event" | "timer";
    event_type?: string;
    cron?: string;
    conditions?: Array<{
      field: string;
      operator: string;
      value: unknown;
    }>;
  };
  workflow: WorkflowStep[];
  variables?: Record<string, unknown>;
  enabled?: boolean;
  tags?: string[];
  author?: string;
  created_at?: string;
  updated_at?: string;
  executions?: WorkflowExecution[];
}

export const WorkflowList: React.FC = () => {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedTag, setSelectedTag] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("all");
  const [selectedWorkflow, setSelectedWorkflow] = useState<Workflow | null>(null);
  const [executingWorkflow, setExecutingWorkflow] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchWorkflows();
  }, []);

  const fetchWorkflows = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/workflows");
      if (response.ok) {
        const data = await response.json();
        setWorkflows(data.workflows || []);
      }
    } catch (error) {
      console.error("获取工作流失败:", error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleEnable = async (workflowName: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/workflows/${workflowName}/enable`, {
        method: "POST",
      });
      if (response.ok) {
        fetchWorkflows();
        alert("工作流已启用");
      }
    } catch (error) {
      console.error("启用工作流失败:", error);
      alert("启用失败");
    }
  };

  const handleDisable = async (workflowName: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/workflows/${workflowName}/disable`, {
        method: "POST",
      });
      if (response.ok) {
        fetchWorkflows();
        alert("工作流已禁用");
      }
    } catch (error) {
      console.error("禁用工作流失败:", error);
      alert("禁用失败");
    }
  };

  const handleExecute = async (workflowName: string) => {
    setExecutingWorkflow(workflowName);
    try {
      const response = await fetch(`http://localhost:8000/api/workflows/${workflowName}/execute`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({}),
      });
      if (response.ok) {
        alert("工作流执行成功");
        fetchWorkflows();
      } else {
        const error = await response.json();
        alert(`工作流执行失败：${error.detail}`);
      }
    } catch (error) {
      console.error("执行工作流失败:", error);
      alert("执行失败");
    } finally {
      setExecutingWorkflow(null);
    }
  };

  const handleDelete = async (workflowName: string) => {
    if (!confirm(`确定要删除工作流 "${workflowName}" 吗？此操作不可恢复。`)) {
      return;
    }
    try {
      const response = await fetch(`http://localhost:8000/api/workflows/${workflowName}`, {
        method: "DELETE",
      });
      if (response.ok) {
        fetchWorkflows();
        alert("工作流已删除");
      } else {
        const error = await response.json();
        alert(`删除失败：${error.detail}`);
      }
    } catch (error) {
      console.error("删除工作流失败:", error);
      alert("删除失败");
    }
  };

  const handleRefresh = () => {
    setRefreshing(true);
    fetchWorkflows();
  };

  const getFilteredWorkflows = () => {
    let filtered = workflows;

    // 按标签筛选
    if (selectedTag) {
      filtered = filtered.filter((w) => w.tags?.includes(selectedTag));
    }

    // 按搜索词筛选
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (w) =>
          w.name.toLowerCase().includes(query) ||
          w.description.toLowerCase().includes(query) ||
          w.tags?.some((tag) => tag.toLowerCase().includes(query)),
      );
    }

    // 按标签页筛选
    if (activeTab === "enabled") {
      filtered = filtered.filter((w) => w.enabled !== false);
    } else if (activeTab === "disabled") {
      filtered = filtered.filter((w) => w.enabled === false);
    } else if (activeTab === "manual") {
      filtered = filtered.filter((w) => w.trigger.type === "manual");
    } else if (activeTab === "timer") {
      filtered = filtered.filter((w) => w.trigger.type === "timer");
    } else if (activeTab === "event") {
      filtered = filtered.filter((w) => w.trigger.type === "event");
    }

    return filtered;
  };

  const getAllTags = () => {
    const tags = new Set<string>();
    workflows.forEach((w) => {
      w.tags?.forEach((tag) => tags.add(tag));
    });
    return Array.from(tags);
  };

  const getTriggerIcon = (type: string) => {
    switch (type) {
      case "manual":
        return <Zap className="w-4 h-4" />;
      case "timer":
        return <Clock className="w-4 h-4" />;
      case "event":
        return <AlertCircle className="w-4 h-4" />;
      default:
        return <FileText className="w-4 h-4" />;
    }
  };

  const getStatusBadge = (workflow: Workflow) => {
    if (workflow.enabled) {
      return (
        <Badge className="bg-green-500">
          <CheckCircle className="w-3 h-3 mr-1" />
          已启用
        </Badge>
      );
    } else {
      return (
        <Badge variant="secondary">
          <XCircle className="w-3 h-3 mr-1" />
          已禁用
        </Badge>
      );
    }
  };

  const getTriggerBadge = (trigger: Workflow["trigger"]) => {
    const icon = getTriggerIcon(trigger.type);
    let label = trigger.type;
    
    if (trigger.type === "timer" && trigger.cron) {
      label = `定时 (${trigger.cron})`;
    } else if (trigger.type === "event" && trigger.event_type) {
      label = `事件 (${trigger.event_type})`;
    }

    return (
      <Badge variant="outline" className="flex items-center gap-1">
        {icon}
        {label}
      </Badge>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <RefreshCw className="w-12 h-12 animate-spin mx-auto mb-4 text-blue-500" />
          <p className="text-gray-600">加载工作流列表...</p>
        </div>
      </div>
    );
  }

  const filteredWorkflows = getFilteredWorkflows();
  const allTags = getAllTags();

  return (
    <div className="container mx-auto p-6">
      {/* 头部 */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold mb-2">工作流管理</h1>
          <p className="text-gray-600">管理和执行自动化工作流</p>
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
          <Button onClick={() => window.location.href = "/workflows/editor"} size="sm">
            <Zap className="w-4 h-4 mr-2" />
            新建工作流
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
                placeholder="搜索工作流名称、描述或标签..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            
            {allTags.length > 0 && (
              <div className="flex items-center gap-2">
                <Filter className="w-4 h-4 text-gray-500" />
                <select
                  value={selectedTag || ""}
                  onChange={(e) => setSelectedTag(e.target.value || null)}
                  className="p-2 border rounded"
                >
                  <option value="">所有标签</option>
                  {allTags.map((tag) => (
                    <option key={tag} value={tag}>
                      {tag}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* 标签页 */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="mb-4">
          <TabsTrigger value="all">全部 ({workflows.length})</TabsTrigger>
          <TabsTrigger value="enabled">已启用</TabsTrigger>
          <TabsTrigger value="disabled">已禁用</TabsTrigger>
          <TabsTrigger value="manual">手动触发</TabsTrigger>
          <TabsTrigger value="timer">定时触发</TabsTrigger>
          <TabsTrigger value="event">事件触发</TabsTrigger>
        </TabsList>

        <TabsContent value="all" className="mt-0">
          <WorkflowGrid
            workflows={filteredWorkflows}
            getStatusBadge={getStatusBadge}
            getTriggerBadge={getTriggerBadge}
            handleEnable={handleEnable}
            handleDisable={handleDisable}
            handleExecute={handleExecute}
            handleDelete={handleDelete}
            setSelectedWorkflow={setSelectedWorkflow}
            executingWorkflow={executingWorkflow}
          />
        </TabsContent>

        <TabsContent value="enabled" className="mt-0">
          <WorkflowGrid
            workflows={filteredWorkflows}
            getStatusBadge={getStatusBadge}
            getTriggerBadge={getTriggerBadge}
            handleEnable={handleEnable}
            handleDisable={handleDisable}
            handleExecute={handleExecute}
            handleDelete={handleDelete}
            setSelectedWorkflow={setSelectedWorkflow}
            executingWorkflow={executingWorkflow}
          />
        </TabsContent>

        <TabsContent value="disabled" className="mt-0">
          <WorkflowGrid
            workflows={filteredWorkflows}
            getStatusBadge={getStatusBadge}
            getTriggerBadge={getTriggerBadge}
            handleEnable={handleEnable}
            handleDisable={handleDisable}
            handleExecute={handleExecute}
            handleDelete={handleDelete}
            setSelectedWorkflow={setSelectedWorkflow}
            executingWorkflow={executingWorkflow}
          />
        </TabsContent>

        <TabsContent value="manual" className="mt-0">
          <WorkflowGrid
            workflows={filteredWorkflows}
            getStatusBadge={getStatusBadge}
            getTriggerBadge={getTriggerBadge}
            handleEnable={handleEnable}
            handleDisable={handleDisable}
            handleExecute={handleExecute}
            handleDelete={handleDelete}
            setSelectedWorkflow={setSelectedWorkflow}
            executingWorkflow={executingWorkflow}
          />
        </TabsContent>

        <TabsContent value="timer" className="mt-0">
          <WorkflowGrid
            workflows={filteredWorkflows}
            getStatusBadge={getStatusBadge}
            getTriggerBadge={getTriggerBadge}
            handleEnable={handleEnable}
            handleDisable={handleDisable}
            handleExecute={handleExecute}
            handleDelete={handleDelete}
            setSelectedWorkflow={setSelectedWorkflow}
            executingWorkflow={executingWorkflow}
          />
        </TabsContent>

        <TabsContent value="event" className="mt-0">
          <WorkflowGrid
            workflows={filteredWorkflows}
            getStatusBadge={getStatusBadge}
            getTriggerBadge={getTriggerBadge}
            handleEnable={handleEnable}
            handleDisable={handleDisable}
            handleExecute={handleExecute}
            handleDelete={handleDelete}
            setSelectedWorkflow={setSelectedWorkflow}
            executingWorkflow={executingWorkflow}
          />
        </TabsContent>
      </Tabs>

      {/* 工作流详情对话框 */}
      {selectedWorkflow && (
        <WorkflowDetailDialog
          workflow={selectedWorkflow}
          open={!!selectedWorkflow}
          onOpenChange={() => setSelectedWorkflow(null)}
        />
      )}
    </div>
  );
};

interface WorkflowGridProps {
  workflows: Workflow[];
  getStatusBadge: (workflow: Workflow) => React.ReactNode;
  getTriggerBadge: (trigger: Workflow["trigger"]) => React.ReactNode;
  handleEnable: (name: string) => void;
  handleDisable: (name: string) => void;
  handleExecute: (name: string) => void;
  handleDelete: (name: string) => void;
  setSelectedWorkflow: (workflow: Workflow) => void;
  executingWorkflow: string | null;
}

const WorkflowGrid: React.FC<WorkflowGridProps> = ({
  workflows,
  getStatusBadge,
  getTriggerBadge,
  handleEnable,
  handleDisable,
  handleExecute,
  handleDelete,
  setSelectedWorkflow,
  executingWorkflow,
}) => {
  if (workflows.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
        <p>暂无工作流</p>
        <p className="text-sm">点击"新建工作流"创建第一个工作流</p>
      </div>
    );
  }

  return (
    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
      {workflows.map((workflow) => (
        <Card key={workflow.name} className="hover:shadow-lg transition-shadow">
          <CardHeader>
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <CardTitle className="text-lg mb-1">{workflow.name}</CardTitle>
                <CardDescription className="text-sm">
                  {workflow.description || "无描述"}
                </CardDescription>
              </div>
              {getStatusBadge(workflow)}
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {/* 基本信息 */}
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <span>版本：{workflow.version}</span>
                {workflow.author && <span>• 作者：{workflow.author}</span>}
              </div>

              {/* 触发器类型 */}
              <div className="flex items-center gap-2">
                {getTriggerBadge(workflow.trigger)}
              </div>

              {/* 标签 */}
              {workflow.tags && workflow.tags.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {workflow.tags.map((tag) => (
                    <Badge key={tag} variant="secondary" className="text-xs">
                      {tag}
                    </Badge>
                  ))}
                </div>
              )}

              {/* 步骤数量 */}
              <div className="text-sm text-gray-500">
                步骤数：{workflow.workflow?.length || 0}
              </div>

              {/* 操作按钮 */}
              <div className="flex gap-2 pt-2 border-t">
                {workflow.enabled ? (
                  <Button
                    onClick={() => handleDisable(workflow.name)}
                    variant="outline"
                    size="sm"
                    className="flex-1"
                  >
                    <Pause className="w-4 h-4 mr-1" />
                    禁用
                  </Button>
                ) : (
                  <Button
                    onClick={() => handleEnable(workflow.name)}
                    size="sm"
                    className="flex-1"
                  >
                    <Play className="w-4 h-4 mr-1" />
                    启用
                  </Button>
                )}

                <Button
                  onClick={() => handleExecute(workflow.name)}
                  disabled={!workflow.enabled || executingWorkflow === workflow.name}
                  size="sm"
                  variant="outline"
                >
                  {executingWorkflow === workflow.name ? (
                    <RefreshCw className="w-4 h-4 animate-spin" />
                  ) : (
                    <Zap className="w-4 h-4" />
                  )}
                </Button>

                <Dialog>
                  <DialogTrigger asChild>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setSelectedWorkflow(workflow)}
                    >
                      <Eye className="w-4 h-4" />
                    </Button>
                  </DialogTrigger>
                </Dialog>

                <Button
                  onClick={() => handleDelete(workflow.name)}
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

interface WorkflowDetailDialogProps {
  workflow: Workflow;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const WorkflowDetailDialog: React.FC<WorkflowDetailDialogProps> = ({
  workflow,
  open,
  onOpenChange,
}) => {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl">{workflow.name}</DialogTitle>
        </DialogHeader>
        <div className="space-y-6 mt-4">
          {/* 基本信息 */}
          <div>
            <h3 className="font-semibold mb-2">基本信息</h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-500">版本：</span>
                <span>{workflow.version}</span>
              </div>
              <div>
                <span className="text-gray-500">作者：</span>
                <span>{workflow.author || "未知"}</span>
              </div>
              <div>
                <span className="text-gray-500">状态：</span>
                <Badge variant={workflow.enabled ? "default" : "secondary"}>
                  {workflow.enabled ? "已启用" : "已禁用"}
                </Badge>
              </div>
              <div>
                <span className="text-gray-500">触发器：</span>
                <span>{workflow.trigger.type}</span>
              </div>
            </div>
          </div>

          {/* 描述 */}
          <div>
            <h3 className="font-semibold mb-2">描述</h3>
            <p className="text-gray-600">{workflow.description || "无描述"}</p>
          </div>

          {/* 触发器配置 */}
          <div>
            <h3 className="font-semibold mb-2">触发器配置</h3>
            <Card>
              <CardContent className="p-4">
                <div className="space-y-2 text-sm">
                  <div>
                    <span className="text-gray-500">类型：</span>
                    <span className="font-medium">{workflow.trigger.type}</span>
                  </div>
                  {workflow.trigger.type === "timer" && workflow.trigger.cron && (
                    <div>
                      <span className="text-gray-500">Cron 表达式：</span>
                      <code className="bg-gray-100 px-2 py-1 rounded">
                        {workflow.trigger.cron}
                      </code>
                    </div>
                  )}
                  {workflow.trigger.type === "event" && workflow.trigger.event_type && (
                    <div>
                      <span className="text-gray-500">事件类型：</span>
                      <span>{workflow.trigger.event_type}</span>
                    </div>
                  )}
                  {workflow.trigger.conditions && workflow.trigger.conditions.length > 0 && (
                    <div>
                      <span className="text-gray-500">触发条件：</span>
                      <pre className="bg-gray-100 p-2 rounded mt-1 text-xs overflow-auto">
                        {JSON.stringify(workflow.trigger.conditions, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* 工作流步骤 */}
          <div>
            <h3 className="font-semibold mb-2">工作流步骤 ({workflow.workflow?.length || 0})</h3>
            <div className="space-y-2">
              {workflow.workflow?.map((step, index) => (
                <Card key={index}>
                  <CardContent className="p-3">
                    <div className="flex items-center gap-3">
                      <Badge variant="outline" className="w-8 h-8 flex items-center justify-center rounded-full">
                        {index + 1}
                      </Badge>
                      <div className="flex-1">
                        <div className="font-medium">{step.name}</div>
                        <div className="text-xs text-gray-500">
                          {step.type} {step.action_type && `• ${step.action_type}`}
                        </div>
                      </div>
                      {step.timeout && (
                        <div className="text-xs text-gray-500">
                          <Clock className="w-3 h-3 inline mr-1" />
                          {step.timeout}s
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>

          {/* 标签 */}
          {workflow.tags && workflow.tags.length > 0 && (
            <div>
              <h3 className="font-semibold mb-2">标签</h3>
              <div className="flex flex-wrap gap-2">
                {workflow.tags.map((tag) => (
                  <Badge key={tag} variant="secondary">
                    {tag}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* 变量 */}
          {workflow.variables && Object.keys(workflow.variables).length > 0 && (
            <div>
              <h3 className="font-semibold mb-2">变量</h3>
              <pre className="bg-gray-100 p-4 rounded text-xs overflow-auto">
                {JSON.stringify(workflow.variables, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default WorkflowList;
