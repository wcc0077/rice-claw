-- Order State Machine Lua Script for Redis
-- 保证状态流转的原子性
--
-- KEYS[1] = order state key (e.g., "shrimp:order:{order_id}:state")
-- KEYS[2] = order info key (e.g., "shrimp:order:{order_id}:info")
-- KEYS[3] = pub/sub channel (e.g., "shrimp:channel:order_state")
--
-- ARGV[1] = expected current state (or "*" for any)
-- ARGV[2] = new state
-- ARGV[3] = order_id
-- ARGV[4] = timestamp
-- ARGV[5] = extra data (JSON, optional)

local state_key = KEYS[1]
local info_key = KEYS[2]
local channel = KEYS[3]

local expected_state = ARGV[1]
local new_state = ARGV[2]
local order_id = ARGV[3]
local timestamp = ARGV[4]
local extra_data = ARGV[5] or "{}"

-- 1. 获取当前状态
local current_state = redis.call("HGET", state_key, "current_state")

-- 2. 验证状态流转
if current_state == false then
    -- 状态不存在，返回错误
    return {0, "STATE_NOT_FOUND", current_state}
end

current_state = current_state[1] or current_state

-- 检查期望状态（* 表示接受任何状态）
if expected_state ~= "*" and current_state ~= expected_state then
    return {0, "STATE_MISMATCH", current_state}
end

-- 3. 验证状态流转合法性
local valid_transitions = {
    ["OPEN"] = {"ACTIVE", "CLOSED"},
    ["ACTIVE"] = {"REVIEW", "CLOSED", "CANCELLED"},
    ["REVIEW"] = {"CLOSED", "REJECTED"},
    ["CLOSED"] = {},  -- 终态
    ["CANCELLED"] = {},  -- 终态
    ["REJECTED"] = {},  -- 终态
}

local allowed = valid_transitions[current_state]
if not allowed then
    return {0, "INVALID_CURRENT_STATE", current_state}
end

local is_valid = false
for _, s in ipairs(allowed) do
    if s == new_state then
        is_valid = true
        break
    end
end

if not is_valid then
    return {0, "INVALID_TRANSITION", current_state .. " -> " .. new_state}
end

-- 4. 更新状态
redis.call("HSET", state_key, "current_state", new_state)
redis.call("HSET", state_key, "previous_state", current_state)
redis.call("HSET", state_key, "updated_at", timestamp)

-- 5. 更新 info 中的状态
if redis.call("EXISTS", info_key) == 1 then
    redis.call("HSET", info_key, "status", new_state, "updated_at", timestamp)
end

-- 6. 发布状态变更通知
local message = cjson.encode({
    order_id = order_id,
    previous_state = current_state,
    new_state = new_state,
    timestamp = timestamp,
    extra = cjson.decode(extra_data)
})
redis.call("PUBLISH", channel, message)

-- 7. 返回成功
return {1, "OK", current_state, new_state}
