import { useState, useEffect } from 'react'
import { formatDate, formatCurrency } from '../utils/helpers'

interface Order {
  id: string
  buyer_username: string
  status: string
  price: number
  currency: string
  description: string
  created_at: string
  updated_at: string
}

const statusColors: Record<string, string> = {
  active: 'bg-green-500/10 text-green-400 border-green-500/50',
  pending: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/50',
  completed: 'bg-blue-500/10 text-blue-400 border-blue-500/50',
  cancelled: 'bg-red-500/10 text-red-400 border-red-500/50',
  delivered: 'bg-purple-500/10 text-purple-400 border-purple-500/50',
}

const statusLabels: Record<string, string> = {
  active: '进行中',
  pending: '待处理',
  completed: '已完成',
  cancelled: '已取消',
  delivered: '已交付',
}

function OrderCard({ order }: { order: Order }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="card hover:border-dark-600 transition-colors">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <span className="font-mono text-sm text-dark-400">#{order.id}</span>
            <span
              className={`px-2 py-0.5 text-xs font-medium rounded border ${
                statusColors[order.status] || 'bg-dark-500/10 text-dark-300 border-dark-500/50'
              }`}
            >
              {statusLabels[order.status] || order.status}
            </span>
          </div>
          <h3 className="font-medium text-dark-100 mb-1">
            {order.buyer_username}
          </h3>
          <p className="text-sm text-dark-400 line-clamp-2">
            {order.description}
          </p>
        </div>
        <div className="text-right ml-4">
          <p className="text-lg font-semibold text-dark-100">
            {formatCurrency(order.price, order.currency)}
          </p>
          <p className="text-xs text-dark-500 mt-1">
            {formatDate(order.created_at)}
          </p>
        </div>
      </div>

      {expanded && (
        <div className="mt-4 pt-4 border-t border-dark-700">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-dark-400">买家:</span>
              <span className="ml-2 text-dark-200">{order.buyer_username}</span>
            </div>
            <div>
              <span className="text-dark-400">更新时间:</span>
              <span className="ml-2 text-dark-200">{formatDate(order.updated_at)}</span>
            </div>
          </div>
          <div className="mt-3 flex gap-2">
            <button className="btn btn-secondary text-sm">查看详情</button>
            <button className="btn btn-ghost text-sm">发送消息</button>
          </div>
        </div>
      )}

      <button
        onClick={() => setExpanded(!expanded)}
        className="mt-3 text-sm text-primary-400 hover:text-primary-300 transition-colors"
      >
        {expanded ? '收起' : '展开详情'}
      </button>
    </div>
  )
}

export default function Orders() {
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<string>('')
  const [search, setSearch] = useState('')

  useEffect(() => {
    const mockOrders: Order[] = [
      {
        id: 'ORD-001',
        buyer_username: 'john_designer',
        status: 'active',
        price: 150,
        currency: 'USD',
        description: 'Logo设计项目 - 需要为一家科技公司设计现代风格的logo',
        created_at: '2024-01-15T10:30:00Z',
        updated_at: '2024-01-16T14:20:00Z',
      },
      {
        id: 'ORD-002',
        buyer_username: 'sarah_marketing',
        status: 'pending',
        price: 280,
        currency: 'USD',
        description: '社交媒体营销方案 - 包含内容策划和发布排期',
        created_at: '2024-01-14T09:00:00Z',
        updated_at: '2024-01-14T09:00:00Z',
      },
      {
        id: 'ORD-003',
        buyer_username: 'mike_developer',
        status: 'completed',
        price: 500,
        currency: 'USD',
        description: '网站开发项目 - 响应式企业官网开发',
        created_at: '2024-01-10T08:00:00Z',
        updated_at: '2024-01-13T16:30:00Z',
      },
      {
        id: 'ORD-004',
        buyer_username: 'emma_writer',
        status: 'delivered',
        price: 75,
        currency: 'USD',
        description: '博客文章撰写 - 5篇关于AI技术的深度文章',
        created_at: '2024-01-12T11:00:00Z',
        updated_at: '2024-01-15T09:00:00Z',
      },
    ]

    setTimeout(() => {
      setOrders(mockOrders)
      setLoading(false)
    }, 500)
  }, [])

  const filteredOrders = orders.filter((order) => {
    const matchesFilter = !filter || order.status === filter
    const matchesSearch =
      !search ||
      order.buyer_username.toLowerCase().includes(search.toLowerCase()) ||
      order.description.toLowerCase().includes(search.toLowerCase())
    return matchesFilter && matchesSearch
  })

  const stats = {
    total: orders.length,
    active: orders.filter((o) => o.status === 'active').length,
    pending: orders.filter((o) => o.status === 'pending').length,
    revenue: orders.reduce((sum, o) => sum + o.price, 0),
  }

  return (
    <div className="h-full flex flex-col">
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-dark-100">订单管理</h1>
        <p className="text-sm text-dark-400">管理Fiverr订单和客户沟通</p>
      </div>

      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="card">
          <p className="text-sm text-dark-400">总订单</p>
          <p className="text-2xl font-semibold text-dark-100 mt-1">{stats.total}</p>
        </div>
        <div className="card">
          <p className="text-sm text-dark-400">进行中</p>
          <p className="text-2xl font-semibold text-green-400 mt-1">{stats.active}</p>
        </div>
        <div className="card">
          <p className="text-sm text-dark-400">待处理</p>
          <p className="text-2xl font-semibold text-yellow-400 mt-1">{stats.pending}</p>
        </div>
        <div className="card">
          <p className="text-sm text-dark-400">总收入</p>
          <p className="text-2xl font-semibold text-primary-400 mt-1">
            {formatCurrency(stats.revenue)}
          </p>
        </div>
      </div>

      <div className="flex items-center gap-4 mb-4">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="搜索订单..."
          className="input max-w-xs"
        />
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-dark-100 focus:outline-none focus:border-primary-500"
        >
          <option value="">全部状态</option>
          <option value="active">进行中</option>
          <option value="pending">待处理</option>
          <option value="completed">已完成</option>
          <option value="delivered">已交付</option>
          <option value="cancelled">已取消</option>
        </select>
      </div>

      <div className="flex-1 overflow-auto space-y-4">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary-500"></div>
          </div>
        ) : filteredOrders.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-dark-400">
            <svg className="w-12 h-12 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            <p>暂无订单</p>
          </div>
        ) : (
          filteredOrders.map((order) => <OrderCard key={order.id} order={order} />)
        )}
      </div>
    </div>
  )
}
