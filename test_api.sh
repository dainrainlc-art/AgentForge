#!/bin/bash

echo "=========================================="
echo "  AgentForge API 测试脚本"
echo "=========================================="

BASE_URL="http://localhost:8000"

echo -e "\n=== 1. 健康检查 ==="
curl -s $BASE_URL/api/health | python3 -m json.tool

echo -e "\n=== 2. 用户注册 ==="
curl -s -X POST $BASE_URL/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "test123", "name": "Test User"}' | python3 -m json.tool

echo -e "\n=== 3. 用户登录（获取Token） ==="
RESPONSE=$(curl -s -X POST $BASE_URL/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "test123"}')
echo "$RESPONSE" | python3 -m json.tool

TOKEN=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
echo -e "\n获取到的Token: ${TOKEN:0:50}..."

echo -e "\n=== 4. 发送聊天消息 ==="
curl -s -X POST $BASE_URL/api/chat/message \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"message": "你好，请介绍一下你自己"}' | python3 -m json.tool

echo -e "\n=== 5. 获取对话历史 ==="
curl -s $BASE_URL/api/chat/history \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo -e "\n=== 6. 获取Agent状态 ==="
curl -s $BASE_URL/api/chat/status \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo -e "\n=========================================="
echo "  测试完成"
echo "=========================================="
