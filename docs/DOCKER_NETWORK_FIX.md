# Docker 构建网络问题修复指南

## 问题描述

Docker 构建时出现以下错误：
```
Err:3 http://deb.debian.org/debian-security trixie-security InRelease
  Unable to connect to deb.debian.org:http:
E: Unable to locate package gcc
E: Unable to locate package libpq-dev
```

**原因**: 无法连接到 Debian 官方软件源（网络问题）

---

## 解决方案

### 方案 1: 已自动修复 ✅

我已经修改了以下 Dockerfile，使用国内镜像源：

- `Dockerfile.prod` - 使用阿里云镜像 + 清华 pip 镜像
- `Dockerfile` - 使用阿里云镜像 + 清华 pip 镜像

现在可以直接运行：
```bash
sudo docker-compose -f docker-compose.prod.yml up -d
```

### 方案 2: 手动配置 Docker 镜像加速

如果仍然遇到网络问题，可以配置 Docker 镜像加速器：

#### 1. 配置 Docker Hub 镜像加速

编辑 `/etc/docker/daemon.json`：

```json
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://registry.docker-cn.com",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com"
  ]
}
```

然后重启 Docker：
```bash
sudo systemctl daemon-reload
sudo systemctl restart docker
```

#### 2. 在 docker-compose 中指定镜像

在 `docker-compose.prod.yml` 中添加：

```yaml
services:
  agentforge-api:
    build:
      context: .
      dockerfile: Dockerfile.prod
      args:
        - PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## 快速测试

### 测试网络连接

```bash
# 测试能否访问阿里云
ping mirrors.aliyun.com

# 测试能否访问清华 pypi
curl https://pypi.tuna.tsinghua.edu.cn/simple
```

### 测试 Docker 构建

```bash
# 测试构建（只构建不启动）
sudo docker-compose -f docker-compose.prod.yml build --no-cache

# 如果成功，启动服务
sudo docker-compose -f docker-compose.prod.yml up -d
```

---

## 常见问题

### Q1: 构建仍然失败怎么办？

**A**: 尝试使用代理或 VPN，或者在离线环境下使用本地缓存：

```bash
# 先在本地安装依赖
pip download -r requirements.txt -d ./local-packages

# 修改 Dockerfile 使用本地包
COPY local-packages /tmp/local-packages
RUN pip install --no-index --find-links=/tmp/local-packages -r requirements.txt
```

### Q2: 如何查看构建日志？

```bash
# 查看详细构建日志
sudo docker-compose -f docker-compose.prod.yml build --progress=plain

# 查看特定服务日志
sudo docker-compose -f docker-compose.prod.yml logs agentforge-api
```

### Q3: 如何清理构建缓存？

```bash
# 清理 Docker 构建缓存
sudo docker builder prune -a -f

# 清理未使用的镜像
sudo docker image prune -a -f

# 重新构建
sudo docker-compose -f docker-compose.prod.yml build --no-cache
```

---

## 替代方案

如果网络问题无法解决，可以考虑：

### 方案 A: 使用预构建镜像

```bash
# 从 Docker Hub 拉取预构建镜像
sudo docker pull python:3.12-slim

# 然后构建应用
sudo docker-compose -f docker-compose.prod.yml build
```

### 方案 B: 离线安装

1. 在有网络的机器上下载所有依赖
2. 复制到离线机器
3. 使用本地源安装

---

## 验证修复

运行以下命令验证：

```bash
# 1. 构建镜像
sudo docker-compose -f docker-compose.prod.yml build

# 2. 启动服务
sudo docker-compose -f docker-compose.prod.yml up -d

# 3. 查看状态
sudo docker-compose -f docker-compose.prod.yml ps

# 4. 测试 API
curl http://localhost:8000/api/health
```

---

**最后更新**: 2026-03-30  
**状态**: ✅ 已修复（使用国内镜像源）
