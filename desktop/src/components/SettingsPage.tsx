import React, { useEffect, useState } from 'react';
import TauriAPI from '../utils/tauri';

interface ConfigField {
  key: string;
  label: string;
  type: string;
  value: any;
  description?: string;
  placeholder?: string;
  required?: boolean;
  sensitive?: boolean;
  options?: Array<{ value: string; label: string }>;
  min_value?: number;
  max_value?: number;
}

interface ConfigGroup {
  id: string;
  title: string;
  icon: string;
  description: string;
  fields: ConfigField[];
}

interface ConfigResponse {
  groups: ConfigGroup[];
  last_updated?: string;
}

interface ConfigTestResult {
  service: string;
  status: string;
  message: string;
  details?: Record<string, any>;
}

interface ConfigSaveResponse {
  success: boolean;
  message: string;
  requires_restart: boolean;
}

interface NotificationProps {
  type: 'success' | 'error' | 'info' | 'warning';
  message: string;
  onClose: () => void;
}

const Notification: React.FC<NotificationProps> = ({ type, message, onClose }) => {
  useEffect(() => {
    const timer = setTimeout(onClose, 5000);
    return () => clearTimeout(timer);
  }, [onClose]);

  const bgColors = {
    success: 'bg-green-600',
    error: 'bg-red-600',
    info: 'bg-blue-600',
    warning: 'bg-yellow-600',
  };

  const icons = {
    success: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
      </svg>
    ),
    error: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
      </svg>
    ),
    info: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    warning: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
    ),
  };

  return (
    <div className={`fixed top-4 right-4 ${bgColors[type]} text-white px-4 py-3 rounded-lg shadow-lg flex items-center gap-3 z-50 animate-slide-in`}>
      {icons[type]}
      <span className="text-sm font-medium">{message}</span>
      <button onClick={onClose} className="ml-2 hover:opacity-75">
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  );
};

interface TestResultDisplayProps {
  result: ConfigTestResult | null;
  onClose: () => void;
}

const TestResultDisplay: React.FC<TestResultDisplayProps> = ({ result, onClose }) => {
  if (!result) return null;

  const statusColors = {
    success: 'text-green-600 bg-green-50 border-green-200',
    error: 'text-red-600 bg-red-50 border-red-200',
    warning: 'text-yellow-600 bg-yellow-50 border-yellow-200',
  };

  const statusText = {
    success: '成功',
    error: '失败',
    warning: '警告',
  };

  return (
    <div className={`fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50`}>
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4 shadow-2xl">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">测试结果</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <div className={`p-4 rounded-lg border-2 ${statusColors[result.status as keyof typeof statusColors]}`}>
          <div className="flex items-center gap-2 mb-2">
            <span className="font-semibold">{result.service}</span>
            <span className="text-sm">({statusText[result.status as keyof typeof statusText]})</span>
          </div>
          <p className="text-sm">{result.message}</p>
          {result.details && (
            <div className="mt-2 text-xs opacity-75">
              {Object.entries(result.details).map(([key, value]) => (
                <div key={key}>
                  <strong>{key}:</strong> {String(value)}
                </div>
              ))}
            </div>
          )}
        </div>
        
        <div className="mt-4 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded transition-colors"
          >
            关闭
          </button>
        </div>
      </div>
    </div>
  );
};

const SettingsPage: React.FC = () => {
  const [config, setConfig] = useState<ConfigResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<string | null>(null);
  const [testing, setTesting] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>('ai_model');
  const [notification, setNotification] = useState<{ type: 'success' | 'error' | 'info' | 'warning'; message: string } | null>(null);
  const [testResult, setTestResult] = useState<ConfigTestResult | null>(null);
  const [modifiedValues, setModifiedValues] = useState<Record<string, any>>({});
  const [isDesktop, setIsDesktop] = useState(false);

  useEffect(() => {
    setIsDesktop(TauriAPI.isTauri());
  }, []);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('jwt_token') || 'your-secret-key-change-in-production';
      
      const response = await fetch('http://localhost:8000/api/config', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        if (response.status === 401) {
          setNotification({ type: 'error', message: '认证失败，请检查 JWT 密钥' });
        } else {
          setNotification({ type: 'error', message: '加载配置失败' });
        }
        return;
      }

      const data: ConfigResponse = await response.json();
      setConfig(data);
    } catch (error) {
      setNotification({ type: 'error', message: '无法连接到后端服务' });
    } finally {
      setLoading(false);
    }
  };

  const handleFieldChange = (key: string, value: any) => {
    setModifiedValues(prev => ({ ...prev, [key]: value }));
  };

  const handleSave = async (key: string, value: any) => {
    try {
      setSaving(key);
      const token = localStorage.getItem('jwt_token') || 'your-secret-key-change-in-production';
      
      const response = await fetch('http://localhost:8000/api/config/save', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ key, value }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || '保存失败');
      }

      const result: ConfigSaveResponse = await response.json();
      
      if (result.success) {
        setNotification({ 
          type: result.requires_restart ? 'warning' : 'success', 
          message: result.message 
        });
        
        if (!result.requires_restart) {
          setModifiedValues(prev => {
            const newValues = { ...prev };
            delete newValues[key];
            return newValues;
          });
          loadConfig();
        }
      }
    } catch (error: any) {
      setNotification({ type: 'error', message: error.message || '保存失败' });
    } finally {
      setSaving(null);
    }
  };

  const handleTest = async (key: string, value: any) => {
    try {
      setTesting(key);
      const token = localStorage.getItem('jwt_token') || 'your-secret-key-change-in-production';
      
      const response = await fetch('http://localhost:8000/api/config/test', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ key, value }),
      });

      if (!response.ok) {
        throw new Error('测试失败');
      }

      const result: ConfigTestResult = await response.json();
      setTestResult(result);
    } catch (error: any) {
      setNotification({ type: 'error', message: error.message || '测试失败' });
    } finally {
      setTesting(null);
    }
  };

  const renderField = (field: ConfigField) => {
    const currentValue = modifiedValues[field.key] !== undefined 
      ? modifiedValues[field.key] 
      : field.value;

    const isModified = modifiedValues[field.key] !== undefined;
    const isSaving = saving === field.key;
    const isTesting = testing === field.key;

    const inputClasses = `w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors ${
      isModified ? 'border-yellow-400 bg-yellow-50' : 'border-gray-300 bg-white'
    }`;

    const renderInput = () => {
      switch (field.type) {
        case 'password':
          return (
            <input
              type="password"
              value={currentValue || ''}
              onChange={(e) => handleFieldChange(field.key, e.target.value)}
              placeholder={field.placeholder}
              className={inputClasses}
              disabled={isSaving}
            />
          );

        case 'number':
          return (
            <input
              type="number"
              value={currentValue || ''}
              onChange={(e) => handleFieldChange(field.key, parseFloat(e.target.value))}
              placeholder={field.placeholder}
              min={field.min_value}
              max={field.max_value}
              className={inputClasses}
              disabled={isSaving}
            />
          );

        case 'select':
          return (
            <select
              value={currentValue || ''}
              onChange={(e) => handleFieldChange(field.key, e.target.value)}
              className={inputClasses}
              disabled={isSaving}
            >
              {field.options?.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          );

        case 'boolean':
          return (
            <label className="flex items-center cursor-pointer">
              <div className="relative">
                <input
                  type="checkbox"
                  checked={currentValue || false}
                  onChange={(e) => handleFieldChange(field.key, e.target.checked)}
                  className="sr-only"
                  disabled={isSaving}
                />
                <div className={`block w-14 h-8 rounded-full transition-colors ${
                  currentValue ? 'bg-blue-600' : 'bg-gray-300'
                }`}></div>
                <div className={`absolute left-1 top-1 bg-white w-6 h-6 rounded-full transition-transform ${
                  currentValue ? 'transform translate-x-6' : ''
                }`}></div>
              </div>
            </label>
          );

        case 'text':
        default:
          return (
            <input
              type="text"
              value={currentValue || ''}
              onChange={(e) => handleFieldChange(field.key, e.target.value)}
              placeholder={field.placeholder}
              className={inputClasses}
              disabled={isSaving}
            />
          );
      }
    };

    return (
      <div key={field.key} className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <label className="block text-sm font-medium text-gray-700">
            {field.label}
            {field.required && <span className="text-red-500 ml-1">*</span>}
            {isModified && <span className="text-yellow-600 ml-2 text-xs">(已修改)</span>}
          </label>
          
          <div className="flex items-center gap-2">
            {['qianfan_api_key', 'postgres_host', 'redis_host', 'qdrant_host', 'n8n_host'].includes(field.key) && (
              <button
                onClick={() => handleTest(field.key, currentValue)}
                disabled={isTesting || isSaving}
                className="px-3 py-1 text-xs bg-purple-100 hover:bg-purple-200 text-purple-700 rounded transition-colors disabled:opacity-50"
              >
                {isTesting ? '测试中...' : '测试连接'}
              </button>
            )}
            
            {isModified && (
              <button
                onClick={() => handleSave(field.key, currentValue)}
                disabled={isSaving}
                className="px-3 py-1 text-xs bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors disabled:opacity-50"
              >
                {isSaving ? '保存中...' : '保存'}
              </button>
            )}
          </div>
        </div>
        
        {renderInput()}
        
        {field.description && (
          <p className="mt-1 text-xs text-gray-500">{field.description}</p>
        )}
        
        {field.sensitive && (
          <p className="mt-1 text-xs text-red-500 flex items-center gap-1">
            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
            </svg>
            敏感信息，请妥善保管
          </p>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">加载配置中...</p>
        </div>
      </div>
    );
  }

  if (!config) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <svg className="w-16 h-16 text-red-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-gray-600 mb-4">无法加载配置</p>
          <button
            onClick={loadConfig}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
          >
            重新加载
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {notification && (
        <Notification
          type={notification.type}
          message={notification.message}
          onClose={() => setNotification(null)}
        />
      )}

      {testResult && (
        <TestResultDisplay
          result={testResult}
          onClose={() => setTestResult(null)}
        />
      )}

      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">系统配置</h1>
            <p className="text-sm text-gray-500 mt-1">管理和配置系统各项参数</p>
          </div>
          
          <div className="flex items-center gap-4">
            <button
              onClick={loadConfig}
              className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900 transition-colors"
            >
              <svg className="w-5 h-5 inline-block mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              刷新
            </button>
            
            {isDesktop && (
              <button
                onClick={() => TauriAPI.showNotification('配置管理', '配置已同步到桌面端')}
                className="px-4 py-2 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded transition-colors"
              >
                桌面通知测试
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        <div className="w-64 bg-white border-r border-gray-200 overflow-y-auto">
          <nav className="p-4 space-y-1">
            {config.groups.map((group) => (
              <button
                key={group.id}
                onClick={() => setActiveTab(group.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors ${
                  activeTab === group.id
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-gray-700 hover:bg-gray-50'
                }`}
              >
                <span className="text-xl">{group.icon}</span>
                <span>{group.title}</span>
              </button>
            ))}
          </nav>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {config.groups.map((group) => (
            activeTab === group.id && (
              <div key={group.id} className="max-w-4xl">
                <div className="mb-6">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-3xl">{group.icon}</span>
                    <h2 className="text-xl font-semibold text-gray-900">{group.title}</h2>
                  </div>
                  <p className="text-sm text-gray-600 ml-12">{group.description}</p>
                </div>

                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                  {group.fields.map(renderField)}
                </div>

                <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="flex items-start gap-3">
                    <svg className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <div className="text-sm text-blue-800">
                      <p className="font-medium mb-1">配置说明</p>
                      <ul className="list-disc list-inside space-y-1 text-blue-700">
                        <li>修改配置后请点击"保存"按钮</li>
                        <li>部分配置需要重启服务后生效</li>
                        <li>敏感信息（如 API 密钥）会加密存储</li>
                        <li>可以使用"测试连接"功能验证配置是否正确</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            )
          ))}
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
