import { useState, useEffect } from 'react'
import { Card, Table, Tag, Space, Typography, Input, Button, Modal, Form, Select, message } from 'antd'
import type { TableColumnsType } from 'antd'
import { Agent } from '@/types/agent'
import { agentApi } from '@/services/api'

const { Search } = Input
const { Title } = Typography

const AgentListPage = () => {
  const [agents, setAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState(true)
  const [searchText, setSearchText] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [form] = Form.useForm()

  useEffect(() => {
    fetchAgents()
  }, [])

  const fetchAgents = async () => {
    try {
      const res = await agentApi.list()
      setAgents(res.data.agents || [])
    } catch (error) {
      message.error('获取代理列表失败')
    } finally {
      setLoading(false)
    }
  }

  const filteredAgents = agents.filter((agent) =>
    agent.name.toLowerCase().includes(searchText.toLowerCase()) ||
    agent.capabilities.some((cap) => cap.toLowerCase().includes(searchText.toLowerCase()))
  )

  const columns: TableColumnsType<Agent> = [
    {
      title: '代理ID',
      dataIndex: 'agent_id',
      key: 'agent_id',
      width: 150,
    },
    {
      title: '姓名',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '类型',
      dataIndex: 'agent_type',
      key: 'agent_type',
      width: 100,
      render: (type) => <Tag color={type === 'employer' ? 'blue' : 'green'}>{type === 'employer' ? '雇主' : '打工人'}</Tag>,
    },
    {
      title: '技能标签',
      key: 'capabilities',
      render: (_, record) => (
        <Space size={[8, 0]} wrap>
          {record.capabilities.map((cap) => (
            <Tag key={cap} color="purple">{cap}</Tag>
          ))}
        </Space>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => {
        const colors: Record<string, string> = {
          idle: 'green',
          busy: 'orange',
          offline: 'gray',
        }
        return <Tag color={colors[status] || 'default'}>{status === 'idle' ? '空闲' : status === 'busy' ? '工作中' : '离线'}</Tag>
      },
    },
    {
      title: '完成任务',
      dataIndex: 'completed_jobs',
      key: 'completed_jobs',
      width: 100,
    },
    {
      title: '评分',
      dataIndex: 'rating',
      key: 'rating',
      width: 100,
      render: (rating) => <Tag color={rating >= 4.5 ? 'gold' : 'default'}>{rating.toFixed(1)}★</Tag>,
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_, record) => (
        <Space size="small">
          <Button type="link" size="small">详情</Button>
        </Space>
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
    <Card>
      <div className="flex justify-between items-center mb-4">
        <Title level={3} className="m-0">
          代理管理
        </Title>
        <Button type="primary" onClick={() => setModalOpen(true)}>
          + 添加代理
        </Button>
      </div>

      <Search
        placeholder="搜索代理ID、姓名或技能..."
        allowClear
        enterButton="搜索"
        size="middle"
        value={searchText}
        onChange={(e) => setSearchText(e.target.value)}
        className="mb-4"
      />

      <Table
        dataSource={filteredAgents}
        columns={columns}
        rowKey="agent_id"
        loading={loading}
        pagination={{
          pageSize: 20,
          showSizeChanger: true,
        }}
      />

      <Modal
        title="添加新代理"
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        footer={null}
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
            <Input placeholder="例如: worker_001" />
          </Form.Item>

          <Form.Item
            name="agent_type"
            label="类型"
            rules={[{ required: true, message: '请选择类型' }]}
          >
            <Select>
              <Select.Option value="worker">打工人</Select.Option>
              <Select.Option value="employer">雇主</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="name"
            label="姓名"
            rules={[{ required: true, message: '请输入姓名' }]}
          >
            <Input placeholder="例如: Python开发虾" />
          </Form.Item>

          <Form.Item
            name="capabilities"
            label="技能标签"
            rules={[{ required: true, message: '请输入技能标签' }]}
          >
            <Select mode="tags" placeholder="例如: python,fastapi,react">
              <Select.Option value="python">Python</Select.Option>
              <Select.Option value="fastapi">FastAPI</Select.Option>
              <Select.Option value="react">React</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" block>
              确认添加
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  )
}

export default AgentListPage
