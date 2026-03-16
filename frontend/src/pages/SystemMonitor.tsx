/**
 * 系统监控页面 - 可观测性 Dashboard
 * 展示 API 性能指标、业务指标和系统健康状态
 */

import { useEffect, useState } from 'react';
import { Card, Col, Row, Statistic, Table, Tag, Spin, Alert } from 'antd';
import {
  CheckCircleOutlined,
  WarningOutlined,
  CloseCircleOutlined,
  DashboardOutlined,
  LineChartOutlined,
  TeamOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import { fetchObservabilityMetrics, fetchHealthStatus } from '@/services/observabilityService';

interface MetricData {
  api_metrics: {
    latency: {
      avg: number;
      p50: number;
      p95: number;
      p99: number;
      count: number;
    };
    qps: Record<string, number>;
    error_rate: Record<string, number>;
  };
  business_metrics: {
    active_agents: number | null;
    job_stats: Record<string, number>;
    bid_stats: Record<string, number>;
  };
}

interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  database: {
    status: string;
    error: string | null;
  };
  api_metrics: {
    avg_latency_ms: number;
    p95_latency_ms: number;
    request_count: number;
  };
  error_rate: number;
}

const SystemMonitor: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [metrics, setMetrics] = useState<MetricData | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);

  // 加载指标数据
  const loadMetrics = async () => {
    try {
      const data = await fetchObservabilityMetrics();
      setMetrics(data);
    } catch (error) {
      console.error('Failed to load metrics:', error);
    }
  };

  // 加载健康状态
  const loadHealth = async () => {
    try {
      const data = await fetchHealthStatus();
      setHealth(data);
    } catch (error) {
      console.error('Failed to load health status:', error);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([loadMetrics(), loadHealth()]);
      setLoading(false);
    };

    loadData();

    // 每 30 秒刷新一次
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  // 获取健康状态图标
  const getHealthIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'degraded':
        return <WarningOutlined style={{ color: '#faad14' }} />;
      case 'unhealthy':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
      default:
        return <DashboardOutlined />;
    }
  };

  // 获取健康状态文本
  const getHealthText = (status: string) => {
    switch (status) {
      case 'healthy':
        return '系统健康';
      case 'degraded':
        return '性能降级';
      case 'unhealthy':
        return '系统异常';
      default:
        return status;
    }
  };

  // Job 状态表格数据
  const getJobStatsData = () => {
    if (!metrics?.business_metrics?.job_stats) return [];
    const stats = metrics.business_metrics.job_stats;
    return [
      { key: 'open', name: '公开招募', count: stats.open || 0, color: 'blue' },
      { key: 'active', name: '进行中', count: stats.active || 0, color: 'green' },
      { key: 'review', name: '审核中', count: stats.review || 0, color: 'orange' },
      { key: 'closed', name: '已完成', count: stats.closed || 0, color: 'gray' },
    ];
  };

  // Bid 状态表格数据
  const getBidStatsData = () => {
    if (!metrics?.business_metrics?.bid_stats) return [];
    const stats = metrics.business_metrics.bid_stats;
    return [
      { key: 'bidding', name: '竞标中', count: stats.bidding || 0, color: 'blue' },
      { key: 'selected', name: '已中标', count: stats.selected || 0, color: 'green' },
      { key: 'in_progress', name: '实施中', count: stats.in_progress || 0, color: 'orange' },
      { key: 'completed', name: '已完成', count: stats.completed || 0, color: 'gray' },
    ];
  };

  // 计算错误率
  const getOverallErrorRate = () => {
    if (!metrics?.api_metrics?.error_rate) return 0;
    const rates = Object.values(metrics.api_metrics.error_rate);
    if (rates.length === 0) return 0;
    return (rates.reduce((sum, rate) => sum + rate, 0) / rates.length) * 100;
  };

  // 延迟指标表格列
  const latencyColumns = [
    { title: '指标', dataIndex: 'name', key: 'name' },
    { title: '数值 (ms)', dataIndex: 'value', key: 'value', render: (v: number) => `${v.toFixed(2)} ms` },
  ];

  const latencyData = metrics?.api_metrics?.latency
    ? [
        { key: 'avg', name: '平均延迟', value: metrics.api_metrics.latency.avg },
        { key: 'p50', name: 'P50 延迟', value: metrics.api_metrics.latency.p50 },
        { key: 'p95', name: 'P95 延迟', value: metrics.api_metrics.latency.p95 },
        { key: 'p99', name: 'P99 延迟', value: metrics.api_metrics.latency.p99 },
      ]
    : [];

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '100px' }}>
        <Spin size="large" tip="加载监控数据..." />
      </div>
    );
  }

  const errorRate = getOverallErrorRate();

  return (
    <div style={{ padding: '24px' }}>
      {/* 健康状态卡片 */}
      <Card style={{ marginBottom: 24 }}>
        <Row align="middle" gutter={16}>
          <Col style={{ fontSize: 48 }}>
            {health && getHealthIcon(health.status)}
          </Col>
          <Col flex={1}>
            <Row gutter={24}>
              <Col>
                <Statistic
                  title="系统状态"
                  value={health ? getHealthText(health.status) : '未知'}
                  valueStyle={{ fontSize: 20 }}
                />
              </Col>
              <Col>
                <Statistic
                  title="数据库"
                  value={health?.database.status || '未知'}
                  valueStyle={{ fontSize: 20 }}
                />
              </Col>
              <Col>
                <Statistic
                  title="平均延迟"
                  value={health?.api_metrics.avg_latency_ms || 0}
                  suffix="ms"
                  valueStyle={{ fontSize: 20 }}
                />
              </Col>
              <Col>
                <Statistic
                  title="错误率"
                  value={errorRate.toFixed(2)}
                  suffix="%"
                  valueStyle={{
                    fontSize: 20,
                    color: errorRate > 5 ? '#ff4d4f' : errorRate > 1 ? '#faad14' : '#52c41a',
                  }}
                />
              </Col>
            </Row>
          </Col>
        </Row>
      </Card>

      {/* 核心指标卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="活跃 Agent"
              value={metrics?.business_metrics?.active_agents || 0}
              prefix={<TeamOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="请求总数"
              value={metrics?.api_metrics?.latency?.count || 0}
              prefix={<LineChartOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="平均延迟"
              value={metrics?.api_metrics?.latency?.avg?.toFixed(2) || '0.00'}
              suffix="ms"
              prefix={<DashboardOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="P95 延迟"
              value={metrics?.api_metrics?.latency?.p95?.toFixed(2) || '0.00'}
              suffix="ms"
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 延迟详情和业务统计 */}
      <Row gutter={16}>
        <Col xs={24} lg={12}>
          <Card title="延迟详情">
            <Table
              columns={latencyColumns}
              dataSource={latencyData}
              pagination={false}
              size="small"
              showHeader={false}
            />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="Job 状态分布">
            <Row gutter={16}>
              {getJobStatsData().map((item) => (
                <Col key={item.key} xs={12} lg={6} style={{ textAlign: 'center' }}>
                  <div style={{ marginBottom: 8 }}>
                    <Tag color={item.color}>{item.name}</Tag>
                  </div>
                  <div style={{ fontSize: 24, fontWeight: 'bold' }}>{item.count}</div>
                </Col>
              ))}
            </Row>
          </Card>
        </Col>
      </Row>

      {/* Bid 状态 */}
      <Card title="Bid 状态分布" style={{ marginTop: 16 }}>
        <Row gutter={16}>
          {getBidStatsData().map((item) => (
            <Col key={item.key} xs={12} sm={6} style={{ textAlign: 'center' }}>
              <div style={{ marginBottom: 8 }}>
                <Tag color={item.color}>{item.name}</Tag>
              </div>
              <div style={{ fontSize: 24, fontWeight: 'bold' }}>{item.count}</div>
            </Col>
          ))}
        </Row>
      </Card>

      {/* 告警信息 */}
      {health?.status === 'degraded' || health?.status === 'unhealthy' ? (
        <Alert
          message="系统告警"
          description={
            health.status === 'degraded'
              ? '系统性能下降，请检查延迟指标和错误率'
              : '系统异常，请立即检查数据库连接和 API 状态'
          }
          type={health.status === 'unhealthy' ? 'error' : 'warning'}
          style={{ marginTop: 16 }}
          showIcon
        />
      ) : null}
    </div>
  );
};

export default SystemMonitor;
