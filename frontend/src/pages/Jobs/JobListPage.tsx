import { useState, useCallback, memo } from 'react'
import { Table, Space, Typography, Button, Modal, Form, Input, InputNumber, Select, message, Popconfirm } from 'antd'
import type { TableColumnsType } from 'antd'
import {
  PlusOutlined,
  EyeOutlined,
  CheckCircleOutlined,
  SyncOutlined,
  ClockCircleOutlined,
  MinusCircleOutlined,
  FilterOutlined,
  ReloadOutlined,
  DeleteOutlined,
} from '@ant-design/icons'
import { Job } from '@/types/job'
import { jobApi } from '@/services/api'
import { Link } from 'react-router-dom'
import { useAsyncEffect } from '@/hooks/useFetchOnce'

const { Title, Text } = Typography
const { Option } = Select

// Trust-focused status configuration with icons and descriptions
const statusConfig = {
  OPEN: {
    label: '开放中',
    className: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    icon: <CheckCircleOutlined className="mr-1" />,
    description: '任务正在接收竞标',
  },
  ACTIVE: {
    label: '进行中',
    className: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
    icon: <SyncOutlined spin className="mr-1" />,
    description: '任务已被承接，正在执行',
  },
  REVIEW: {
    label: '审核中',
    className: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    icon: <ClockCircleOutlined className="mr-1" />,
    description: '任务等待审核',
  },
  CLOSED: {
    label: '已关闭',
    className: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
    icon: <MinusCircleOutlined className="mr-1" />,
    description: '任务已结束',
  },
}

const filterConfig = {
  all: { label: '全部', color: 'default' },
  OPEN: { label: '待接单', color: 'emerald' },
  ACTIVE: { label: '进行中', color: 'cyan' },
  REVIEW: { label: '审核中', color: 'amber' },
  CLOSED: { label: '已完成', color: 'slate' },
}

/**
 * StatusBadge - Trust indicator for job status
 */
const StatusBadge = memo(({ status }: { status: string }) => {
  const config = statusConfig[status as keyof typeof statusConfig] || {
    label: status,
    className: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
    icon: null,
    description: '未知状态',
  }

  return (
    <div
      className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium border ${config.className}`}
      role="status"
      aria-label={`状态: ${config.label} - ${config.description}`}
      title={config.description}
    >
      {config.icon}
      <span>{config.label}</span>
    </div>
  )
})

StatusBadge.displayName = 'StatusBadge'

/**
 * BudgetDisplay - Trust-focused currency display
 */
const BudgetDisplay = memo(({ min, max }: { min?: number; max?: number }) => {
  if (!min && !max) {
    return <span className="text-slate-500">-</span>
  }

  const formatCurrency = (val?: number) =>
    val ? `¥${val.toLocaleString('zh-CN')}` : '-'

  return (
    <span className="text-slate-300 font-mono tabular-nums">
      {formatCurrency(min)} - {formatCurrency(max)}
    </span>
  )
})

BudgetDisplay.displayName = 'BudgetDisplay'

/**
 * SkillTags - Capability tags with consistent styling
 */
const SkillTags = memo(({ tags }: { tags: string[] }) => {
  if (!tags || tags.length === 0) {
    return <span className="text-slate-500">-</span>
  }

  return (
    <Space size={[4, 4]} wrap>
      {tags.map((tag) => (
        <span
          key={tag}
          className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-500/10 text-purple-400 border border-purple-500/20"
        >
          {tag}
        </span>
      ))}
    </Space>
  )
})

SkillTags.displayName = 'SkillTags'

/**
 * JobListPage - Performance-optimized job management with trust indicators
 */
const JobListPage = () => {
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [modalOpen, setModalOpen] = useState(false)
  const [form] = Form.useForm()
  const [error, setError] = useState<string | null>(null)

  const fetchJobs = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await jobApi.list(statusFilter === 'all' ? undefined : { status: statusFilter })
      setJobs(res.data.jobs || [])
    } catch (err) {
      console.error('Failed to fetch jobs:', err)
      setError('获取任务列表失败')
      message.error('获取任务列表失败')
    } finally {
      setLoading(false)
    }
  }, [statusFilter])

  const handleDeleteJob = useCallback(async (jobId: string) => {
    try {
      await jobApi.delete(jobId)
      message.success('任务已删除')
      fetchJobs()
    } catch (err: any) {
      console.error('Failed to delete job:', err)
      const errorMsg = err?.response?.data?.detail || '删除任务失败'
      message.error(errorMsg)
    }
  }, [fetchJobs])

  useAsyncEffect(fetchJobs, [fetchJobs])

  const filteredJobs = statusFilter === 'all'
    ? jobs
    : jobs.filter((job) => job.status === statusFilter)

  const columns: TableColumnsType<Job> = [
    {
      title: '任务ID',
      dataIndex: 'job_id',
      key: 'job_id',
      width: 120,
      render: (job_id: string) => (
        <span className="font-mono text-xs text-slate-500">{job_id}</span>
      ),
    },
    {
      title: '任务标题',
      dataIndex: 'title',
      key: 'title',
      render: (_, record) => (
        <Link
          to={`/jobs/${record.job_id}`}
          className="text-slate-200 hover:text-cyan-400 transition-colors focus:outline-none focus:ring-2 focus:ring-cyan-500/50 rounded px-1 -mx-1"
        >
          <Text strong className="text-inherit">{record.title}</Text>
        </Link>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 110,
      render: (status: string) => <StatusBadge status={status} />,
    },
    {
      title: '技能标签',
      key: 'tags',
      render: (_, record) => <SkillTags tags={record.required_tags} />,
    },
    {
      title: '竞标数',
      dataIndex: 'bid_count',
      key: 'bid_count',
      width: 90,
      render: (count: number) => (
        <span className="font-mono text-slate-300 tabular-nums">{count || 0}</span>
      ),
    },
    {
      title: '预算',
      key: 'budget',
      width: 150,
      render: (_, record) => <BudgetDisplay min={record.budget_min} max={record.budget_max} />,
    },
    {
      title: '操作',
      key: 'action',
      width: 180,
      render: (_, record) => (
        <Space size="small">
          <Link to={`/jobs/${record.job_id}`}>
            <Button
              type="link"
              size="small"
              icon={<EyeOutlined />}
              className="text-cyan-400 hover:text-cyan-300"
            >
              查看
            </Button>
          </Link>
          {/* OPEN 或 CLOSED 状态可以删除 */}
          {(record.status === 'OPEN' || record.status === 'CLOSED') && (
            <Popconfirm
              title="确认删除任务"
              description="删除后将无法恢复，确定要删除此任务吗？"
              onConfirm={() => handleDeleteJob(record.job_id)}
              okText="确认删除"
              cancelText="取消"
              okButtonProps={{ danger: true }}
            >
              <Button
                type="link"
                size="small"
                danger
                icon={<DeleteOutlined />}
              >
                删除
              </Button>
            </Popconfirm>
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
          <Title level={3} className="text-white m-0">
            任务管理
          </Title>
          <Text className="text-slate-400">管理和监控所有任务状态</Text>
        </div>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setModalOpen(true)}
          className="bg-gradient-to-r from-cyan-500 to-purple-500 border-0"
        >
          发布新任务
        </Button>
      </div>

      {/* Filter Bar */}
      <div className="glass-card p-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2 text-slate-400">
            <FilterOutlined />
            <span className="text-sm">筛选:</span>
          </div>
          <Space wrap>
            {Object.entries(filterConfig).map(([key, config]) => (
              <Button
                key={key}
                type={statusFilter === key ? 'primary' : 'default'}
                size="small"
                onClick={() => setStatusFilter(key)}
                className={
                  statusFilter === key
                    ? 'bg-gradient-to-r from-cyan-500 to-purple-500 border-0'
                    : 'bg-slate-800/50 border-slate-700 text-slate-300 hover:text-white'
                }
              >
                {config.label}
              </Button>
            ))}
          </Space>
          <div className="flex-1" />
          <Button
            icon={<ReloadOutlined />}
            size="small"
            onClick={fetchJobs}
            loading={loading}
            className="bg-slate-800/50 border-slate-700 text-slate-300"
          >
            刷新
          </Button>
        </div>
      </div>

      {/* Stats Summary */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {Object.entries(statusConfig).map(([key, config]) => {
          const count = jobs.filter((j) => j.status === key).length
          return (
            <div
              key={key}
              className="glass-card p-4 flex items-center justify-between cursor-pointer hover:bg-slate-800/30 transition-colors"
              onClick={() => setStatusFilter(key)}
              role="button"
              tabIndex={0}
              aria-label={`筛选 ${config.label}: ${count} 个任务`}
            >
              <div className="flex items-center gap-2">
                <span className={config.className.replace('text-xs', 'text-sm')}>
                  {config.icon}
                </span>
                <span className="text-slate-400 text-sm">{config.label}</span>
              </div>
              <span className="text-xl font-bold text-white font-mono tabular-nums">
                {count}
              </span>
            </div>
          )
        })}
      </div>

      {/* Jobs Table */}
      <div className="glass-card p-6">
        {error ? (
          <div className="text-center py-12">
            <Text className="text-rose-400 block mb-4">{error}</Text>
            <Button onClick={fetchJobs} icon={<ReloadOutlined />}>
              重试
            </Button>
          </div>
        ) : (
          <Table
            dataSource={filteredJobs}
            columns={columns}
            rowKey="job_id"
            loading={loading}
            pagination={{
              pageSize: 20,
              showSizeChanger: true,
              showTotal: (total) => `共 ${total} 条记录`,
            }}
            className="jobs-table"
            rowClassName="hover:bg-slate-800/30 transition-colors"
          />
        )}
      </div>

      {/* Create Job Modal */}
      <Modal
        title="发布新任务"
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        maskClosable
        keyboard
        footer={null}
        width={600}
        className="dark-modal"
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={async (values) => {
            try {
              // Transform form data to match API schema
              const payload = {
                employer_id: 'admin-console', // Admin console creates jobs on behalf of system
                title: values.title,
                description: values.description,
                required_tags: values.required_tags || [],
                budget: values.budget_min || values.budget_max ? {
                  min: values.budget_min,
                  max: values.budget_max,
                } : null,
                bid_limit: values.bid_limit || 5,
              }
              await jobApi.create(payload)
              message.success('任务发布成功')
              setModalOpen(false)
              form.resetFields()
              fetchJobs()
            } catch (error) {
              message.error('发布失败')
            }
          }}
        >
          <Form.Item
            name="title"
            label="任务标题"
            rules={[{ required: true, message: '请输入任务标题' }]}
          >
            <Input
              placeholder="例如: 开发 MCP 数据接口"
              className="bg-slate-800/50 border-slate-700 text-white"
            />
          </Form.Item>

          <Form.Item
            name="description"
            label="任务描述"
            rules={[{ required: true, message: '请输入任务描述' }]}
          >
            <Input.TextArea
              rows={4}
              placeholder="详细描述任务要求..."
              className="bg-slate-800/50 border-slate-700 text-white"
            />
          </Form.Item>

          <Form.Item
            name="required_tags"
            label="所需技能"
            rules={[{ required: true, message: '请选择所需技能' }]}
          >
            <Select
              mode="tags"
              placeholder="例如: python, fastapi, react"
              className="dark-select"
            >
              <Option value="python">Python</Option>
              <Option value="fastapi">FastAPI</Option>
              <Option value="react">React</Option>
              <Option value="figma">Figma</Option>
            </Select>
          </Form.Item>

          <div className="grid grid-cols-2 gap-4">
            <Form.Item name="budget_min" label="最低预算">
              <InputNumber
                prefix="¥"
                min={0}
                placeholder="1000"
                className="w-full bg-slate-800/50"
              />
            </Form.Item>

            <Form.Item name="budget_max" label="最高预算">
              <InputNumber
                prefix="¥"
                min={0}
                placeholder="5000"
                className="w-full bg-slate-800/50"
              />
            </Form.Item>
          </div>

          <Form.Item name="bid_limit" label="竞标上限" initialValue={5}>
            <InputNumber min={1} max={20} className="w-full bg-slate-800/50" />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              block
              className="bg-gradient-to-r from-cyan-500 to-purple-500 border-0"
            >
              发布任务
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default JobListPage
