import { useState, useCallback } from 'react'
import { Card, Typography, Row, Col, DatePicker, Table } from 'antd'
import { Line } from '@ant-design/plots'
import type { DailyAnalytics } from '@/types/dashboard'
import { adminApi } from '@/services/api'
import { useAsyncEffect } from '@/hooks/useFetchOnce'

const { Title } = Typography
const { RangePicker } = DatePicker

const AnalyticsPage = () => {
  const [analytics, setAnalytics] = useState<DailyAnalytics[]>([])
  const [loading, setLoading] = useState(true)

  const fetchAnalytics = useCallback(async () => {
    try {
      const res = await adminApi.dailyAnalytics()
      setAnalytics(res.data || [])
    } catch (error) {
      console.error('Failed to fetch analytics:', error)
    } finally {
      setLoading(false)
    }
  }, [])

  useAsyncEffect(fetchAnalytics, [fetchAnalytics])

  if (loading) {
    return <div>加载中...</div>
  }

  const chartData = analytics.flatMap((item) => [
    { date: item.date, type: '新代理', value: item.new_agents },
    { date: item.date, type: '新任务', value: item.new_jobs },
  ])

  const config = {
    data: chartData,
    xField: 'date',
    yField: 'value',
    seriesField: 'type',
  }

  const columns = [
    { title: '日期', dataIndex: 'date', key: 'date' },
    { title: '新代理', dataIndex: 'new_agents', key: 'new_agents' },
    { title: '新任务', dataIndex: 'new_jobs', key: 'new_jobs' },
    { title: '已完成', dataIndex: 'completed_jobs', key: 'completed_jobs' },
    { title: '营收', dataIndex: 'total_revenue', key: 'total_revenue', render: (v: number) => `¥${v}` },
  ]

  return (
    <div className="space-y-6">
      <Title level={2}>数据分析</Title>

      <RangePicker onChange={() => {}} className="mb-4" />

      <Row gutter={[16, 16]}>
        <Col span={8}>
          <Card title="趋势图">
            <div className="h-[300px]">
              <Line {...config} />
            </div>
          </Card>
        </Col>
        <Col span={16}>
          <Card title="每日数据表">
            <Table
              dataSource={analytics}
              columns={columns}
              rowKey="date"
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default AnalyticsPage
