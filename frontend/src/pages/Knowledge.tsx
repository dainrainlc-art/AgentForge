import { useState } from 'react'

interface KnowledgeItem {
  id: string
  title: string
  content: string
  source: string
  tags: string[]
  created_at: string
}

const mockItems: KnowledgeItem[] = [
  {
    id: '1',
    title: 'Fiverr最佳实践指南',
    content: '如何在Fiverr上获得更多订单：1. 优化Gig标题和描述 2. 提供有竞争力的价格 3. 快速响应客户消息...',
    source: 'manual',
    tags: ['fiverr', 'best-practices', 'sales'],
    created_at: '2024-01-15T10:00:00Z',
  },
  {
    id: '2',
    title: '社交媒体内容策略',
    content: '有效的社交媒体内容策略包括：定期发布、内容多样化、互动参与、数据分析...',
    source: 'notion',
    tags: ['social-media', 'marketing', 'content'],
    created_at: '2024-01-14T09:00:00Z',
  },
  {
    id: '3',
    title: '客户沟通模板',
    content: '常用客户沟通模板：订单确认、进度更新、交付提醒、满意度调查...',
    source: 'obsidian',
    tags: ['communication', 'templates', 'customer-service'],
    created_at: '2024-01-13T08:00:00Z',
  },
]

function KnowledgeCard({ item }: { item: KnowledgeItem }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="card hover:border-dark-600 transition-colors">
      <div className="flex items-start justify-between mb-2">
        <h3 className="font-medium text-dark-100">{item.title}</h3>
        <span className="text-xs text-dark-500 bg-dark-800 px-2 py-1 rounded">
          {item.source}
        </span>
      </div>

      <p className={`text-sm text-dark-400 ${expanded ? '' : 'line-clamp-2'}`}>
        {item.content}
      </p>

      <div className="flex flex-wrap gap-2 mt-3">
        {item.tags.map((tag) => (
          <span
            key={tag}
            className="text-xs bg-primary-500/10 text-primary-400 px-2 py-0.5 rounded"
          >
            {tag}
          </span>
        ))}
      </div>

      <div className="flex items-center justify-between mt-3 pt-3 border-t border-dark-700">
        <span className="text-xs text-dark-500">
          {new Date(item.created_at).toLocaleDateString('zh-CN')}
        </span>
        <div className="flex gap-2">
          <button className="text-xs text-dark-400 hover:text-dark-200">编辑</button>
          <button className="text-xs text-dark-400 hover:text-dark-200">删除</button>
        </div>
      </div>
    </div>
  )
}

export default function Knowledge() {
  const [search, setSearch] = useState('')
  const [selectedTag, setSelectedTag] = useState('')

  const allTags = [...new Set(mockItems.flatMap((item) => item.tags))]

  const filteredItems = mockItems.filter((item) => {
    const matchesSearch =
      !search ||
      item.title.toLowerCase().includes(search.toLowerCase()) ||
      item.content.toLowerCase().includes(search.toLowerCase())
    const matchesTag = !selectedTag || item.tags.includes(selectedTag)
    return matchesSearch && matchesTag
  })

  return (
    <div className="h-full flex flex-col">
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-dark-100">知识库</h1>
        <p className="text-sm text-dark-400">管理和检索知识文档</p>
      </div>

      <div className="flex items-center gap-4 mb-6">
        <div className="flex-1 relative">
          <svg
            className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="搜索知识库..."
            className="input pl-10"
          />
        </div>
        <button className="btn btn-primary">添加文档</button>
      </div>

      <div className="flex flex-wrap gap-2 mb-4">
        <button
          onClick={() => setSelectedTag('')}
          className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
            !selectedTag
              ? 'bg-primary-500/20 text-primary-400'
              : 'bg-dark-800 text-dark-300 hover:text-dark-100'
          }`}
        >
          全部
        </button>
        {allTags.map((tag) => (
          <button
            key={tag}
            onClick={() => setSelectedTag(tag)}
            className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
              selectedTag === tag
                ? 'bg-primary-500/20 text-primary-400'
                : 'bg-dark-800 text-dark-300 hover:text-dark-100'
            }`}
          >
            {tag}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-auto">
        {filteredItems.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-dark-400">
            <svg className="w-12 h-12 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
              />
            </svg>
            <p>暂无知识文档</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredItems.map((item) => (
              <KnowledgeCard key={item.id} item={item} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
