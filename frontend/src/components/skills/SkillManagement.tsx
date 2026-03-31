/**
 * AI 技能市场 - 技能管理页面
 */

import React, { useState, useEffect } from "react";

interface Skill {
  name: string;
  version: string;
  description: string;
  enabled: boolean;
  tags: string[];
  trigger: {
    type: string;
    cron?: string;
    event_type?: string;
  };
  actions: Array<{
    type: string;
    params: Record<string, unknown>;
  }>;
}

interface SkillListResponse {
  count: number;
  skills: Skill[];
}

export const SkillManagement: React.FC = () => {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | "enabled" | "disabled">("all");
  const [selectedSkill, setSelectedSkill] = useState<Skill | null>(null);

  useEffect(() => {
    loadSkills();
  }, []);

  const loadSkills = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/skills");
      const data: SkillListResponse = await response.json();
      setSkills(data.skills);
    } catch (error) {
      console.error("加载技能失败:", error);
    } finally {
      setLoading(false);
    }
  };

  const toggleSkill = async (skillName: string, enabled: boolean) => {
    try {
      const endpoint = enabled ? "enable" : "disable";
      await fetch(`http://localhost:8000/api/skills/${skillName}/${endpoint}`, {
        method: "POST",
      });
      await loadSkills();
    } catch (error) {
      console.error("切换技能状态失败:", error);
    }
  };

  const triggerSkill = async (skillName: string) => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/skills/${skillName}/trigger`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({}),
        },
      );
      const result = await response.json();
      alert(`技能触发${result.success ? "成功" : "失败"}`);
    } catch (error) {
      console.error("触发技能失败:", error);
      alert("触发技能失败");
    }
  };

  const filteredSkills = skills.filter((skill) => {
    if (filter === "enabled") return skill.enabled;
    if (filter === "disabled") return !skill.enabled;
    return true;
  });

  if (loading) {
    return <div className="p-4">加载中...</div>;
  }

  return (
    <div className="p-4">
      <div className="mb-4 flex justify-between items-center">
        <h1 className="text-2xl font-bold">AI 技能市场</h1>
        <div className="space-x-2">
          <button
            onClick={() => setFilter("all")}
            className={`px-3 py-1 rounded ${filter === "all" ? "bg-blue-500 text-white" : "bg-gray-200"}`}
          >
            全部
          </button>
          <button
            onClick={() => setFilter("enabled")}
            className={`px-3 py-1 rounded ${filter === "enabled" ? "bg-blue-500 text-white" : "bg-gray-200"}`}
          >
            启用中
          </button>
          <button
            onClick={() => setFilter("disabled")}
            className={`px-3 py-1 rounded ${filter === "disabled" ? "bg-blue-500 text-white" : "bg-gray-200"}`}
          >
            已禁用
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredSkills.map((skill) => (
          <div
            key={skill.name}
            className="border rounded-lg p-4 hover:shadow-lg transition-shadow"
          >
            <div className="flex justify-between items-start mb-2">
              <h3 className="text-lg font-semibold">{skill.name}</h3>
              <span
                className={`px-2 py-1 rounded text-xs ${skill.enabled ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}`}
              >
                {skill.enabled ? "启用" : "禁用"}
              </span>
            </div>

            <p className="text-gray-600 text-sm mb-2">{skill.description}</p>

            <div className="mb-2">
              <span className="text-xs text-gray-500">版本：{skill.version}</span>
            </div>

            <div className="flex flex-wrap gap-1 mb-3">
              {skill.tags.map((tag) => (
                <span
                  key={tag}
                  className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded"
                >
                  {tag}
                </span>
              ))}
            </div>

            <div className="text-xs text-gray-500 mb-3">
              <div>触发器：{skill.trigger.type}</div>
              {skill.trigger.type === "timer" && (
                <div>Cron: {skill.trigger.cron}</div>
              )}
              {skill.trigger.type === "event" && (
                <div>事件：{skill.trigger.event_type}</div>
              )}
            </div>

            <div className="flex space-x-2">
              <button
                onClick={() => toggleSkill(skill.name, !skill.enabled)}
                className={`flex-1 px-3 py-1 rounded text-sm ${
                  skill.enabled
                    ? "bg-red-500 text-white hover:bg-red-600"
                    : "bg-green-500 text-white hover:bg-green-600"
                }`}
              >
                {skill.enabled ? "禁用" : "启用"}
              </button>
              <button
                onClick={() => triggerSkill(skill.name)}
                className="flex-1 px-3 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600"
              >
                触发
              </button>
              <button
                onClick={() => setSelectedSkill(skill)}
                className="px-3 py-1 bg-gray-500 text-white rounded text-sm hover:bg-gray-600"
              >
                详情
              </button>
            </div>
          </div>
        ))}
      </div>

      {selectedSkill && (
        <SkillDetailModal
          skill={selectedSkill}
          onClose={() => setSelectedSkill(null)}
        />
      )}
    </div>
  );
};

interface SkillDetailModalProps {
  skill: Skill;
  onClose: () => void;
}

const SkillDetailModal: React.FC<SkillDetailModalProps> = ({
  skill,
  onClose,
}) => {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">{skill.name}</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl"
          >
            ×
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <h3 className="font-semibold mb-1">描述</h3>
            <p className="text-gray-600">{skill.description}</p>
          </div>

          <div>
            <h3 className="font-semibold mb-1">版本</h3>
            <p className="text-gray-600">{skill.version}</p>
          </div>

          <div>
            <h3 className="font-semibold mb-1">状态</h3>
            <p className="text-gray-600">{skill.enabled ? "启用" : "禁用"}</p>
          </div>

          <div>
            <h3 className="font-semibold mb-1">标签</h3>
            <div className="flex flex-wrap gap-1">
              {skill.tags.map((tag) => (
                <span
                  key={tag}
                  className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>

          <div>
            <h3 className="font-semibold mb-1">触发器</h3>
            <div className="bg-gray-50 p-3 rounded">
              <div className="text-sm">类型：{skill.trigger.type}</div>
              {skill.trigger.cron && (
                <div className="text-sm">Cron: {skill.trigger.cron}</div>
              )}
              {skill.trigger.event_type && (
                <div className="text-sm">事件类型：{skill.trigger.event_type}</div>
              )}
            </div>
          </div>

          <div>
            <h3 className="font-semibold mb-1">动作列表</h3>
            <div className="space-y-2">
              {skill.actions.map((action, index) => (
                <div key={index} className="bg-gray-50 p-3 rounded">
                  <div className="text-sm font-medium">{action.type}</div>
                  <div className="text-xs text-gray-500 mt-1">
                    参数：{JSON.stringify(action.params, null, 2)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="mt-6 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
          >
            关闭
          </button>
        </div>
      </div>
    </div>
  );
};
