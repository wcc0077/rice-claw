# CI/CD Deployment Guide

本文档说明如何配置 GitHub Actions CI/CD 自动部署。

## 架构概览

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CI/CD 流程                                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  git push main ──────► 构建镜像 ──────► 部署测试环境                 │
│                        │              test.xiayouqian.online        │
│                        │                                             │
│                        ▼                                             │
│                   ghcr.io                                           │
│                   镜像仓库                                           │
│                        │                                             │
│  Release ──────────────┴──────────► 部署生产环境                     │
│                                     xiayouqian.online               │
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
# 下载并运行设置脚本
curl -fsSL https://raw.githubusercontent.com/wcc0077/rice-claw/main/deploy/setup-server.sh | sudo bash
```

或手动创建目录：

```bash
sudo mkdir -p /opt/shrimp-market
cd /opt/shrimp-market

# 下载 docker-compose 文件
curl -O https://raw.githubusercontent.com/wcc0077/rice-claw/main/deploy/docker-compose.staging.yml
curl -O https://raw.githubusercontent.com/wcc0077/rice-claw/main/deploy/docker-compose.prod.yml
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

```bash
# 在本地电脑执行（已有 SSH 密钥的情况）
cat ~/.ssh/id_rsa

# 如果没有密钥，先生成
ssh-keygen -t ed25519 -C "github-actions"
ssh-copy-id user@your-server  # 将公钥复制到服务器
cat ~/.ssh/id_ed25519  # 复制私钥内容到 GitHub Secret
```

### 第四步：启用 GitHub Packages

确保仓库有权限写入 Container Registry：

1. 进入仓库 Settings → Actions → General
2. 在 "Workflow permissions" 中选择 "Read and write permissions"
3. 勾选 "Allow GitHub Actions to create and approve pull requests"

## 触发部署

### 部署测试环境

```bash
git push origin main
```

GitHub Actions 自动：
1. 构建镜像并标记为 `staging`
2. 推送到 ghcr.io
3. SSH 连接服务器部署

### 部署生产环境

1. 进入 GitHub 仓库页面
2. 点击右侧 "Releases" → "Create a new release"
3. 输入版本号（如 `v1.0.0`）
4. 点击 "Publish release"

GitHub Actions 自动：
1. 构建镜像并标记为版本号 + `latest`
2. 推送到 ghcr.io
3. SSH 连接服务器部署到生产环境

### 手动触发

1. 进入 Actions 页面
2. 选择 "CI/CD Pipeline"
3. 点击 "Run workflow"
4. 选择环境（staging 或 production）

## 访问地址

| 环境 | 地址 |
|------|------|
| 测试前端 | http://test.xiayouqian.online |
| 测试后端 API | http://test.xiayouqian.online/api |
| 生产前端 | http://xiayouqian.online |
| 生产后端 API | http://xiayouqian.online/api |

## 查看日志

### GitHub Actions 日志

进入 Actions 页面查看每次部署的详细日志。

### 服务器日志

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

## 回滚

如果部署出现问题，可以回滚到之前的版本：

```bash
# 登录服务器
ssh user@xiayouqian.online

# 查看镜像历史
docker images | grep rice-claw

# 修改 docker-compose 使用指定版本
# 编辑 docker-compose.prod.yml，将 :latest 改为 :v1.0.0

# 重启服务
cd /opt/shrimp-market
docker compose -f docker-compose.prod.yml up -d
```

## SSL/HTTPS 配置（可选）

使用 Let's Encrypt 免费证书：

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

### 构建失败

1. 检查 Dockerfile 是否正确
2. 查看 Actions 日志中的错误信息
3. 本地测试构建：`docker compose build`

### 部署失败

1. 检查 SSH 密钥是否正确
2. 检查服务器 Docker 是否运行
3. 手动登录服务器测试：`docker compose pull && docker compose up -d`

### 访问失败

1. 检查防火墙端口是否开放
2. 检查 Nginx 配置是否正确
3. 检查 DNS 解析是否生效：`nslookup xiayouqian.online`

## 文件清单

```
.github/workflows/
└── ci-cd.yml              # CI/CD 配置

deploy/
├── docker-compose.staging.yml  # 测试环境
├── docker-compose.prod.yml     # 生产环境
├── nginx.conf                  # Nginx 配置
└── setup-server.sh             # 服务器设置脚本
```