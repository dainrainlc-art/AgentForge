# AgentForge Mobile App

> 跨平台移动端应用 - React Native

## 📱 技术选型

### 方案对比

| 技术 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **React Native** | JS生态、热更新、社区活跃 | 性能略低于原生 | 快速开发、跨平台 |
| **Flutter** | 性能优秀、UI一致 | Dart学习成本 | 高性能要求 |
| **原生开发** | 性能最佳 | 开发成本高 | 极致体验 |

### 选择: React Native

**理由**:
- 前端团队技术栈一致（React）
- 丰富的第三方库
- 热更新支持
- 社区活跃

## 🏗️ 项目结构

```
mobile/
├── src/
│   ├── components/          # 通用组件
│   │   ├── common/          # 基础组件
│   │   ├── chat/            # 聊天相关
│   │   ├── orders/          # 订单相关
│   │   └── settings/        # 设置相关
│   ├── screens/             # 页面
│   │   ├── HomeScreen.tsx
│   │   ├── ChatScreen.tsx
│   │   ├── OrdersScreen.tsx
│   │   ├── KnowledgeScreen.tsx
│   │   └── SettingsScreen.tsx
│   ├── navigation/          # 导航配置
│   │   ├── AppNavigator.tsx
│   │   └── TabNavigator.tsx
│   ├── hooks/               # 自定义 Hooks
│   ├── services/            # API 服务
│   ├── store/               # 状态管理 (Redux/Zustand)
│   ├── utils/               # 工具函数
│   └── types/               # TypeScript 类型
├── assets/                  # 静态资源
│   ├── images/
│   ├── fonts/
│   └── icons/
├── android/                 # Android 原生代码
├── ios/                     # iOS 原生代码
├── App.tsx                  # 入口文件
├── package.json
├── tsconfig.json
└── README.md
```

## 🚀 核心功能

### 1. AI 聊天
- 💬 实时对话
- 🎙️ 语音输入
- 📎 附件发送
- 🔔 消息通知

### 2. Fiverr 订单管理
- 📦 订单列表
- 📊 订单详情
- 💬 客户沟通
- 📤 交付管理

### 3. 知识库
- 📚 文档查看
- 🔍 智能搜索
- ⭐ 收藏管理
- 📝 笔记编辑

### 4. 工作流
- 📋 任务列表
- ✅ 任务执行
- 📈 进度跟踪
- 🔔 提醒通知

### 5. 设置
- 👤 账户管理
- 🔔 通知设置
- 🌙 主题切换
- 🌐 语言选择

## 📦 依赖清单

```json
{
  "dependencies": {
    "react": "18.2.0",
    "react-native": "0.73.0",
    "@react-navigation/native": "^6.1.9",
    "@react-navigation/bottom-tabs": "^6.5.11",
    "@react-navigation/stack": "^6.3.20",
    "react-native-screens": "^3.29.0",
    "react-native-safe-area-context": "^4.8.2",
    "@reduxjs/toolkit": "^2.0.1",
    "react-redux": "^9.0.4",
    "axios": "^1.6.2",
    "react-native-vector-icons": "^10.0.3",
    "react-native-paper": "^5.11.4",
    "react-native-gesture-handler": "^2.14.1",
    "react-native-reanimated": "^3.6.1",
    "react-native-async-storage": "^1.21.0",
    "react-native-push-notification": "^8.1.1",
    "react-native-webview": "^13.6.4",
    "react-native-image-picker": "^7.1.0",
    "react-native-document-picker": "^9.1.0",
    "react-native-fs": "^2.20.0",
    "react-native-share": "^10.0.2",
    "react-native-localize": "^3.0.4",
    "i18next": "^23.7.11",
    "react-i18next": "^13.5.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.45",
    "@types/react-native": "^0.72.8",
    "typescript": "^5.3.3",
    "metro-react-native-babel-preset": "^0.77.0",
    "jest": "^29.7.0",
    "@testing-library/react-native": "^12.4.0",
    "eslint": "^8.56.0",
    "prettier": "^3.1.1"
  }
}
```

## 🎨 UI 设计

### 主题
- 主色调: #0ea5e9 (蓝色)
- 背景色: #0f172a (深色)
- 文字色: #f8fafc (白色)
- 强调色: #22d3ee (青色)

### 导航
- 底部 Tab 导航
- 5 个主页面: 首页、聊天、订单、知识、设置

### 组件库
- React Native Paper
- 自定义组件

## 🔧 开发计划

### Week 1: 环境搭建
- [ ] 初始化 React Native 项目
- [ ] 配置导航
- [ ] 设置状态管理
- [ ] 配置 API 客户端

### Week 2: 基础功能
- [ ] 登录/注册页面
- [ ] 首页 Dashboard
- [ ] 底部导航
- [ ] 主题切换

### Week 3: 核心功能
- [ ] AI 聊天界面
- [ ] 订单列表/详情
- [ ] 知识库浏览

### Week 4: 高级功能
- [ ] 推送通知
- [ ] 离线支持
- [ ] 性能优化

### Week 5: 测试发布
- [ ] 单元测试
- [ ] 集成测试
- [ ] iOS/Android 打包
- [ ] 应用商店提交

## 📱 预览

```bash
# 安装依赖
cd mobile
npm install

# iOS
cd ios && pod install && cd ..
npx react-native run-ios

# Android
npx react-native run-android
```

## 📚 文档

- [React Native 官方文档](https://reactnative.dev/)
- [React Navigation](https://reactnavigation.org/)
- [React Native Paper](https://callstack.github.io/react-native-paper/)

## 🤝 贡献

欢迎提交 Issue 和 PR!

## 📄 许可证

MIT
