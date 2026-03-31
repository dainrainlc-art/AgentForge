import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { authApi } from '../utils/api'

interface AuthContextType {
  isAuthenticated: boolean
  loading: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const verifyAuth = async () => {
      const token = localStorage.getItem('token')
      if (token) {
        try {
          await authApi.verify()
          setIsAuthenticated(true)
        } catch {
          localStorage.removeItem('token')
          setIsAuthenticated(false)
        }
      }
      setLoading(false)
    }
    verifyAuth()
  }, [])

  const login = async (username: string, password: string) => {
    const response = await authApi.login({ username, password })
    localStorage.setItem('token', response.access_token)
    setIsAuthenticated(true)
  }

  const logout = () => {
    localStorage.removeItem('token')
    setIsAuthenticated(false)
  }

  return (
    <AuthContext.Provider value={{ isAuthenticated, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
