import { Table, Space, Button, Typography, Skeleton } from 'antd'
import type { TableColumnsType } from 'antd'
import { Link } from 'react-router-dom'
import { Job } from '@/types/job'
import {
  CheckCircleOutlined,
  SyncOutlined,
  ExclamationCircleOutlined,
  ClockCircleOutlined,
  MinusCircleOutlined,
} from '@ant-design/icons'

const { Text } = Typography

interface RecentJobsTableProps {
  jobs: Job[]
  loading?: boolean
}

// Trust-focused status configuration with icons and accessibility
const statusConfig = {
  OPEN: {
    label: '开放中',
    color: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    icon: <CheckCircleOutlined className="mr-1" />,
    description: '任务正在接收竞标',
  },
  ACTIVE: {
    label: '进行中',
    color: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
    icon: <SyncOutlined spin className="mr-1" />,
    description: '任务已被承接，正在执行',
  },
  REVIEW: {
    label: '审核中',
    color: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    icon: <ClockCircleOutlined className="mr-1" />,
    description: '任务等待审核',
  },
  CLOSED: {
    label: '已关闭',
    color: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
    icon: <MinusCircleOutlined className="mr-1" />,
    description: '任务已结束',
  },
}

/**
 * StatusBadge - Accessible status indicator with icon
 * Provides clear visual feedback for job states
 */
const StatusBadge = ({ status }: { status: string }) => {
  const config = statusConfig[status as keyof typeof statusConfig] || {
    label: status,
    color: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
    icon: null,
    description: '未知状态',
  }

  return (
    <div
      className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium border ${config.color}`}
      role="status"
      aria-label={`状态: ${config.label} - ${config.description}`}
      title={config.description}
    >
      {config.icon}
      <span>{config.label}</span>
    </div>
  )
}

/**
 * TimeRemaining - Trust indicator showing deadline urgency
 * Color-coded based on urgency level
 */
const TimeRemaining = ({ deadline }: { deadline?: string }) => {
  if (!deadline) {
    return (
      <span className="text-slate-500" aria-label="无截止日期">
        -
      </span>
    )
  }

  const daysLeft = Math.ceil(
    (new Date(deadline).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24)
  )

  if (daysLeft < 0) {
    return (
      <div
        className="inline-flex items-center gap-1 text-rose-400"
        role="alert"
        aria-label="任务已过期"
      >
        <ExclamationCircleOutlined aria-hidden="true" />
        <span className="font-medium">已过期</span>
      </div>
    )
  }

  // Trust indicator: color-coded urgency
  const urgencyClass =
    daysLeft <= 1
      ? 'text-rose-400 font-medium'
      : daysLeft <= 3
      ? 'text-amber-400'
      : 'text-slate-400'

  return (
    <span className={urgencyClass} aria-label={`剩余 ${daysLeft} 天`}>
      {daysLeft} 天
    </span>
  )
}

/**
 * BudgetDisplay - Formatted budget display with trust indicators
 */
const BudgetDisplay = ({
  min,
  max,
}: {
  min?: number
  max?: number
}) => {
  if (!min && !max) {
    return <span className="text-slate-500">-</span>
  }

  const formatCurrency = (val?: number) =>
    val ? `¥${val.toLocaleString('zh-CN')}` : '-'

  return (
    <span className="text-slate-300 font-mono tabular-nums" aria-label={`预算范围: ${formatCurrency(min)} 至 ${formatCurrency(max)}`}>
      {formatCurrency(min)} - {formatCurrency(max)}
    </span>
  )
}

/**
 * RecentJobsTable - Trust-focused job listing with loading states
 * Features: Skeleton loading, accessible status badges, urgency indicators
 */
const RecentJobsTable = ({ jobs, loading = false }: RecentJobsTableProps) => {
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
          <Text strong className="text-inherit">
            {record.title}
          </Text>
        </Link>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => <StatusBadge status={status} />,
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
      render: (_, record) => <BudgetDisplay min={record.budget_min} max={record.budget_max} />,
    },
    {
      title: '剩余时间',
      key: 'deadline',
      width: 100,
      render: (_, record) => <TimeRemaining deadline={record.deadline} />,
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_, record) => (
        <Space size="small">
          <Link to={`/jobs/${record.job_id}`}>
            <Button
              type="link"
              size="small"
              className="text-cyan-400 hover:text-cyan-300"
            >
              查看
            </Button>
          </Link>
        </Space>
      ),
    },
  ]

  // Skeleton loading state
  if (loading) {
    return (
      <div className="space-y-4" aria-label="加载中">
        <Skeleton active paragraph={{ rows: 1 }} title={false} />
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div
              key={i}
              className="flex items-center gap-4 p-3 rounded-lg bg-slate-800/30"
            >
              <Skeleton.Input style={{ width: 80 }} active size="small" />
              <Skeleton.Input style={{ width: 200 }} active size="small" />
              <Skeleton.Input style={{ width: 60 }} active size="small" />
              <Skeleton.Input style={{ width: 40 }} active size="small" />
              <Skeleton.Input style={{ width: 100 }} active size="small" />
              <Skeleton.Input style={{ width: 60 }} active size="small" />
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <Table
      dataSource={jobs}
      columns={columns}
      rowKey="job_id"
      pagination={false}
      size="small"
      className="recent-jobs-table"
      rowClassName="hover:bg-slate-800/30 transition-colors"
      aria-label="最近任务列表"
    />
  )
}

export default RecentJobsTable
