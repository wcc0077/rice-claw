import { memo } from 'react'
import { Typography, Button, Rate } from 'antd'
import { HeartOutlined, ShareAltOutlined, RobotOutlined, CheckCircleOutlined, ClockCircleOutlined } from '@ant-design/icons'

const { Text, Paragraph } = Typography

interface AgentCardProps {
  agent: {
    agent_id: string
    name: string
    description?: string
    capabilities: string[]
    status: string
    rating: number
    completed_jobs: number
    updated_at: string
  }
  onInteract: () => void
  formatTime: (date: string) => string
}

const AgentCard = memo(({ agent, onInteract, formatTime }: AgentCardProps) => {
  const statusConfig: Record<string, { label: string; color: string; icon: React.ReactNode }> = {
    idle: { label: '空闲中', color: 'text-emerald-400', icon: <CheckCircleOutlined className="mr-1" /> },
    busy: { label: '忙碌中', color: 'text-amber-400', icon: <ClockCircleOutlined className="mr-1" /> },
    offline: { label: '离线', color: 'text-slate-500', icon: null },
  }

  const status = statusConfig[agent.status] || { label: agent.status, color: 'text-slate-400', icon: null }

  const handleClick = () => {
    window.open(`/market/agents/${agent.agent_id}`, '_blank')
  }

  return (
    <div
      className="glass-card p-4 cursor-pointer hover:border-purple-500/30 transition-all group"
      onClick={handleClick}
    >
      {/* Header with Avatar */}
      <div className="flex items-center gap-3 mb-3">
        <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-500 to-cyan-500 flex items-center justify-center">
          <RobotOutlined className="text-white text-xl" />
        </div>
        <div className="flex-1">
          <Text strong className="text-white text-base group-hover:text-purple-400 transition-colors">
            {agent.name}
          </Text>
          <div className="flex items-center gap-2">
            <Rate disabled defaultValue={agent.rating} className="text-xs" style={{ fontSize: 12 }} />
            <Text className="text-slate-400 text-sm">
              {agent.rating.toFixed(1)} · {agent.completed_jobs} 个任务
            </Text>
          </div>
        </div>
      </div>

      {/* Description */}
      {agent.description && (
        <Paragraph
          className="text-slate-400 text-sm mb-3 line-clamp-2"
          style={{ marginBottom: 12 }}
        >
          {agent.description}
        </Paragraph>
      )}

      {/* Capabilities */}
      <div className="flex flex-wrap gap-1.5 mb-3">
        {agent.capabilities.slice(0, 4).map(cap => (
          <span
            key={cap}
            className="px-2 py-0.5 rounded text-xs bg-cyan-500/10 text-cyan-400 border border-cyan-500/20"
          >
            {cap}
          </span>
        ))}
        {agent.capabilities.length > 4 && (
          <span className="text-xs text-slate-500">+{agent.capabilities.length - 4}</span>
        )}
      </div>

      {/* Status & Response Time */}
      <div className="flex items-center justify-between mb-3 text-sm">
        <span className={`flex items-center ${status.color}`}>
          {status.icon}
          {status.label}
        </span>
        <span className="text-slate-500">
          最近活跃: {formatTime(agent.updated_at)}
        </span>
      </div>

      {/* Actions */}
      <div className="flex justify-end gap-2 pt-2 border-t border-slate-700/50">
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
          className="text-slate-400 hover:text-purple-400"
          onClick={(e) => { e.stopPropagation(); onInteract(); }}
        >
          分享
        </Button>
      </div>
    </div>
  )
})

AgentCard.displayName = 'AgentCard'

export default AgentCard