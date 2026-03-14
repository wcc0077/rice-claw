import { useState, useCallback, memo } from 'react'
import { Table, Space, Typography, Input, Button, Modal, Form, Select, message, Avatar, Tooltip, Drawer, Popconfirm, Descriptions, Divider } from 'antd'
import type { TableColumnsType } from 'antd'
import {
  PlusOutlined,
  UserOutlined,
  StarOutlined,
  ReloadOutlined,
  SearchOutlined,
  CheckCircleOutlined,
  MinusCircleOutlined,
  SyncOutlined,
  EyeOutlined,
  EditOutlined,
  DeleteOutlined,
  CalendarOutlined,
  IdcardOutlined,
  QuestionCircleOutlined,
} from '@ant-design/icons'
import axios from 'axios'
import { Agent } from '@/types/agent'
import { agentApi } from '@/services/api'
import { useAsyncEffect } from '@/hooks/useFetchOnce'

const { Search } = Input
const { Title, Text } = Typography
const { Option } = Select

// 龙虾状态配置
const lobsterStatusConfig = {
  idle: {
    label: '空闲',
    className: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    icon: <CheckCircleOutlined className="mr-1" />,
    description: '龙虾当前空闲，可接受任务',
    pulse: 'bg-emerald-400',
  },
  busy: {
    label: '工作中',
    className: 'bg-pink-500/10 text-pink-400 border-pink-500/20',
    icon: <SyncOutlined spin className="mr-1" />,
    description: '龙虾正在执行任务',
    pulse: 'bg-pink-400',
  },
  offline: {
    label: '离线',
    className: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
    icon: <MinusCircleOutlined className="mr-1" />,
    description: '龙虾当前离线',
    pulse: 'bg-slate-400',
  },
}

/**
 * LobsterStatusBadge - 龙虾状态徽章
 */
const LobsterStatusBadge = memo(({ status }: { status: string }) => {
  const config = lobsterStatusConfig[status as keyof typeof lobsterStatusConfig] || {
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
        aria-label={`龙虾状态: ${config.label}`}
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

LobsterStatusBadge.displayName = 'LobsterStatusBadge'

/**
 * SkillTags - 技能标签
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
 * RatingDisplay - 评分显示
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
 * LobsterListPage - 龙虾管理页面
 */
const LobsterListPage = () => {
  const [lobsters, setLobsters] = useState<Agent[]>([])
  const [loading, setLoading] = useState(true)
  const [searchText, setSearchText] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editModalOpen, setEditModalOpen] = useState(false)
  const [detailDrawerOpen, setDetailDrawerOpen] = useState(false)
  const [selectedLobster, setSelectedLobster] = useState<Agent | null>(null)
  const [form] = Form.useForm()
  const [editForm] = Form.useForm()
  const [error, setError] = useState<string | null>(null)

  const fetchLobsters = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await agentApi.list()
      setLobsters(res.data.agents || [])
    } catch (err) {
      console.error('Failed to fetch lobsters:', err)
      setError('获取龙虾列表失败')
      message.error('获取龙虾列表失败')
    } finally {
      setLoading(false)
    }
  }, [])

  useAsyncEffect(fetchLobsters, [fetchLobsters])

  const filteredLobsters = lobsters.filter((lobster) =>
    lobster.name.toLowerCase().includes(searchText.toLowerCase()) ||
    lobster.agent_id.toLowerCase().includes(searchText.toLowerCase()) ||
    lobster.capabilities.some((cap) => cap.toLowerCase().includes(searchText.toLowerCase()))
  )

  // 统计数据
  const stats = {
    total: lobsters.length,
    online: lobsters.filter((l) => l.status === 'idle').length,
    busy: lobsters.filter((l) => l.status === 'busy').length,
    offline: lobsters.filter((l) => l.status === 'offline').length,
  }

  const handleAddLobster = async (values: any) => {
    try {
      // 默认类型为 agent（既能接单也能发单）
      await agentApi.register({ ...values, agent_type: 'agent' })
      message.success('添加成功')
      setModalOpen(false)
      form.resetFields()
      fetchLobsters()
    } catch (error) {
      message.error('添加失败')
    }
  }

  const handleViewDetail = (lobster: Agent) => {
    setSelectedLobster(lobster)
    setDetailDrawerOpen(true)
  }

  const handleEdit = (lobster: Agent) => {
    setSelectedLobster(lobster)
    editForm.setFieldsValue({
      name: lobster.name,
      capabilities: lobster.capabilities,
      description: lobster.description,
    })
    setEditModalOpen(true)
  }

  const handleEditSubmit = async (values: any) => {
    if (!selectedLobster) return
    try {
      await agentApi.update(selectedLobster.agent_id, values)
      message.success('更新成功')
      setEditModalOpen(false)
      editForm.resetFields()
      fetchLobsters()
    } catch (error) {
      message.error('更新失败')
    }
  }

  const handleDelete = async (lobsterId: string) => {
    try {
      await agentApi.delete(lobsterId)
      message.success('删除成功')
      setDetailDrawerOpen(false)
      fetchLobsters()
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.data?.detail) {
        message.error(error.response.data.detail)
      } else {
        message.error('删除失败')
      }
    }
  }

  const columns: TableColumnsType<Agent> = [
    {
      title: '龙虾',
      key: 'lobster',
      render: (_, record) => (
        <div className="flex items-center gap-3">
          <Avatar
            size={40}
            icon={<UserOutlined />}
            className="bg-gradient-to-br from-orange-500/20 to-red-500/10 border-2 border-slate-700"
          />
          <div>
            <Text strong className="text-white">{record.name}</Text>
            <Text className="text-xs text-slate-500 font-mono block">{record.agent_id}</Text>
          </div>
        </div>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 110,
      render: (status: string) => <LobsterStatusBadge status={status} />,
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
      width: 180,
      render: (_, record) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            className="text-cyan-400 hover:text-cyan-300"
            onClick={() => handleViewDetail(record)}
          >
            详情
          </Button>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            className="text-amber-400 hover:text-amber-300"
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确认删除"
            description="删除后无法恢复，确定要删除这只龙虾吗？"
            onConfirm={() => handleDelete(record.agent_id)}
            okText="确认"
            cancelText="取消"
            okButtonProps={{ danger: true }}
          >
            <Button
              type="link"
              size="small"
              icon={<DeleteOutlined />}
              className="text-rose-400 hover:text-rose-300"
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <Title level={3} className="text-white m-0">
            龙虾管理
          </Title>
          <Text className="text-slate-400">管理和监控所有龙虾状态</Text>
        </div>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setModalOpen(true)}
          className="bg-gradient-to-r from-orange-500 to-red-500 border-0"
        >
          添加龙虾
        </Button>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="glass-card p-4">
          <div className="flex items-center justify-between">
            <div>
              <Text className="text-xs text-slate-500 uppercase tracking-wider">总龙虾</Text>
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

      {/* 搜索栏 */}
      <div className="glass-card p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <Search
            placeholder="搜索龙虾ID、姓名或技能..."
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
            onClick={fetchLobsters}
            loading={loading}
            className="bg-slate-800/50 border-slate-700 text-slate-300"
          >
            刷新
          </Button>
        </div>
      </div>

      {/* 龙虾表格 */}
      <div className="glass-card p-6">
        {error ? (
          <div className="text-center py-12">
            <Text className="text-rose-400 block mb-4">{error}</Text>
            <Button onClick={fetchLobsters} icon={<ReloadOutlined />}>
              重试
            </Button>
          </div>
        ) : (
          <Table
            dataSource={filteredLobsters}
            columns={columns}
            rowKey="agent_id"
            loading={loading}
            pagination={{
              pageSize: 20,
              showSizeChanger: true,
              showTotal: (total) => `共 ${total} 条记录`,
            }}
            className="lobsters-table"
            rowClassName="hover:bg-slate-800/30 transition-colors"
          />
        )}
      </div>

      {/* 添加龙虾弹窗 */}
      <Modal
        title="添加新龙虾"
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        footer={null}
        width={500}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleAddLobster}
        >
          <Form.Item
            name="agent_id"
            label={
              <div className="flex items-center gap-2">
                <span>龙虾ID</span>
                <Tooltip title={
                  <div className="text-xs">
                    <div className="mb-1">在你的 Agent 终端运行以下命令，复制输出的 Device ID：</div>
                    <code className="bg-slate-700 px-1 rounded text-cyan-300">
                      cat ~/.openclaw/identity/device.json
                    </code>
                  </div>
                }>
                  <QuestionCircleOutlined className="text-cyan-400 cursor-help" />
                </Tooltip>
              </div>
            }
            rules={[{ required: true, message: '请输入龙虾ID' }]}
          >
            <Input
              placeholder="例如: device_abc123..."
              className="bg-slate-800/50 border-slate-700 text-white"
            />
          </Form.Item>

          <Form.Item
            name="name"
            label="姓名"
            rules={[{ required: true, message: '请输入姓名' }]}
          >
            <Input
              placeholder="例如: Python龙虾"
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
              className="bg-gradient-to-r from-orange-500 to-red-500 border-0"
            >
              确认添加
            </Button>
          </Form.Item>
        </Form>
      </Modal>

      {/* 编辑龙虾弹窗 */}
      <Modal
        title="编辑龙虾"
        open={editModalOpen}
        onCancel={() => setEditModalOpen(false)}
        footer={null}
        width={500}
      >
        <Form
          form={editForm}
          layout="vertical"
          onFinish={handleEditSubmit}
        >
          <Form.Item
            name="name"
            label="姓名"
            rules={[{ required: true, message: '请输入姓名' }]}
          >
            <Input
              placeholder="龙虾名称"
              className="bg-slate-800/50 border-slate-700 text-white"
            />
          </Form.Item>

          <Form.Item
            name="capabilities"
            label="技能标签"
          >
            <Select
              mode="tags"
              placeholder="技能标签"
              className="dark-select"
            >
              <Option value="python">Python</Option>
              <Option value="fastapi">FastAPI</Option>
              <Option value="react">React</Option>
              <Option value="typescript">TypeScript</Option>
              <Option value="nodejs">Node.js</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="description"
            label="描述"
          >
            <Input.TextArea
              placeholder="龙虾描述（可选）"
              rows={3}
              className="bg-slate-800/50 border-slate-700 text-white"
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              block
              className="bg-gradient-to-r from-amber-500 to-orange-500 border-0"
            >
              保存修改
            </Button>
          </Form.Item>
        </Form>
      </Modal>

      {/* 龙虾详情抽屉 */}
      <Drawer
        title={
          <div className="flex items-center gap-2">
            <IdcardOutlined className="text-orange-400" />
            <span>龙虾详情</span>
          </div>
        }
        placement="right"
        width={480}
        onClose={() => setDetailDrawerOpen(false)}
        open={detailDrawerOpen}
        className="lobster-detail-drawer"
      >
        {selectedLobster && (
          <div className="space-y-6">
            {/* 头像和名称 */}
            <div className="flex items-center gap-4">
              <Avatar
                size={64}
                icon={<UserOutlined />}
                className="bg-gradient-to-br from-orange-500/30 to-red-500/20 border-2 border-slate-600"
              />
              <div>
                <Title level={4} className="text-white m-0">{selectedLobster.name}</Title>
                <div className="mt-1">
                  <LobsterStatusBadge status={selectedLobster.status} />
                </div>
              </div>
            </div>

            <Divider className="border-slate-700" />

            {/* 基本信息 */}
            <Descriptions column={1} styles={{ label: { color: '#94a3b8' } }}>
              <Descriptions.Item label={<><IdcardOutlined className="mr-2" />龙虾ID</>}>
                <Text className="text-white font-mono">{selectedLobster.agent_id}</Text>
              </Descriptions.Item>
              <Descriptions.Item label={<><CalendarOutlined className="mr-2" />创建时间</>}>
                <Text className="text-white">
                  {new Date(selectedLobster.created_at).toLocaleString('zh-CN')}
                </Text>
              </Descriptions.Item>
              <Descriptions.Item label={<><CalendarOutlined className="mr-2" />更新时间</>}>
                <Text className="text-white">
                  {new Date(selectedLobster.updated_at).toLocaleString('zh-CN')}
                </Text>
              </Descriptions.Item>
            </Descriptions>

            {/* 技能 */}
            <div>
              <Text className="text-slate-400 block mb-2">技能标签</Text>
              <SkillTags tags={selectedLobster.capabilities} />
            </div>

            {/* 描述 */}
            {selectedLobster.description && (
              <div>
                <Text className="text-slate-400 block mb-2">描述</Text>
                <Text className="text-white">{selectedLobster.description}</Text>
              </div>
            )}

            <Divider className="border-slate-700" />

            {/* 统计 */}
            <div className="grid grid-cols-2 gap-4">
              <div className="glass-card p-4 text-center">
                <div className="text-2xl font-bold text-amber-400 font-mono">
                  {selectedLobster.rating?.toFixed(1) || '0.0'}
                </div>
                <Text className="text-slate-500 text-sm">评分</Text>
              </div>
              <div className="glass-card p-4 text-center">
                <div className="text-2xl font-bold text-orange-400 font-mono">
                  {selectedLobster.completed_jobs || 0}
                </div>
                <Text className="text-slate-500 text-sm">完成任务</Text>
              </div>
            </div>

            <Divider className="border-slate-700" />

            {/* 操作 */}
            <div className="flex gap-3">
              <Button
                icon={<EditOutlined />}
                onClick={() => {
                  setDetailDrawerOpen(false)
                  handleEdit(selectedLobster)
                }}
                className="flex-1 bg-amber-500/10 border-amber-500/30 text-amber-400 hover:bg-amber-500/20"
              >
                编辑
              </Button>
              <Popconfirm
                title="确认删除"
                description="删除后无法恢复，确定要删除这只龙虾吗？"
                onConfirm={() => handleDelete(selectedLobster.agent_id)}
                okText="确认"
                cancelText="取消"
                okButtonProps={{ danger: true }}
              >
                <Button
                  icon={<DeleteOutlined />}
                  danger
                  className="flex-1"
                >
                  删除
                </Button>
              </Popconfirm>
            </div>
          </div>
        )}
      </Drawer>
    </div>
  )
}

export default LobsterListPage