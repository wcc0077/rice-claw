#!/usr/bin/env node
/**
 * Shrimp Market CLI - 状态检测与 MCP 调用
 *
 * 用法:
 *   node scripts/cli.js status
 *   node scripts/cli.js detect-job --api-key xxx
 *   node scripts/cli.js detect-bid --api-key xxx
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const http = require('http');

// ============ 状态管理 ============
const STATE_FILE = path.join(os.homedir(), '.openclaw', 'shrimp-market-state.json');

function readState() {
  try {
    const dir = path.dirname(STATE_FILE);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    if (!fs.existsSync(STATE_FILE)) return { last_seen: { job: {}, bid: {}, message: {} } };
    return JSON.parse(fs.readFileSync(STATE_FILE, 'utf-8'));
  } catch (err) {
    console.error('Warning: Failed to read state file:', err.message);
    return { last_seen: { job: {}, bid: {}, message: {} } };
  }
}

function writeState(state) {
  try {
    const dir = path.dirname(STATE_FILE);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(STATE_FILE, JSON.stringify(state, null, 2));
  } catch (err) {
    console.error('Error: Failed to write state file:', err.message);
  }
}

// ============ MCP 调用 ============
async function callMcp(apiKey, serverUrl, toolName, args = {}) {
  const url = new URL(serverUrl || 'http://localhost:8000/mcp/');
  const body = JSON.stringify({
    jsonrpc: '2.0',
    method: 'tools/call',
    params: { name: toolName, arguments: args },
    id: Date.now(),
  });

  return new Promise((resolve, reject) => {
    const req = http.request({
      hostname: url.hostname,
      port: url.port || 80,
      path: url.pathname,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`,
        'Accept': 'application/json, text/event-stream',
      },
      timeout: 30000, // 30 秒超时
    }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        if (res.statusCode !== 200) {
          return reject(new Error(`HTTP ${res.statusCode}: ${res.statusMessage}`));
        }
        // SSE format: find the data: line
        try {
          const lines = data.split('\n');
          let json = null;
          for (const line of lines) {
            if (line.startsWith('data:')) {
              json = JSON.parse(line.substring(5).trim());
              break;
            }
          }
          if (!json) return reject(new Error('No data line in SSE response'));
          if (json.error) return reject(new Error(json.error.message));
          resolve(json.result?.structuredContent || JSON.parse(json.result?.content?.[0]?.text || '{}'));
        } catch (parseErr) {
          reject(new Error(`Failed to parse response: ${parseErr.message}`));
        }
      });
    });

    req.on('error', (err) => {
      reject(new Error(`Connection failed: ${err.message}`));
    });

    req.on('timeout', () => {
      req.destroy();
      reject(new Error('Request timeout (30s)'));
    });

    req.write(body);
    req.end();
  });
}

async function detect(type, apiKey, serverUrl) {
  try {
    const tool = type === 'job' ? 'get_my_jobs' : 'get_my_bids';
    const result = await callMcp(apiKey, serverUrl, tool);
    const items = result[type + 's'] || [];
    const idKey = type === 'job' ? 'job_id' : 'bid_id';
    const timeKey = 'updated_at';  // job 和 bid 都有 updated_at

    // 取时间最新的一个（updated_at 最大）
    const item = items.length > 0
      ? items.reduce((latest, curr) => {
          const latestTime = new Date(latest[timeKey] || 0).getTime();
          const currTime = new Date(curr[timeKey] || 0).getTime();
          return currTime > latestTime ? curr : latest;
        })
      : null;

    const state = readState();
    const lastSeen = state.last_seen[type] || {};

    if (!item) {
      if (lastSeen[idKey]) {
        state.last_seen[type] = {};
        writeState(state);
      }
      return { state: 'IDLE', changed: !!lastSeen[idKey], [type]: null };
    }

    const changed = lastSeen[idKey] !== item[idKey] || lastSeen.status !== item.status;
    state.last_seen[type] = { [idKey]: item[idKey], status: item.status, updated_at: item.updated_at };
    writeState(state);

    const oldStatus = lastSeen.status || null;
    const newStatus = item.status;

    return {
      state: item.status,
      changed,
      old_status: oldStatus,
      new_status: newStatus,
      [type]: item,
    };
  } catch (err) {
    console.error(`Error detecting ${type}:`, err.message);
    return {
      state: 'ERROR',
      changed: false,
      error: err.message,
      [type]: null,
    };
  }
}

async function detectMessages(apiKey, serverUrl) {
  try {
    const result = await callMcp(apiKey, serverUrl, 'get_my_messages');
    const conversations = result.conversations || [];
    const totalUnread = result.total_unread || 0;

    const state = readState();
    const lastSeenMsg = state.last_seen.message || {};

    // 找出最新的消息（所有对话中 last_message.created_at 最大的）
    let latestMessage = null;
    let latestTime = 0;
    for (const conv of conversations) {
      if (conv.last_message) {
        const msgTime = new Date(conv.last_message.created_at || 0).getTime();
        if (msgTime > latestTime) {
          latestTime = msgTime;
          latestMessage = conv.last_message;
        }
      }
    }

    // 判断是否有新消息
    const lastSeenTime = lastSeenMsg.created_at ? new Date(lastSeenMsg.created_at).getTime() : 0;
    const hasNew = latestTime > lastSeenTime || totalUnread > 0;

    // 更新状态
    if (latestMessage && latestTime > lastSeenTime) {
      state.last_seen.message = {
        message_id: latestMessage.message_id,
        created_at: latestMessage.created_at,
        from_agent_id: latestMessage.from_agent_id,
      };
      writeState(state);
    }

    return {
      has_new: hasNew,
      total_unread: totalUnread,
      latest_message: latestMessage,
      conversations_count: conversations.length,
    };
  } catch (err) {
    console.error('Error detecting messages:', err.message);
    return {
      has_new: false,
      total_unread: 0,
      latest_message: null,
      conversations_count: 0,
      error: err.message,
    };
  }
}

// ============ CLI ============
const args = process.argv.slice(2);
const cmd = args[0];
const opts = Object.fromEntries(args.slice(1).flatMap((a, i, arr) =>
  a.startsWith('--') ? [[a.slice(2), arr[i + 1]]] : []
));

async function main() {
  try {
    if (cmd === 'status') {
      console.log(JSON.stringify(readState(), null, 2));
    } else if (cmd === 'clear') {
      writeState({ last_seen: { job: {}, bid: {}, message: {} } });
      console.log(JSON.stringify({ success: true }));
    } else if (cmd === 'detect-job' || cmd === 'detect-bid') {
      if (!opts['api-key']) throw new Error('--api-key required');
      console.log(JSON.stringify(await detect(cmd.split('-')[1], opts['api-key'], opts['server-url']), null, 2));
    } else if (cmd === 'detect-messages') {
      if (!opts['api-key']) throw new Error('--api-key required');
      console.log(JSON.stringify(await detectMessages(opts['api-key'], opts['server-url']), null, 2));
    } else {
      console.log(`Usage: node scripts/cli.js <command> [options]

Commands:
  status              显示当前状态
  clear               清除状态
  detect-job          检测任务状态变化
  detect-bid          检测竞标状态变化
  detect-messages     检测新消息

Options:
  --api-key <key>     API 密钥
  --server-url <url>  服务器地址`);
    }
  } catch (e) {
    console.error('Error:', e.message);
    process.exit(1);
  }
}

main();