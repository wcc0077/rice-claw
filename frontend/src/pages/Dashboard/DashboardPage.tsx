import { Card, Row, Col, Typography } from 'antd'
import StatCard from './StatCard'
import JobStatusChart from './JobStatusChart'
import AgentStatusChart from './AgentStatusChart'
import RecentJobsTable from './RecentJobsTable'
import { useEffect, useState } from 'react'
import { dashboardApi } from '@/services/api'

const { Title } = Typography

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
    return <div>加载中...</div>
  }

  return (
    <div className="space-y-6">
      <Title level={2} className="m-0">
        仪表盘
      </Title>

      <Row gutter={[16, 16]}>
        <Col span={6}>
          <StatCard
            title="总代理数"
            value={stats?.total_agents || 0}
            suffix="个"
            trend="+12%"
            color="blue"
          />
        </Col>
        <Col span={6}>
          <StatCard
            title="活跃任务"
            value={stats?.active_jobs || 0}
            suffix="个"
            trend="-2"
            color="green"
          />
        </Col>
        <Col span={6}>
          <StatCard
            title="待审核竞标"
            value={stats?.pending_bids || 0}
            suffix="个"
            trend="+8"
            color="orange"
          />
        </Col>
        <Col span={6}>
          <StatCard
            title="今日营收"
            value={stats?.revenue_today || 0}
            suffix="¥"
            trend="+23%"
            color="green"
          />
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col span={12}>
          <JobStatusChart data={stats?.job_status_breakdown || {}} />
        </Col>
        <Col span={12}>
          <AgentStatusChart agents={[]} />
        </Col>
      </Row>

      <Card title="最近任务">
        <RecentJobsTable jobs={jobs} />
      </Card>
    </div>
  )
}

export default DashboardPage
