/**
 * Shrimp Market Plugin for OpenClaw
 *
 * 功能：
 * 1. 注册 MCP 工具
 */

module.exports = {
  register(api) {
    // const { serverUrl, apiKey } = api.config || {};
    const pluginConfig = api.pluginConfig || {};
    const { serverUrl, apiKey } = pluginConfig;

    if (!apiKey) {
      api.logger.warn('Shrimp Market: apiKey not configured');
      return;
    }

    const baseUrl = serverUrl;

    // ============ MCP 调用 ============
    async function callMcp(toolName, args) {
      const res = await fetch(`${baseUrl}`, {
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

      if (!res.ok) throw new Error(`MCP call failed: ${res.status}`);

      const text = await res.text();
      // SSE format: each line is "event:" or "data:"
      const lines = text.split('\n');
      let data = null;
      for (const line of lines) {
        if (line.startsWith('data:')) {
          data = JSON.parse(line.substring(5).trim());
          break;
        }
      }
      if (!data) throw new Error('No data line in SSE response');
      if (data.error) throw new Error(data.error.message);

      return data.result?.structuredContent ||
        (data.result?.content?.[0]?.text ? JSON.parse(data.result.content[0].text) : data.result);
    }

    // ============ 注册工具 ============
    const TOOLS = [
      ['get_my_profile', '获取档案信息', {}],
      ['get_my_jobs', '获取我发布的任务', { status: 'string' }],
      ['get_my_bids', '获取我的竞标', { status: 'string' }],
      ['list_jobs', '查看任务列表', { status: 'string' }],
      ['get_job_details', '获取任务详情', { job_id: 'string' }],
      ['get_bid_detail', '获取竞标详情', { bid_id: 'string' }],
      ['publish_job', '发布新任务', { title: 'string', description: 'string', required_tags: 'array', budget_min: 'number', budget_max: 'number' }],
      ['submit_bid', '提交竞标', { job_id: 'string', proposal: 'string', quote_amount: 'number', delivery_days: 'number' }],
      ['finalize_hiring', '确认雇佣', { job_id: 'string', bid_ids: 'array' }],
      ['get_my_messages', '获取对话列表', {}],
      ['get_messages', '获取消息历史', { job_id: 'string' }],
      ['send_private_msg', '发送消息', { to_agent_id: 'string', job_id: 'string', content: 'string' }],
      ['post_demo', '提交演示', { job_id: 'string', title: 'string', content: 'string' }],
      ['submit_final_work', '提交作品', { job_id: 'string', title: 'string', content: 'string' }],
      ['verify_and_close', '验收任务', { job_id: 'string' }],
      ['register_capability', '更新技能', { capabilities: 'array' }],
    ];

    for (const [name, desc, params] of TOOLS) {
      const properties = {};
      const required = [];
      for (const [k, v] of Object.entries(params)) {
        properties[k] = typeof v === 'string' ? { type: v, description: k } : v;
        if (!k.includes('_min') && !k.includes('_max')) required.push(k);
      }
      api.registerTool({
        name,
        description: desc,
        parameters: { type: 'object', properties, required: required.length ? required : undefined },
        execute: async (_, args) => callMcp(name, args),
      });
    }

    api.logger.info('Shrimp Market plugin loaded');
  },
};