import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../hooks/useAuth';

interface AuditItem {
  id: string;
  type: 'social_post' | 'message_reply' | 'content_creation' | 'quotation';
  platform?: string;
  content: string;
  originalContent?: string;
  generatedAt: string;
  status: 'pending' | 'approved' | 'rejected' | 'modified';
  metadata?: Record<string, any>;
  confidence?: number;
  riskLevel?: 'low' | 'medium' | 'high';
  aiRecommend?: 'approve' | 'reject' | 'review';
}

interface AuditStats {
  pending: number;
  approved: number;
  rejected: number;
  todayTotal: number;
  avgReviewTime: number;
  passRate: number;
}

interface TrendData {
  date: string;
  approved: number;
  rejected: number;
  pending: number;
}

export function AuditQueue() {
  const { user } = useAuth();
  const [items, setItems] = useState<AuditItem[]>([]);
  const [stats, setStats] = useState<AuditStats>({ 
    pending: 0, 
    approved: 0, 
    rejected: 0, 
    todayTotal: 0,
    avgReviewTime: 0,
    passRate: 0
  });
  const [selectedItem, setSelectedItem] = useState<AuditItem | null>(null);
  const [editContent, setEditContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'pending' | 'approved' | 'rejected'>('pending');
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set());
  const [showDiff, setShowDiff] = useState(false);
  const [trendData, setTrendData] = useState<TrendData[]>([]);

  useEffect(() => {
    fetchAuditItems();
    fetchTrendData();
  }, [filter]);

  // 键盘快捷键
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (!selectedItem) return;
      
      // 跳过输入框
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }

      switch (e.key.toLowerCase()) {
        case 'a': // 通过
          e.preventDefault();
          handleApprove(selectedItem);
          break;
        case 'r': // 驳回
          e.preventDefault();
          const reason = prompt('请输入驳回原因:');
          if (reason) handleReject(selectedItem, reason);
          break;
        case 'm': // 修改
          e.preventDefault();
          handleModify(selectedItem, editContent);
          break;
        case 'd': // 切换 diff 视图
          e.preventDefault();
          setShowDiff(!showDiff);
          break;
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [selectedItem, editContent, showDiff]);

  const fetchAuditItems = async () => {
    try {
      const response = await fetch(`/api/audit/items?status=${filter}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      const data = await response.json();
      setItems(data.items || []);
      setStats(data.stats || stats);
    } catch (error) {
      console.error('Failed to fetch audit items:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchTrendData = async () => {
    try {
      const response = await fetch('/api/audit/trend', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      const data = await response.json();
      setTrendData(data.trend || []);
    } catch (error) {
      console.error('Failed to fetch trend data:', error);
    }
  };

  const handleApprove = async (item: AuditItem) => {
    try {
      const response = await fetch(`/api/audit/${item.id}/approve`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        setItems(items.filter(i => i.id !== item.id));
        setSelectedItem(null);
        fetchAuditItems();
      }
    } catch (error) {
      console.error('Failed to approve:', error);
    }
  };

  const handleReject = async (item: AuditItem, reason: string) => {
    try {
      const response = await fetch(`/api/audit/${item.id}/reject`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ reason })
      });
      
      if (response.ok) {
        setItems(items.filter(i => i.id !== item.id));
        setSelectedItem(null);
        fetchAuditItems();
      }
    } catch (error) {
      console.error('Failed to reject:', error);
    }
  };

  const handleModify = async (item: AuditItem, newContent: string) => {
    try {
      const response = await fetch(`/api/audit/${item.id}/modify`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ content: newContent })
      });
      
      if (response.ok) {
        fetchAuditItems();
        setSelectedItem(null);
      }
    } catch (error) {
      console.error('Failed to modify:', error);
    }
  };

  const handleRegenerate = async (item: AuditItem) => {
    try {
      const response = await fetch(`/api/audit/${item.id}/regenerate`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setItems(items.map(i => i.id === item.id ? { ...i, content: data.content } : i));
        if (selectedItem?.id === item.id) {
          setSelectedItem({ ...selectedItem, content: data.content });
          setEditContent(data.content);
        }
      }
    } catch (error) {
      console.error('Failed to regenerate:', error);
    }
  };

  const handleBatchApprove = async () => {
    if (selectedItems.size === 0) {
      alert('请选择要批量通过的项目');
      return;
    }

    if (!confirm(`确定要批量通过 ${selectedItems.size} 个项目吗？`)) {
      return;
    }

    try {
      const response = await fetch('/api/audit/batch/approve', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ ids: Array.from(selectedItems) })
      });

      if (response.ok) {
        setItems(items.filter(i => !selectedItems.has(i.id)));
        setSelectedItems(new Set());
        fetchAuditItems();
        alert(`已成功通过 ${selectedItems.size} 个项目`);
      }
    } catch (error) {
      console.error('Failed to batch approve:', error);
      alert('批量操作失败');
    }
  };

  const handleBatchReject = async () => {
    if (selectedItems.size === 0) {
      alert('请选择要批量驳回的项目');
      return;
    }

    const reason = prompt('请输入驳回原因:');
    if (!reason) return;

    try {
      const response = await fetch('/api/audit/batch/reject', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
          ids: Array.from(selectedItems),
          reason 
        })
      });

      if (response.ok) {
        setItems(items.filter(i => !selectedItems.has(i.id)));
        setSelectedItems(new Set());
        fetchAuditItems();
        alert(`已成功驳回 ${selectedItems.size} 个项目`);
      }
    } catch (error) {
      console.error('Failed to batch reject:', error);
      alert('批量操作失败');
    }
  };

  const toggleSelectItem = (id: string) => {
    const newSelected = new Set(selectedItems);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedItems(newSelected);
  };

  const selectAll = () => {
    if (selectedItems.size === items.length) {
      setSelectedItems(new Set());
    } else {
      setSelectedItems(new Set(items.map(i => i.id)));
    }
  };

  const getTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      social_post: '社交媒体帖子',
      message_reply: '客户消息回复',
      content_creation: '内容创作',
      quotation: '报价建议'
    };
    return labels[type] || type;
  };

  const getPlatformIcon = (platform?: string) => {
    const icons: Record<string, string> = {
      twitter: '𝕏',
      linkedin: 'in',
      youtube: '▶',
      facebook: 'f',
      instagram: '📷'
    };
    return platform ? icons[platform] || platform : '';
  };

  const getConfidenceColor = (confidence?: number) => {
    if (!confidence) return 'text-gray-400';
    if (confidence >= 0.8) return 'text-green-400';
    if (confidence >= 0.6) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getRiskColor = (risk?: string) => {
    switch (risk) {
      case 'low': return 'text-green-400 bg-green-900/20';
      case 'medium': return 'text-yellow-400 bg-yellow-900/20';
      case 'high': return 'text-red-400 bg-red-900/20';
      default: return 'text-gray-400 bg-gray-900/20';
    }
  };

  const getRecommendationIcon = (recommendation?: string) => {
    switch (recommendation) {
      case 'approve': return '✅';
      case 'reject': return '❌';
      case 'review': return '⚠️';
      default: return '';
    }
  };

  // 简单的 diff 视图（高亮差异）
  const renderDiffView = () => {
    if (!selectedItem || !selectedItem.originalContent) return null;

    return (
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <label className="block text-sm text-gray-400">内容对比</label>
          <button
            onClick={() => setShowDiff(!showDiff)}
            className="text-xs text-blue-400 hover:text-blue-300"
          >
            {showDiff ? '关闭对比' : '显示对比'}
          </button>
        </div>
        
        {showDiff && (
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-red-900/10 rounded p-3 border border-red-900/30">
              <div className="text-xs text-red-400 mb-2">原始内容</div>
              <pre className="text-sm text-gray-300 whitespace-pre-wrap">
                {selectedItem.originalContent}
              </pre>
            </div>
            <div className="bg-green-900/10 rounded p-3 border border-green-900/30">
              <div className="text-xs text-green-400 mb-2">AI 生成内容</div>
              <pre className="text-sm text-gray-300 whitespace-pre-wrap">
                {selectedItem.content}
              </pre>
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">AI 内容审核中心</h1>
          <p className="text-gray-400">审核 AI 生成的内容，确保品牌形象一致性</p>
          <div className="mt-4 flex gap-2 text-sm text-gray-500">
            <span>快捷键:</span>
            <kbd className="px-2 py-1 bg-gray-800 rounded">A</kbd>
            <span>通过</span>
            <kbd className="px-2 py-1 bg-gray-800 rounded">R</kbd>
            <span>驳回</span>
            <kbd className="px-2 py-1 bg-gray-800 rounded">M</kbd>
            <span>修改</span>
            <kbd className="px-2 py-1 bg-gray-800 rounded">D</kbd>
            <span>对比</span>
          </div>
        </div>

        {/* 统计卡片 */}
        <div className="grid grid-cols-6 gap-4 mb-8">
          <div className="bg-gray-800 rounded-lg p-4">
            <div className="text-2xl font-bold text-yellow-500">{stats.pending}</div>
            <div className="text-gray-400 text-sm">待审核</div>
          </div>
          <div className="bg-gray-800 rounded-lg p-4">
            <div className="text-2xl font-bold text-green-500">{stats.approved}</div>
            <div className="text-gray-400 text-sm">已通过</div>
          </div>
          <div className="bg-gray-800 rounded-lg p-4">
            <div className="text-2xl font-bold text-red-500">{stats.rejected}</div>
            <div className="text-gray-400 text-sm">已驳回</div>
          </div>
          <div className="bg-gray-800 rounded-lg p-4">
            <div className="text-2xl font-bold text-blue-500">{stats.todayTotal}</div>
            <div className="text-gray-400 text-sm">今日生成</div>
          </div>
          <div className="bg-gray-800 rounded-lg p-4">
            <div className="text-2xl font-bold text-purple-500">{stats.avgReviewTime.toFixed(1)}h</div>
            <div className="text-gray-400 text-sm">平均审核时间</div>
          </div>
          <div className="bg-gray-800 rounded-lg p-4">
            <div className="text-2xl font-bold text-cyan-500">{(stats.passRate * 100).toFixed(1)}%</div>
            <div className="text-gray-400 text-sm">通过率</div>
          </div>
        </div>

        {/* 趋势图表 */}
        {trendData.length > 0 && (
          <div className="bg-gray-800 rounded-lg p-6 mb-8">
            <h2 className="text-xl font-semibold mb-4">审核趋势</h2>
            <div className="h-48 flex items-end gap-2">
              {trendData.map((day, index) => (
                <div key={index} className="flex-1 flex flex-col items-center gap-1">
                  <div className="w-full flex gap-1">
                    <div 
                      className="flex-1 bg-green-600 rounded-t"
                      style={{ height: `${Math.max(day.approved * 10, 4)}px` }}
                      title={`通过：${day.approved}`}
                    />
                    <div 
                      className="flex-1 bg-red-600 rounded-t"
                      style={{ height: `${Math.max(day.rejected * 10, 4)}px` }}
                      title={`驳回：${day.rejected}`}
                    />
                    <div 
                      className="flex-1 bg-yellow-600 rounded-t"
                      style={{ height: `${Math.max(day.pending * 10, 4)}px` }}
                      title={`待审核：${day.pending}`}
                    />
                  </div>
                  <div className="text-xs text-gray-400">{day.date}</div>
                </div>
              ))}
            </div>
            <div className="flex gap-4 mt-4 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-green-600 rounded" />
                <span className="text-gray-400">通过</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-red-600 rounded" />
                <span className="text-gray-400">驳回</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-yellow-600 rounded" />
                <span className="text-gray-400">待审核</span>
              </div>
            </div>
          </div>
        )}

        {/* 筛选和批量操作 */}
        <div className="flex justify-between items-center mb-6">
          <div className="flex gap-2">
            {(['pending', 'all', 'approved', 'rejected'] as const).map((status) => (
              <button
                key={status}
                onClick={() => setFilter(status)}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  filter === status
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                }`}
              >
                {status === 'pending' ? '待审核' : status === 'all' ? '全部' : status === 'approved' ? '已通过' : '已驳回'}
              </button>
            ))}
          </div>

          {selectedItems.size > 0 && (
            <div className="flex gap-2">
              <button
                onClick={handleBatchApprove}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg font-semibold"
              >
                ✓ 批量通过 ({selectedItems.size})
              </button>
              <button
                onClick={handleBatchReject}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg font-semibold"
              >
                ✗ 批量驳回 ({selectedItems.size})
              </button>
            </div>
          )}
        </div>

        {/* 主内容区 */}
        <div className="grid grid-cols-3 gap-6">
          {/* 左侧列表 */}
          <div className="col-span-1 space-y-4 max-h-[calc(100vh-400px)] overflow-y-auto">
            {/* 全选按钮 */}
            {filter === 'pending' && items.length > 0 && (
              <div className="flex items-center gap-2 mb-4">
                <input
                  type="checkbox"
                  checked={selectedItems.size === items.length}
                  onChange={selectAll}
                  className="rounded"
                />
                <span className="text-sm text-gray-400">
                  {selectedItems.size === items.length ? '取消全选' : '全选'}
                </span>
              </div>
            )}

            {loading ? (
              <div className="text-center py-8 text-gray-400">加载中...</div>
            ) : items.length === 0 ? (
              <div className="text-center py-8 text-gray-400">暂无待审核内容</div>
            ) : (
              items.map((item) => (
                <div
                  key={item.id}
                  onClick={() => {
                    setSelectedItem(item);
                    setEditContent(item.content);
                  }}
                  className={`bg-gray-800 rounded-lg p-4 cursor-pointer transition-all hover:bg-gray-750 ${
                    selectedItem?.id === item.id ? 'ring-2 ring-blue-500' : ''
                  }`}
                >
                  <div className="flex items-center gap-2 mb-2">
                    {filter === 'pending' && (
                      <input
                        type="checkbox"
                        checked={selectedItems.has(item.id)}
                        onChange={(e) => {
                          e.stopPropagation();
                          toggleSelectItem(item.id);
                        }}
                        onClick={(e) => e.stopPropagation()}
                        className="rounded"
                      />
                    )}
                    <span className="text-sm text-gray-400">{getTypeLabel(item.type)}</span>
                    {item.platform && (
                      <span className="text-xs bg-gray-700 px-2 py-1 rounded">
                        {getPlatformIcon(item.platform)} {item.platform}
                      </span>
                    )}
                  </div>
                  <p className="text-sm line-clamp-3">{item.content}</p>
                  <div className="flex items-center justify-between mt-2">
                    <div className="text-xs text-gray-500">
                      {new Date(item.generatedAt).toLocaleString('zh-CN')}
                    </div>
                    <div className="flex items-center gap-2">
                      {item.confidence && (
                        <span className={`text-xs ${getConfidenceColor(item.confidence)}`}>
                          {(item.confidence * 100).toFixed(0)}%
                        </span>
                      )}
                      {item.aiRecommend && (
                        <span title={item.aiRecommend}>
                          {getRecommendationIcon(item.aiRecommend)}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* 右侧详情 */}
          <div className="col-span-2 bg-gray-800 rounded-lg p-6">
            {selectedItem ? (
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-semibold">内容详情</h2>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleRegenerate(selectedItem)}
                      className="px-3 py-1 bg-gray-700 rounded hover:bg-gray-600 text-sm"
                    >
                      🔄 重新生成
                    </button>
                  </div>
                </div>

                {/* AI 推荐 */}
                {selectedItem.aiRecommend && (
                  <div className="mb-4 p-3 bg-blue-900/20 border border-blue-900/30 rounded">
                    <div className="flex items-center gap-2">
                      <span className="text-lg">{getRecommendationIcon(selectedItem.aiRecommend)}</span>
                      <span className="text-sm text-blue-400">
                        AI 建议：
                        {selectedItem.aiRecommend === 'approve' ? '通过' : 
                         selectedItem.aiRecommend === 'reject' ? '驳回' : '人工审核'}
                      </span>
                      {selectedItem.confidence && (
                        <span className={`text-xs ${getConfidenceColor(selectedItem.confidence)}`}>
                          (置信度：{(selectedItem.confidence * 100).toFixed(0)}%)
                        </span>
                      )}
                    </div>
                  </div>
                )}

                {/* 风险提示 */}
                {selectedItem.riskLevel && (
                  <div className={`mb-4 p-3 rounded ${getRiskColor(selectedItem.riskLevel)}`}>
                    <span className="text-sm">
                      风险等级：{selectedItem.riskLevel === 'low' ? '低' : 
                               selectedItem.riskLevel === 'medium' ? '中' : '高'}
                    </span>
                  </div>
                )}

                {/* 内容对比 */}
                {renderDiffView()}

                <div className="mb-4">
                  <label className="block text-sm text-gray-400 mb-2">类型</label>
                  <span className="bg-blue-600/20 text-blue-400 px-3 py-1 rounded-full text-sm">
                    {getTypeLabel(selectedItem.type)}
                  </span>
                </div>

                {selectedItem.originalContent && (
                  <div className="mb-4">
                    <label className="block text-sm text-gray-400 mb-2">原始输入</label>
                    <div className="bg-gray-900 rounded p-3 text-sm text-gray-300">
                      {selectedItem.originalContent}
                    </div>
                  </div>
                )}

                <div className="mb-4">
                  <label className="block text-sm text-gray-400 mb-2">AI 生成内容</label>
                  <textarea
                    value={editContent}
                    onChange={(e) => setEditContent(e.target.value)}
                    className="w-full h-48 bg-gray-900 rounded p-3 text-white resize-none focus:ring-2 focus:ring-blue-500 outline-none"
                  />
                </div>

                {selectedItem.metadata && (
                  <div className="mb-4">
                    <label className="block text-sm text-gray-400 mb-2">元数据</label>
                    <div className="bg-gray-900 rounded p-3 text-sm text-gray-300">
                      <pre>{JSON.stringify(selectedItem.metadata, null, 2)}</pre>
                    </div>
                  </div>
                )}

                <div className="flex gap-3">
                  <button
                    onClick={() => handleApprove(selectedItem)}
                    className="flex-1 py-3 bg-green-600 hover:bg-green-700 rounded-lg font-semibold transition-colors"
                  >
                    ✓ 通过并发布 (A)
                  </button>
                  <button
                    onClick={() => handleModify(selectedItem, editContent)}
                    className="flex-1 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-semibold transition-colors"
                  >
                    ✏️ 修改后发布 (M)
                  </button>
                  <button
                    onClick={() => {
                      const reason = prompt('请输入驳回原因:');
                      if (reason) handleReject(selectedItem, reason);
                    }}
                    className="flex-1 py-3 bg-red-600 hover:bg-red-700 rounded-lg font-semibold transition-colors"
                  >
                    ✗ 驳回 (R)
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

// 导出其他组件
export function AuditHistory() {
  // ... (保持原有实现)
  return <div>Audit History Component</div>;
}

export function AuditSettings() {
  // ... (保持原有实现)
  return <div>Audit Settings Component</div>;
}
