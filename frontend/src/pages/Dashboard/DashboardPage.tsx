import { Row, Col, Typography } from 'antd'
import {
  TeamOutlined,
  FileTextOutlined,
  ClockCircleOutlined,
  DollarOutlined,
} from '@ant-design/icons'
import StatCard from './StatCard'
import JobStatusChart from './JobStatusChart'
import AgentStatusChart from './AgentStatusChart'
import RecentJobsTable from './RecentJobsTable'
import { useEffect, useState } from 'react'
import { dashboardApi } from '@/services/api'

const { Title, Text } = Typography

const DashboardPage = () => {
  const [stats, setStats] = useState<any>(null)
  const [jobs, setJobs] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      const [statsRes, jobsRes] = await Promise.all([
        dashboardApi.stats(),
        dashboardApi.jobs({ status: 'OPEN', limit: 5 }),
      ])
      setStats(statsRes.data)
      setJobs(jobsRes.data.jobs || [])
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-[400px] flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
          <Text className="text-slate-400">加载数据中...</Text>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <Title level={2} className="text-2xl font-bold text-white mb-1">
            仪表盘
          </Title>
          <Text className="text-slate-400">实时数据监控与概览</Text>
        </div>
        <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800/50 border border-slate-700/50">
          <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
          <Text className="text-sm text-slate-300">系统正常运行中</Text>
        </div>
      </div>

      {/* Stats Grid */}
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
          />
        </Col>
      </Row>

      {/* Charts Row */}
      <Row gutter={[24, 24]}>
        <Col xs={24} lg={12}>
          <div className="glass-card p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <Title level={4} className="text-lg font-semibold text-white mb-1">任务状态分布</Title>
                <Text className="text-slate-400 text-sm">各状态任务数量统计</Text>
              </div>
              <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center">
                <FileTextOutlined className="text-cyan-400" />
              </div>
            </div>
            <JobStatusChart data={stats?.job_status_breakdown || {}} />
          </div>
        </Col>
        <Col xs={24} lg={12}>
          <div className="glass-card p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <Title level={4} className="text-lg font-semibold text-white mb-1">代理状态</Title>
                <Text className="text-slate-400 text-sm">在线代理实时监控</Text>
              </div>
              <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center">
                <TeamOutlined className="text-purple-400" />
              </div>
            </div>
            <AgentStatusChart agents={[]} />
          </div>
        </Col>
      </Row>

      {/* Recent Jobs Table */}
      <div className="glass-card p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <Title level={4} className="text-lg font-semibold text-white mb-1">最近任务</Title>
            <Text className="text-slate-400 text-sm">最新发布的任务列表</Text>
          </div>
        </div>
        <RecentJobsTable jobs={jobs} />
      </div>
    </div>
  )
}

export default DashboardPage