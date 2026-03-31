import { useState, useCallback } from 'react'
import { chatApi, ChatMessage, ChatResponse } from '../utils/api'

interface UseChatOptions {
  agent?: string
  onError?: (error: Error) => void
}

interface UseChatReturn {
  messages: ChatMessage[]
  loading: boolean
  conversationId: string | null
  sendMessage: (content: string) => Promise<void>
  clearMessages: () => void
}

export function useChat(options: UseChatOptions = {}): UseChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [loading, setLoading] = useState(false)
  const [conversationId, setConversationId] = useState<string | null>(null)

  const sendMessage = useCallback(
    async (content: string) => {
      const userMessage: ChatMessage = {
        role: 'user',
        content,
        timestamp: new Date().toISOString(),
      }

      setMessages((prev) => [...prev, userMessage])
      setLoading(true)

      try {
        const response: ChatResponse = await chatApi.send({
          message: content,
          conversation_id: conversationId || undefined,
          agent: options.agent,
        })

        const assistantMessage: ChatMessage = {
          role: 'assistant',
          content: response.response,
          timestamp: new Date().toISOString(),
        }

        setMessages((prev) => [...prev, assistantMessage])
        setConversationId(response.conversation_id)
      } catch (error) {
        options.onError?.(error as Error)
        setMessages((prev) => prev.slice(0, -1))
      } finally {
        setLoading(false)
      }
    },
    [conversationId, options.agent, options.onError]
  )

  const clearMessages = useCallback(() => {
    setMessages([])
    setConversationId(null)
  }, [])

  return {
    messages,
    loading,
    conversationId,
    sendMessage,
    clearMessages,
  }
}
