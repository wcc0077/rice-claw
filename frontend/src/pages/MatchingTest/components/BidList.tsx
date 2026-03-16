import { Table, Typography, Tag } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { StarOutlined } from '@ant-design/icons'
import { bidStatusConfig } from '@/types/job-status'

interface Bid {
  bid_id: string
  job_id: string
  worker_id: string
  proposal: string
  quote: { amount: number; currency: string; delivery_days: number }
  is_hired: boolean
  status: string
  submitted_at: string
  worker_name?: string | null
  worker_rating?: number | null
}

interface Worker {
  job_worker_id: string
  bid_id: string
  worker_id: string
  worker_name?: string | null
  worker_rating?: number | null
  status: string
  is_confirmed: boolean
  is_winner: boolean
  quote_amount?: number | null
  proposal?: string | null
}

interface BidListProps {
  bids: Bid[]
  workers: Worker[]
  selectedBidId: string | null
  onSelectBid: (bidId: string) => void
  loading?: boolean
}

const { Paragraph } = Typography

/**
 * BidList - 竞标列表组件
 * 显示所有竞标，并高亮显示已选中的竞标
 */
const BidList = ({ bids, workers, selectedBidId, onSelectBid, loading = false }: BidListProps) => {
  // Merge bid and worker info
  const mergedData = bids.map((bid) => {
    const worker = workers.find((w) => w.bid_id === bid.bid_id)
    return {
      ...bid,
      worker_name: worker?.worker_name || bid.worker_name,
      worker_rating: worker?.worker_rating || bid.worker_rating,
      is_confirmed: worker?.is_confirmed || false,
      is_winner: worker?.is_winner || false,
      worker_status: worker?.status || bid.status,
    }
  })

  const columns: ColumnsType<typeof mergedData[0]> = [
    {
      title: '工人',
      key: 'worker',
      width: 150,
      render: (_, record) => (
        <div>
          <div className="font-medium text-slate-200">{record.worker_name || 'Unknown'}</div>
          <div className="flex items-center gap-1 text-xs text-slate-400">
            <StarOutlined className={record.worker_rating ? 'text-amber-400' : 'text-slate-500'} />
            <span>{record.worker_rating?.toFixed(1) || '-'}</span>
            {record.is_confirmed && (
              <Tag color="blue" className="ml-1 text-xs">
                已确认
              </Tag>
            )}
            {record.is_winner && (
              <Tag color="green" className="ml-1 text-xs">
                中标
              </Tag>
            )}
          </div>
        </div>
      ),
    },
    {
      title: '报价',
      key: 'quote',
      width: 100,
      render: (_, record) => (
        <div className="text-cyan-400 font-mono">
          ¥{record.quote.amount.toLocaleString('zh-CN')}
        </div>
      ),
    },
    {
      title: '交付周期',
      key: 'delivery',
      width: 80,
      render: (_, record) => (
        <span className="text-slate-300">{record.quote.delivery_days} 天</span>
      ),
    },
    {
      title: '方案',
      key: 'proposal',
      render: (_, record) => (
        <Paragraph
          ellipsis={{ rows: 2, tooltip: record.proposal }}
          className="text-slate-400 text-sm mb-0"
        >
          {record.proposal || '-'}
        </Paragraph>
      ),
    },
    {
      title: '状态',
      key: 'status',
      width: 100,
      render: (_, record) => {
        const config = bidStatusConfig[record.status]
        if (!config) {
          return <Tag color="gray">{record.status}</Tag>
        }
        return <Tag color={config.color}>{config.label}</Tag>
      },
    },
  ]

  return (
    <div className="glass-card p-4">
      <h3 className="text-lg font-semibold text-white mb-4">竞标列表</h3>
      {mergedData.length === 0 ? (
        <div className="text-center py-12 text-slate-500">
          暂无竞标数据
        </div>
      ) : (
        <Table
          dataSource={mergedData}
          columns={columns}
          rowKey="bid_id"
          rowClassName={(record) =>
            selectedBidId === record.bid_id
              ? 'bg-cyan-500/10 border border-cyan-500/30 rounded-lg'
              : 'hover:bg-slate-800/30 transition-colors'
          }
          loading={loading}
          pagination={false}
          size="small"
          onRow={(record) => ({
            onClick: () => onSelectBid(record.bid_id),
            className: 'cursor-pointer',
          })}
          aria-label="竞标列表"
        />
      )}
    </div>
  )
}

export default BidList
