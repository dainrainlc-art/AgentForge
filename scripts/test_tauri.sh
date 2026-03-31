#!/bin/bash
# ==========================================
# AgentForge Tauri 桌面端测试脚本
# 创建日期：2026-03-29
# 用途：自动化测试 Tauri 桌面端功能
# ==========================================

set -e

echo "============================================================"
echo "  AgentForge Tauri 桌面端自动化测试"
echo "============================================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试统计
TESTS_PASSED=0
TESTS_FAILED=0

# 进入项目目录
cd "$(dirname "$0")/.."

echo "📦 检查 Tauri 项目结构..."
echo ""

# 测试 1: 检查 Tauri 配置文件
echo "1️⃣ 检查 Tauri 配置文件..."
if [ -f "desktop/src-tauri/tauri.conf.json" ]; then
    echo -e "${GREEN}✅ tauri.conf.json 存在${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}❌ tauri.conf.json 不存在${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# 测试 2: 检查 Cargo.toml
echo "2️⃣ 检查 Cargo.toml..."
if [ -f "desktop/src-tauri/Cargo.toml" ]; then
    echo -e "${GREEN}✅ Cargo.toml 存在${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}❌ Cargo.toml 不存在${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# 测试 3: 检查主入口文件
echo "3️⃣ 检查 main.rs..."
if [ -f "desktop/src-tauri/src/main.rs" ]; then
    echo -e "${GREEN}✅ main.rs 存在${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}❌ main.rs 不存在${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# 测试 4: 检查命令文件
echo "4️⃣ 检查 commands.rs..."
if [ -f "desktop/src-tauri/src/commands.rs" ]; then
    echo -e "${GREEN}✅ commands.rs 存在${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}❌ commands.rs 不存在${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# 测试 5: 检查托盘图标文件
echo "5️⃣ 检查 tray.rs..."
if [ -f "desktop/src-tauri/src/tray.rs" ]; then
    echo -e "${GREEN}✅ tray.rs 存在${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}❌ tray.rs 不存在${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# 测试 6: 检查更新器文件
echo "6️⃣ 检查 updater.rs..."
if [ -f "desktop/src-tauri/src/updater.rs" ]; then
    echo -e "${GREEN}✅ updater.rs 存在${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}❌ updater.rs 不存在${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

echo ""
echo "📦 检查 Tauri 依赖..."
echo ""

# 测试 7: 检查 tauri.conf.json 配置
echo "7️⃣ 验证 tauri.conf.json 配置..."
if grep -q '"bundleName"' desktop/src-tauri/tauri.conf.json; then
    echo -e "${GREEN}✅ bundleName 已配置${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${YELLOW}⚠️  bundleName 未配置${NC}"
fi

if grep -q '"identifier"' desktop/src-tauri/tauri.conf.json; then
    echo -e "${GREEN}✅ identifier 已配置${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${YELLOW}⚠️  identifier 未配置${NC}"
fi

if grep -q '"version"' desktop/src-tauri/tauri.conf.json; then
    echo -e "${GREEN}✅ version 已配置${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${YELLOW}⚠️  version 未配置${NC}"
fi

echo ""
echo "🔍 检查 Cargo.toml 依赖..."
echo ""

# 测试 8: 检查必要的依赖
echo "8️⃣ 验证 Cargo.toml 依赖..."
if grep -q 'tauri' desktop/src-tauri/Cargo.toml; then
    echo -e "${GREEN}✅ tauri 依赖已添加${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}❌ tauri 依赖未添加${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

if grep -q 'serde' desktop/src-tauri/Cargo.toml; then
    echo -e "${GREEN}✅ serde 依赖已添加${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${YELLOW}⚠️  serde 依赖未添加${NC}"
fi

if grep -q 'tokio' desktop/src-tauri/Cargo.toml; then
    echo -e "${GREEN}✅ tokio 依赖已添加${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${YELLOW}⚠️  tokio 依赖未添加${NC}"
fi

echo ""
echo "📝 检查代码质量..."
echo ""

# 测试 9: 检查 main.rs 基本结构
echo "9️⃣ 验证 main.rs 基本结构..."
if grep -q 'fn main' desktop/src-tauri/src/main.rs; then
    echo -e "${GREEN}✅ main 函数已定义${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}❌ main 函数未定义${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

if grep -q 'tauri::Builder' desktop/src-tauri/src/main.rs || grep -q 'tauri::generate_handler' desktop/src-tauri/src/main.rs; then
    echo -e "${GREEN}✅ Tauri Builder 已配置${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${YELLOW}⚠️  Tauri Builder 配置待检查${NC}"
fi

# 测试 10: 检查 commands.rs
echo "🔟 验证 commands.rs..."
if [ -s "desktop/src-tauri/src/commands.rs" ]; then
    echo -e "${GREEN}✅ commands.rs 非空${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${YELLOW}⚠️  commands.rs 为空${NC}"
fi

echo ""
echo "🎨 检查前端资源..."
echo ""

# 测试 11: 检查前端目录
echo "1️⃣1️⃣ 检查前端目录..."
if [ -d "desktop/src" ] || [ -d "desktop/dist" ]; then
    echo -e "${GREEN}✅ 前端目录存在${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${YELLOW}⚠️  前端目录不存在（可能需要构建）${NC}"
fi

# 测试 12: 检查 package.json
echo "1️⃣2️⃣ 检查 package.json..."
if [ -f "desktop/package.json" ]; then
    echo -e "${GREEN}✅ package.json 存在${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${YELLOW}⚠️  package.json 不存在${NC}"
fi

echo ""
echo "🔧 检查 Rust 工具链..."
echo ""

# 测试 13: 检查 Rust 是否安装
echo "1️⃣3️⃣ 检查 Rust 工具链..."
if command -v rustc &> /dev/null; then
    RUST_VERSION=$(rustc --version)
    echo -e "${GREEN}✅ Rust 已安装：$RUST_VERSION${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${YELLOW}⚠️  Rust 未安装，请安装：https://rustup.rs/${NC}"
fi

# 测试 14: 检查 Cargo
echo "1️⃣4️⃣ 检查 Cargo..."
if command -v cargo &> /dev/null; then
    CARGO_VERSION=$(cargo --version)
    echo -e "${GREEN}✅ Cargo 已安装：$CARGO_VERSION${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${YELLOW}⚠️  Cargo 未安装${NC}"
fi

# 测试 15: 检查 Tauri CLI
echo "1️⃣5️⃣ 检查 Tauri CLI..."
if command -v cargo &> /dev/null && cargo install --list | grep -q tauri-cli; then
    echo -e "${GREEN}✅ Tauri CLI 已安装${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${YELLOW}⚠️  Tauri CLI 未安装，运行：cargo install tauri-cli${NC}"
fi

echo ""
echo "============================================================"
echo "  测试结果汇总"
echo "============================================================"
echo ""
echo -e "通过：${GREEN}$TESTS_PASSED${NC}"
echo -e "失败：${RED}$TESTS_FAILED${NC}"
echo ""

TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))
if [ $TOTAL_TESTS -gt 0 ]; then
    PASS_RATE=$((TESTS_PASSED * 100 / TOTAL_TESTS))
    echo "通过率：${PASS_RATE}%"
fi

echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 所有测试通过！Tauri 桌面端配置正确！${NC}"
    echo ""
    echo "下一步："
    echo "  1. 运行开发服务器：cd desktop && npm run dev"
    echo "  2. 启动 Tauri 应用：cd desktop/src-tauri && cargo tauri dev"
    echo "  3. 构建生产版本：cargo tauri build"
    exit 0
else
    echo -e "${RED}❌ 部分测试失败，请检查上述错误${NC}"
    echo ""
    echo "修复建议："
    echo "  - 确保所有必需文件存在"
    echo "  - 安装 Rust 和 Tauri CLI"
    echo "  - 检查配置文件格式"
    exit 1
fi
