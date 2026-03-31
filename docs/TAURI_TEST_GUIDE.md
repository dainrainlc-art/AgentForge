# Tauri 桌面端测试指南

## 📋 测试前准备

### 1. 安装依赖

**Rust 环境**:
```bash
# 安装 Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# 验证安装
rustc --version
cargo --version
```

**Node.js 依赖**:
```bash
cd desktop
npm install
```

**Tauri CLI**:
```bash
cargo install tauri-cli
```

### 2. 系统要求

- **Windows**: Windows 10/11 + Visual Studio Build Tools
- **macOS**: macOS 12+ + Xcode Command Line Tools
- **Linux**: Ubuntu 20.04+ + build-essential + libwebkit2gtk-4.0-dev

---

## 🧪 测试步骤

### 1. 开发模式测试

```bash
# 进入 Tauri 目录
cd desktop/src-tauri

# 启动开发模式
cargo tauri dev
```

**预期结果**:
- ✅ 应用窗口正常打开
- ✅ 前端页面正常加载
- ✅ 控制台无严重错误

**检查项**:
- [ ] 窗口标题正确
- [ ] 聊天页面可以访问
- [ ] 设置页面可以访问
- [ ] 系统托盘图标显示

---

### 2. 构建测试

```bash
# 构建生产版本
cargo tauri build
```

**预期输出位置**:
- **Windows**: `desktop/src-tauri/target/release/bundle/msi/`
- **macOS**: `desktop/src-tauri/target/release/bundle/dmg/`
- **Linux**: `desktop/src-tauri/target/release/bundle/deb/`

**检查项**:
- [ ] 构建成功无错误
- [ ] 安装包生成成功
- [ ] 安装包大小合理（< 50MB）

---

### 3. 功能测试

#### 3.1 AI 聊天功能

**测试步骤**:
1. 打开应用
2. 进入聊天页面
3. 输入测试消息
4. 发送消息

**预期结果**:
- [ ] 消息正常发送
- [ ] 收到 AI 回复
- [ ] 聊天记录保存
- [ ] 支持 Markdown 格式

**测试用例**:
```
测试 1: 简单问题
输入："你好"
期望：收到友好问候

测试 2: 复杂问题
输入："请解释量子纠缠"
期望：收到详细解释

测试 3: 代码生成
输入："写一个 Python 函数计算斐波那契数列"
期望：收到正确的代码
```

#### 3.2 设置功能

**测试步骤**:
1. 打开设置页面
2. 修改 API Key
3. 修改主题
4. 保存设置

**预期结果**:
- [ ] 设置可以修改
- [ ] 设置保存成功
- [ ] 重启后设置保留
- [ ] 主题切换生效

**测试用例**:
```
测试 1: API Key 配置
输入：有效的 API Key
期望：保存成功，可以正常使用 AI 功能

测试 2: 主题切换
操作：切换到 Dark Mode
期望：界面立即变为深色主题

测试 3: 无效配置
输入：无效的 API Key
期望：提示错误，不允许保存
```

#### 3.3 系统托盘

**测试步骤**:
1. 查看系统托盘图标
2. 右键点击图标
3. 选择菜单项

**预期结果**:
- [ ] 托盘图标正常显示
- [ ] 右键菜单正常弹出
- [ ] "显示窗口" 可以恢复窗口
- [ ] "退出" 可以正常退出应用

**测试用例**:
```
测试 1: 最小化到托盘
操作：点击窗口关闭按钮
期望：窗口隐藏，托盘图标仍在

测试 2: 从托盘恢复
操作：右键托盘 -> 显示窗口
期望：窗口重新显示

测试 3: 退出应用
操作：右键托盘 -> 退出
期望：应用完全退出
```

#### 3.4 窗口管理

**测试步骤**:
1. 调整窗口大小
2. 移动窗口位置
3. 最小化/最大化窗口

**预期结果**:
- [ ] 窗口大小可以调整
- [ ] 窗口位置可以移动
- [ ] 最小化/最大化正常
- [ ] 窗口状态保存

---

### 4. API 连接测试

**配置文件**: `desktop/src-tauri/tauri.conf.json`

```json
{
  "app": {
    "windows": [
      {
        "title": "AgentForge",
        "width": 1200,
        "height": 800
      }
    ]
  },
  "build": {
    "devPath": "http://localhost:5173",
    "distPath": "../dist"
  }
}
```

**测试步骤**:
1. 确保后端服务运行
2. 配置正确的 API 地址
3. 测试 API 调用

**预期结果**:
- [ ] 可以连接后端 API
- [ ] API 调用成功
- [ ] 错误处理正常

---

## 🐛 常见问题

### 问题 1: Rust 编译错误

**错误信息**:
```
error: package `xxx` cannot be built because it requires rustc 1.xx
```

**解决方案**:
```bash
# 更新 Rust
rustup update

# 检查版本
rustc --version
```

### 问题 2: 前端资源找不到

**错误信息**:
```
failed to load frontend
```

**解决方案**:
```bash
# 先构建前端
cd desktop
npm run build

# 再构建 Tauri
cargo tauri build
```

### 问题 3: WebKitGTK 依赖缺失 (Linux)

**错误信息**:
```
package webkit2gtk-4.0 was not found
```

**解决方案**:
```bash
# Ubuntu/Debian
sudo apt install libwebkit2gtk-4.0-dev

# Fedora
sudo dnf install webkit2gtk3-devel
```

### 问题 4: API 连接失败

**错误信息**:
```
Failed to connect to API
```

**解决方案**:
1. 检查后端服务是否运行
2. 检查 API 地址配置
3. 检查防火墙设置

---

## 📊 测试结果记录

### 测试环境

| 项目 | 配置 |
|------|------|
| 操作系统 | |
| Rust 版本 | |
| Node.js 版本 | |
| Tauri 版本 | |

### 测试用例执行

| 测试项 | 结果 | 备注 |
|--------|------|------|
| 构建测试 | ⬜ 通过 ⬜ 失败 | |
| AI 聊天 | ⬜ 通过 ⬜ 失败 | |
| 设置功能 | ⬜ 通过 ⬜ 失败 | |
| 系统托盘 | ⬜ 通过 ⬜ 失败 | |
| 窗口管理 | ⬜ 通过 ⬜ 失败 | |
| API 连接 | ⬜ 通过 ⬜ 失败 | |

### 发现的 Bug

| 编号 | 描述 | 严重程度 | 状态 |
|------|------|----------|------|
| 1 | | 高/中/低 | 待修复/修复中/已修复 |

---

## 🚀 性能测试

### 启动时间

```bash
# 测量冷启动时间
time cargo tauri dev
```

**目标**: < 3 秒

### 内存占用

**检查方式**:
- Windows: 任务管理器
- macOS: 活动监视器
- Linux: `ps aux | grep tauri`

**目标**: < 200MB

### CPU 占用

**目标**: 空闲时 < 5%

---

## 📝 测试报告模板

```markdown
# Tauri 桌面端测试报告

**测试日期**: YYYY-MM-DD  
**测试人员**:  
**测试环境**: 

## 测试结果

### 构建测试
- [ ] 成功
- [ ] 失败（原因：）

### 功能测试
- AI 聊天：[ ] 通过 [ ] 失败
- 设置功能：[ ] 通过 [ ] 失败
- 系统托盘：[ ] 通过 [ ] 失败
- 窗口管理：[ ] 通过 [ ] 失败

### 性能测试
- 启动时间：秒
- 内存占用：MB
- CPU 占用：%

## 发现的问题

1. 
2. 
3. 

## 建议

1. 
2. 
3. 

## 结论

[ ] 可以发布  
[ ] 需要修复后发布  
[ ] 需要重大修改
```

---

## 🔗 相关资源

- [Tauri 官方文档](https://tauri.app/docs)
- [Rust 官方文档](https://doc.rust-lang.org/)
- [项目配置](desktop/src-tauri/tauri.conf.json)
- [源码目录](desktop/src-tauri/src/)

---

**最后更新**: 2026-03-29
