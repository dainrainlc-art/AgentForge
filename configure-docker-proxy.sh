#!/bin/bash
# 配置Docker代理

echo "=========================================="
echo "配置Docker代理"
echo "=========================================="
echo ""

# 检查是否提供了代理地址
if [ -z "$1" ]; then
    echo "❌ 错误：请提供代理地址"
    echo ""
    echo "用法：$0 <代理地址>"
    echo ""
    echo "示例："
    echo "  $0 http://127.0.0.1:7890"
    echo "  $0 socks5://127.0.0.1:7890"
    echo ""
    exit 1
fi

PROXY_URL="$1"
echo "使用代理地址: $PROXY_URL"
echo ""

# 创建Docker服务目录
sudo mkdir -p /etc/systemd/system/docker.service.d

# 创建代理配置文件
sudo tee /etc/systemd/system/docker.service.d/http-proxy.conf > /dev/null <<EOF
[Service]
Environment="HTTP_PROXY=$PROXY_URL"
Environment="HTTPS_PROXY=$PROXY_URL"
Environment="NO_PROXY=localhost,127.0.0.1,.local,.internal"
EOF

echo "✅ Docker代理配置已创建"
echo ""
echo "正在重启Docker服务..."
echo ""

# 重启Docker服务
sudo systemctl daemon-reload
sudo systemctl restart docker

echo ""
echo "✅ Docker服务已重启"
echo ""
echo "验证配置："
sudo systemctl show --property=Environment docker
echo ""
echo "=========================================="
echo "Docker代理配置完成！"
echo "现在可以运行 ./start-services.sh 启动服务了"
echo "=========================================="
