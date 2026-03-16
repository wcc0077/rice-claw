import { Button, message, Modal, Form, Input, InputNumber } from 'antd'
import { useState } from 'react'
import {
  PlusOutlined,
  ThunderboltOutlined,
  SwapOutlined,
  LockOutlined,
  PlayCircleOutlined,
  CheckCircleOutlined,
  WalletOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons'
import { matchingApi } from '@/services/api'
import { TEST_FIXTURES } from '@/config/test-fixtures'
import { AgentSelector } from '@/components/AgentSelector'

interface ActionPanelProps {
  jobId: string | null
  jobStatus: string
  selectedBidId: string | null
  workerId: string | null
  selectedAgentId: string | null
  onAgentChange: (agentId: string) => void
  onActionComplete: () => void
}

interface CreateJobFormData {
  title: string
  description: string
  budget_min: number
  budget_max: number
  required_tags: string
  agent_id: string
}

/**
 * ActionPanel - 操作面板
 * 包含 8 个核心操作按钮，根据任务状态启用/禁用
 *
 * 状态流转：
 * OPEN → [2.抢单] → BIDDING → [3.派单] → LOCKED → [4.确认订金] →
 * LOCKED → [5.开始工作] → WORKING → [6.交付] → SELECTED →
 * [7.确认收货] → SELECTED → [8.支付尾款] → CLOSED
 */
const ActionPanel = ({
  jobId,
  jobStatus,
  selectedBidId,
  workerId,
  selectedAgentId,
  onAgentChange,
  onActionComplete,
}: ActionPanelProps) => {
  const [loading, setLoading] = useState<string | null>(null)
  const [modalOpen, setModalOpen] = useState(false)
  const [form] = Form.useForm()

  // Check if action is enabled based on job status
  const isActionEnabled = (action: string) => {
    if (!jobId) return false

    const actionMap: Record<string, boolean> = {
      create: !jobId, // Only enabled when no job selected
      grab: jobStatus === 'OPEN',
      dispatch: jobStatus === 'BIDDING' && !!selectedBidId,
      lockPayment: jobStatus === 'LOCKED' && !!selectedBidId && !!workerId,
      workerReady: jobStatus === 'LOCKED',
      deliver: jobStatus === 'WORKING',
      confirmDelivery: jobStatus === 'SELECTED',
      finalPayment: jobStatus === 'SELECTED',
      close: jobStatus === 'SELECTED',
    }

    return actionMap[action] || false
  }

  // Handle create job
  const handleCreateJob = async () => {
    setModalOpen(true)
  }

  const handleCreateJobSubmit = async (values: CreateJobFormData) => {
    try {
      setLoading('create')
      const payload = {
        employer_id: values.agent_id,
        title: values.title,
        description: values.description,
        required_tags: values.required_tags.split(',').map((t) => t.trim()).filter(Boolean),
        reward_amount: values.budget_min,
        budget_min: values.budget_min,
        budget_max: values.budget_max,
        bid_limit: 3,
      }
      await matchingApi.publishJob(payload)
      message.success('任务创建成功')
      setModalOpen(false)
      form.resetFields()
      onActionComplete()
    } catch (err: any) {
      console.error('Failed to create job:', err)
      const errorMsg = err?.response?.data?.detail || '创建任务失败'
      message.error(errorMsg)
    } finally {
      setLoading(null)
    }
  }

  // Handle grab order
  const handleGrabOrder = async () => {
    if (!jobId || !selectedAgentId) {
      message.warning('请先选择接单 Agent')
      return
    }

    try {
      setLoading('grab')
      await matchingApi.grabOrder(jobId, {
        worker_id: selectedAgentId,
        proposal: TEST_FIXTURES.DEFAULT_PROPOSAL,
        quote: TEST_FIXTURES.DEFAULT_QUOTE,
      })
      message.success('抢单成功')
      onActionComplete()
    } catch (err: any) {
      console.error('Failed to grab order:', err)
      const errorMsg = err?.response?.data?.detail || '抢单失败'
      message.error(errorMsg)
    } finally {
      setLoading(null)
    }
  }

  // Handle dispatch order
  const handleDispatchOrder = async () => {
    if (!jobId || !selectedBidId) return

    try {
      setLoading('dispatch')
      await matchingApi.dispatchOrder(jobId, {
        selected_bid_ids: [selectedBidId],
        employer_id: TEST_FIXTURES.DEFAULT_EMPLOYER_ID,
      })
      message.success('派单成功')
      onActionComplete()
    } catch (err: any) {
      console.error('Failed to dispatch order:', err)
      const errorMsg = err?.response?.data?.detail || '派单失败'
      message.error(errorMsg)
    } finally {
      setLoading(null)
    }
  }

  // Handle lock payment (confirm deposit)
  const handleLockPayment = async () => {
    if (!jobId || !selectedBidId || !workerId) return

    try {
      setLoading('lockPayment')
      await matchingApi.lockPayment(jobId, {
        bid_id: selectedBidId,
        worker_id: workerId,
        transaction_id: `test_tx_${Date.now()}`,
      })
      message.success('订金支付确认成功')
      onActionComplete()
    } catch (err: any) {
      console.error('Failed to lock payment:', err)
      const errorMsg = err?.response?.data?.detail || '订金支付确认失败'
      message.error(errorMsg)
    } finally {
      setLoading(null)
    }
  }

  // Handle worker ready (start working)
  const handleWorkerReady = async () => {
    if (!jobId || !workerId) return

    try {
      setLoading('workerReady')
      await matchingApi.confirmWorkerReady({
        worker_id: workerId,
      })
      message.success('工人已就绪，开始工作')
      onActionComplete()
    } catch (err: any) {
      console.error('Failed to confirm worker ready:', err)
      const errorMsg = err?.response?.data?.detail || '开始工作失败'
      message.error(errorMsg)
    } finally {
      setLoading(null)
    }
  }

  // Handle deliver (worker delivers work)
  const handleDeliver = async () => {
    if (!jobId) return

    try {
      setLoading('deliver')
      // This would normally create an artifact
      // For testing, we might need a test endpoint
      message.info('交付功能需要创建交付物，请使用测试专用端点')
      onActionComplete()
    } catch (err: any) {
      console.error('Failed to deliver:', err)
      const errorMsg = err?.response?.data?.detail || '交付失败'
      message.error(errorMsg)
    } finally {
      setLoading(null)
    }
  }

  // Handle confirm delivery
  const handleConfirmDelivery = async () => {
    if (!jobId) return

    try {
      setLoading('confirmDelivery')
      // This might need a test endpoint or update job status
      message.info('确认收货功能需要更新任务状态')
      onActionComplete()
    } catch (err: any) {
      console.error('Failed to confirm delivery:', err)
      const errorMsg = err?.response?.data?.detail || '确认收货失败'
      message.error(errorMsg)
    } finally {
      setLoading(null)
    }
  }

  // Handle final payment
  const handleFinalPayment = async () => {
    if (!jobId || !selectedBidId) return

    try {
      setLoading('finalPayment')
      await matchingApi.finalPayment({
        winner_bid_id: selectedBidId,
        transaction_id: `test_tx_${Date.now()}`,
      })
      message.success('尾款支付成功')
      onActionComplete()
    } catch (err: any) {
      console.error('Failed to make final payment:', err)
      const errorMsg = err?.response?.data?.detail || '尾款支付失败'
      message.error(errorMsg)
    } finally {
      setLoading(null)
    }
  }

  // Handle close job
  const handleCloseJob = async () => {
    if (!jobId) return

    try {
      setLoading('close')
      await matchingApi.closeJob(jobId, {
        winner_bid_id: selectedBidId || undefined,
      })
      message.success('任务已关闭')
      onActionComplete()
    } catch (err: any) {
      console.error('Failed to close job:', err)
      const errorMsg = err?.response?.data?.detail || '关闭任务失败'
      message.error(errorMsg)
    } finally {
      setLoading(null)
    }
  }

  const buttonStyle = "h-auto py-3 px-4 flex flex-col items-center justify-center gap-1"

  return (
    <>
      <div className="glass-card p-6">
        <h3 className="text-lg font-semibold text-white mb-4">操作面板</h3>

        {/* Agent Selector */}
        <div className="mb-4">
          <label className="block text-sm text-slate-300 mb-2">
            接单 Agent
          </label>
          <AgentSelector
            value={selectedAgentId || undefined}
            onChange={onAgentChange}
            placeholder="选择要使用的 Agent"
          />
        </div>

        <div className="grid grid-cols-4 gap-3">
          {/* 1. 创建任务 */}
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleCreateJob}
            loading={loading === 'create'}
            className={buttonStyle}
            size="large"
          >
            <span className="text-sm">1. 创建任务</span>
          </Button>

          {/* 2. 抢单 */}
          <Button
            type="primary"
            icon={<ThunderboltOutlined />}
            onClick={handleGrabOrder}
            loading={loading === 'grab'}
            disabled={!isActionEnabled('grab')}
            className={buttonStyle}
            size="large"
          >
            <span className="text-sm">2. 抢单</span>
          </Button>

          {/* 3. 派单 */}
          <Button
            type="primary"
            icon={<SwapOutlined />}
            onClick={handleDispatchOrder}
            loading={loading === 'dispatch'}
            disabled={!isActionEnabled('dispatch')}
            className={buttonStyle}
            size="large"
          >
            <span className="text-sm">3. 派单</span>
          </Button>

          {/* 4. 确认订金 */}
          <Button
            type="primary"
            icon={<LockOutlined />}
            onClick={handleLockPayment}
            loading={loading === 'lockPayment'}
            disabled={!isActionEnabled('lockPayment')}
            className={buttonStyle}
            size="large"
          >
            <span className="text-sm">4. 订金</span>
          </Button>

          {/* 5. 开始工作 */}
          <Button
            type="primary"
            icon={<PlayCircleOutlined />}
            onClick={handleWorkerReady}
            loading={loading === 'workerReady'}
            disabled={!isActionEnabled('workerReady')}
            className={buttonStyle}
            size="large"
          >
            <span className="text-sm">5. 开始</span>
          </Button>

          {/* 6. 交付 */}
          <Button
            type="primary"
            icon={<CheckCircleOutlined />}
            onClick={handleDeliver}
            loading={loading === 'deliver'}
            disabled={!isActionEnabled('deliver')}
            className={buttonStyle}
            size="large"
          >
            <span className="text-sm">6. 交付</span>
          </Button>

          {/* 7. 确认收货 */}
          <Button
            type="primary"
            icon={<CheckCircleOutlined />}
            onClick={handleConfirmDelivery}
            loading={loading === 'confirmDelivery'}
            disabled={!isActionEnabled('confirmDelivery')}
            className={buttonStyle}
            size="large"
          >
            <span className="text-sm">7. 确认</span>
          </Button>

          {/* 8. 支付尾款 */}
          <Button
            type="primary"
            icon={<WalletOutlined />}
            onClick={handleFinalPayment}
            loading={loading === 'finalPayment'}
            disabled={!isActionEnabled('finalPayment')}
            className={buttonStyle}
            size="large"
          >
            <span className="text-sm">8. 尾款</span>
          </Button>

          {/* 9. 关闭任务 */}
          <Button
            danger
            icon={<CloseCircleOutlined />}
            onClick={handleCloseJob}
            loading={loading === 'close'}
            disabled={!isActionEnabled('close')}
            className={buttonStyle}
            size="large"
          >
            <span className="text-sm">9. 关闭</span>
          </Button>
        </div>

        {/* Status hint */}
        <div className="mt-4 p-3 bg-slate-800/50 rounded-lg">
          <div className="text-sm text-slate-400">
            <strong className="text-slate-300">当前状态:</strong> {jobStatus || '无'}
          </div>
          <div className="text-xs text-slate-500 mt-1">
            已选竞标：{selectedBidId || '无'} | 工人 ID: {workerId || '无'}
          </div>
        </div>
      </div>

      {/* Create Job Modal */}
      <Modal
        title="创建测试任务"
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        footer={null}
        width={500}
        className="dark-modal"
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreateJobSubmit}
        >
          <Form.Item
            name="agent_id"
            label="雇主 ID"
            rules={[{ required: true, message: '请输入雇主 ID' }]}
            initialValue="test_employer_001"
          >
            <Input placeholder="test_employer_001" className="bg-slate-800/50" />
          </Form.Item>

          <Form.Item
            name="title"
            label="任务标题"
            rules={[{ required: true, message: '请输入任务标题' }]}
          >
            <Input placeholder="测试任务" className="bg-slate-800/50" />
          </Form.Item>

          <Form.Item
            name="description"
            label="任务描述"
            rules={[{ required: true, message: '请输入任务描述' }]}
          >
            <Input.TextArea
              rows={3}
              placeholder="这是一个测试任务..."
              className="bg-slate-800/50"
            />
          </Form.Item>

          <Form.Item
            name="required_tags"
            label="技能标签 (逗号分隔)"
            rules={[{ required: true, message: '请输入技能标签' }]}
            initialValue="python,fastapi"
          >
            <Input placeholder="python,fastapi,react" className="bg-slate-800/50" />
          </Form.Item>

          <div className="grid grid-cols-2 gap-4">
            <Form.Item
              name="budget_min"
              label="最低预算"
              rules={[{ required: true, message: '请输入最低预算' }]}
              initialValue={1000}
            >
              <InputNumber prefix="¥" min={0} className="w-full bg-slate-800/50" />
            </Form.Item>

            <Form.Item
              name="budget_max"
              label="最高预算"
              rules={[{ required: true, message: '请输入最高预算' }]}
              initialValue={5000}
            >
              <InputNumber prefix="¥" min={0} className="w-full bg-slate-800/50" />
            </Form.Item>
          </div>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              block
              loading={loading === 'create'}
              className="bg-gradient-to-r from-cyan-500 to-purple-500 border-0"
            >
              创建任务
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </>
  )
}

export default ActionPanel
