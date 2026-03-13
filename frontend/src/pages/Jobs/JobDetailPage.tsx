import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { Card, Typography, Tag, Space, Tabs, Table, Button, message, Avatar } from 'antd'
import type { TableColumnsType } from 'antd'
import { Job } from '@/types/job'
import { Bid } from '@/types/bid'
import { jobApi, bidApi } from '@/services/api'

const { Title, Text } = Typography

const JobDetailPage = () => {
  const { jobId } = useParams<{ jobId: string }>()
  const [job, setJob] = useState<Job | null>(null)
  const [bids, setBids] = useState<Bid[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('1')

  useEffect(() => {
    if (jobId) {
      fetchJobDetail()
    }
  }, [jobId])

  const fetchJobDetail = async () => {
    if (!jobId) return
    try {
      const [jobRes, bidsRes] = await Promise.all([
        jobApi.get(jobId),
        bidApi.list(jobId),
      ])
      setJob(jobRes.data)
      setBids(bidsRes.data.bids || [])
    } catch (error) {
      message.error('获取任务详情失败')
    } finally {
      setLoading(false)
    }
  }

  const handleAcceptBid = async (bidId: string) => {
    if (!jobId) return
    try {
      await bidApi.accept(jobId, bidId)
      message.success('竞标已接受')
      fetchJobDetail()
    } catch (error) {
      message.error('接受竞标失败')
    }
  }

  const handleRejectBid = async (bidId: string) => {
    if (!jobId) return
    try {
      await bidApi.reject(jobId, bidId)
      message.success('竞标已拒绝')
      fetchJobDetail()
    } catch (error) {
      message.error('拒绝竞标失败')
    }
  }

  const bidColumns: TableColumnsType<Bid> = [
    {
      title: ' worker',
      key: 'worker',
      render: (_: any, bid: Bid) => (
        <Space>
          <Avatar>{bid.worker_name?.charAt(0) || 'W'}</Avatar>
          <div>
            <Text strong>{bid.worker_name || bid.worker_id}</Text>
            <div className="text-xs text-gray-500">评分: {bid.worker_rating?.toFixed(1) || '-'}★</div>
          </div>
        </Space>
      ),
    },
    {
      title: '方案',
      key: 'proposal',
      render: (_: any, bid: Bid) => <Text>{bid.proposal}</Text>,
    },
    {
      title: '报价',
      key: 'quote',
      render: (_: any, bid: Bid) => (
        <Text>
          ¥{bid.quote?.amount || '-'} / {bid.quote?.delivery_days || '-'}天
        </Text>
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, bid: Bid) => {
        if (bid.is_hired) {
          return <Tag color="success">已接受</Tag>
        }
        return (
          <Space size="small">
            <Button size="small" type="primary" onClick={() => handleAcceptBid(bid.bid_id)}>
              接受
            </Button>
            <Button size="small" onClick={() => handleRejectBid(bid.bid_id)}>
              拒绝
            </Button>
          </Space>
        )
      },
    },
  ]

  const items = [
    {
      key: '1',
      label: `竞标列表 (${bids.length})`,
      children: (
        <Card>
          <Table
            dataSource={bids}
            columns={bidColumns}
            rowKey="bid_id"
            pagination={false}
            size="small"
          />
        </Card>
      ),
    },
    {
      key: '2',
      label: '消息',
      children: (
        <Card>
          <Text>消息功能开发中...</Text>
        </Card>
      ),
    },
  ]

  if (loading) {
    return <div>加载中...</div>
  }

  if (!job) {
    return <div>任务不存在</div>
  }

  return (
    <div className="space-y-4">
      <Button type="link" onClick={() => window.history.back()}>&larr; 返回列表</Button>

      <Card>
        <Title level={3}>{job.title}</Title>
        <Space size="small" className="mb-2">
          <Tag color={job.status === 'OPEN' ? 'green' : job.status === 'ACTIVE' ? 'blue' : 'gray'}>{job.status}</Tag>
          {job.required_tags.map((tag) => (
            <Tag key={tag} color="purple">{tag}</Tag>
          ))}
        </Space>
        <Text type="secondary">{job.description}</Text>

        <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <Text type="secondary">预算</Text>
            <div>¥{job.budget_min || '-'} - ¥{job.budget_max || '-'}</div>
          </div>
          <div>
            <Text type="secondary">竞标上限</Text>
            <div>{job.bid_limit}</div>
          </div>
          <div>
            <Text type="secondary">当前竞标</Text>
            <div>{job.bid_count}</div>
          </div>
          <div>
            <Text type="secondary">创建时间</Text>
            <div>{new Date(job.created_at).toLocaleDateString()}</div>
          </div>
        </div>
      </Card>

      <Tabs activeKey={activeTab} onChange={setActiveTab} items={items} />
    </div>
  )
}

export default JobDetailPage
