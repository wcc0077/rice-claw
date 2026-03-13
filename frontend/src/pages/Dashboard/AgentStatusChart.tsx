import { memo } from 'react'
import { Progress } from 'antd'
import { Agent } from '@/types/agent'

interface AgentStatusChartProps {
  agents: Agent[]
}

/**
 * AgentStatusChart - Dark mode agent status visualization
 */
const AgentStatusChart = memo(({ agents }: AgentStatusChartProps) => {
  const statusCounts = agents.reduce(
    (acc, agent) => {
      acc[agent.status] = (acc[agent.status] || 0) + 1
      return acc
    },
    { idle: 0, busy: 0, offline: 0 }
  )

  const total = agents.length || 1 // Prevent division by zero

  const statusData = [
    {
      key: 'idle',
      label: '空闲',
      value: statusCounts.idle,
      color: '#34d399',
      className: 'text-emerald-400',
      bgClass: 'bg-emerald-500/10 border-emerald-500/20',
    },
    {
      key: 'busy',
      label: '工作中',
      value: statusCounts.busy,
      color: '#f472b6',
      className: 'text-pink-400',
      bgClass: 'bg-pink-500/10 border-pink-500/20',
    },
    {
      key: 'offline',
      label: '离线',
      value: statusCounts.offline,
      color: '#64748b',
      className: 'text-slate-400',
      bgClass: 'bg-slate-500/10 border-slate-500/20',
    },
  ]

  if (total === 0) {
    return (
      <div className="h-[250px] flex items-center justify-center">
        <div className="text-center">
          <div className="text-slate-500 text-sm">暂无数据</div>
          <div className="text-slate-600 text-xs mt-1">等待代理注册</div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Status bars */}
      <div className="space-y-3">
        {statusData.map((item) => {
          const percentage = Math.round((item.value / total) * 100)
          return (
            <div
              key={item.key}
              className="flex items-center gap-3 p-3 rounded-lg hover:bg-slate-800/30 transition-colors"
            >
              {/* Status dot */}
              <div
                className={`w-3 h-3 rounded-full flex-shrink-0`}
                style={{ backgroundColor: item.color }}
              />

              {/* Label */}
              <div className="w-16 text-sm text-slate-300 flex-shrink-0">
                {item.label}
              </div>

              {/* Progress bar */}
              <div className="flex-1">
                <Progress
                  percent={percentage}
                  size="small"
                  showInfo={false}
                  strokeColor={item.color}
                  trailColor="rgba(255,255,255,0.1)"
                />
              </div>

              {/* Count */}
              <div className={`w-12 text-right font-mono text-sm ${item.className}`}>
                {item.value} 个
              </div>
            </div>
          )
        })}
      </div>

      {/* Total summary */}
      <div className="pt-4 border-t border-slate-700/30">
        <div className="flex items-center justify-between">
          <span className="text-slate-400 text-sm">总代理数</span>
          <span className="text-xl font-bold text-white font-mono">
            {total}
          </span>
        </div>
      </div>
    </div>
  )
})

AgentStatusChart.displayName = 'AgentStatusChart'

export default AgentStatusChart
