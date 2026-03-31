/**
 * 工作流模板市场 - 工作流可视化编辑器
 */

import React, { useState, useCallback } from "react";

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

interface WorkflowDefinition {
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
}

export const WorkflowEditor: React.FC = () => {
  const [workflow, setWorkflow] = useState<WorkflowDefinition>({
    name: "",
    version: "1.0.0",
    description: "",
    trigger: {
      type: "manual",
    },
    workflow: [],
    enabled: true,
    tags: [],
    author: "User",
  });

  const [selectedStep, setSelectedStep] = useState<number | null>(null);

  const addStep = useCallback(() => {
    const newStep: WorkflowStep = {
      name: `步骤 ${workflow.workflow.length + 1}`,
      type: "action",
      action_type: "send_message",
      params: {},
      timeout: 300,
      retry: 3,
      on_error: "abort",
    };

    setWorkflow((prev) => ({
      ...prev,
      workflow: [...prev.workflow, newStep],
    }));
  }, [workflow.workflow.length]);

  const updateStep = useCallback(
    (index: number, updates: Partial<WorkflowStep>) => {
      setWorkflow((prev) => ({
        ...prev,
        workflow: prev.workflow.map((step, i) =>
          i === index ? { ...step, ...updates } : step,
        ),
      }));
    },
    [],
  );

  const deleteStep = useCallback((index: number) => {
    setWorkflow((prev) => ({
      ...prev,
      workflow: prev.workflow.filter((_, i) => i !== index),
    }));
    if (selectedStep === index) {
      setSelectedStep(null);
    }
  }, [selectedStep]);

  const moveStep = useCallback(
    (index: number, direction: "up" | "down") => {
      if (
        (direction === "up" && index === 0) ||
        (direction === "down" && index === workflow.workflow.length - 1)
      ) {
        return;
      }

      const newWorkflow = [...workflow.workflow];
      const targetIndex = direction === "up" ? index - 1 : index + 1;
      [newWorkflow[index], newWorkflow[targetIndex]] = [
        newWorkflow[targetIndex],
        newWorkflow[index],
      ];

      setWorkflow((prev) => ({
        ...prev,
        workflow: newWorkflow,
      }));

      setSelectedStep(targetIndex);
    },
    [workflow.workflow],
  );

  const saveWorkflow = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/workflows", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(workflow),
      });

      if (response.ok) {
        alert("工作流保存成功！");
      } else {
        alert("工作流保存失败");
      }
    } catch (error) {
      console.error("保存工作流失败:", error);
      alert("保存失败");
    }
  };

  return (
    <div className="flex h-screen">
      {/* 左侧：步骤列表 */}
      <div className="w-1/3 border-r p-4 overflow-y-auto">
        <div className="mb-4">
          <h2 className="text-xl font-bold mb-2">工作流编辑器</h2>
          <input
            type="text"
            placeholder="工作流名称"
            value={workflow.name}
            onChange={(e) =>
              setWorkflow((prev) => ({ ...prev, name: e.target.value }))
            }
            className="w-full p-2 border rounded mb-2"
          />
          <textarea
            placeholder="工作流描述"
            value={workflow.description}
            onChange={(e) =>
              setWorkflow((prev) => ({ ...prev, description: e.target.value }))
            }
            className="w-full p-2 border rounded mb-2"
            rows={2}
          />
        </div>

        <div className="mb-4">
          <div className="flex justify-between items-center mb-2">
            <h3 className="font-semibold">工作流步骤</h3>
            <button
              onClick={addStep}
              className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              + 添加步骤
            </button>
          </div>

          <div className="space-y-2">
            {workflow.workflow.map((step, index) => (
              <div
                key={index}
                className={`p-3 border rounded cursor-pointer transition-colors ${
                  selectedStep === index
                    ? "bg-blue-100 border-blue-500"
                    : "bg-white hover:bg-gray-50"
                }`}
                onClick={() => setSelectedStep(index)}
              >
                <div className="flex justify-between items-center">
                  <div>
                    <div className="font-medium">{step.name}</div>
                    <div className="text-xs text-gray-500">
                      {step.type}
                      {step.action_type && ` - ${step.action_type}`}
                    </div>
                  </div>
                  <div className="flex space-x-1">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        moveStep(index, "up");
                      }}
                      className="px-2 py-1 text-xs bg-gray-200 rounded hover:bg-gray-300"
                      disabled={index === 0}
                    >
                      ↑
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        moveStep(index, "down");
                      }}
                      className="px-2 py-1 text-xs bg-gray-200 rounded hover:bg-gray-300"
                      disabled={index === workflow.workflow.length - 1}
                    >
                      ↓
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteStep(index);
                      }}
                      className="px-2 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600"
                    >
                      ×
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <button
          onClick={saveWorkflow}
          className="w-full px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
        >
          保存工作流
        </button>
      </div>

      {/* 右侧：步骤配置 */}
      <div className="w-2/3 p-4 overflow-y-auto">
        {selectedStep !== null && workflow.workflow[selectedStep] ? (
          <StepConfigurator
            step={workflow.workflow[selectedStep]}
            onChange={(updates) => updateStep(selectedStep, updates)}
          />
        ) : (
          <div className="text-center text-gray-500 mt-20">
            <p>请选择一个步骤进行配置</p>
            <p className="text-sm">或点击"添加步骤"创建新步骤</p>
          </div>
        )}
      </div>
    </div>
  );
};

interface StepConfiguratorProps {
  step: WorkflowStep;
  onChange: (updates: Partial<WorkflowStep>) => void;
}

const StepConfigurator: React.FC<StepConfiguratorProps> = ({
  step,
  onChange,
}) => {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-bold">步骤配置</h3>

      {/* 基本信息 */}
      <div>
        <label className="block text-sm font-medium mb-1">步骤名称</label>
        <input
          type="text"
          value={step.name}
          onChange={(e) => onChange({ name: e.target.value })}
          className="w-full p-2 border rounded"
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">步骤类型</label>
        <select
          value={step.type}
          onChange={(e) =>
            onChange({ type: e.target.value as "action" | "condition" | "parallel" })
          }
          className="w-full p-2 border rounded"
        >
          <option value="action">动作</option>
          <option value="condition">条件</option>
          <option value="parallel">并行</option>
        </select>
      </div>

      {step.type === "action" && (
        <>
          <div>
            <label className="block text-sm font-medium mb-1">动作类型</label>
            <select
              value={step.action_type || ""}
              onChange={(e) => onChange({ action_type: e.target.value })}
              className="w-full p-2 border rounded"
            >
              <option value="">选择动作类型</option>
              <option value="send_message">发送消息</option>
              <option value="ai_generate">AI 生成</option>
              <option value="create_task">创建任务</option>
              <option value="http_request">HTTP 请求</option>
              <option value="query_data">数据查询</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              动作参数（JSON）
            </label>
            <textarea
              value={JSON.stringify(step.params, null, 2)}
              onChange={(e) => {
                try {
                  onChange({ params: JSON.parse(e.target.value) });
                } catch {
                  // 忽略无效的 JSON
                }
              }}
              className="w-full p-2 border rounded font-mono text-sm"
              rows={6}
            />
          </div>
        </>
      )}

      {step.type === "condition" && (
        <div>
          <label className="block text-sm font-medium mb-1">
            条件列表（JSON）
          </label>
          <textarea
            value={JSON.stringify(step.conditions, null, 2)}
            onChange={(e) => {
              try {
                onChange({ conditions: JSON.parse(e.target.value) });
              } catch {
                // 忽略无效的 JSON
              }
            }}
            className="w-full p-2 border rounded font-mono text-sm"
            rows={6}
          />
        </div>
      )}

      {/* 高级配置 */}
      <div className="border-t pt-4">
        <h4 className="font-semibold mb-2">高级配置</h4>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">
              超时时间（秒）
            </label>
            <input
              type="number"
              value={step.timeout || 300}
              onChange={(e) =>
                onChange({ timeout: parseInt(e.target.value) })
              }
              className="w-full p-2 border rounded"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">重试次数</label>
            <input
              type="number"
              value={step.retry || 3}
              onChange={(e) => onChange({ retry: parseInt(e.target.value) })}
              className="w-full p-2 border rounded"
            />
          </div>
        </div>

        <div className="mt-4">
          <label className="block text-sm font-medium mb-1">错误处理</label>
          <select
            value={step.on_error || "abort"}
            onChange={(e) =>
              onChange({
                on_error: e.target.value as "continue" | "abort" | "retry",
              })
            }
            className="w-full p-2 border rounded"
          >
            <option value="abort">中止</option>
            <option value="continue">继续</option>
            <option value="retry">重试</option>
          </select>
        </div>
      </div>
    </div>
  );
};
