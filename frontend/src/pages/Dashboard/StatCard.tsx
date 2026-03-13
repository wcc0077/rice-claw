import { memo } from 'react'
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons'
import { Skeleton } from 'antd'

interface StatCardProps {
  title: string
  value: number
  suffix?: string
  trend?: string
  trendType?: 'up' | 'down' | 'neutral'
  icon: React.ReactNode
  gradient: 'cyan' | 'purple' | 'pink' | 'amber'
  loading?: boolean
}

const gradientMap = {
  cyan: 'from-cyan-500/20 to-cyan-600/10 border-cyan-500/30',
  purple: 'from-purple-500/20 to-purple-600/10 border-purple-500/30',
  pink: 'from-pink-500/20 to-pink-600/10 border-pink-500/30',
  amber: 'from-amber-500/20 to-amber-600/10 border-amber-500/30',
}

const iconColorMap = {
  cyan: 'text-cyan-400',
  purple: 'text-purple-400',
  pink: 'text-pink-400',
  amber: 'text-amber-400',
}

const trendColorMap = {
  up: 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20',
  down: 'bg-rose-500/10 text-rose-400 border border-rose-500/20',
  neutral: 'bg-slate-500/10 text-slate-400 border border-slate-500/20',
}

/**
 * StatCard - Performance-optimized statistic card with skeleton loading
 * Wrapped in React.memo to prevent unnecessary re-renders when parent updates
 */
const StatCard = memo(({ title, value, suffix = '', trend, trendType = 'up', icon, gradient, loading = false }: StatCardProps) => {
  const displayTrend = trend || '+0%'

  if (loading) {
    return (
      <div className="relative overflow-hidden rounded-2xl bg-slate-800/50 border border-slate-700/50 p-6">
        <Skeleton active paragraph={{ rows: 2 }} title={false} />
      </div>
    )
  }

  return (
    <div
      className="relative group cursor-pointer"
      role="region"
      aria-label={`${title} statistic`}
    >
      {/* Card Background with glass morphism */}
      <div
        className={`relative overflow-hidden rounded-2xl bg-gradient-to-br ${gradientMap[gradient]} border backdrop-blur-sm p-6 transition-all duration-300 hover:shadow-lg hover:shadow-${gradient}-500/10 focus-within:ring-2 focus-within:ring-${gradient}-500/50`}
        tabIndex={0}
      >
        {/* Ambient glow effect - subtle trust indicator */}
        <div className="absolute -top-20 -right-20 w-40 h-40 bg-white/5 rounded-full blur-3xl group-hover:bg-white/10 transition-all duration-500" />

        {/* Content */}
        <div className="relative z-10">
          {/* Icon and Title Row */}
          <div className="flex items-start justify-between mb-4">
            <div>
              <p className="text-slate-400 text-sm font-medium">{title}</p>
            </div>
            <div
              className={`w-10 h-10 rounded-xl bg-slate-800/50 border border-slate-700/50 flex items-center justify-center ${iconColorMap[gradient]} transition-transform duration-300 group-hover:scale-110`}
              aria-hidden="true"
            >
              {icon}
            </div>
          </div>

          {/* Value with trust indicator */}
          <div className="flex items-baseline gap-1 mb-3">
            <span
              className="text-3xl font-bold text-white font-mono tracking-tight tabular-nums"
              aria-live="polite"
            >
              {value.toLocaleString('zh-CN')}
            </span>
            {suffix && <span className="text-lg text-slate-500 font-medium">{suffix}</span>}
          </div>

          {/* Trend with accessibility */}
          <div className="flex items-center gap-2" aria-label={`趋势: ${displayTrend}`}>
            <div className={`flex items-center gap-1 text-xs font-medium px-2 py-1 rounded-full ${trendColorMap[trendType]}`}>
              {trendType === 'up' ? (
                <ArrowUpOutlined className="text-[10px]" aria-hidden="true" />
              ) : trendType === 'down' ? (
                <ArrowDownOutlined className="text-[10px]" aria-hidden="true" />
              ) : null}
              <span>{displayTrend}</span>
            </div>
            <span className="text-xs text-slate-500">较昨日</span>
          </div>
        </div>

        {/* Bottom accent line - trust indicator */}
        <div
          className={`absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-current to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 ${iconColorMap[gradient]}`}
          aria-hidden="true"
        />
      </div>
    </div>
  )
})

// Display name for debugging
StatCard.displayName = 'StatCard'

export default StatCard
