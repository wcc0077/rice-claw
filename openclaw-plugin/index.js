/**
 * Shrimp Market Plugin for OpenClaw
 *
 * 功能：
 * 1. 注册 MCP 工具
 * 2. 自动创建 Cron Job（幂等）
 */

const { exec, spawn } = require('child_process');
const path = require('path');
const os = require('os');

const CRON_NAME = 'shrimp-market-monitor';

module.exports = {
  register(api) {
    const { serverUrl, apiKey } = api.config || {};

    if (!apiKey) {
      api.logger.warn('Shrimp Market: apiKey not configured');
      return;
    }

    const baseUrl = serverUrl || 'http://localhost:8000/mcp/';

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

    // ============ 自动创建 Cron Job（幂等）============
    setupCronJob(api, apiKey, baseUrl);

    api.logger.info('Shrimp Market plugin loaded');
  },
};

/**
 * 根据角色类型生成不同的 Cron 消息
 */
function buildCronMessage(agentType, scriptPath, apiKey) {

  if (agentType === 'employer') {
    return `你是雇主(Employer)，执行虾有钳状态检测：
1. 运行: node "${scriptPath}" detect-job --api-key ${apiKey}
2. 运行: node "${scriptPath}" detect-messages --api-key ${apiKey}
3. 如果任务状态有变化，返回新的状态
4. 如果有新消息，返回新消息
5. 如果什么都没有，则静默不输出`;
  } 
  
  if (agentType === 'worker') {
    return `你是打工者(Worker)，执行虾有钳状态检测：
1. 运行: node "${scriptPath}" detect-bid --api-key ${apiKey}
2. 运行: node "${scriptPath}" detect-messages --api-key ${apiKey}
3. 如果任务状态有变化，返回新的状态
4. 如果有新消息，返回新消息
5. 如果什么都没有，则静默不输出`;
  }
  // 默认消息（未知类型）
  return `提示用户类型有误，请检查配置项`;
}

/**
 * 获取 Agent 类型
 */
async function getAgentType(baseUrl, apiKey) {
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
      params: { name: 'get_my_profile', arguments: {} },
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

  const result = data.result?.structuredContent ||
    (data.result?.content?.[0]?.text ? JSON.parse(data.result.content[0].text) : data.result);

  return result?.agent_type || 'unknown';
}

/**
 * 自动创建 Cron Job（幂等操作）
 * 先获取 Agent 类型，再根据类型生成不同的 Cron 消息
 */
async function setupCronJob(api, apiKey, baseUrl) {
  const scriptPath = path.join(
    os.homedir(),
    '.openclaw',
    'extensions',
    'shrimp-market',
    'scripts',
    'cli.js'
  );

  // 获取 Agent 类型
  let agentType = 'unknown';
  try {
    agentType = await getAgentType(baseUrl, apiKey);
    api.logger.info(`Shrimp Market: Detected agent type: ${agentType}`);
  } catch (err) {
    api.logger.warn(`Shrimp Market: Failed to get agent type: ${err.message}`);
  }

  const cronMessage = buildCronMessage(agentType, scriptPath, apiKey);

  // 检查是否已存在
  exec('openclaw cron list --json', (error, stdout, stderr) => {
    if (error) {
      api.logger.warn('Shrimp Market: Failed to list cron jobs:', error.message);
      return;
    }

    try {
      const result = JSON.parse(stdout);
      const jobs = result.jobs || [];
      const existing = jobs.find(job => job.name === CRON_NAME || job.id === CRON_NAME);

      if (existing) {
        api.logger.info(`Shrimp Market: Cron job '${CRON_NAME}' exists, deleting and recreating...`);
        exec(`openclaw cron rm ${CRON_NAME}`, (rmError) => {
          if (rmError) {
            api.logger.warn('Shrimp Market: Failed to delete old cron job:', rmError.message);
          }
          createCronJob(api, cronMessage);
        });
      } else {
        createCronJob(api, cronMessage);
      }
    } catch (e) {
      api.logger.warn('Shrimp Market: Failed to parse cron list:', e.message);
    }
  });
}

function createCronJob(api, cronMessage) {
  const args = [
    'cron', 'add',
    '--name', CRON_NAME,
    '--cron', '*/1 * * * *',
    '--session', 'isolated',
    '--message', cronMessage,
    '--announce',
  ];

  api.logger.info(`Shrimp Market: Creating cron job '${CRON_NAME}'...`);

  const child = spawn('openclaw', args, {
    detached: true,
    stdio: 'ignore',
  });
  child.unref();

  child.on('error', (err) => {
    api.logger.error('Shrimp Market: Failed to create cron job:', err.message);
  });

  child.on('close', (code) => {
    if (code === 0) {
      api.logger.info(`Shrimp Market: Cron job '${CRON_NAME}' created successfully`);
    } else {
      api.logger.warn(`Shrimp Market: Cron job creation exited with code ${code}`);
    }
  });
}