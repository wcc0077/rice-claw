# CI/CD Deployment Guide

本文档说明如何配置 GitHub Actions CI/CD 自动部署。

## 架构概览

```
┌─────────────────────────────────────────────────────────────────────┐
│                   CI/CD 流程（本地构建）                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  git push main ──────► SSH 连接服务器 ──────► git pull              │
│                                                   │                  │
│                                                   ▼                  │
│                                           docker compose build       │
│                                                   │                  │
│                                                   ▼                  │
│                                           docker compose up          │
│                                                   │                  │
│                                                   ▼                  │
│                                          部署测试环境                 │
│                                        test.xiayouqian.online       │
│                                                                     │
│  Release ───────────► 同样流程 ──────► 部署生产环境                   │
│                                       xiayouqian.online             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## 部署环境

| 环境 | 触发条件 | 域名 | 端口 |
|------|----------|------|------|
| 测试环境 | push 到 main | test.xiayouqian.online | 3000, 8080 |
| 生产环境 | GitHub Release | xiayouqian.online | 80, 8000 |

## 配置步骤

### 第一步：服务器设置

SSH 登录服务器，运行设置脚本：

```bash
curl -fsSL https://raw.githubusercontent.com/wcc0077/rice-claw/main/deploy/setup-server.sh | sudo bash
```

### 第二步：配置 DNS 解析

在你的域名服务商处添加 DNS 记录：

| 主机记录 | 记录类型 | 记录值 |
|----------|----------|--------|
| @ | A | 服务器 IP |
| www | A | 服务器 IP |
| test | A | 服务器 IP |

### 第三步：添加 GitHub Secrets

在 GitHub 仓库中添加以下 Secrets：

**路径：** Settings → Secrets and variables → Actions → New repository secret

| Secret 名称 | 说明 | 示例 |
|-------------|------|------|
| `SERVER_HOST` | 服务器 IP 或域名 | `xiayouqian.online` 或 `123.45.67.89` |
| `SERVER_USER` | SSH 用户名 | `root` |
| `SERVER_SSH_KEY` | SSH 私钥内容 | 见下方说明 |
| `SERVER_SSH_PORT` | SSH 端口 | `22` |

#### 获取 SSH 私钥

**方式一：本地生成（推荐）**

```bash
# 在本地电脑执行
ssh-keygen -t ed25519 -C "github-actions"
ssh-copy-id root@你的服务器IP  # 将公钥复制到服务器
cat ~/.ssh/id_ed25519  # 复制私钥内容到 GitHub Secret
```

**方式二：服务器生成**

```bash
# 在服务器执行
ssh-keygen -t ed25519 -C "github-actions"
cat ~/.ssh/id_ed25519.pub >> ~/.ssh/authorized_keys
cat ~/.ssh/id_ed25519  # 复制私钥内容到 GitHub Secret
```

### 第四步：启用 GitHub Actions 权限

1. 进入仓库 Settings → Actions → General
2. 在 "Workflow permissions" 中选择 "Read and write permissions"

## 触发部署

### 部署测试环境

```bash
git push origin main
```

### 部署生产环境

1. 进入 GitHub 仓库页面
2. 点击右侧 "Releases" → "Create a new release"
3. 输入版本号（如 `v1.0.0`）
4. 点击 "Publish release"

### 手动触发

1. 进入 Actions 页面
2. 选择 "CI/CD Pipeline"
3. 点击 "Run workflow"
4. 选择环境

## 访问地址

| 环境 | 地址 |
|------|------|
| 测试前端 | http://test.xiayouqian.online |
| 测试后端 API | http://test.xiayouqian.online/api |
| 生产前端 | http://xiayouqian.online |
| 生产后端 API | http://xiayouqian.online/api |

## 手动部署

如果需要手动部署：

```bash
# 登录服务器
ssh root@xiayouqian.online

# 进入项目目录
cd /opt/shrimp-market

# 拉取最新代码
git pull origin main

# 部署测试环境
docker compose -f deploy/docker-compose.staging.yml up -d --build

# 或部署生产环境
docker compose -f deploy/docker-compose.prod.yml up -d --build
```

## 查看日志

```bash
# 查看容器日志
docker logs shrimp-backend-staging
docker logs shrimp-frontend-staging
docker logs shrimp-backend-prod
docker logs shrimp-frontend-prod

# 查看 Nginx 日志
tail -f /var/log/nginx/shrimp-staging.access.log
tail -f /var/log/nginx/shrimp-prod.access.log
```

## SSL/HTTPS 配置

```bash
# 安装 certbot
yum install -y certbot python3-certbot-nginx

# 获取证书
certbot --nginx -d xiayouqian.online -d www.xiayouqian.online
certbot --nginx -d test.xiayouqian.online

# 自动续期
systemctl enable certbot-renew.timer
```

## 故障排查

### SSH 连接失败

```bash
# 测试 SSH 连接
ssh -v root@xiayouqian.online

# 检查 authorized_keys
cat ~/.ssh/authorized_keys
```

### Docker 构建失败

```bash
# 查看构建日志
docker compose -f deploy/docker-compose.staging.yml build --no-cache

# 检查磁盘空间
df -h
```

### 端口被占用

```bash
# 查看端口占用
netstat -tlnp | grep -E '80|3000|8000|8080'

# 停止容器
docker compose -f deploy/docker-compose.staging.yml down
```