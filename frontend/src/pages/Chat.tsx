import { useState, useRef, useEffect } from 'react'
import { useChat } from '../hooks/useChat'
import { ChatMessage } from '../utils/api'
import { formatRelativeTime, copyToClipboard } from '../utils/helpers'

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`max-w-[80%] rounded-xl px-4 py-3 ${
          isUser
            ? 'bg-primary-600 text-white'
            : 'bg-dark-800 text-dark-100'
        }`}
      >
        {!isUser && (
          <div className="flex items-center gap-2 mb-2 text-xs text-dark-400">
            <span className="font-medium text-primary-400">AgentForge</span>
            <span>·</span>
            <span>{formatRelativeTime(message.timestamp || '')}</span>
          </div>
        )}
        
        <div className="prose prose-invert prose-sm max-w-none">
          <p className="whitespace-pre-wrap break-words">{message.content}</p>
        </div>

        {!isUser && (
          <div className="flex items-center gap-2 mt-2 pt-2 border-t border-dark-700">
            <button
              onClick={() => copyToClipboard(message.content)}
              className="text-xs text-dark-400 hover:text-dark-200 transition-colors"
            >
              复制
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

function AgentSelector({ 
  selected, 
  onChange 
}: { 
  selected: string
  onChange: (agent: string) => void 
}) {
  const agents = [
    { id: 'default', name: '默认助手', model: 'GLM-5' },
    { id: 'fiverr', name: 'Fiverr专家', model: 'GLM-5' },
    { id: 'social', name: '社交媒体', model: 'GLM-5' },
    { id: 'content', name: '内容创作', model: 'Kimi-K2.5' },
    { id: 'code', name: '代码助手', model: 'DeepSeek-V3.2' },
  ]

  return (
    <div className="flex items-center gap-2 mb-4">
      <span className="text-sm text-dark-400">当前Agent:</span>
      <select
        value={selected}
        onChange={(e) => onChange(e.target.value)}
        className="bg-dark-800 border border-dark-600 rounded-lg px-3 py-1.5 text-sm text-dark-100 focus:outline-none focus:border-primary-500"
      >
        {agents.map((agent) => (
          <option key={agent.id} value={agent.id}>
            {agent.name} ({agent.model})
          </option>
        ))}
      </select>
    </div>
  )
}

export default function Chat() {
  const [agent, setAgent] = useState('default')
  const { messages, loading, sendMessage, clearMessages } = useChat({
    agent,
    onError: (error) => {
      console.error('Chat error:', error)
    },
  })
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || loading) return

    const message = input.trim()
    setInput('')
    await sendMessage(message)
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-xl font-semibold text-dark-100">智能对话</h1>
          <p className="text-sm text-dark-400">与AI助手进行对话</p>
        </div>
        <button
          onClick={clearMessages}
          className="btn btn-ghost text-sm"
        >
          清空对话
        </button>
      </div>

      <AgentSelector selected={agent} onChange={setAgent} />

      <div className="flex-1 overflow-auto rounded-xl bg-dark-900 border border-dark-700 p-4">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-dark-400">
            <svg className="w-16 h-16 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            <p className="text-lg font-medium">开始对话</p>
            <p className="text-sm mt-1">输入消息开始与AI助手对话</p>
          </div>
        ) : (
          <>
            {messages.map((message, index) => (
              <MessageBubble key={index} message={message} />
            ))}
            {loading && (
              <div className="flex justify-start mb-4">
                <div className="bg-dark-800 rounded-xl px-4 py-3">
                  <div className="flex items-center gap-2">
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                      <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                      <div className="w-2 h-2 bg-primary-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                    </div>
                    <span className="text-sm text-dark-400">正在思考...</span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      <form onSubmit={handleSubmit} className="mt-4">
        <div className="flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="输入消息..."
            className="input flex-1"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="btn btn-primary px-6"
          >
            发送
          </button>
        </div>
      </form>
    </div>
  )
}
