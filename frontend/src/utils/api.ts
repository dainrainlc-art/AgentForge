import axios from 'axios'

const API_BASE_URL = '/api'

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp?: string
}

export interface ChatRequest {
  message: string
  conversation_id?: string
  agent?: string
}

export interface ChatResponse {
  response: string
  conversation_id: string
  agent: string
  model: string
}

export interface Order {
  id: string
  buyer_username: string
  status: string
  price: number
  currency: string
  description: string
  created_at: string
  updated_at: string
}

export interface KnowledgeItem {
  id: string
  title: string
  content: string
  source: string
  tags: string[]
  created_at: string
}

export const authApi = {
  login: async (data: LoginRequest): Promise<LoginResponse> => {
    const formData = new FormData()
    formData.append('username', data.username)
    formData.append('password', data.password)
    const response = await api.post<LoginResponse>('/auth/login', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },

  verify: async (): Promise<{ valid: boolean }> => {
    const response = await api.get('/auth/verify')
    return response.data
  },
}

export const chatApi = {
  send: async (data: ChatRequest): Promise<ChatResponse> => {
    const response = await api.post<ChatResponse>('/chat', data)
    return response.data
  },

  stream: async (data: ChatRequest, onChunk: (chunk: string) => void): Promise<void> => {
    const token = localStorage.getItem('token')
    const response = await fetch(`${API_BASE_URL}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: token ? `Bearer ${token}` : '',
      },
      body: JSON.stringify(data),
    })

    const reader = response.body?.getReader()
    const decoder = new TextDecoder()

    if (reader) {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        const chunk = decoder.decode(value)
        onChunk(chunk)
      }
    }
  },
}

export const ordersApi = {
  list: async (status?: string): Promise<Order[]> => {
    const params = status ? { status } : {}
    const response = await api.get<Order[]>('/orders', { params })
    return response.data
  },

  get: async (id: string): Promise<Order> => {
    const response = await api.get<Order>(`/orders/${id}`)
    return response.data
  },
}

export const knowledgeApi = {
  list: async (): Promise<KnowledgeItem[]> => {
    const response = await api.get<KnowledgeItem[]>('/knowledge')
    return response.data
  },

  search: async (query: string): Promise<KnowledgeItem[]> => {
    const response = await api.get<KnowledgeItem[]>('/knowledge/search', {
      params: { query },
    })
    return response.data
  },
}

export const healthApi = {
  check: async (): Promise<{ status: string }> => {
    const response = await api.get('/health')
    return response.data
  },
}
