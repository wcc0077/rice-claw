import { Table, Typography, Tag } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { JobStatus, jobStatusConfig } from '@/types/job-status'

interface Job {
  job_id: string
  title: string
  status: string
  required_tags: string[]
  budget_min?: number | null
  budget_max?: number | null
  bid_count: number
  created_at: string
}

interface TaskListProps {
  jobs: Job[]
  selectedJobId: string | null
  onSelectJob: (jobId: string) => void
  loading?: boolean
}

const { Text } = Typography

const StatusBadge = ({ status }: { status: string }) => {
  const config = jobStatusConfig[status as JobStatus] || {
    label: status,
    color: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
    icon: null,
  }

  return (
    <div
      className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium border ${config.color}`}
      role="status"
    >
      {config.icon}
      <span>{config.label}</span>
    </div>
  )
}

const BudgetDisplay = ({ min, max }: { min?: number | null; max?: number | null }) => {
  if (!min && !max) {
    return <span className="text-slate-500">-</span>
  }

  const formatCurrency = (val?: number | null) =>
    val ? `¥${val.toLocaleString('zh-CN')}` : '-'

  return (
    <span className="text-slate-300 font-mono tabular-nums">
      {formatCurrency(min)} - {formatCurrency(max)}
    </span>
  )
}

/**
 * TaskList - 任务列表组件
 * 支持选择任务，高亮显示已选中的任务
 */
const TaskList = ({ jobs, selectedJobId, onSelectJob, loading = false }: TaskListProps) => {
  const columns: ColumnsType<Job> = [
    {
      title: '任务 ID',
      dataIndex: 'job_id',
      key: 'job_id',
      width: 140,
      render: (job_id: string) => (
        <span className="font-mono text-xs text-slate-500">{job_id}</span>
      ),
    },
    {
      title: '任务标题',
      dataIndex: 'title',
      key: 'title',
      render: (_, record) => (
        <Text
          strong
          className={`cursor-pointer ${selectedJobId === record.job_id ? 'text-cyan-400' : 'text-slate-200'}`}
          onClick={() => onSelectJob(record.job_id)}
        >
          {record.title}
        </Text>
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
      title: '技能标签',
      key: 'tags',
      width: 150,
      render: (_, record) => (
        <>
          {record.required_tags?.slice(0, 3).map((tag: string) => (
            <Tag key={tag} color="purple" className="text-xs">
              {tag}
            </Tag>
          ))}
          {(record.required_tags?.length ?? 0) > 3 && (
            <Tag color="gray" className="text-xs">
              +{record.required_tags.length - 3}
            </Tag>
          )}
        </>
      ),
    },
    {
      title: '竞标数',
      dataIndex: 'bid_count',
      key: 'bid_count',
      width: 80,
      render: (count: number) => (
        <span className="font-mono text-slate-300 tabular-nums">{count}</span>
      ),
    },
    {
      title: '预算',
      key: 'budget',
      width: 120,
      render: (_, record) => (
        <BudgetDisplay min={record.budget_min} max={record.budget_max} />
      ),
    },
  ]

  return (
    <div className="glass-card p-4">
      <h3 className="text-lg font-semibold text-white mb-4">任务列表</h3>
      <Table
        dataSource={jobs}
        columns={columns}
        rowKey="job_id"
        rowClassName={(record) =>
          selectedJobId === record.job_id
            ? 'bg-cyan-500/10 border border-cyan-500/30 rounded-lg'
            : 'hover:bg-slate-800/30 transition-colors'
        }
        loading={loading}
        pagination={{
          pageSize: 10,
          showSizeChanger: false,
          showTotal: (total) => `共 ${total} 条记录`,
        }}
        size="small"
        onRow={(record) => ({
          onClick: () => onSelectJob(record.job_id),
          className: 'cursor-pointer',
        })}
        aria-label="测试任务列表"
      />
    </div>
  )
}

export default TaskList
