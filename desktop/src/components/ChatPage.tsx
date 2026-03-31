import React, { useState, useRef, useEffect, useCallback } from 'react';
import TauriAPI from '../utils/tauri';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
}

export interface Agent {
  id: string;
  name: string;
  description: string;
  icon: string;
}

const AGENTS: Agent[] = [
  {
    id: 'fiverr-assistant',
    name: 'Fiverr 助手',
    description: '帮助您管理 Fiverr 订单和客户沟通',
    icon: '🛒',
  },
  {
    id: 'social-media',
    name: '社交媒体专家',
    description: '生成社交媒体内容和营销策略',
    icon: '📱',
  },
  {
    id: 'content-writer',
    name: '内容创作者',
    description: '撰写高质量文章和营销文案',
    icon: '✍️',
  },
  {
    id: 'code-assistant',
    name: '代码助手',
    description: '帮助您解决编程问题',
    icon: '💻',
  },
  {
    id: 'general',
    name: '通用助手',
    description: '多功能 AI 助手',
    icon: '🤖',
  },
];

const ChatPage: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<string>('general');
  const [isStreaming, setIsStreaming] = useState(false);
  const [showAgentSelector, setShowAgentSelector] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    if (autoScroll && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [autoScroll]);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const handleScroll = () => {
    if (chatContainerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = chatContainerRef.current;
      const isNearBottom = scrollHeight - scrollTop - clientHeight < 100;
      setAutoScroll(isNearBottom);
    }
  };

  const generateId = () => {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  };

  const sendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: generateId(),
      role: 'user',
      content: inputValue.trim(),
      timestamp: Date.now(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);
    setIsStreaming(true);

    const assistantMessage: Message = {
      id: generateId(),
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
    };

    setMessages((prev) => [...prev, assistantMessage]);

    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage.content,
          agent_id: selectedAgent,
          stream: true,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('No reader available');
      }

      let accumulatedContent = '';

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') {
              break;
            }
            try {
              const parsed = JSON.parse(data);
              if (parsed.content) {
                accumulatedContent += parsed.content;
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMessage.id
                      ? { ...msg, content: accumulatedContent }
                      : msg
                  )
                );
              }
            } catch {
              // 忽略解析错误
            }
          }
        }
      }
    } catch (error) {
      console.error('发送消息失败:', error);
      
      const errorMessage = error instanceof Error ? error.message : '发送消息失败，请检查后端服务是否运行';
      
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessage.id
            ? { ...msg, content: `❌ 错误：${errorMessage}`, timestamp: Date.now() }
            : msg
        )
      );

      if (TauriAPI.isTauri()) {
        await TauriAPI.showNotification('发送失败', errorMessage);
      }
    } finally {
      setIsLoading(false);
      setIsStreaming(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = () => {
    setMessages([]);
    if (TauriAPI.isTauri()) {
      TauriAPI.showNotification('对话已清空', '开始新的对话');
    }
  };

  const copyMessage = async (content: string) => {
    try {
      await TauriAPI.setClipboard(content);
      if (TauriAPI.isTauri()) {
        TauriAPI.showNotification('已复制', '消息已复制到剪贴板');
      }
    } catch (error) {
      console.error('复制失败:', error);
    }
  };

  const formatTime = (timestamp: number) => {
    return new Date(timestamp).toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getAgentById = (id: string) => {
    return AGENTS.find((a) => a.id === id) || AGENTS[4];
  };

  return (
    <div className="flex flex-col h-full bg-gray-900">
      {/* 顶部栏 */}
      <div className="flex items-center justify-between px-4 py-3 bg-gray-800 border-b border-gray-700">
        <div className="flex items-center gap-3">
          <div className="relative">
            <button
              onClick={() => setShowAgentSelector(!showAgentSelector)}
              className="flex items-center gap-2 px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
            >
              <span className="text-xl">{getAgentById(selectedAgent).icon}</span>
              <span className="text-white font-medium">
                {getAgentById(selectedAgent).name}
              </span>
              <svg
                className={`w-4 h-4 text-gray-400 transition-transform ${
                  showAgentSelector ? 'rotate-180' : ''
                }`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 9l-7 7-7-7"
                />
              </svg>
            </button>

            {showAgentSelector && (
              <div className="absolute top-full left-0 mt-2 w-72 bg-gray-800 border border-gray-700 rounded-lg shadow-xl z-50">
                <div className="p-2">
                  {AGENTS.map((agent) => (
                    <button
                      key={agent.id}
                      onClick={() => {
                        setSelectedAgent(agent.id);
                        setShowAgentSelector(false);
                      }}
                      className={`w-full flex items-start gap-3 p-3 rounded-lg transition-colors ${
                        selectedAgent === agent.id
                          ? 'bg-blue-600'
                          : 'hover:bg-gray-700'
                      }`}
                    >
                      <span className="text-2xl">{agent.icon}</span>
                      <div className="flex-1 text-left">
                        <div className="text-white font-medium">{agent.name}</div>
                        <div className="text-gray-400 text-sm">
                          {agent.description}
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={clearChat}
            className="flex items-center gap-2 px-3 py-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
            title="清空对话"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
              />
            </svg>
            <span className="text-sm">清空对话</span>
          </button>
        </div>
      </div>

      {/* 消息列表 */}
      <div
        ref={chatContainerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto px-4 py-6"
      >
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="text-6xl mb-4">{getAgentById(selectedAgent).icon}</div>
            <h2 className="text-2xl font-bold text-white mb-2">
              {getAgentById(selectedAgent).name}
            </h2>
            <p className="text-gray-400 max-w-md mb-8">
              {getAgentById(selectedAgent).description}
            </p>
            <div className="grid grid-cols-2 gap-4 max-w-2xl">
              <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
                <div className="text-gray-300 text-sm">💡 提示</div>
                <div className="text-gray-500 text-xs mt-1">
                  按 Enter 发送消息，Shift+Enter 换行
                </div>
              </div>
              <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
                <div className="text-gray-300 text-sm">📋 复制</div>
                <div className="text-gray-500 text-xs mt-1">
                  点击消息右上角的复制按钮
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="max-w-3xl mx-auto space-y-6">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${
                  message.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                <div
                  className={`group relative max-w-[80%] ${
                    message.role === 'user' ? 'order-1' : 'order-2'
                  }`}
                >
                  <div
                    className={`px-4 py-3 rounded-2xl ${
                      message.role === 'user'
                        ? 'bg-blue-600 text-white rounded-br-md'
                        : 'bg-gray-800 text-gray-100 rounded-bl-md border border-gray-700'
                    }`}
                  >
                    {message.role === 'assistant' && (
                      <div className="flex items-center gap-2 mb-2 text-xs text-gray-400">
                        <span className="text-lg">
                          {getAgentById(selectedAgent).icon}
                        </span>
                        <span>{getAgentById(selectedAgent).name}</span>
                      </div>
                    )}
                    <div className="whitespace-pre-wrap break-words">
                      {message.content}
                      {message.role === 'assistant' && isStreaming && 
                       messages[messages.length - 1].id === message.id && (
                        <span className="inline-block w-2 h-4 ml-1 bg-blue-500 animate-pulse" />
                      )}
                    </div>
                  </div>
                  <div
                    className={`flex items-center gap-2 mt-1 text-xs text-gray-500 ${
                      message.role === 'user' ? 'justify-end' : 'justify-start'
                    }`}
                  >
                    <span>{formatTime(message.timestamp)}</span>
                    {message.role === 'assistant' && (
                      <button
                        onClick={() => copyMessage(message.content)}
                        className="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-gray-700 rounded"
                        title="复制消息"
                      >
                        <svg
                          className="w-4 h-4"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                          />
                        </svg>
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* 输入区域 */}
      <div className="border-t border-gray-700 bg-gray-800 px-4 py-4">
        <div className="max-w-3xl mx-auto">
          <div className="flex items-end gap-3">
            <div className="flex-1 bg-gray-700 rounded-xl border border-gray-600 focus-within:border-blue-500 transition-colors">
              <textarea
                ref={inputRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="输入消息..."
                rows={1}
                className="w-full bg-transparent text-white px-4 py-3 resize-none focus:outline-none max-h-32 min-h-[48px]"
                style={{
                  height: 'auto',
                  minHeight: '48px',
                }}
                onInput={(e) => {
                  const target = e.target as HTMLTextAreaElement;
                  target.style.height = 'auto';
                  target.style.height = `${Math.min(target.scrollHeight, 128)}px`;
                }}
              />
            </div>
            <button
              onClick={sendMessage}
              disabled={!inputValue.trim() || isLoading}
              className={`flex items-center justify-center w-12 h-12 rounded-xl transition-all ${
                !inputValue.trim() || isLoading
                  ? 'bg-gray-600 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700 active:scale-95'
              }`}
            >
              {isLoading ? (
                <svg
                  className="animate-spin w-5 h-5 text-white"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
              ) : (
                <svg
                  className="w-5 h-5 text-white"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                  />
                </svg>
              )}
            </button>
          </div>
          <div className="flex items-center justify-between mt-2 text-xs text-gray-500">
            <div className="flex items-center gap-3">
              <span>Enter 发送，Shift+Enter 换行</span>
              {isStreaming && (
                <span className="flex items-center gap-1 text-blue-400">
                  <span className="w-2 h-2 bg-blue-400 rounded-full animate-pulse" />
                  正在生成...
                </span>
              )}
            </div>
            <div className="flex items-center gap-2">
              <span>AI 生成内容可能不准确</span>
            </div>
          </div>
        </div>
      </div>

      {/* 点击外部关闭 Agent 选择器 */}
      {showAgentSelector && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setShowAgentSelector(false)}
        />
      )}
    </div>
  );
};

export default ChatPage;
