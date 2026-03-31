#!/bin/bash
# 配置Docker镜像加速器

echo "=========================================="
echo "配置Docker镜像加速器"
echo "=========================================="
echo ""

# 创建daemon.json配置文件
sudo mkdir -p /etc/docker

sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com"
  ],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "3"
  }
}
EOF

echo "✅ Docker镜像加速器配置已创建"
echo ""
echo "配置的镜像源："
echo "  - 中科大镜像源"
echo "  - 网易镜像源"
echo "  - 百度云镜像源"
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
sudo docker info | grep -A 10 "Registry Mirrors"
echo ""
echo "=========================================="
echo "镜像加速器配置完成！"
echo "现在可以重新运行 ./start-services.sh 启动服务了"
echo "=========================================="
