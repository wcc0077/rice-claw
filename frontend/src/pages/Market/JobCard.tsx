import { memo } from 'react'
import { Typography, Button } from 'antd'
import { HeartOutlined, ShareAltOutlined, CheckCircleOutlined, SyncOutlined, ThunderboltOutlined } from '@ant-design/icons'

const { Text, Paragraph } = Typography

interface JobCardProps {
  job: {
    job_id: string
    title: string
    description: string
    required_tags: string[]
    budget_min?: number
    budget_max?: number
    status: string
    bid_count: number
    bid_limit: number
    created_at: string
  }
  isLoggedIn: boolean
  onInteract: () => void
  onApply: (jobId: string) => void
  formatTime: (date: string) => string
}

const JobCard = memo(({ job, isLoggedIn, onInteract, onApply, formatTime }: JobCardProps) => {
  const statusConfig: Record<string, { label: string; color: string; icon: React.ReactNode }> = {
    OPEN: { label: '开放中', color: 'text-emerald-400', icon: <CheckCircleOutlined className="mr-1" /> },
    ACTIVE: { label: '进行中', color: 'text-cyan-400', icon: <SyncOutlined spin className="mr-1" /> },
  }

  const status = statusConfig[job.status] || { label: job.status, color: 'text-slate-400', icon: null }

  const formatBudget = (min?: number, max?: number) => {
    if (!min && !max) return '面议'
    const formatNum = (n?: number) => n ? `¥${n.toLocaleString('zh-CN')}` : '-'
    if (min && max) return `${formatNum(min)} - ${formatNum(max)}`
    return formatNum(min || max)
  }

  const handleClick = () => {
    window.open(`/market/jobs/${job.job_id}`, '_blank')
  }

  const handleApply = () => {
    if (isLoggedIn) {
      onApply(job.job_id)
    } else {
      onInteract()
    }
  }

  return (
    <div
      className="glass-card p-4 cursor-pointer hover:border-cyan-500/30 transition-all group"
      onClick={handleClick}
    >
      {/* Title */}
      <div className="flex items-start justify-between gap-2 mb-2">
        <Text strong className="text-white text-base line-clamp-1 group-hover:text-cyan-400 transition-colors">
          {job.title}
        </Text>
      </div>

      {/* Description */}
      <Paragraph
        className="text-slate-400 text-sm mb-3 line-clamp-2"
        style={{ marginBottom: 12 }}
      >
        {job.description}
      </Paragraph>

      {/* Tags */}
      <div className="flex flex-wrap gap-1.5 mb-3">
        {job.required_tags.slice(0, 4).map(tag => (
          <span
            key={tag}
            className="px-2 py-0.5 rounded text-xs bg-purple-500/10 text-purple-400 border border-purple-500/20"
          >
            {tag}
          </span>
        ))}
        {job.required_tags.length > 4 && (
          <span className="text-xs text-slate-500">+{job.required_tags.length - 4}</span>
        )}
      </div>

      {/* Budget & Status */}
      <div className="flex items-center justify-between mb-3 text-sm">
        <span className="text-cyan-400 font-mono">
          {formatBudget(job.budget_min, job.budget_max)}
        </span>
        <span className={`flex items-center ${status.color}`}>
          {status.icon}
          {status.label}
        </span>
      </div>

      {/* Bids & Time */}
      <div className="flex items-center justify-between text-sm text-slate-500 mb-3">
        <span>竞标: {job.bid_count}/{job.bid_limit} 人</span>
        <span>{formatTime(job.created_at)}</span>
      </div>

      {/* Actions */}
      <div className="flex justify-between items-center pt-2 border-t border-slate-700/50">
        {/* Apply Button */}
        {job.status === 'OPEN' && (
          <Button
            type="primary"
            size="small"
            icon={<ThunderboltOutlined />}
            onClick={(e) => { e.stopPropagation(); handleApply(); }}
            className="bg-gradient-to-r from-cyan-500 to-purple-500 border-0"
          >
            接单
          </Button>
        )}

        <div className="flex gap-2 ml-auto">
          <Button
            type="text"
            size="small"
            icon={<HeartOutlined />}
            className="text-slate-400 hover:text-rose-400"
            onClick={(e) => { e.stopPropagation(); onInteract(); }}
          >
            收藏
          </Button>
          <Button
            type="text"
            size="small"
            icon={<ShareAltOutlined />}
            className="text-slate-400 hover:text-cyan-400"
            onClick={(e) => { e.stopPropagation(); onInteract(); }}
          >
            分享
          </Button>
        </div>
      </div>
    </div>
  )
})

JobCard.displayName = 'JobCard'

export default JobCard