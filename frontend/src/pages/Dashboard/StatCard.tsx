import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons'

interface StatCardProps {
  title: string
  value: number
  suffix?: string
  trend?: string
  trendType?: 'up' | 'down' | 'neutral'
  icon: React.ReactNode
  gradient: 'cyan' | 'purple' | 'pink' | 'amber'
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

const StatCard = ({ title, value, suffix = '', trend, trendType = 'up', icon, gradient }: StatCardProps) => {
  const displayTrend = trend || '+0%'
  const isPositive = trendType === 'up'

  return (
    <div className="relative group">
      {/* Card Background */}
      <div className={`relative overflow-hidden rounded-2xl bg-gradient-to-br ${gradientMap[gradient]} border p-6 transition-all duration-300 hover:scale-[1.02] hover:shadow-lg`}>
        {/* Glow Effect */}
        <div className="absolute -top-20 -right-20 w-40 h-40 bg-white/5 rounded-full blur-3xl group-hover:bg-white/10 transition-all duration-500" />

        {/* Content */}
        <div className="relative z-10">
          {/* Icon and Title Row */}
          <div className="flex items-start justify-between mb-4">
            <div>
              <p className="text-slate-400 text-sm font-medium">{title}</p>
            </div>
            <div className={`w-10 h-10 rounded-xl bg-slate-800/50 border border-slate-700/50 flex items-center justify-center ${iconColorMap[gradient]}`}>
              {icon}
            </div>
          </div>

          {/* Value */}
          <div className="flex items-baseline gap-1 mb-3">
            <span className="text-3xl font-bold text-white font-mono-display tracking-tight">
              {value.toLocaleString()}
            </span>
            {suffix && <span className="text-lg text-slate-500 font-medium">{suffix}</span>}
          </div>

          {/* Trend */}
          <div className="flex items-center gap-2">
            <div className={`flex items-center gap-1 text-xs font-medium px-2 py-1 rounded-full ${
              isPositive
                ? 'bg-green-500/10 text-green-400 border border-green-500/20'
                : 'bg-red-500/10 text-red-400 border border-red-500/20'
            }`}>
              {isPositive ? <ArrowUpOutlined className="text-[10px]" /> : <ArrowDownOutlined className="text-[10px]" />}
              <span>{displayTrend}</span>
            </div>
            <span className="text-xs text-slate-500">较昨日</span>
          </div>
        </div>

        {/* Bottom Glow Line */}
        <div className={`absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-${gradient === 'cyan' ? 'cyan' : gradient === 'purple' ? 'purple' : gradient === 'pink' ? 'pink' : 'amber'}-500/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300`} />
      </div>
    </div>
  )
}

export default StatCard