import { useState, useCallback, memo, useEffect } from 'react'
import { Card, Tabs, Typography, Button, message, Empty, Spin, Badge, Select } from 'antd'
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
  UserOutlined,
  DollarOutlined,
  CalendarOutlined,
  FileTextOutlined,
} from '@ant-design/icons'
import { orderApi, agentApi } from '@/services/api'
import { useAsyncEffect } from '@/hooks/useFetchOnce'

const { Paragraph } = Typography

// Order status configuration - 更细腻的配色
const ORDER_STATUS: Record<string, {
  label: string
  icon: React.ReactNode
  color: string
  bgClass: string
  textClass: string
  borderClass: string
}> = {
  BIDDING: {
    label: '竞标中',
    icon: <ThunderboltOutlined className="text-xs" />,
    color: 'cyan',
    bgClass: 'bg-cyan-500/10',
    textClass: 'text-cyan-400',
    borderClass: 'border-cyan-500/20',
  },
  SELECTED: {
    label: '中标',
    icon: <TrophyOutlined className="text-xs" />,
    color: 'gold',
    bgClass: 'bg-amber-500/10',
    textClass: 'text-amber-400',
    borderClass: 'border-amber-500/20',
  },
  NOT_SELECTED: {
    label: '未中标',
    icon: <CloseCircleOutlined className="text-xs" />,
    color: 'default',
    bgClass: 'bg-slate-500/10',
    textClass: 'text-slate-400',
    borderClass: 'border-slate-500/20',
  },
  IN_PROGRESS: {
    label: '实施中',
    icon: <SyncOutlined spin className="text-xs" />,
    color: 'processing',
    bgClass: 'bg-blue-500/10',
    textClass: 'text-blue-400',
    borderClass: 'border-blue-500/20',
  },
  COMPLETED: {
    label: '实施完成',
    icon: <CheckCircleOutlined className="text-xs" />,
    color: 'success',
    bgClass: 'bg-emerald-500/10',
    textClass: 'text-emerald-400',
    borderClass: 'border-emerald-500/20',
  },
  DELIVERED: {
    label: '已交付',
    icon: <SendOutlined className="text-xs" />,
    color: 'success',
    bgClass: 'bg-green-500/10',
    textClass: 'text-green-400',
    borderClass: 'border-green-500/20',
  },
  CANCELLED: {
    label: '已取消',
    icon: <CloseCircleOutlined className="text-xs" />,
    color: 'default',
    bgClass: 'bg-slate-500/10',
    textClass: 'text-slate-500',
    borderClass: 'border-slate-500/20',
  },
  // Legacy compatibility
  PENDING: {
    label: '竞标中',
    icon: <ClockCircleOutlined className="text-xs" />,
    color: 'cyan',
    bgClass: 'bg-cyan-500/10',
    textClass: 'text-cyan-400',
    borderClass: 'border-cyan-500/20',
  },
  ACCEPTED: {
    label: '中标',
    icon: <TrophyOutlined className="text-xs" />,
    color: 'gold',
    bgClass: 'bg-amber-500/10',
    textClass: 'text-amber-400',
    borderClass: 'border-amber-500/20',
  },
  REJECTED: {
    label: '未中标',
    icon: <CloseCircleOutlined className="text-xs" />,
    color: 'default',
    bgClass: 'bg-slate-500/10',
    textClass: 'text-slate-400',
    borderClass: 'border-slate-500/20',
  },
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
 * StatusTag - 精细的状态标签
 */
const StatusTag = memo(({ status }: { status: string }) => {
  const config = ORDER_STATUS[status] || ORDER_STATUS.BIDDING

  return (
    <span
      className={`
        inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium
        ${config.bgClass} ${config.textClass} ${config.borderClass} border
      `}
    >
      {config.icon}
      <span>{config.label}</span>
    </span>
  )
})

StatusTag.displayName = 'StatusTag'

/**
 * OrderCard - 精细的订单卡片
 */
const OrderCard = memo(({ order, onAction }: { order: Order; onAction?: (order: Order, action: string) => void }) => {
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('zh-CN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <Card
      className="group glass-card hover:border-slate-600/50 transition-all duration-300 hover:shadow-lg hover:shadow-cyan-500/5"
      styles={{
        body: {
          padding: '20px',
        }
      }}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-4 mb-4">
        <div className="flex-1 min-w-0">
          <h4 className="text-base font-medium text-white mb-1 truncate tracking-wide">
            {order.job_title}
          </h4>
          <p className="text-xs text-slate-500 font-mono tracking-tight">
            {order.job_id}
          </p>
        </div>
        <StatusTag status={order.status} />
      </div>

      {/* Info Grid */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        {/* Employer */}
        {order.employer_name && (
          <div className="flex items-center gap-2 text-sm">
            <UserOutlined className="text-slate-500 text-xs" />
            <span className="text-slate-400 text-xs">雇主</span>
            <span className="text-slate-300 text-sm font-medium truncate">{order.employer_name}</span>
          </div>
        )}

        {/* Quote */}
        {order.quote_amount && (
          <div className="flex items-center gap-2 text-sm">
            <DollarOutlined className="text-slate-500 text-xs" />
            <span className="text-slate-400 text-xs">报价</span>
            <span className="text-cyan-400 font-mono text-sm font-medium">
              ¥{order.quote_amount.toLocaleString()}
            </span>
          </div>
        )}

        {/* Delivery Days */}
        {order.delivery_days && (
          <div className="flex items-center gap-2 text-sm">
            <CalendarOutlined className="text-slate-500 text-xs" />
            <span className="text-slate-400 text-xs">周期</span>
            <span className="text-slate-300 text-sm">{order.delivery_days} 天</span>
          </div>
        )}

        {/* Submitted Time */}
        <div className="flex items-center gap-2 text-sm">
          <ClockCircleOutlined className="text-slate-500 text-xs" />
          <span className="text-slate-400 text-xs">提交</span>
          <span className="text-slate-400 text-xs">{formatDate(order.submitted_at)}</span>
        </div>
      </div>

      {/* Proposal */}
      {order.proposal && (
        <div className="mb-4 p-3 rounded-lg bg-slate-800/30 border border-slate-700/30">
          <div className="flex items-center gap-1.5 mb-1.5">
            <FileTextOutlined className="text-slate-500 text-xs" />
            <span className="text-xs text-slate-500 font-medium">方案</span>
          </div>
          <Paragraph
            className="text-slate-300 text-sm m-0 leading-relaxed"
            ellipsis={{ rows: 2, expandable: true, symbol: '展开' }}
          >
            {order.proposal}
          </Paragraph>
        </div>
      )}

      {/* Actions */}
      {(order.status === 'SELECTED' || order.status === 'IN_PROGRESS' ||
        order.status === 'BIDDING') && (
        <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-700/30">
          {order.status === 'SELECTED' && (
            <Button
              type="primary"
              size="small"
              onClick={() => onAction?.(order, 'start')}
              className="h-7 px-4 text-xs font-medium bg-gradient-to-r from-cyan-500 to-blue-500 border-0 rounded-md"
            >
              开始执行
            </Button>
          )}
          {order.status === 'IN_PROGRESS' && (
            <Button
              type="primary"
              size="small"
              onClick={() => onAction?.(order, 'complete')}
              className="h-7 px-4 text-xs font-medium bg-gradient-to-r from-emerald-500 to-green-500 border-0 rounded-md"
            >
              完成工作
            </Button>
          )}
          {(order.status === 'BIDDING' || order.status === 'SELECTED' || order.status === 'IN_PROGRESS') && (
            <Button
              size="small"
              danger
              ghost
              onClick={() => onAction?.(order, 'cancel')}
              className="h-7 px-4 text-xs font-medium rounded-md"
            >
              取消
            </Button>
          )}
        </div>
      )}
    </Card>
  )
})

OrderCard.displayName = 'OrderCard'

/**
 * TabLabel - 精细的标签页标签
 */
const TabLabel = memo(({
  icon,
  label,
  count,
  active
}: {
  icon: React.ReactNode
  label: string
  count?: number
  active?: boolean
}) => (
  <span className={`flex items-center gap-1.5 px-1 ${active ? 'text-white' : 'text-slate-400'}`}>
    <span className="text-sm">{icon}</span>
    <span className="text-sm font-medium">{label}</span>
    {count !== undefined && count > 0 && (
      <Badge
        count={count}
        size="small"
        style={{
          backgroundColor: active ? '#06b6d4' : '#475569',
          fontSize: '10px',
          minWidth: '16px',
          height: '16px',
          lineHeight: '16px',
        }}
      />
    )}
  </span>
))

TabLabel.displayName = 'TabLabel'

/**
 * OrderListPage - 精细的接单管理页面
 */
const OrderListPage = () => {
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('all')
  const [statusCounts, setStatusCounts] = useState<Record<string, number>>({})
  const [workerAgents, setWorkerAgents] = useState<Array<{ agent_id: string; name: string }>>([])
  const [selectedWorkerId, setSelectedWorkerId] = useState<string | null>(null)

  // Fetch user's worker agents
  useEffect(() => {
    const fetchWorkerAgents = async () => {
      try {
        const res = await agentApi.list()
        const agents = res.data.agents || []
        const workers = agents.filter(
          (a: any) => a.agent_type === 'worker' || a.agent_type === 'all'
        )
        setWorkerAgents(workers)
        if (!selectedWorkerId) {
          setSelectedWorkerId('all')
        }
      } catch (err) {
        console.error('Failed to fetch worker agents:', err)
      }
    }
    fetchWorkerAgents()
  }, [])

  const fetchOrders = useCallback(async (status?: string) => {
    if (!selectedWorkerId) return
    setLoading(true)
    try {
      const res = await orderApi.list(selectedWorkerId, status === 'all' ? undefined : status)
      const data: OrdersResponse = res.data
      setOrders(data.orders || [])
      setStatusCounts(data.status_counts || {})
    } catch (err) {
      console.error('Failed to fetch orders:', err)
      message.error('获取订单列表失败')
    } finally {
      setLoading(false)
    }
  }, [selectedWorkerId])

  useAsyncEffect(() => {
    if (selectedWorkerId) {
      fetchOrders(activeTab === 'all' ? undefined : activeTab)
    }
  }, [activeTab, selectedWorkerId, fetchOrders])

  const handleOrderAction = useCallback(async (order: Order, action: string) => {
    if (!selectedWorkerId) return
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

      await orderApi.updateStatus(order.bid_id, selectedWorkerId, newStatus)
      message.success('状态更新成功')
      fetchOrders(activeTab === 'all' ? undefined : activeTab)
    } catch (err) {
      console.error('Failed to update order:', err)
      message.error('更新失败')
    }
  }, [selectedWorkerId, activeTab, fetchOrders])

  const totalCount = statusCounts ? Object.values(statusCounts).reduce((a, b) => a + b, 0) : 0

  const tabItems: TabsProps['items'] = [
    {
      key: 'all',
      label: <TabLabel icon={<span>📋</span>} label="全部" count={totalCount} active={activeTab === 'all'} />,
    },
    {
      key: 'BIDDING',
      label: <TabLabel icon={<ThunderboltOutlined />} label="竞标中" count={statusCounts?.BIDDING} active={activeTab === 'BIDDING'} />,
    },
    {
      key: 'SELECTED',
      label: <TabLabel icon={<TrophyOutlined />} label="中标" count={statusCounts?.SELECTED} active={activeTab === 'SELECTED'} />,
    },
    {
      key: 'NOT_SELECTED',
      label: <TabLabel icon={<CloseCircleOutlined />} label="未中标" count={statusCounts?.NOT_SELECTED} active={activeTab === 'NOT_SELECTED'} />,
    },
    {
      key: 'IN_PROGRESS',
      label: <TabLabel icon={<SyncOutlined />} label="实施中" count={statusCounts?.IN_PROGRESS} active={activeTab === 'IN_PROGRESS'} />,
    },
    {
      key: 'COMPLETED',
      label: <TabLabel icon={<CheckCircleOutlined />} label="已完成" active={activeTab === 'COMPLETED'} />,
    },
  ]

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold text-white m-0 tracking-wide">
            接单管理
          </h2>
          <p className="text-sm text-slate-400 mt-1">查看和管理您的竞标与订单</p>
        </div>
        <div className="flex items-center gap-3">
          {/* Worker Selector */}
          <Select
            value={selectedWorkerId}
            onChange={setSelectedWorkerId}
            placeholder="选择 Worker"
            className="min-w-[180px]"
            style={{
              borderRadius: '8px',
            }}
            options={[
              { value: 'all', label: '🤖 全部 Agent' },
              ...workerAgents.map((a) => ({
                value: a.agent_id,
                label: `${a.name}`,
              })),
            ]}
          />
          <Button
            icon={<ReloadOutlined className="text-xs" />}
            onClick={() => fetchOrders(activeTab === 'all' ? undefined : activeTab)}
            loading={loading}
            disabled={!selectedWorkerId}
            className="h-9 px-4 bg-slate-800/50 border-slate-700 text-slate-300 hover:text-white hover:border-slate-600 rounded-lg text-sm"
          >
            刷新
          </Button>
        </div>
      </div>

      {/* Stats Overview */}
      {selectedWorkerId && totalCount > 0 && (
        <div className="grid grid-cols-3 sm:grid-cols-6 gap-3">
          {Object.entries(ORDER_STATUS).slice(0, 6).map(([key, config]) => {
            const count = statusCounts[key] || 0
            if (['PENDING', 'ACCEPTED', 'REJECTED'].includes(key)) return null
            return (
              <div
                key={key}
                className={`
                  p-3 rounded-lg border cursor-pointer transition-all duration-200
                  ${activeTab === key ? 'ring-1 ring-cyan-500/50' : 'hover:border-slate-600'}
                  ${config.bgClass} ${config.borderClass}
                `}
                onClick={() => setActiveTab(key)}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className={config.textClass}>{config.icon}</span>
                  <span className="text-xs text-slate-400">{config.label}</span>
                </div>
                <div className={`text-xl font-bold ${config.textClass} font-mono`}>
                  {count}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* No Worker Message */}
      {workerAgents.length === 0 && (
        <Card className="glass-card border-slate-700/50">
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={
              <span className="text-slate-400 text-sm">
                您还没有 Worker Agent，请先创建一个
              </span>
            }
          />
        </Card>
      )}

      {/* Status Tabs */}
      {selectedWorkerId && (
        <>
          <Tabs
            activeKey={activeTab}
            onChange={setActiveTab}
            items={tabItems}
            className="order-tabs"
            style={{
              marginBottom: '16px',
            }}
          />

          {/* Order List */}
          <div className="min-h-[300px]">
            {loading ? (
              <div className="flex justify-center items-center py-16">
                <Spin size="large" />
              </div>
            ) : orders.length === 0 ? (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description={
                  <span className="text-slate-400 text-sm">
                    {activeTab === 'all' ? '暂无订单' : `暂无${ORDER_STATUS[activeTab]?.label || ''}订单`}
                  </span>
                }
                className="py-16"
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
        </>
      )}
    </div>
  )
}

export default OrderListPage