# Deployment Guide

## 环境说明

| 环境 | 用途 | 数据库 | 部署方式 |
|------|------|--------|----------|
| Development | 本地开发 | shrimp_market_dev | Docker (PostgreSQL + Redis) + 本地后端 |
| Staging | 测试环境 | shrimp_market_staging | 完整 Docker 部署 |
| Production | 生产环境 | shrimp_market | 完整 Docker 部署 |

## 目录结构

```
deploy/
├── docker-compose.dev.yml      # 本地开发 (仅数据库服务)
├── docker-compose.staging.yml  # 测试环境 (完整部署)
├── docker-compose.prod.yml     # 生产环境 (完整部署)
├── .env.development            # 本地开发配置
├── .env.staging                # 测试环境配置
└── .env.production             # 生产环境配置

backend/
├── .env.example                # 配置模板
└── .env.development            # 本地开发配置 (后端读取)

frontend/
└── .env.example                # 前端配置模板
```

## 本地开发 (Development)

```bash
# 1. 启动数据库服务
cd deploy
docker-compose -f docker-compose.dev.yml up -d

# 2. 配置环境变量
cp backend/.env.example backend/.env.development
# 编辑 backend/.env.development 填入配置

# 3. 运行数据库迁移
cd backend
uv run alembic upgrade head

# 4. 启动后端
uv run uvicorn src.main:app --reload

# 5. 启动前端
cd frontend
npm install
npm run dev
```

**服务地址：**
- Backend: http://localhost:8000
- Frontend: http://localhost:5173
- PostgreSQL: localhost:5432
- Redis: localhost:6379

## 测试环境 (Staging)

```bash
# 1. 配置环境变量
cd deploy
cp .env.staging.example .env.staging  # 如果有示例文件
# 编辑 .env.staging 填入配置

# 2. 部署
docker-compose -f docker-compose.staging.yml up -d

# 3. 查看日志
docker-compose -f docker-compose.staging.yml logs -f
```

**服务地址：**
- Backend: http://localhost:8080
- Frontend: http://localhost:3000

## 生产环境 (Production)

```bash
# 1. 配置环境变量
cd deploy
# 编辑 .env.production 填入生产配置（密码等敏感信息）

# 2. 部署
docker-compose -f docker-compose.prod.yml up -d

# 3. 查看日志
docker-compose -f docker-compose.prod.yml logs -f
```

**服务地址：**
- Backend: http://localhost:8000
- Frontend: http://localhost:8001

## 配置说明

### 必填配置

| 配置项 | 说明 |
|--------|------|
| POSTGRES_PASSWORD | PostgreSQL 密码 |
| REDIS_PASSWORD | Redis 密码 (Staging/Production) |
| ALIYUN_ACCESS_KEY_ID | 阿里云 AccessKey ID |
| ALIYUN_ACCESS_KEY_SECRET | 阿里云 AccessKey Secret |
| ALIYUN_SMS_TEMPLATE_CODE | 短信模板 Code |

### 可选配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| POSTGRES_USER | shrimp | PostgreSQL 用户名 |
| POSTGRES_DB | shrimp_market | 数据库名 |
| SERVER_NODE_NAME | node-1 | 服务器节点名 |
| WS_PING_INTERVAL | 30 | WebSocket 心跳间隔(秒) |

## 常用命令

```bash
# 查看容器状态
docker-compose -f docker-compose.dev.yml ps

# 停止服务
docker-compose -f docker-compose.dev.yml down

# 停止并删除数据卷
docker-compose -f docker-compose.dev.yml down -v

# 查看后端日志
docker logs shrimp-backend-staging -f

# 进入数据库容器
docker exec -it shrimp-postgres-dev psql -U shrimp -d shrimp_market_dev
```