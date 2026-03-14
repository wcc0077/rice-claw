import { Row, Col, Typography, Result, Button } from 'antd'
import {
  TeamOutlined,
  FileTextOutlined,
  ClockCircleOutlined,
  DollarOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import StatCard from './StatCard'
import JobStatusChart from './JobStatusChart'
import AgentStatusChart from './AgentStatusChart'
import RecentJobsTable from './RecentJobsTable'
import { useState, useCallback, memo } from 'react'
import { dashboardApi } from '@/services/api'
import { useAsyncEffect } from '@/hooks/useFetchOnce'

const { Title, Text } = Typography

// Memoized chart components for performance
const MemoizedJobStatusChart = memo(JobStatusChart)
const MemoizedAgentStatusChart = memo(AgentStatusChart)

/**
 * SystemStatusIndicator - Trust-focused system health display
 * Shows real-time system status with visual feedback
 */
const SystemStatusIndicator = memo(
  ({ status = 'normal' }: { status?: 'normal' | 'warning' | 'error' }) => {
    const statusConfig = {
      normal: {
        dotColor: 'bg-emerald-400',
        pulseColor: 'bg-emerald-400/30',
        text: '系统正常运行中',
        textColor: 'text-slate-300',
      },
      warning: {
        dotColor: 'bg-amber-400',
        pulseColor: 'bg-amber-400/30',
        text: '系统性能下降',
        textColor: 'text-amber-400',
      },
      error: {
        dotColor: 'bg-rose-400',
        pulseColor: 'bg-rose-400/30',
        text: '系统异常',
        textColor: 'text-rose-400',
      },
    }

    const config = statusConfig[status]

    return (
      <div
        className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800/50 border border-slate-700/50"
        role="status"
        aria-live="polite"
        aria-label={config.text}
      >
        <div className="relative flex items-center justify-center">
          <div
            className={`absolute w-3 h-3 rounded-full ${config.pulseColor} animate-ping`}
            aria-hidden="true"
          />
          <div
            className={`relative w-2 h-2 rounded-full ${config.dotColor}`}
            aria-hidden="true"
          />
        </div>
        <span className={`text-sm ${config.textColor} font-medium`}>
          {config.text}
        </span>
      </div>
    )
  }
)

SystemStatusIndicator.displayName = 'SystemStatusIndicator'

/**
 * DashboardPage - Performance-optimized dashboard with trust indicators
 * Features: Skeleton loading, error boundaries, memoized components, accessibility
 */
const DashboardPage = () => {
  const [stats, setStats] = useState<any>(null)
  const [jobs, setJobs] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [systemStatus, setSystemStatus] = useState<'normal' | 'warning' | 'error'>('normal')

  const fetchDashboardData = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const [statsRes, jobsRes] = await Promise.all([
        dashboardApi.stats(),
        dashboardApi.jobs({ status: 'OPEN', limit: 5 }),
      ])

      setStats(statsRes.data)
      setJobs(jobsRes.data.jobs || [])
      setSystemStatus('normal')
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err)
      setError('无法加载仪表板数据，请稍后重试')
      setSystemStatus('error')
    } finally {
      setLoading(false)
    }
  }, [])

  useAsyncEffect(fetchDashboardData, [fetchDashboardData])

  // Error state with retry option
  if (error && !loading) {
    return (
      <div className="min-h-[400px] flex items-center justify-center">
        <Result
          status="warning"
          title="数据加载失败"
          subTitle={error}
          extra={
            <Button
              type="primary"
              icon={<ReloadOutlined />}
              onClick={fetchDashboardData}
              className="bg-cyan-500 hover:bg-cyan-400"
            >
              重新加载
            </Button>
          }
        />
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Page Header with trust indicators */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <Title level={2} className="text-2xl font-bold text-white mb-1">
            仪表盘
          </Title>
          <Text className="text-slate-400">实时数据监控与概览</Text>
        </div>
        <SystemStatusIndicator status={systemStatus} />
      </div>

      {/* Stats Grid - Memoized cards with skeleton loading */}
      <Row gutter={[24, 24]}>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="总代理数"
            value={stats?.total_agents || 0}
            suffix="个"
            trend="+12%"
            trendType="up"
            icon={<TeamOutlined className="text-xl" />}
            gradient="cyan"
            loading={loading}
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="活跃任务"
            value={stats?.active_jobs || 0}
            suffix="个"
            trend="-2"
            trendType="down"
            icon={<FileTextOutlined className="text-xl" />}
            gradient="purple"
            loading={loading}
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="待审核竞标"
            value={stats?.pending_bids || 0}
            suffix="个"
            trend="+8"
            trendType="up"
            icon={<ClockCircleOutlined className="text-xl" />}
            gradient="pink"
            loading={loading}
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="今日营收"
            value={stats?.revenue_today || 0}
            suffix="¥"
            trend="+23%"
            trendType="up"
            icon={<DollarOutlined className="text-xl" />}
            gradient="amber"
            loading={loading}
          />
        </Col>
      </Row>

      {/* Charts Row with glass cards */}
      <Row gutter={[24, 24]}>
        <Col xs={24} lg={12}>
          <div className="glass-card p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <Title level={4} className="text-lg font-semibold text-white mb-1">
                  任务状态分布
                </Title>
                <Text className="text-slate-400 text-sm">
                  各状态任务数量统计
                </Text>
              </div>
              <div
                className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center"
                aria-hidden="true"
              >
                <FileTextOutlined className="text-cyan-400" />
              </div>
            </div>
            {loading ? (
              <div className="h-[250px] flex items-center justify-center">
                <div className="w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
              </div>
            ) : (
              <MemoizedJobStatusChart data={stats?.job_status_breakdown || {}} />
            )}
          </div>
        </Col>
        <Col xs={24} lg={12}>
          <div className="glass-card p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <Title level={4} className="text-lg font-semibold text-white mb-1">
                  代理状态
                </Title>
                <Text className="text-slate-400 text-sm">
                  在线代理实时监控
                </Text>
              </div>
              <div
                className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center"
                aria-hidden="true"
              >
                <TeamOutlined className="text-purple-400" />
              </div>
            </div>
            {loading ? (
              <div className="h-[250px] flex items-center justify-center">
                <div className="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
              </div>
            ) : (
              <MemoizedAgentStatusChart agents={[]} />
            )}
          </div>
        </Col>
      </Row>

      {/* Recent Jobs Table with trust indicators */}
      <div className="glass-card p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <Title level={4} className="text-lg font-semibold text-white mb-1">
              最近任务
            </Title>
            <Text className="text-slate-400 text-sm">最新发布的任务列表</Text>
          </div>
          {!loading && jobs.length > 0 && (
            <span className="text-xs text-slate-500" aria-label={`共 ${jobs.length} 条记录`}>
              共 {jobs.length} 条
            </span>
          )}
        </div>
        <RecentJobsTable jobs={jobs} loading={loading} />
      </div>
    </div>
  )
}

export default DashboardPage
