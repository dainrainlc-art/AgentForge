import { Routes, Route, Navigate } from 'react-router-dom'
import { Suspense, lazy } from 'react'
import Layout from './components/Layout'
import Login from './pages/Login'
import { AuthProvider, useAuth } from './hooks/useAuth'

const Chat = lazy(() => import('./pages/Chat'))
const Orders = lazy(() => import('./pages/Orders'))
const Knowledge = lazy(() => import('./pages/Knowledge'))
const Settings = lazy(() => import('./pages/Settings'))

function LoadingSpinner() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-dark-950">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
    </div>
  )
}

function PageLoader() {
  return (
    <div className="flex-1 flex items-center justify-center">
      <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary-500"></div>
    </div>
  )
}

function AppRoutes() {
  const { isAuthenticated, loading } = useAuth()

  if (loading) {
    return <LoadingSpinner />
  }

  if (!isAuthenticated) {
    return (
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    )
  }

  return (
    <Routes>
      <Route path="/login" element={<Navigate to="/" replace />} />
      <Route path="/" element={<Layout />}>
        <Route index element={
          <Suspense fallback={<PageLoader />}>
            <Chat />
          </Suspense>
        } />
        <Route path="chat" element={
          <Suspense fallback={<PageLoader />}>
            <Chat />
          </Suspense>
        } />
        <Route path="orders" element={
          <Suspense fallback={<PageLoader />}>
            <Orders />
          </Suspense>
        } />
        <Route path="knowledge" element={
          <Suspense fallback={<PageLoader />}>
            <Knowledge />
          </Suspense>
        } />
        <Route path="settings" element={
          <Suspense fallback={<PageLoader />}>
            <Settings />
          </Suspense>
        } />
      </Route>
    </Routes>
  )
}

function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  )
}

export default App
