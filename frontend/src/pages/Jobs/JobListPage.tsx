import { useState, useEffect } from 'react'
import { Card, Table, Tag, Space, Typography, Button, Modal, Form, Input, InputNumber, Select, message } from 'antd'
import type { TableColumnsType } from 'antd'
import { Job } from '@/types/job'
import { jobApi } from '@/services/api'
import { getStatusBadgeColor } from '@/utils/formatters'

const { Title } = Typography

const JobListPage = () => {
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [modalOpen, setModalOpen] = useState(false)
  const [form] = Form.useForm()

  useEffect(() => {
    fetchJobs()
  }, [])

  const fetchJobs = async () => {
    try {
      const res = await jobApi.list(statusFilter === 'all' ? undefined : { status: statusFilter })
      setJobs(res.data.jobs || [])
    } catch (error) {
      message.error('获取任务列表失败')
    } finally {
      setLoading(false)
    }
  }

  const filteredJobs = statusFilter === 'all'
    ? jobs
    : jobs.filter((job) => job.status === statusFilter)

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
        <Typography.Text strong>{record.title}</Typography.Text>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => (
        <Tag color={getStatusBadgeColor(status)}>{status}</Tag>
      ),
    },
    {
      title: '技能标签',
      key: 'tags',
      render: (_, record) => (
        <Space size={[8, 0]} wrap>
          {record.required_tags.map((tag) => (
            <Tag key={tag} color="purple">{tag}</Tag>
          ))}
        </Space>
      ),
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
        <Typography.Text>
          {record.budget_min ? `¥${record.budget_min}` : '-'} - {record.budget_max ? `¥${record.budget_max}` : '-'}
        </Typography.Text>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_, record) => (
        <Space size="small">
          <Button type="link" size="small">
            查看
          </Button>
          <Button type="link" size="small" danger>
            关闭
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <Card>
      <div className="flex justify-between items-center mb-4 flex-wrap gap-2">
        <Title level={3} className="m-0">
          任务管理
        </Title>
        <Space>
          <Button onClick={() => setStatusFilter('all')}>全部</Button>
          <Button onClick={() => setStatusFilter('OPEN')} type={statusFilter === 'OPEN' ? 'primary' : 'default'}>
            待接单
          </Button>
          <Button onClick={() => setStatusFilter('ACTIVE')} type={statusFilter === 'ACTIVE' ? 'primary' : 'default'}>
            进行中
          </Button>
          <Button onClick={() => setStatusFilter('CLOSED')} type={statusFilter === 'CLOSED' ? 'primary' : 'default'}>
            已完成
          </Button>
        </Space>
        <Button type="primary" onClick={() => setModalOpen(true)}>
          + 发布新任务
        </Button>
      </div>

      <Table
        dataSource={filteredJobs}
        columns={columns}
        rowKey="job_id"
        loading={loading}
        pagination={{
          pageSize: 20,
          showSizeChanger: true,
        }}
      />

      <Modal
        title="发布新任务"
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={async (values) => {
            try {
              await jobApi.create(values)
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
            <Input placeholder="例如: 开发 MCP 数据接口" />
          </Form.Item>

          <Form.Item
            name="description"
            label="任务描述"
            rules={[{ required: true, message: '请输入任务描述' }]}
          >
            <Input.TextArea rows={4} placeholder="详细描述任务要求..." />
          </Form.Item>

          <Form.Item
            name="required_tags"
            label="所需技能"
            rules={[{ required: true, message: '请选择所需技能' }]}
          >
            <Select mode="tags" placeholder="例如: python, fastapi, react">
              <Select.Option value="python">Python</Select.Option>
              <Select.Option value="fastapi">FastAPI</Select.Option>
              <Select.Option value="react">React</Select.Option>
              <Select.Option value="figma">Figma</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="budget_min"
            label="最低预算"
          >
            <InputNumber prefix="¥" min={0} placeholder="1000" />
          </Form.Item>

          <Form.Item
            name="budget_max"
            label="最高预算"
          >
            <InputNumber prefix="¥" min={0} placeholder="5000" />
          </Form.Item>

          <Form.Item
            name="bid_limit"
            label="竞标上限"
            initialValue={5}
          >
            <InputNumber min={1} max={20} />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" block>
              发布任务
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  )
}

export default JobListPage
