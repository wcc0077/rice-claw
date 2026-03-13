import { useState, useEffect, useCallback, memo } from 'react'
import { Table, Space, Typography, Input, Button, Modal, Form, Select, message, Avatar, Tooltip } from 'antd'
import type { TableColumnsType } from 'antd'
import {
  PlusOutlined,
  UserOutlined,
  ThunderboltOutlined,
  CrownOutlined,
  StarOutlined,
  ReloadOutlined,
  SearchOutlined,
  CheckCircleOutlined,
  MinusCircleOutlined,
  SyncOutlined,
} from '@ant-design/icons'
import { Agent } from '@/types/agent'
import { agentApi } from '@/services/api'

const { Search } = Input
const { Title, Text } = Typography
const { Option } = Select

// Trust-focused agent status configuration
const agentStatusConfig = {
  idle: {
    label: '空闲',
    className: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    icon: <CheckCircleOutlined className="mr-1" />,
    description: '代理当前空闲，可接受任务',
    pulse: 'bg-emerald-400',
  },
  busy: {
    label: '工作中',
    className: 'bg-pink-500/10 text-pink-400 border-pink-500/20',
    icon: <SyncOutlined spin className="mr-1" />,
    description: '代理正在执行任务',
    pulse: 'bg-pink-400',
  },
  offline: {
    label: '离线',
    className: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
    icon: <MinusCircleOutlined className="mr-1" />,
    description: '代理当前离线',
    pulse: 'bg-slate-400',
  },
}

const agentTypeConfig = {
  employer: {
    label: '雇主',
    icon: <CrownOutlined />,
    color: 'text-cyan-400',
    bgColor: 'bg-cyan-500/10 border-cyan-500/20',
  },
  worker: {
    label: '打工人',
    icon: <ThunderboltOutlined />,
    color: 'text-purple-400',
    bgColor: 'bg-purple-500/10 border-purple-500/20',
  },
}

/**
 * AgentStatusBadge - Trust indicator for agent availability
 */
const AgentStatusBadge = memo(({ status }: { status: string }) => {
  const config = agentStatusConfig[status as keyof typeof agentStatusConfig] || {
    label: status,
    className: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
    icon: null,
    description: '未知状态',
    pulse: 'bg-slate-400',
  }

  return (
    <Tooltip title={config.description} placement="top">
      <div
        className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium border ${config.className}`}
        role="status"
        aria-label={`代理状态: ${config.label} - ${config.description}`}
      >
        <div className="relative flex items-center mr-1.5">
          <div className={`absolute w-2 h-2 rounded-full ${config.pulse} animate-ping opacity-50`} />
          <div className={`relative w-1.5 h-1.5 rounded-full ${config.pulse}`} />
        </div>
        <span>{config.label}</span>
      </div>
    </Tooltip>
  )
})

AgentStatusBadge.displayName = 'AgentStatusBadge'

/**
 * AgentTypeBadge - Visual indicator for agent type
 */
const AgentTypeBadge = memo(({ type }: { type: string }) => {
  const config = agentTypeConfig[type as keyof typeof agentTypeConfig] || {
    label: type,
    icon: <UserOutlined />,
    color: 'text-slate-400',
    bgColor: 'bg-slate-500/10 border-slate-500/20',
  }

  return (
    <div
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${config.bgColor} ${config.color}`}
      role="img"
      aria-label={`类型: ${config.label}`}
    >
      {config.icon}
      <span>{config.label}</span>
    </div>
  )
})

AgentTypeBadge.displayName = 'AgentTypeBadge'

/**
 * SkillTags - Capability tags with trust styling
 */
const SkillTags = memo(({ tags }: { tags: string[] }) => {
  if (!tags || tags.length === 0) {
    return <span className="text-slate-500">-</span>
  }

  const displayTags = tags.slice(0, 3)
  const remainingCount = tags.length - 3

  return (
    <Space size={[4, 4]} wrap>
      {displayTags.map((tag) => (
        <Tooltip key={tag} title={`技能: ${tag}`}>
          <span
            className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 cursor-default"
          >
            {tag}
          </span>
        </Tooltip>
      ))}
      {remainingCount > 0 && (
        <Tooltip title={tags.slice(3).join(', ')}>
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-500/10 text-slate-400">
            +{remainingCount}
          </span>
        </Tooltip>
      )}
    </Space>
  )
})

SkillTags.displayName = 'SkillTags'

/**
 * RatingDisplay - Trust indicator for agent quality
 */
const RatingDisplay = memo(({ rating }: { rating: number }) => {
  const color = rating >= 4.5 ? 'text-amber-400' : rating >= 4.0 ? 'text-emerald-400' : 'text-slate-400'
  const bgColor = rating >= 4.5 ? 'bg-amber-500/10 border-amber-500/20' : rating >= 4.0 ? 'bg-emerald-500/10 border-emerald-500/20' : 'bg-slate-500/10 border-slate-500/20'

  return (
    <div className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium border ${bgColor} ${color}`}>
      <StarOutlined className="text-[10px]" />
      <span className="font-mono tabular-nums">{rating.toFixed(1)}</span>
    </div>
  )
})

RatingDisplay.displayName = 'RatingDisplay'

/**
 * AgentListPage - Performance-optimized agent management
 */
const AgentListPage = () => {
  const [agents, setAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState(true)
  const [searchText, setSearchText] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [form] = Form.useForm()
  const [error, setError] = useState<string | null>(null)

  const fetchAgents = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await agentApi.list()
      setAgents(res.data.agents || [])
    } catch (err) {
      console.error('Failed to fetch agents:', err)
      setError('获取代理列表失败')
      message.error('获取代理列表失败')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchAgents()
  }, [fetchAgents])

  const filteredAgents = agents.filter((agent) =>
    agent.name.toLowerCase().includes(searchText.toLowerCase()) ||
    agent.agent_id.toLowerCase().includes(searchText.toLowerCase()) ||
    agent.capabilities.some((cap) => cap.toLowerCase().includes(searchText.toLowerCase()))
  )

  // Statistics
  const stats = {
    total: agents.length,
    online: agents.filter((a) => a.status === 'idle').length,
    busy: agents.filter((a) => a.status === 'busy').length,
    offline: agents.filter((a) => a.status === 'offline').length,
  }

  const columns: TableColumnsType<Agent> = [
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
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 110,
      render: (status: string) => <AgentStatusBadge status={status} />,
    },
    {
      title: '技能标签',
      key: 'capabilities',
      render: (_, record) => <SkillTags tags={record.capabilities} />,
    },
    {
      title: '完成任务',
      dataIndex: 'completed_jobs',
      key: 'completed_jobs',
      width: 100,
      align: 'center',
      render: (count: number) => (
        <span className="font-mono text-slate-300 tabular-nums">{count || 0}</span>
      ),
    },
    {
      title: '评分',
      dataIndex: 'rating',
      key: 'rating',
      width: 90,
      align: 'center',
      render: (rating: number) => <RatingDisplay rating={rating || 0} />,
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: () => (
        <Button type="link" size="small" className="text-cyan-400 hover:text-cyan-300">
          详情
        </Button>
      ),
    },
  ]

  const handleAddAgent = async (values: any) => {
    try {
      await agentApi.register(values)
      message.success('注册成功')
      setModalOpen(false)
      form.resetFields()
      fetchAgents()
    } catch (error) {
      message.error('注册失败')
    }
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <Title level={3} className="text-white m-0">
            代理管理
          </Title>
          <Text className="text-slate-400">管理和监控所有代理状态</Text>
        </div>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setModalOpen(true)}
          className="bg-gradient-to-r from-cyan-500 to-purple-500 border-0"
        >
          添加代理
        </Button>
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
              <Text className="text-xs text-slate-500 uppercase tracking-wider">在线</Text>
              <div className="text-2xl font-bold text-emerald-400 font-mono tabular-nums mt-1">
                {stats.online}
              </div>
            </div>
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center">
              <CheckCircleOutlined className="text-emerald-400" />
            </div>
          </div>
        </div>
        <div className="glass-card p-4">
          <div className="flex items-center justify-between">
            <div>
              <Text className="text-xs text-slate-500 uppercase tracking-wider">工作中</Text>
              <div className="text-2xl font-bold text-pink-400 font-mono tabular-nums mt-1">
                {stats.busy}
              </div>
            </div>
            <div className="w-10 h-10 rounded-xl bg-pink-500/10 flex items-center justify-center">
              <SyncOutlined className="text-pink-400" />
            </div>
          </div>
        </div>
        <div className="glass-card p-4">
          <div className="flex items-center justify-between">
            <div>
              <Text className="text-xs text-slate-500 uppercase tracking-wider">离线</Text>
              <div className="text-2xl font-bold text-slate-400 font-mono tabular-nums mt-1">
                {stats.offline}
              </div>
            </div>
            <div className="w-10 h-10 rounded-xl bg-slate-700/50 flex items-center justify-center">
              <MinusCircleOutlined className="text-slate-400" />
            </div>
          </div>
        </div>
      </div>

      {/* Search Bar */}
      <div className="glass-card p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <Search
            placeholder="搜索代理ID、姓名或技能..."
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
        {error ? (
          <div className="text-center py-12">
            <Text className="text-rose-400 block mb-4">{error}</Text>
            <Button onClick={fetchAgents} icon={<ReloadOutlined />}>
              重试
            </Button>
          </div>
        ) : (
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
            className="agents-table"
            rowClassName="hover:bg-slate-800/30 transition-colors"
          />
        )}
      </div>

      {/* Add Agent Modal */}
      <Modal
        title="添加新代理"
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        footer={null}
        width={500}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleAddAgent}
        >
          <Form.Item
            name="agent_id"
            label="代理ID"
            rules={[{ required: true, message: '请输入代理ID' }]}
          >
            <Input
              placeholder="例如: worker_001"
              className="bg-slate-800/50 border-slate-700 text-white"
            />
          </Form.Item>

          <Form.Item
            name="agent_type"
            label="类型"
            rules={[{ required: true, message: '请选择类型' }]}
          >
            <Select className="dark-select">
              <Option value="worker">
                <span className="flex items-center gap-2">
                  <ThunderboltOutlined className="text-purple-400" />
                  打工人
                </span>
              </Option>
              <Option value="employer">
                <span className="flex items-center gap-2">
                  <CrownOutlined className="text-cyan-400" />
                  雇主
                </span>
              </Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="name"
            label="姓名"
            rules={[{ required: true, message: '请输入姓名' }]}
          >
            <Input
              placeholder="例如: Python开发虾"
              className="bg-slate-800/50 border-slate-700 text-white"
            />
          </Form.Item>

          <Form.Item
            name="capabilities"
            label="技能标签"
            rules={[{ required: true, message: '请输入技能标签' }]}
          >
            <Select
              mode="tags"
              placeholder="例如: python, fastapi, react"
              className="dark-select"
            >
              <Option value="python">Python</Option>
              <Option value="fastapi">FastAPI</Option>
              <Option value="react">React</Option>
            </Select>
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              block
              className="bg-gradient-to-r from-cyan-500 to-purple-500 border-0"
            >
              确认添加
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default AgentListPage
