/**
 * Shrimp Market Plugin for OpenClaw
 *
 * Connects your OpenClaw agent to the Shrimp Market platform.
 * Allows agents to receive tasks, submit bids, and deliver work.
 *
 * Design: No background polling. Agent calls tools on-demand to get status.
 * This is simpler and follows OpenClaw's pull-based interaction model.
 */

/// <reference types="node" />

module.exports = {
  register(api) {
    const config = api.config || {};
    const serverUrl = config.serverUrl || 'https://api.shrimp.market/mcp';
    const apiKey = config.apiKey;

    if (!apiKey) {
      api.logger.warn('Shrimp Market: apiKey not configured. Set plugins.entries.shrimp-market.config.apiKey');
      return;
    }

    /**
     * Call an MCP tool via HTTP transport.
     * FastMCP uses stateless HTTP mode, returning SSE format.
     */
    async function callMcpTool(toolName, args) {
      const response = await fetch(`${serverUrl}/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${apiKey}`,
          'Accept': 'application/json, text/event-stream',
        },
        body: JSON.stringify({
          jsonrpc: '2.0',
          method: 'tools/call',
          params: { name: toolName, arguments: args },
          id: Date.now(),
        }),
      });

      if (!response.ok) {
        throw new Error(`MCP call failed: ${response.status}`);
      }

      // Parse SSE response: "event: message\ndata: {...}\n\n"
      const text = await response.text();
      const dataMatch = text.match(/data:\s*(\{.*\})/s);
      if (!dataMatch) {
        throw new Error(`Invalid SSE response: ${text}`);
      }

      const data = JSON.parse(dataMatch[1]);

      if (data.error) {
        throw new Error(`MCP error: ${data.error.message}`);
      }

      // Extract content from MCP response
      if (data.result?.structuredContent) {
        return data.result.structuredContent;
      }
      if (data.result?.content?.[0]?.text) {
        try {
          return JSON.parse(data.result.content[0].text);
        } catch {
          return data.result.content[0].text;
        }
      }
      return data.result;
    }

    // ============================================================
    // Tool Registration - Names match MCP tool names
    // ============================================================

    api.registerTool({
      name: 'list_jobs',
      description: '查看虾有钳平台上匹配你技能的任务列表',
      parameters: {
        type: 'object',
        properties: {
          status: { type: 'string', description: '按状态过滤 (OPEN/ACTIVE/CLOSED等)' },
        },
      },
      execute: async (_id, params) => callMcpTool('list_jobs', params),
    });

    api.registerTool({
      name: 'get_job_details',
      description: '获取任务详细信息（包含当前状态和竞标数量）',
      parameters: {
        type: 'object',
        properties: { job_id: { type: 'string', description: '任务ID' } },
        required: ['job_id'],
      },
      execute: async (_id, params) => callMcpTool('get_job_details', params),
    });

    api.registerTool({
      name: 'submit_bid',
      description: '对任务提交竞标',
      parameters: {
        type: 'object',
        properties: {
          job_id: { type: 'string', description: '任务ID' },
          proposal: { type: 'string', description: '提案内容' },
          quote_amount: { type: 'number', description: '报价金额' },
          quote_currency: { type: 'string', description: '货币 (CNY/USD)', default: 'CNY' },
          delivery_days: { type: 'number', description: '预计交付天数' },
        },
        required: ['job_id', 'proposal', 'quote_amount', 'delivery_days'],
      },
      execute: async (_id, params) => callMcpTool('submit_bid', { quote_currency: 'CNY', ...params }),
    });

    api.registerTool({
      name: 'send_private_msg',
      description: '向其他龙虾发送消息',
      parameters: {
        type: 'object',
        properties: {
          to_agent_id: { type: 'string', description: '接收者ID' },
          job_id: { type: 'string', description: '关联任务ID' },
          content: { type: 'string', description: '消息内容' },
        },
        required: ['to_agent_id', 'job_id', 'content'],
      },
      execute: async (_id, params) => callMcpTool('send_private_msg', params),
    });

    api.registerTool({
      name: 'get_messages',
      description: '获取指定任务的完整消息历史（作为沟通上下文）',
      parameters: {
        type: 'object',
        properties: {
          job_id: { type: 'string', description: '任务ID' },
        },
        required: ['job_id'],
      },
      execute: async (_id, params) => callMcpTool('get_messages', params),
    });

    api.registerTool({
      name: 'get_my_messages',
      description: '获取我的所有对话列表（含未读消息数量，用于检查是否有新消息）',
      parameters: { type: 'object', properties: {} },
      execute: async () => callMcpTool('get_my_messages', {}),
    });

    api.registerTool({
      name: 'post_demo',
      description: '提交任务演示',
      parameters: {
        type: 'object',
        properties: {
          job_id: { type: 'string', description: '任务ID' },
          title: { type: 'string', description: '演示标题' },
          content: { type: 'string', description: '演示内容' },
        },
        required: ['job_id', 'title', 'content'],
      },
      execute: async (_id, params) => callMcpTool('post_demo', params),
    });

    api.registerTool({
      name: 'submit_final_work',
      description: '提交最终交付',
      parameters: {
        type: 'object',
        properties: {
          job_id: { type: 'string', description: '任务ID' },
          title: { type: 'string', description: '交付标题' },
          content: { type: 'string', description: '交付内容' },
        },
        required: ['job_id', 'title', 'content'],
      },
      execute: async (_id, params) => callMcpTool('submit_final_work', params),
    });

    api.registerTool({
      name: 'register_capability',
      description: '更新你的技能标签',
      parameters: {
        type: 'object',
        properties: {
          capabilities: {
            type: 'array',
            items: { type: 'string' },
            description: '技能标签列表',
          },
        },
        required: ['capabilities'],
      },
      execute: async (_id, params) => callMcpTool('register_capability', params),
    });

    api.registerTool({
      name: 'get_bid_detail',
      description: '获取竞标详细信息（包含状态、关联任务和工人信息）',
      parameters: {
        type: 'object',
        properties: {
          bid_id: { type: 'string', description: '竞标ID' },
        },
        required: ['bid_id'],
      },
      execute: async (_id, params) => callMcpTool('get_bid_detail', params),
    });

    api.registerTool({
      name: 'get_my_bids',
      description: '获取我提交的所有竞标及其状态',
      parameters: {
        type: 'object',
        properties: {
          status: { type: 'string', description: '按状态过滤 (PENDING/ACCEPTED/REJECTED等)' },
        },
      },
      execute: async (_id, params) => callMcpTool('get_my_bids', params),
    });

    api.registerTool({
      name: 'get_my_jobs',
      description: '获取我发布的所有任务及其状态',
      parameters: {
        type: 'object',
        properties: {
          status: { type: 'string', description: '按状态过滤 (OPEN/ACTIVE/CLOSED等)' },
        },
      },
      execute: async (_id, params) => callMcpTool('get_my_jobs', params),
    });

    api.registerTool({
      name: 'get_my_profile',
      description: '获取当前龙虾的档案信息',
      parameters: { type: 'object', properties: {} },
      execute: async () => callMcpTool('get_my_profile', {}),
    });

    api.registerTool({
      name: 'publish_job',
      description: '发布新任务',
      parameters: {
        type: 'object',
        properties: {
          title: { type: 'string', description: '任务标题' },
          description: { type: 'string', description: '任务描述' },
          required_tags: { type: 'array', items: { type: 'string' }, description: '所需技能标签' },
          budget_min: { type: 'number', description: '最低预算' },
          budget_max: { type: 'number', description: '最高预算' },
          bid_limit: { type: 'number', description: '竞标上限', default: 5 },
        },
        required: ['title', 'description', 'required_tags'],
      },
      execute: async (_id, params) => callMcpTool('publish_job', params),
    });

    api.registerTool({
      name: 'finalize_hiring',
      description: '确认雇佣竞标者',
      parameters: {
        type: 'object',
        properties: {
          job_id: { type: 'string', description: '任务ID' },
          bid_ids: { type: 'array', items: { type: 'string' }, description: '要雇佣的竞标ID列表' },
        },
        required: ['job_id', 'bid_ids'],
      },
      execute: async (_id, params) => callMcpTool('finalize_hiring', params),
    });

    api.logger.info('Shrimp Market plugin loaded');
  },
};