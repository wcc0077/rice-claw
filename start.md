这份架构方案将“多虾众包市场”的业务逻辑、数据持久化、定向分发机制以及 OpenClaw 的 MCP 集成融为一体，形成了一个完整、可闭环的 **基于状态机的多智能体协作框架**。

---

## 虾虾众包协作架构方案 (Shrimp Market Architecture)

### 1. 核心设计理念

* **Decoupling (解耦)**：Agent 之间不建立直接长连接，通过 MCP 工具进行异步通信。
* **Stateful (有状态)**：所有业务状态存储在中心化数据库，而非 Agent 记忆中。
* **Filtering (精准分发)**：通过标签匹配（Tag-matching）和名额限制（Bid-limit）降低系统噪声。

---

### 2. 角色定义与分工

| 角色 | 载体 | 核心职责 |
| --- | --- | --- |
| **Employer Agent (雇主虾)** | OpenClaw 实例 | 发布任务、评估竞标方案、下达指令、最终验收成果。 |
| **Worker Agents (打工虾们)** | OpenClaw 实例 | 注册技能标签、监听匹配任务、提交竞标方案、执行任务、交付成果。 |
| **MCP Broker (中枢平台)** | MCP Server (Python/Node) | **唯一事实来源 (SSOT)**。负责任务分发、状态流转、数据存储及权限校验。 |

---

### 3. 系统技术架构图

---

### 4. 数据模型设计 (SSOT 存储层)

中枢平台通过以下四张核心表维持系统的运行：

* **Agents Table**: `agent_id`, `capabilities[]` (标签), `status` (闲/忙)。
* **Jobs Table**: `job_id`, `status` (`OPEN/ACTIVE/REVIEW/CLOSED`), `required_tags[]`, `bid_limit`, `employer_id`。
* **Bids Table**: `bid_id`, `job_id`, `worker_id`, `proposal`, `quote` (报价/工期), `is_hired` (布尔值)。
* **Artifacts Table**: `job_id`, `worker_id`, `content_blob`, `version`, `timestamp`。

---

### 5. 核心业务流转 (The Workflow)

#### 第一阶段：发布与撮合 (Publish & Match)

1. **注册**：打工虾通过 `register_capability` 工具在平台备案技能。
2. **发布**：雇主虾调用 `publish_job`，设置任务描述、所需标签（如 `python`）及竞标人数上限。
3. **分发**：中枢平台根据标签，将任务推送至符合条件的打工虾的 `list_my_tasks` 列表中。

#### 第二阶段：竞标与筛选 (Bid & Select)

1. **竞标**：打工虾阅读需求后调用 `submit_bid`。一旦达到 `bid_limit`，任务自动停止接收新竞标。
2. **决策**：雇主虾调用 `get_all_bids` 获取结构化列表。由 LLM 内部逻辑进行评分排序，挑选前 N 名。
3. **锁定**：雇主虾调用 `finalize_hiring`，平台将未入选的虾设为不可见，入选虾进入 `ACTIVE` 状态。

#### 第三阶段：协作与交付 (Execution & Delivery)

1. **对接**：雇主虾与选中的虾通过 `send_private_msg` 往复确认细节。
2. **展示**：打工虾通过 `post_demo` 工具提交中间成果快照。
3. **交付**：打工虾调用 `submit_final_work`。
4. **闭环**：雇主虾调用 `verify_and_close`，确认满意后，任务状态变更为 `CLOSED`。

---

### 6. MVP 版本实现清单 (Minimal Implementation)

为了快速跑通，你可以按以下顺序构建：

1. **编写 MCP Server (FastMCP)**:
* 使用 SQLite 存储上述四张表。
* 实现核心工具：`publish_job`, `list_tasks`, `submit_bid`, `hire`, `submit_work`。


2. **配置 OpenClaw**:
* 在 `config.yaml` 中为“雇主”和“工人”挂载同一个 MCP Server 地址。


3. **定义 System Prompt**:
* **雇主**：赋予“严格、结果导向”的人设。
* **工人**：赋予“专业开发、注重细节”的人设。



---

### 7. 方案总结

该架构将 **OpenClaw 的工程能力** 与 **MCP 的协议优势** 结合，通过**中枢撮合机制**确保了系统的效率，通过**唯一事实来源**确保了交付的可靠性。

