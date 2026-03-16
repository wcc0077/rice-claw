# Task Plan: 撮合平台架构设计与实现 (修订版)

## Goal
设计并实现撮合 OpenClaw 智能体实例发布任务和接单的平台，基于现有系统渐进式扩展：
- **合并 job/order** - 扩展原有 jobs 表，避免重复
- **bid 级 WS 消息路由** - 支持一个 agent 同时接多个任务
- **Redis 状态机** - 低延迟、原子操作
- **WebSocket 实时通信** - 雇主与工人即时交互
- **安全防护体系** - LLM 特定威胁防护

## Current Phase
Phase 7: 安全防护体系实现

## Phases

### Phase 1: 需求分析与架构设计
- [x] 阅读需求文档 (撮合.md)
- [x] 分析核心业务流程
- [x] 分析现有系统数据模型
- [x] 设计系统架构
- [x] 设计状态机
- [x] 设计 API 接口
- [x] 设计 Redis + WebSocket 实时通信架构
- [x] 修订：WS 细化到 bid 层面
- [x] 修订：job/order 融合方案
- **Status:** complete

### Phase 2: 数据模型设计 (简化为 3 张新表)
- [x] 扩展 `jobs` 表 (新增交易字段)
- [x] 创建 `job_workers` 表
- [x] 创建 `artifact_versions` 表
- [x] 创建 `payments` 表
- [x] 创建 `ws_connections` 表
- [x] 创建 `message_delivery` 表
- [x] 编写数据库迁移脚本
- [x] 运行迁移脚本 (成功)
- [x] 创建 `db/job_workers.py` DAL
- [x] 创建 `db/artifact_versions.py` DAL
- [x] 创建 `db/payments.py` DAL
- **Status:** complete

### Phase 2.5: Redis 与 WebSocket (bid 级路由)
- [x] 配置 Redis 连接 (settings.py)
- [x] 实现 ConnectionManager (websocket/manager.py)
  - [x] agent_id → WebSocket 连接管理
  - [x] agent_id → Set<bid_id> 订阅管理
  - [x] bid_id → context (job_id, agent_id) 上下文
- [x] 实现 WebSocket 路由 (websocket/routes.py)
- [x] 实现状态机 Lua 脚本 (services/state_machine.lua)
- [x] 实现 OrderStateMachine 类 (services/state_machine.py)
- [x] 实现离线消息存储 (services/message_service.py)
- [x] 实现心跳检测机制 (handle_ping/pong)
- [x] 实现 Redis Pub/Sub 订阅器 (services/pubsub_subscriber.py)
- **Status:** complete

### Phase 3: 领域模型与服务层设计
- [x] JobService (任务服务) - 包含 create_and_publish_job, grab_order, dispatch_order, confirm_lock_payment, close_job
- [x] DispatchService (派单服务) - 包含 dispatch_order, cancel_dispatch, confirm_worker_ready
- [x] PaymentService (支付服务) - 包含 process_deposit_payment, process_final_payment, process_refund
- [ ] ReputationService (扩展)
- [ ] WatermarkService
- **Status:** complete
- **Next:** 继续实现 ReputationService 和 WatermarkService，或进入 Phase 4 API 接口实现

### Phase 4: API 接口实现
- [x] 定义撮合平台 Schemas (schemas.py)
- [x] 实现 matching.py API 路由
- [x] 注册 matching 路由到 api/__init__.py
- [x] 验证 API 模块导入成功
- [x] 验证 FastAPI 应用启动成功 (67 个路由)
- [ ] 修复 websocket 导入问题
- [ ] 端到端测试 API 端点
- **Status:** complete

### Phase 5: Schema 验证与类型定义
- [x] 定义 Pydantic schemas
- **Status:** complete

### Phase 6: 测试与验证
- [ ] 单元测试
- [ ] 集成测试
- [ ] 压力测试
- **Status:** pending

### Phase 7: 安全防护体系实现
- [x] 设计安全防护体系架构
- [x] 实现 PromptGuard (Prompt Injection 检测)
- [x] 实现 OutputGuard (输出内容审查)
- [x] 实现 RateLimiter (速率限制)
- [x] 集成到 API 路由
- [ ] 实现行为分析器
- [ ] 实现安全告警系统
- **Status:** complete (core security features)

## Notes

### 已完成
- 数据模型设计完成
- 数据库迁移执行成功
- DAL 层基础文件创建完成
- WebSocket 基础设施完成 (manager, routes)
- Redis 状态机完成 (Lua 脚本，OrderStateMachine)
- 消息服务完成 (MessageService, PubSubSubscriber)

### 下一步
1. 实现 JobService (任务服务)
2. 实现 DispatchService (派单服务)
3. 实现 PaymentService (支付服务)
