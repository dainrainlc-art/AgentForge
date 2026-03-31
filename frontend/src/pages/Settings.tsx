import { useState } from 'react'

interface SettingSection {
  title: string
  description: string
  fields: SettingField[]
}

interface SettingField {
  key: string
  label: string
  type: 'text' | 'password' | 'select' | 'switch'
  value: string | boolean
  options?: { value: string; label: string }[]
}

const defaultSettings: SettingSection[] = [
  {
    title: 'AI模型配置',
    description: '配置AI模型相关参数',
    fields: [
      {
        key: 'default_model',
        label: '默认模型',
        type: 'select',
        value: 'glm-5',
        options: [
          { value: 'glm-5', label: 'GLM-5 (推荐)' },
          { value: 'kimi-k2.5', label: 'Kimi-K2.5' },
          { value: 'deepseek-v3.2', label: 'DeepSeek-V3.2' },
          { value: 'minimax-m2.5', label: 'MiniMax-M2.5' },
        ],
      },
      {
        key: 'temperature',
        label: '温度参数',
        type: 'text',
        value: '0.7',
      },
      {
        key: 'max_tokens',
        label: '最大Token数',
        type: 'text',
        value: '4096',
      },
    ],
  },
  {
    title: 'Fiverr配置',
    description: 'Fiverr API集成设置',
    fields: [
      {
        key: 'fiverr_api_key',
        label: 'API密钥',
        type: 'password',
        value: '',
      },
      {
        key: 'auto_reply',
        label: '自动回复',
        type: 'switch',
        value: true,
      },
    ],
  },
  {
    title: '通知设置',
    description: '配置通知方式',
    fields: [
      {
        key: 'desktop_notification',
        label: '桌面通知',
        type: 'switch',
        value: true,
      },
      {
        key: 'telegram_bot_token',
        label: 'Telegram Bot Token',
        type: 'password',
        value: '',
      },
      {
        key: 'email_notification',
        label: '邮件通知',
        type: 'switch',
        value: false,
      },
    ],
  },
  {
    title: '知识库同步',
    description: '配置知识库同步源',
    fields: [
      {
        key: 'notion_api_key',
        label: 'Notion API Key',
        type: 'password',
        value: '',
      },
      {
        key: 'obsidian_vault_path',
        label: 'Obsidian库路径',
        type: 'text',
        value: '',
      },
      {
        key: 'auto_sync',
        label: '自动同步',
        type: 'switch',
        value: true,
      },
    ],
  },
]

function SettingField({
  field,
  onChange,
}: {
  field: SettingField
  onChange: (key: string, value: string | boolean) => void
}) {
  switch (field.type) {
    case 'text':
    case 'password':
      return (
        <input
          type={field.type}
          value={field.value as string}
          onChange={(e) => onChange(field.key, e.target.value)}
          className="input"
        />
      )
    case 'select':
      return (
        <select
          value={field.value as string}
          onChange={(e) => onChange(field.key, e.target.value)}
          className="bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-dark-100 focus:outline-none focus:border-primary-500"
        >
          {field.options?.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      )
    case 'switch':
      return (
        <button
          onClick={() => onChange(field.key, !field.value)}
          className={`relative w-11 h-6 rounded-full transition-colors ${
            field.value ? 'bg-primary-600' : 'bg-dark-600'
          }`}
        >
          <span
            className={`absolute top-1 left-1 w-4 h-4 rounded-full bg-white transition-transform ${
              field.value ? 'translate-x-5' : 'translate-x-0'
            }`}
          />
        </button>
      )
    default:
      return null
  }
}

export default function Settings() {
  const [settings, setSettings] = useState(defaultSettings)
  const [saved, setSaved] = useState(false)

  const handleChange = (sectionIndex: number, key: string, value: string | boolean) => {
    setSettings((prev) => {
      const newSettings = [...prev]
      const field = newSettings[sectionIndex].fields.find((f) => f.key === key)
      if (field) {
        field.value = value
      }
      return newSettings
    })
    setSaved(false)
  }

  const handleSave = () => {
    console.log('Saving settings:', settings)
    setSaved(true)
    setTimeout(() => setSaved(false), 3000)
  }

  return (
    <div className="h-full overflow-auto">
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-dark-100">设置</h1>
        <p className="text-sm text-dark-400">配置系统参数和集成选项</p>
      </div>

      <div className="space-y-6">
        {settings.map((section, sectionIndex) => (
          <div key={section.title} className="card">
            <div className="mb-4">
              <h2 className="text-lg font-medium text-dark-100">{section.title}</h2>
              <p className="text-sm text-dark-400">{section.description}</p>
            </div>

            <div className="space-y-4">
              {section.fields.map((field) => (
                <div key={field.key} className="flex items-center justify-between">
                  <label className="text-sm text-dark-300">{field.label}</label>
                  <SettingField
                    field={field}
                    onChange={(key, value) => handleChange(sectionIndex, key, value)}
                  />
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6 flex items-center gap-4">
        <button onClick={handleSave} className="btn btn-primary">
          保存设置
        </button>
        {saved && (
          <span className="text-sm text-green-400 flex items-center gap-1">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            已保存
          </span>
        )}
      </div>
    </div>
  )
}
