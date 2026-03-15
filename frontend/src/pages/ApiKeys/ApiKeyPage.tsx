import { useState, useCallback, memo } from 'react'
import { Table, Space, Typography, Input, Button, Modal, message, Avatar, Tooltip, Tag, Popconfirm } from 'antd'
import type { TableColumnsType } from 'antd'
import {
  KeyOutlined,
  UserOutlined,
  ReloadOutlined,
  SearchOutlined,
  CrownOutlined,
  ThunderboltOutlined,
  SafetyCertificateOutlined,
  ClockCircleOutlined,
  DeleteOutlined,
  SyncOutlined,
  PlusOutlined,
  CopyOutlined,
  CheckOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons'
import { agentApi } from '@/services/api'
import { useAsyncEffect } from '@/hooks/useFetchOnce'

const { Search } = Input
const { Title, Text, Paragraph } = Typography

interface AgentWithKey {
  agent_id: string
  agent_type: 'employer' | 'worker' | 'all'
  name: string
  capabilities: string[]
  status: string
  rating: number
  completed_jobs: number
  has_api_key?: boolean
  api_key_created_at?: string
  last_seen_at?: string
  is_verified?: boolean
}

/**
 * AgentTypeBadge - Visual indicator for agent type
 */
const AgentTypeBadge = memo(({ type }: { type: string }) => {
  const isEmployer = type === 'employer'
  const isWorker = type === 'worker'
  const isAll = type === 'all'
  return (
    <Tag
      className={`${
        isEmployer
          ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20'
          : isWorker
            ? 'bg-purple-500/10 text-purple-400 border-purple-500/20'
            : 'bg-green-500/10 text-green-400 border-green-500/20'
      } border`}
    >
      {isEmployer && <CrownOutlined className="mr-1" />}
      {isWorker && <ThunderboltOutlined className="mr-1" />}
      {isAll && <SafetyCertificateOutlined className="mr-1" />}
      {isEmployer ? '雇主' : isWorker ? '打工人' : '全能'}
    </Tag>
  )
})
AgentTypeBadge.displayName = 'AgentTypeBadge'

/**
 * KeyStatusBadge - Shows API key status
 */
const KeyStatusBadge = memo(({ agent }: { agent: AgentWithKey }) => {
  if (!agent.has_api_key) {
    return (
      <Tag className="bg-slate-500/10 text-slate-400 border-slate-500/20 border">
        <ExclamationCircleOutlined className="mr-1" />
        未配置
      </Tag>
    )
  }

  return (
    <Tag className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20 border">
      <SafetyCertificateOutlined className="mr-1" />
      已配置
      {agent.is_verified && (
        <Tooltip title="已验证">
          <CheckOutlined className="ml-1 text-emerald-300" />
        </Tooltip>
      )}
    </Tag>
  )
})
KeyStatusBadge.displayName = 'KeyStatusBadge'

/**
 * LastSeenDisplay - Shows last activity time
 */
const LastSeenDisplay = memo(({ lastSeenAt }: { lastSeenAt?: string }) => {
  if (!lastSeenAt) {
    return <span className="text-slate-500">-</span>
  }

  const date = new Date(lastSeenAt)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  let display: string
  let color: string

  if (diffMins < 5) {
    display = '刚刚'
    color = 'text-emerald-400'
  } else if (diffMins < 60) {
    display = `${diffMins}分钟前`
    color = 'text-emerald-400'
  } else if (diffHours < 24) {
    display = `${diffHours}小时前`
    color = 'text-amber-400'
  } else {
    display = `${diffDays}天前`
    color = 'text-slate-400'
  }

  return (
    <Tooltip title={date.toLocaleString('zh-CN')}>
      <span className={`${color} font-mono text-xs`}>
        <ClockCircleOutlined className="mr-1" />
        {display}
      </span>
    </Tooltip>
  )
})
LastSeenDisplay.displayName = 'LastSeenDisplay'

/**
 * ApiKeyPage - API Key management for agents
 */
const ApiKeyPage = () => {
  const [agents, setAgents] = useState<AgentWithKey[]>([])
  const [loading, setLoading] = useState(true)
  const [searchText, setSearchText] = useState('')
  const [newKeyModalOpen, setNewKeyModalOpen] = useState(false)
  const [newApiKey, setNewApiKey] = useState<string | null>(null)
  const [selectedAgent, setSelectedAgent] = useState<AgentWithKey | null>(null)
  const [copied, setCopied] = useState(false)

  const fetchAgents = useCallback(async () => {
    setLoading(true)
    try {
      const res = await agentApi.list()
      setAgents(res.data.agents || [])
    } catch (err) {
      console.error('Failed to fetch agents:', err)
      message.error('获取代理列表失败')
    } finally {
      setLoading(false)
    }
  }, [])

  useAsyncEffect(fetchAgents, [fetchAgents])

  const filteredAgents = agents.filter((agent) =>
    agent.name.toLowerCase().includes(searchText.toLowerCase()) ||
    agent.agent_id.toLowerCase().includes(searchText.toLowerCase())
  )

  // Statistics
  const stats = {
    total: agents.length,
    withKey: agents.filter((a) => a.has_api_key).length,
    verified: agents.filter((a) => a.is_verified).length,
    active: agents.filter((a) => a.last_seen_at && isNewerThan(a.last_seen_at, 24 * 60)).length,
  }

  const handleGenerateKey = async (agent: AgentWithKey) => {
    try {
      const res = await agentApi.generateApiKey(agent.agent_id)
      setNewApiKey(res.data.api_key)
      setSelectedAgent(agent)
      setNewKeyModalOpen(true)
      fetchAgents()
      message.success('API Key 生成成功')
    } catch (err) {
      message.error('生成 API Key 失败')
    }
  }

  const handleRegenerateKey = async (agent: AgentWithKey) => {
    try {
      const res = await agentApi.regenerateApiKey(agent.agent_id)
      setNewApiKey(res.data.api_key)
      setSelectedAgent(agent)
      setNewKeyModalOpen(true)
      fetchAgents()
      message.success('API Key 重新生成成功')
    } catch (err) {
      message.error('重新生成 API Key 失败')
    }
  }

  const handleRevokeKey = async (agent: AgentWithKey) => {
    try {
      await agentApi.revokeApiKey(agent.agent_id)
      fetchAgents()
      message.success('API Key 已撤销')
    } catch (err) {
      message.error('撤销 API Key 失败')
    }
  }

  const handleVerify = async (agent: AgentWithKey) => {
    try {
      await agentApi.verifyAgent(agent.agent_id)
      fetchAgents()
      message.success('代理已验证')
    } catch (err) {
      message.error('验证失败')
    }
  }

  const handleCopyKey = () => {
    if (newApiKey) {
      navigator.clipboard.writeText(newApiKey)
      setCopied(true)
      message.success('已复制到剪贴板')
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const columns: TableColumnsType<AgentWithKey> = [
    {
      title: '代理',
      key: 'agent',
      render: (_, record) => (
        <div className="flex items-center gap-3">
          <Avatar
            size={40}
            icon={<UserOutlined />}
            className={`bg-gradient-to-br ${
              record.agent_type === 'employer'
                ? 'from-cyan-500/20 to-cyan-600/10'
                : 'from-purple-500/20 to-purple-600/10'
            } border-2 border-slate-700`}
          />
          <div>
            <div className="flex items-center gap-2">
              <Text strong className="text-white">{record.name}</Text>
              <AgentTypeBadge type={record.agent_type} />
            </div>
            <Text className="text-xs text-slate-500 font-mono">{record.agent_id}</Text>
          </div>
        </div>
      ),
    },
    {
      title: 'API Key 状态',
      key: 'key_status',
      width: 140,
      render: (_, record) => <KeyStatusBadge agent={record} />,
    },
    {
      title: 'Key 创建时间',
      key: 'key_created',
      width: 160,
      render: (_, record) => {
        if (!record.api_key_created_at) {
          return <span className="text-slate-500">-</span>
        }
        return (
          <Tooltip title={new Date(record.api_key_created_at).toLocaleString('zh-CN')}>
            <span className="text-slate-300 text-xs font-mono">
              {new Date(record.api_key_created_at).toLocaleDateString('zh-CN')}
            </span>
          </Tooltip>
        )
      },
    },
    {
      title: '最后活动',
      key: 'last_seen',
      width: 130,
      render: (_, record) => <LastSeenDisplay lastSeenAt={record.last_seen_at} />,
    },
    {
      title: '操作',
      key: 'action',
      width: 280,
      render: (_, record) => (
        <Space size="small">
          {!record.has_api_key ? (
            <Button
              type="primary"
              size="small"
              icon={<PlusOutlined />}
              onClick={() => handleGenerateKey(record)}
              className="bg-cyan-500 hover:bg-cyan-400 border-0"
            >
              生成 Key
            </Button>
          ) : (
            <>
              <Button
                size="small"
                icon={<SyncOutlined />}
                onClick={() => handleRegenerateKey(record)}
                className="bg-slate-700/50 border-slate-600 text-slate-300 hover:text-white"
              >
                重新生成
              </Button>
              <Popconfirm
                title="确定要撤销此 API Key 吗？"
                description="撤销后代理将无法通过此 Key 进行认证"
                onConfirm={() => handleRevokeKey(record)}
                okText="确定"
                cancelText="取消"
                okButtonProps={{ danger: true }}
              >
                <Button
                  size="small"
                  danger
                  icon={<DeleteOutlined />}
                  className="bg-rose-500/10 border-rose-500/30 text-rose-400 hover:bg-rose-500/20"
                >
                  撤销
                </Button>
              </Popconfirm>
              {!record.is_verified && (
                <Tooltip title="标记代理为已验证">
                  <Button
                    size="small"
                    icon={<SafetyCertificateOutlined />}
                    onClick={() => handleVerify(record)}
                    className="bg-emerald-500/10 border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20"
                  >
                    验证
                  </Button>
                </Tooltip>
              )}
            </>
          )}
        </Space>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <Title level={3} className="text-white m-0 flex items-center gap-2">
            <KeyOutlined className="text-cyan-400" />
            密钥管理
          </Title>
          <Text className="text-slate-400">管理 OpenClaw 代理的 API Key 认证凭证</Text>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="glass-card p-4">
          <div className="flex items-center justify-between">
            <div>
              <Text className="text-xs text-slate-500 uppercase tracking-wider">总代理</Text>
              <div className="text-2xl font-bold text-white font-mono tabular-nums mt-1">
                {stats.total}
              </div>
            </div>
            <div className="w-10 h-10 rounded-xl bg-slate-700/50 flex items-center justify-center">
              <UserOutlined className="text-slate-400" />
            </div>
          </div>
        </div>
        <div className="glass-card p-4">
          <div className="flex items-center justify-between">
            <div>
              <Text className="text-xs text-slate-500 uppercase tracking-wider">已配置 Key</Text>
              <div className="text-2xl font-bold text-emerald-400 font-mono tabular-nums mt-1">
                {stats.withKey}
              </div>
            </div>
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center">
              <KeyOutlined className="text-emerald-400" />
            </div>
          </div>
        </div>
        <div className="glass-card p-4">
          <div className="flex items-center justify-between">
            <div>
              <Text className="text-xs text-slate-500 uppercase tracking-wider">已验证</Text>
              <div className="text-2xl font-bold text-cyan-400 font-mono tabular-nums mt-1">
                {stats.verified}
              </div>
            </div>
            <div className="w-10 h-10 rounded-xl bg-cyan-500/10 flex items-center justify-center">
              <SafetyCertificateOutlined className="text-cyan-400" />
            </div>
          </div>
        </div>
        <div className="glass-card p-4">
          <div className="flex items-center justify-between">
            <div>
              <Text className="text-xs text-slate-500 uppercase tracking-wider">24h 活跃</Text>
              <div className="text-2xl font-bold text-amber-400 font-mono tabular-nums mt-1">
                {stats.active}
              </div>
            </div>
            <div className="w-10 h-10 rounded-xl bg-amber-500/10 flex items-center justify-center">
              <ClockCircleOutlined className="text-amber-400" />
            </div>
          </div>
        </div>
      </div>

      {/* Warning Banner */}
      <div className="glass-card p-4 border-amber-500/30 bg-amber-500/5">
        <div className="flex items-start gap-3">
          <ExclamationCircleOutlined className="text-amber-400 text-lg mt-0.5" />
          <div>
            <Text strong className="text-amber-400 block">安全提示</Text>
            <Text className="text-slate-400 text-sm">
              API Key 仅在生成时显示一次，请立即复制并安全存储。重新生成会使旧 Key 失效。
              确认代理所有者已安全接收 Key 后，请点击"验证"按钮标记。
            </Text>
          </div>
        </div>
      </div>

      {/* Search Bar */}
      <div className="glass-card p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <Search
            placeholder="搜索代理ID或姓名..."
            allowClear
            enterButton={<><SearchOutlined /> 搜索</>}
            size="middle"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            className="flex-1"
            loading={loading}
          />
          <Button
            icon={<ReloadOutlined />}
            onClick={fetchAgents}
            loading={loading}
            className="bg-slate-800/50 border-slate-700 text-slate-300"
          >
            刷新
          </Button>
        </div>
      </div>

      {/* Agents Table */}
      <div className="glass-card p-6">
        <Table
          dataSource={filteredAgents}
          columns={columns}
          rowKey="agent_id"
          loading={loading}
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条记录`,
          }}
          className="api-keys-table"
          rowClassName="hover:bg-slate-800/30 transition-colors"
        />
      </div>

      {/* New API Key Modal */}
      <Modal
        title={
          <div className="flex items-center gap-2 text-white">
            <KeyOutlined className="text-cyan-400" />
            新 API Key 已生成
          </div>
        }
        open={newKeyModalOpen}
        onCancel={() => {
          setNewKeyModalOpen(false)
          setNewApiKey(null)
          setSelectedAgent(null)
        }}
        footer={
          <div className="flex justify-between">
            <Button
              onClick={() => {
                setNewKeyModalOpen(false)
                setNewApiKey(null)
                setSelectedAgent(null)
              }}
              className="bg-slate-700/50 border-slate-600"
            >
              关闭
            </Button>
            <Button
              type="primary"
              icon={copied ? <CheckOutlined /> : <CopyOutlined />}
              onClick={handleCopyKey}
              className="bg-cyan-500 hover:bg-cyan-400 border-0"
            >
              {copied ? '已复制' : '复制 Key'}
            </Button>
          </div>
        }
        width={600}
        className="api-key-modal"
      >
        <div className="space-y-4">
          <div className="p-4 rounded-lg bg-rose-500/10 border border-rose-500/30">
            <Text strong className="text-rose-400 block mb-1">
              重要：请立即复制并安全存储此 Key
            </Text>
            <Text className="text-slate-400 text-sm">
              关闭此对话框后将无法再次查看此 Key。请确保已将其安全传递给代理所有者。
            </Text>
          </div>

          {selectedAgent && (
            <div className="p-3 rounded-lg bg-slate-800/50">
              <Text className="text-slate-500 text-xs">代理</Text>
              <div className="flex items-center gap-2 mt-1">
                <Text strong className="text-white">{selectedAgent.name}</Text>
                <Text className="text-slate-500 font-mono text-xs">({selectedAgent.agent_id})</Text>
              </div>
            </div>
          )}

          <div className="p-4 rounded-lg bg-slate-800/50 border border-slate-700">
            <Text className="text-slate-500 text-xs block mb-2">API Key</Text>
            <div className="flex items-center gap-2">
              <Paragraph
                copyable={{ text: newApiKey || '' }}
                className="font-mono text-sm text-cyan-400 bg-slate-900/50 p-2 rounded border border-slate-700 m-0 flex-1 overflow-x-auto whitespace-nowrap"
              >
                {newApiKey}
              </Paragraph>
            </div>
          </div>

          <div className="flex items-center gap-2 text-sm text-slate-400">
            <ClockCircleOutlined />
            <span>创建时间：{new Date().toLocaleString('zh-CN')}</span>
          </div>
        </div>
      </Modal>
    </div>
  )
}

/**
 * Check if a date string is newer than X minutes ago
 */
function isNewerThan(dateStr: string, minutesAgo: number): boolean {
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = diffMs / 60000
  return diffMins < minutesAgo
}

export default ApiKeyPage