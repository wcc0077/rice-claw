import { Table, Tag, Space, Button, Typography } from 'antd'
import type { TableColumnsType } from 'antd'
import { Link } from 'react-router-dom'
import { Job } from '@/types/job'

const { Text } = Typography

interface RecentJobsTableProps {
  jobs: Job[]
}

const RecentJobsTable = ({ jobs }: RecentJobsTableProps) => {
  const columns: TableColumnsType<Job> = [
    {
      title: '任务ID',
      dataIndex: 'job_id',
      key: 'job_id',
      width: 120,
    },
    {
      title: '任务标题',
      dataIndex: 'title',
      key: 'title',
      render: (_, record) => (
        <Link to={`/jobs/${record.job_id}`}>
          <Text strong>{record.title}</Text>
        </Link>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => {
        const colors: Record<string, string> = {
          OPEN: 'green',
          ACTIVE: 'blue',
          REVIEW: 'orange',
          CLOSED: 'gray',
        }
        return <Tag color={colors[status] || 'default'}>{status}</Tag>
      },
    },
    {
      title: '竞标数',
      dataIndex: 'bid_count',
      key: 'bid_count',
      width: 90,
    },
    {
      title: '预算',
      key: 'budget',
      render: (_, record) => (
        <Text>{record.budget_min ? `¥${record.budget_min}` : '-'} - {record.budget_max ? `¥${record.budget_max}` : '-'}</Text>
      ),
    },
    {
      title: '剩余时间',
      key: 'deadline',
      render: (_, record) => {
        if (!record.deadline) return '-'
        const daysLeft = Math.ceil((new Date(record.deadline).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24))
        if (daysLeft < 0) return <Text type="danger">已过期</Text>
        return <Text>{daysLeft} 天</Text>
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_, record) => (
        <Space size="small">
          <Button type="link" size="small">
            查看
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <Table
      dataSource={jobs}
      columns={columns}
      rowKey="job_id"
      pagination={false}
      size="small"
    />
  )
}

export default RecentJobsTable
