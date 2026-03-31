import React, { useState, useEffect } from 'react';
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
}

interface AuditStats {
  pending: number;
  approved: number;
  rejected: number;
  todayTotal: number;
}

export function AuditQueue() {
  const { user } = useAuth();
  const [items, setItems] = useState<AuditItem[]>([]);
  const [stats, setStats] = useState<AuditStats>({ pending: 0, approved: 0, rejected: 0, todayTotal: 0 });
  const [selectedItem, setSelectedItem] = useState<AuditItem | null>(null);
  const [editContent, setEditContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'pending' | 'approved' | 'rejected'>('pending');

  useEffect(() => {
    fetchAuditItems();
  }, [filter]);

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

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">AI内容审核中心</h1>
          <p className="text-gray-400">审核AI生成的内容，确保品牌形象一致性</p>
        </div>

        <div className="grid grid-cols-4 gap-4 mb-8">
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
        </div>

        <div className="flex gap-2 mb-6">
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

        <div className="grid grid-cols-3 gap-6">
          <div className="col-span-1 space-y-4 max-h-[calc(100vh-300px)] overflow-y-auto">
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
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-gray-400">{getTypeLabel(item.type)}</span>
                    {item.platform && (
                      <span className="text-xs bg-gray-700 px-2 py-1 rounded">
                        {getPlatformIcon(item.platform)} {item.platform}
                      </span>
                    )}
                  </div>
                  <p className="text-sm line-clamp-3">{item.content}</p>
                  <div className="text-xs text-gray-500 mt-2">
                    {new Date(item.generatedAt).toLocaleString('zh-CN')}
                  </div>
                </div>
              ))
            )}
          </div>

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
                  <label className="block text-sm text-gray-400 mb-2">AI生成内容</label>
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
                    ✓ 通过并发布
                  </button>
                  <button
                    onClick={() => handleModify(selectedItem, editContent)}
                    className="flex-1 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-semibold transition-colors"
                  >
                    ✏️ 修改后发布
                  </button>
                  <button
                    onClick={() => {
                      const reason = prompt('请输入驳回原因:');
                      if (reason) handleReject(selectedItem, reason);
                    }}
                    className="flex-1 py-3 bg-red-600 hover:bg-red-700 rounded-lg font-semibold transition-colors"
                  >
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

export function AuditHistory() {
  const [history, setHistory] = useState<AuditItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const response = await fetch('/api/audit/history', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      const data = await response.json();
      setHistory(data.items || []);
    } catch (error) {
      console.error('Failed to fetch history:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <h2 className="text-xl font-semibold mb-4">审核历史</h2>
      {loading ? (
        <div className="text-center py-4 text-gray-400">加载中...</div>
      ) : (
        <div className="space-y-3">
          {history.map((item) => (
            <div key={item.id} className="bg-gray-900 rounded p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-400">{item.type}</span>
                <span
                  className={`text-xs px-2 py-1 rounded ${
                    item.status === 'approved'
                      ? 'bg-green-600/20 text-green-400'
                      : item.status === 'rejected'
                      ? 'bg-red-600/20 text-red-400'
                      : 'bg-blue-600/20 text-blue-400'
                  }`}
                >
                  {item.status === 'approved' ? '已通过' : item.status === 'rejected' ? '已驳回' : '已修改'}
                </span>
              </div>
              <p className="text-sm text-gray-300 line-clamp-2">{item.content}</p>
              <div className="text-xs text-gray-500 mt-2">
                {new Date(item.generatedAt).toLocaleString('zh-CN')}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function AuditSettings() {
  const [settings, setSettings] = useState({
    autoApproveThreshold: 0.9,
    enableAutoApprove: false,
    notifyChannels: ['telegram', 'email'],
    reviewTimeout: 24
  });

  const handleSave = async () => {
    try {
      await fetch('/api/audit/settings', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(settings)
      });
      alert('设置已保存');
    } catch (error) {
      console.error('Failed to save settings:', error);
    }
  };

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <h2 className="text-xl font-semibold mb-4">审核设置</h2>
      
      <div className="space-y-4">
        <div>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={settings.enableAutoApprove}
              onChange={(e) => setSettings({ ...settings, enableAutoApprove: e.target.checked })}
              className="rounded"
            />
            <span>启用自动审核（置信度高于阈值时自动通过）</span>
          </label>
        </div>

        <div>
          <label className="block text-sm text-gray-400 mb-2">
            自动通过置信度阈值: {settings.autoApproveThreshold}
          </label>
          <input
            type="range"
            min="0.5"
            max="1"
            step="0.05"
            value={settings.autoApproveThreshold}
            onChange={(e) => setSettings({ ...settings, autoApproveThreshold: parseFloat(e.target.value) })}
            className="w-full"
          />
        </div>

        <div>
          <label className="block text-sm text-gray-400 mb-2">通知渠道</label>
          <div className="space-y-2">
            {['telegram', 'email', 'desktop'].map((channel) => (
              <label key={channel} className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={settings.notifyChannels.includes(channel)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSettings({ ...settings, notifyChannels: [...settings.notifyChannels, channel] });
                    } else {
                      setSettings({
                        ...settings,
                        notifyChannels: settings.notifyChannels.filter((c) => c !== channel)
                      });
                    }
                  }}
                  className="rounded"
                />
                <span className="capitalize">{channel}</span>
              </label>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm text-gray-400 mb-2">审核超时（小时）</label>
          <input
            type="number"
            value={settings.reviewTimeout}
            onChange={(e) => setSettings({ ...settings, reviewTimeout: parseInt(e.target.value) })}
            className="w-full bg-gray-900 rounded p-2"
          />
        </div>

        <button
          onClick={handleSave}
          className="w-full py-2 bg-blue-600 hover:bg-blue-700 rounded-lg font-semibold"
        >
          保存设置
        </button>
      </div>
    </div>
  );
}
