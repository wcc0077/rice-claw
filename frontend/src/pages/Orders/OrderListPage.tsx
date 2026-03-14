import { useState, useEffect, useCallback, memo } from 'react'
import { Card, Tabs, Typography, Button, message, Empty, Spin, Badge } from 'antd'
import type { TabsProps } from 'antd'
import {
  ThunderboltOutlined,
  TrophyOutlined,
  CloseCircleOutlined,
  SyncOutlined,
  CheckCircleOutlined,
  SendOutlined,
  ClockCircleOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import { orderApi } from '@/services/api'
import { useAsyncEffect } from '@/hooks/useFetchOnce'

const { Title, Text, Paragraph } = Typography

// Order status configuration
const ORDER_STATUS = {
  BIDDING: {
    label: '竞标中',
    icon: <ThunderboltOutlined />,
    color: 'cyan',
    description: '等待雇主选择',
  },
  SELECTED: {
    label: '中标',
    icon: <TrophyOutlined />,
    color: 'gold',
    description: '恭喜！您已被选中',
  },
  NOT_SELECTED: {
    label: '未中标',
    icon: <CloseCircleOutlined />,
    color: 'default',
    description: '雇主选择了其他竞标者',
  },
  IN_PROGRESS: {
    label: '实施中',
    icon: <SyncOutlined spin />,
    color: 'processing',
    description: '正在执行任务',
  },
  COMPLETED: {
    label: '实施完成',
    icon: <CheckCircleOutlined />,
    color: 'success',
    description: '工作已完成，等待确认',
  },
  DELIVERED: {
    label: '已交付',
    icon: <SendOutlined />,
    color: 'success',
    description: '已成功交付',
  },
  CANCELLED: {
    label: '已取消',
    icon: <CloseCircleOutlined />,
    color: 'default',
    description: '订单已取消',
  },
  // Legacy compatibility
  PENDING: { label: '竞标中', icon: <ClockCircleOutlined />, color: 'cyan', description: '等待处理' },
  ACCEPTED: { label: '中标', icon: <TrophyOutlined />, color: 'gold', description: '已被选中' },
  REJECTED: { label: '未中标', icon: <CloseCircleOutlined />, color: 'default', description: '未被选中' },
}

interface Order {
  bid_id: string
  job_id: string
  job_title: string
  job_description?: string
  employer_id: string
  employer_name?: string
  status: string
  status_label: string
  proposal?: string
  quote_amount?: number
  quote_currency: string
  delivery_days?: number
  submitted_at: string
}

interface OrdersResponse {
  orders: Order[]
  pagination: {
    total: number
    page: number
    limit: number
    has_more: boolean
  }
  status_counts: Record<string, number>
}

/**
 * OrderCard - Single order display card
 */
const OrderCard = memo(({ order, onAction }: { order: Order; onAction?: (order: Order, action: string) => void }) => {
  const statusConfig = ORDER_STATUS[order.status as keyof typeof ORDER_STATUS] || ORDER_STATUS.BIDDING

  return (
    <Card
      className="glass-card hover:border-cyan-500/30 transition-all"
      styles={{ body: { padding: '16px' } }}
    >
      <div className="flex flex-col gap-3">
        {/* Header: Title + Status */}
        <div className="flex justify-between items-start gap-3">
          <div className="flex-1 min-w-0">
            <Title level={5} className="text-white m-0 truncate">
              {order.job_title}
            </Title>
            <Text className="text-slate-500 text-xs font-mono">
              {order.job_id}
            </Text>
          </div>
          <Badge
            status={statusConfig.color as 'success' | 'processing' | 'default' | 'error' | 'warning'}
            text={
              <span className="flex items-center gap-1 text-sm">
                {statusConfig.icon}
                {statusConfig.label}
              </span>
            }
          />
        </div>

        {/* Employer */}
        {order.employer_name && (
          <div className="flex items-center gap-2">
            <Text className="text-slate-400 text-sm">雇主:</Text>
            <Text className="text-slate-300">{order.employer_name}</Text>
          </div>
        )}

        {/* Quote Info */}
        <div className="flex flex-wrap gap-4 text-sm">
          {order.quote_amount && (
            <div className="flex items-center gap-1">
              <Text className="text-slate-400">报价:</Text>
              <Text className="text-cyan-400 font-mono">
                ¥{order.quote_amount.toLocaleString()}
              </Text>
            </div>
          )}
          {order.delivery_days && (
            <div className="flex items-center gap-1">
              <Text className="text-slate-400">交付周期:</Text>
              <Text className="text-slate-300">{order.delivery_days} 天</Text>
            </div>
          )}
        </div>

        {/* Proposal */}
        {order.proposal && (
          <Paragraph
            className="text-slate-400 text-sm m-0"
            ellipsis={{ rows: 2, expandable: true }}
          >
            {order.proposal}
          </Paragraph>
        )}

        {/* Actions */}
        <div className="flex justify-end gap-2 pt-2 border-t border-slate-700/50">
          {order.status === 'SELECTED' && (
            <Button
              type="primary"
              size="small"
              onClick={() => onAction?.(order, 'start')}
              className="bg-cyan-500"
            >
              开始执行
            </Button>
          )}
          {order.status === 'IN_PROGRESS' && (
            <Button
              type="primary"
              size="small"
              onClick={() => onAction?.(order, 'complete')}
              className="bg-green-500"
            >
              完成工作
            </Button>
          )}
          {(order.status === 'BIDDING' || order.status === 'SELECTED' || order.status === 'IN_PROGRESS') && (
            <Button
              size="small"
              danger
              onClick={() => onAction?.(order, 'cancel')}
            >
              取消
            </Button>
          )}
        </div>

        {/* Timestamp */}
        <Text className="text-slate-600 text-xs">
          提交于 {new Date(order.submitted_at).toLocaleString('zh-CN')}
        </Text>
      </div>
    </Card>
  )
})

OrderCard.displayName = 'OrderCard'

/**
 * OrderListPage - Worker's order management page
 */
const OrderListPage = () => {
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('all')
  const [statusCounts, setStatusCounts] = useState<Record<string, number>>({})

  // Mock worker ID - in real app, get from auth store
  const workerId = 'worker_001'

  const fetchOrders = useCallback(async (status?: string) => {
    setLoading(true)
    try {
      const res = await orderApi.list(workerId, status === 'all' ? undefined : status)
      const data: OrdersResponse = res.data
      setOrders(data.orders || [])
      setStatusCounts(data.status_counts || {})
    } catch (err) {
      console.error('Failed to fetch orders:', err)
      message.error('获取订单列表失败')
    } finally {
      setLoading(false)
    }
  }, [workerId])

  // Use custom hook to prevent duplicate calls in StrictMode
  useAsyncEffect(() => fetchOrders(activeTab === 'all' ? undefined : activeTab), [activeTab, fetchOrders])

  const handleOrderAction = useCallback(async (order: Order, action: string) => {
    try {
      let newStatus: string
      switch (action) {
        case 'start':
          newStatus = 'IN_PROGRESS'
          break
        case 'complete':
          newStatus = 'COMPLETED'
          break
        case 'cancel':
          newStatus = 'CANCELLED'
          break
        default:
          return
      }

      await orderApi.updateStatus(order.bid_id, workerId, newStatus)
      message.success('状态更新成功')
      fetchOrders(activeTab === 'all' ? undefined : activeTab)
    } catch (err) {
      console.error('Failed to update order:', err)
      message.error('更新失败')
    }
  }, [workerId, activeTab, fetchOrders])

  // Group orders by status for tabs
  const tabItems: TabsProps['items'] = [
    {
      key: 'all',
      label: (
        <span className="flex items-center gap-1">
          全部
          {statusCounts && Object.values(statusCounts).reduce((a, b) => a + b, 0) > 0 && (
            <Badge count={Object.values(statusCounts).reduce((a, b) => a + b, 0)} size="small" />
          )}
        </span>
      ),
    },
    {
      key: 'BIDDING',
      label: (
        <span className="flex items-center gap-1">
          <ThunderboltOutlined />
          竞标中
          {statusCounts?.BIDDING > 0 && <Badge count={statusCounts.BIDDING} size="small" />}
        </span>
      ),
    },
    {
      key: 'SELECTED',
      label: (
        <span className="flex items-center gap-1">
          <TrophyOutlined />
          中标
          {statusCounts?.SELECTED > 0 && <Badge count={statusCounts.SELECTED} size="small" style={{ backgroundColor: '#52c41a' }} />}
        </span>
      ),
    },
    {
      key: 'IN_PROGRESS',
      label: (
        <span className="flex items-center gap-1">
          <SyncOutlined />
          实施中
          {statusCounts?.IN_PROGRESS > 0 && <Badge count={statusCounts.IN_PROGRESS} size="small" />}
        </span>
      ),
    },
    {
      key: 'COMPLETED',
      label: (
        <span className="flex items-center gap-1">
          <CheckCircleOutlined />
          已完成
        </span>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <Title level={3} className="text-white m-0">
            接单管理
          </Title>
          <Text className="text-slate-400">查看和管理您的竞标和订单</Text>
        </div>
        <Button
          icon={<ReloadOutlined />}
          onClick={() => fetchOrders(activeTab === 'all' ? undefined : activeTab)}
          loading={loading}
          className="bg-slate-800/50 border-slate-700 text-slate-300"
        >
          刷新
        </Button>
      </div>

      {/* Status Tabs */}
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={tabItems}
        className="order-tabs"
      />

      {/* Order List */}
      <div className="min-h-[300px]">
        {loading ? (
          <div className="flex justify-center items-center py-12">
            <Spin size="large" />
          </div>
        ) : orders.length === 0 ? (
          <Empty
            description={
              <span className="text-slate-400">
                {activeTab === 'all' ? '暂无订单' : `暂无${ORDER_STATUS[activeTab as keyof typeof ORDER_STATUS]?.label || ''}订单`}
              </span>
            }
            className="py-12"
          />
        ) : (
          <div className="grid gap-4">
            {orders.map((order) => (
              <OrderCard
                key={order.bid_id}
                order={order}
                onAction={handleOrderAction}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default OrderListPage