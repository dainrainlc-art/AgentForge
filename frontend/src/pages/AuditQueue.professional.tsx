/**
 * AuditQueue Professional - 集成 react-diff-viewer 和 recharts
 * 注意：需要先安装依赖：npm install react-diff-viewer recharts
 */

import React, { useState, useEffect, Suspense, lazy } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';

// 懒加载 react-diff-viewer 以优化性能
const ReactDiffViewer = lazy(() => import('react-diff-viewer'));

interface AuditItem {
  id: string;
  type: string;
  content: string;
  originalContent?: string;
  status: string;
  sentiment?: string;
  confidence?: number;
  createdAt: string;
}

interface TrendData {
  date: string;
  approved: number;
  rejected: number;
  pending: number;
}

interface SentimentData {
  name: string;
  value: number;
}

const COLORS = {
  approved: '#10b981',
  rejected: '#ef4444',
  pending: '#f59e0b',
  positive: '#3b82f6',
  negative: '#ef4444',
  neutral: '#6b7280',
};

export function AuditQueueProfessional() {
  const [items, setItems] = useState<AuditItem[]>([]);
  const [selectedItem, setSelectedItem] = useState<AuditItem | null>(null);
  const [showDiff, setShowDiff] = useState(false);
  const [trendData, setTrendData] = useState<TrendData[]>([]);
  const [sentimentData, setSentimentData] = useState<SentimentData[]>([]);

  useEffect(() => {
    // 模拟数据 - 实际应从 API 获取
    const mockTrendData: TrendData[] = [
      { date: '03-22', approved: 12, rejected: 3, pending: 5 },
      { date: '03-23', approved: 15, rejected: 2, pending: 4 },
      { date: '03-24', approved: 18, rejected: 4, pending: 6 },
      { date: '03-25', approved: 14, rejected: 3, pending: 3 },
      { date: '03-26', approved: 20, rejected: 2, pending: 5 },
      { date: '03-27', approved: 16, rejected: 4, pending: 4 },
      { date: '03-28', approved: 19, rejected: 3, pending: 5 },
    ];
    setTrendData(mockTrendData);

    const mockSentimentData: SentimentData[] = [
      { name: '积极', value: 65 },
      { name: '消极', value: 15 },
      { name: '中性', value: 20 },
    ];
    setSentimentData(mockSentimentData);
  }, []);

  const renderDiffView = () => {
    if (!selectedItem || !selectedItem.originalContent) return null;

    return (
      <div className="mb-6">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold text-white">内容对比</h3>
          <button
            onClick={() => setShowDiff(!showDiff)}
            className="text-sm text-blue-400 hover:text-blue-300"
          >
            {showDiff ? '关闭对比' : '显示对比'}
          </button>
        </div>

        {showDiff && (
          <Suspense fallback={<div className="text-gray-400">加载中...</div>}>
            <ReactDiffViewer
              oldValue={selectedItem.originalContent}
              newValue={selectedItem.content}
              splitView={true}
              leftTitle="原始内容"
              rightTitle="AI 生成内容"
              useDarkTheme={true}
              styles={{
                variables: {
                  dark: {
                    diffViewerBackground: '#1f2937',
                    color: '#f3f4f6',
                    addedBackground: '#064e3b',
                    addedColor: '#d1fae5',
                    removedBackground: '#7f1d1d',
                    removedColor: '#fee2e2',
                  }
                }
              }}
            />
          </Suspense>
        )}

        {!showDiff && (
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-red-900/10 rounded p-4 border border-red-900/30">
              <div className="text-xs text-red-400 mb-2 font-semibold">原始内容</div>
              <pre className="text-sm text-gray-300 whitespace-pre-wrap">
                {selectedItem.originalContent}
              </pre>
            </div>
            <div className="bg-green-900/10 rounded p-4 border border-green-900/30">
              <div className="text-xs text-green-400 mb-2 font-semibold">AI 生成内容</div>
              <pre className="text-sm text-gray-300 whitespace-pre-wrap">
                {selectedItem.content}
              </pre>
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderTrendChart = () => {
    return (
      <div className="bg-gray-800 rounded-lg p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4 text-white">审核趋势</h2>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={trendData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="date" stroke="#9ca3af" />
            <YAxis stroke="#9ca3af" />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1f2937',
                border: '1px solid #374151',
                color: '#f3f4f6',
                borderRadius: '8px'
              }}
            />
            <Legend />
            <Bar dataKey="approved" fill={COLORS.approved} name="通过" radius={[4, 4, 0, 0]} />
            <Bar dataKey="rejected" fill={COLORS.rejected} name="驳回" radius={[4, 4, 0, 0]} />
            <Bar dataKey="pending" fill={COLORS.pending} name="待审核" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  };

  const renderSentimentChart = () => {
    return (
      <div className="bg-gray-800 rounded-lg p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4 text-white">情绪分布</h2>
        <ResponsiveContainer width="100%" height={250}>
          <PieChart>
            <Pie
              data={sentimentData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
            >
              {sentimentData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={index === 0 ? COLORS.positive : index === 1 ? COLORS.negative : COLORS.neutral}
                />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: '#1f2937',
                border: '1px solid #374151',
                color: '#f3f4f6',
                borderRadius: '8px'
              }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">AI 内容审核中心（专业版）</h1>

        {/* 图表区域 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div>{renderTrendChart()}</div>
          <div>{renderSentimentChart()}</div>
        </div>

        {/* 主内容区 */}
        <div className="grid grid-cols-3 gap-6">
          {/* 左侧列表 */}
          <div className="col-span-1 space-y-4 max-h-[calc(100vh-400px)] overflow-y-auto">
            {items.length === 0 ? (
              <div className="text-center py-8 text-gray-400">
                暂无待审核内容
              </div>
            ) : (
              items.map((item) => (
                <div
                  key={item.id}
                  onClick={() => setSelectedItem(item)}
                  className={`bg-gray-800 rounded-lg p-4 cursor-pointer transition-all hover:bg-gray-750 ${
                    selectedItem?.id === item.id ? 'ring-2 ring-blue-500' : ''
                  }`}
                >
                  <p className="text-sm line-clamp-3">{item.content}</p>
                  <div className="flex items-center justify-between mt-2">
                    <span className="text-xs text-gray-500">
                      {new Date(item.createdAt).toLocaleString('zh-CN')}
                    </span>
                    {item.confidence && (
                      <span className={`text-xs ${
                        item.confidence >= 0.8 ? 'text-green-400' :
                        item.confidence >= 0.6 ? 'text-yellow-400' : 'text-red-400'
                      }`}>
                        {(item.confidence * 100).toFixed(0)}%
                      </span>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>

          {/* 右侧详情 */}
          <div className="col-span-2 bg-gray-800 rounded-lg p-6">
            {selectedItem ? (
              <div>
                <h2 className="text-xl font-semibold mb-4">内容详情</h2>
                
                {/* Diff 视图 */}
                {renderDiffView()}

                {/* 审核操作 */}
                <div className="flex gap-3 mt-6">
                  <button className="flex-1 py-3 bg-green-600 hover:bg-green-700 rounded-lg font-semibold">
                    ✓ 通过
                  </button>
                  <button className="flex-1 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-semibold">
                    ✏️ 修改
                  </button>
                  <button className="flex-1 py-3 bg-red-600 hover:bg-red-700 rounded-lg font-semibold">
                    ✗ 驳回
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center h-full text-gray-400">
                选择左侧内容进行审核
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default AuditQueueProfessional;
