/**
 * 声誉体系页面 - 分 Tab 展示规则、分数、流水
 */

import { useState, useEffect } from 'react';
import { Card, Tabs, Typography, Tag, Timeline, Empty, Spin, Progress, Row, Col, Table, Alert } from 'antd';
import type { TabsProps } from 'antd';
import {
  TrophyOutlined,
  StarOutlined,
  FireOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  QuestionCircleOutlined,
  InfoCircleOutlined,
  WarningOutlined,
} from '@ant-design/icons';

const { Title, Text } = Typography;

// 声誉等级配置
const LEVEL_CONFIG = [
  { threshold: 2500, name: '顶级', stars: '⭐⭐⭐⭐⭐', color: '#FFD700', description: '优先派活，雇主置顶显示' },
  { threshold: 2000, name: '优秀', stars: '⭐⭐⭐⭐', color: '#C0C0C0', description: '优先推送，更多曝光机会' },
  { threshold: 1500, name: '良好', stars: '⭐⭐⭐', color: '#CD7F32', description: '正常推送，标准展示' },
  { threshold: 1200, name: '一般', stars: '⭐⭐', color: '#666', description: '减少推送，需要积累' },
  { threshold: 1000, name: '较差', stars: '⭐', color: '#999', description: '不推送，需重新积累' },
];

// 变化类型配置
const CHANGE_TYPE_CONFIG: Record<string, { icon: React.ReactNode; color: string; label: string }> = {
  order_completed: { icon: <CheckCircleOutlined />, color: 'text-emerald-400', label: '订单完成' },
  order_cancelled: { icon: <CloseCircleOutlined />, color: 'text-rose-400', label: '订单取消' },
  rating_received: { icon: <StarOutlined />, color: 'text-amber-400', label: '收到评价' },
  activity_bonus: { icon: <FireOutlined />, color: 'text-orange-400', label: '活跃奖励' },
  manual_adjustment: { icon: <TrophyOutlined />, color: 'text-cyan-400', label: '手动调整' },
};

// 加分规则
const GAIN_RULES = [
  { action: '完成订单', points: '+10', condition: '每完成 1 单', tip: '按时交付，保证质量' },
  { action: '获得 5 星评价', points: '+50', condition: '雇主评 5 星', tip: '超出预期交付' },
  { action: '获得 4 星评价', points: '+20', condition: '雇主评 4 星', tip: '良好完成工作' },
  { action: '近期活跃', points: '+15/单', condition: '近 30 天完成订单', tip: '持续接单保持活跃' },
];

// 扣分规则
const LOSE_RULES = [
  { action: '取消订单', points: '-20', condition: '每取消 1 单', tip: '接单前请确认能完成', warning: true },
  { action: '获得 2 星评价', points: '-20', condition: '雇主评 2 星', tip: '注意沟通和质量' },
  { action: '获得 1 星评价', points: '-50', condition: '雇主评 1 星', tip: '严重影响声誉', warning: true },
];

interface ReputationData {
  agent_id: string;
  agent_name: string;
  total_score: number;
  level_name: string;
  level_stars: string;
  next_level: { name: string; stars: string; threshold: number } | null;
  points_to_next: number;
  ranking: {
    rank: number;
    total: number;
    percentile: number;
    same_score_count: number;
  };
  breakdown: {
    fulfillment: { score: number; max: number; completed_orders: number; cancelled_orders: number };
    quality: { score: number; max: number; avg_rating: number | null; rated_orders: number };
    activity: { score: number; max: number; recent_orders: number };
  };
}

interface ReputationLog {
  log_id: string;
  change_type: string;
  score_before: number;
  score_after: number;
  score_change: number;
  description: string;
  created_at: string;
}

// 规则说明 Tab
const RulesTab: React.FC = () => (
  <div className="space-y-6">
    {/* 计算公式 */}
    <Alert
      type="info"
      icon={<InfoCircleOutlined />}
      message={
        <div className="flex items-center gap-2">
          <span className="text-cyan-400 font-bold">声誉分 = 1500 (基准) + 履约分 + 质量分 + 活跃分</span>
          <Tag className="bg-slate-700 text-slate-300">范围 1000-3000</Tag>
        </div>
      }
      className="bg-cyan-500/10 border-cyan-500/30"
    />

    {/* 加分规则 */}
    <Card
      className="glass-card"
      title={
        <div className="flex items-center gap-2 text-emerald-400">
          <ArrowUpOutlined />
          <span>如何提高分数</span>
        </div>
      }
    >
      <Table
        dataSource={GAIN_RULES}
        pagination={false}
        size="small"
        columns={[
          { title: '行为', dataIndex: 'action', width: 120, render: (t) => <Text className="text-white">{t}</Text> },
          {
            title: '分数',
            dataIndex: 'points',
            width: 80,
            render: (t) => <Tag className="bg-emerald-500/20 text-emerald-400 border-0">{t}</Tag>
          },
          { title: '条件', dataIndex: 'condition', render: (t) => <Text className="text-slate-400 text-sm">{t}</Text> },
          { title: '建议', dataIndex: 'tip', render: (t) => <Text className="text-cyan-400 text-sm">{t}</Text> },
        ]}
        rowKey="action"
      />
    </Card>

    {/* 扣分规则 */}
    <Card
      className="glass-card"
      title={
        <div className="flex items-center gap-2 text-rose-400">
          <ArrowDownOutlined />
          <span>如何避免减分</span>
        </div>
      }
    >
      <Table
        dataSource={LOSE_RULES}
        pagination={false}
        size="small"
        columns={[
          {
            title: '行为',
            dataIndex: 'action',
            width: 120,
            render: (t, r) => (
              <div className="flex items-center gap-2">
                {r.warning && <WarningOutlined className="text-amber-400" />}
                <Text className="text-white">{t}</Text>
              </div>
            )
          },
          {
            title: '分数',
            dataIndex: 'points',
            width: 80,
            render: (t) => <Tag className="bg-rose-500/20 text-rose-400 border-0">{t}</Tag>
          },
          { title: '条件', dataIndex: 'condition', render: (t) => <Text className="text-slate-400 text-sm">{t}</Text> },
          { title: '提醒', dataIndex: 'tip', render: (t) => <Text className="text-amber-400 text-sm">{t}</Text> },
        ]}
        rowKey="action"
      />
    </Card>

    {/* 等级说明 */}
    <Card
      className="glass-card"
      title={
        <div className="flex items-center gap-2 text-white">
          <TrophyOutlined className="text-amber-400" />
          <span>等级说明</span>
        </div>
      }
    >
      <div className="space-y-3">
        {LEVEL_CONFIG.map((level) => (
          <div
            key={level.name}
            className="flex items-center justify-between p-3 rounded-lg bg-slate-800/50"
          >
            <div className="flex items-center gap-3">
              <span className="text-xl">{level.stars}</span>
              <div>
                <Text className="text-white font-medium">{level.name}</Text>
                <Text className="text-slate-500 text-xs block">{level.threshold}+ 分</Text>
              </div>
            </div>
            <Text className="text-slate-400 text-sm">{level.description}</Text>
          </div>
        ))}
      </div>
    </Card>
  </div>
);

// 声誉分 Tab
const ScoreTab: React.FC<{ reputation: ReputationData | null; loading: boolean }> = ({ reputation, loading }) => {
  if (loading) {
    return <div className="flex justify-center py-12"><Spin size="large" /></div>;
  }

  if (!reputation) {
    return <Empty description="暂无声誉数据" />;
  }

  const currentLevel = LEVEL_CONFIG.find(l => l.name === reputation.level_name) || LEVEL_CONFIG[2];
  const prevThreshold = LEVEL_CONFIG.find(l => l.name === reputation.level_name)?.threshold || 1500;
  const nextThreshold = reputation.next_level?.threshold || 3000;
  const progressPercent = ((reputation.total_score - prevThreshold) / (nextThreshold - prevThreshold)) * 100;

  return (
    <div className="space-y-4">
      {/* 总分概览 */}
      <Card className="glass-card">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-6">
            {/* 等级徽章 */}
            <div className="text-center">
              <div className="text-3xl mb-1">{reputation.level_stars}</div>
              <Tag
                style={{ backgroundColor: `${currentLevel.color}20`, color: currentLevel.color, border: 'none' }}
                className="text-sm px-3 py-1"
              >
                {reputation.level_name}
              </Tag>
            </div>
            {/* 分数 */}
            <div>
              <div className="flex items-baseline gap-1">
                <span className="text-4xl font-bold text-white font-mono">{reputation.total_score}</span>
                <span className="text-slate-500">分</span>
              </div>
              {reputation.next_level && (
                <Text className="text-slate-400 text-sm">
                  距「{reputation.next_level.name}」还需 <span className="text-cyan-400">{reputation.points_to_next}</span> 分
                </Text>
              )}
            </div>
          </div>
          {/* 进度条 */}
          {reputation.next_level && (
            <div className="w-48">
              <Progress
                percent={Math.min(100, Math.max(0, progressPercent))}
                strokeColor={currentLevel.color}
                trailColor="rgba(255,255,255,0.1)"
              />
            </div>
          )}
        </div>
      </Card>

      {/* 排名概览 */}
      <Card className="glass-card" bodyStyle={{ padding: 16 }}>
        <div className="flex items-center justify-between">
          {/* 排名信息 */}
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <TrophyOutlined className="text-amber-400 text-lg" />
              <div>
                <div className="flex items-baseline gap-1">
                  <span className="text-2xl font-bold text-white font-mono">#{reputation.ranking.rank}</span>
                  <span className="text-slate-500 text-sm">/ {reputation.ranking.total}</span>
                </div>
                <Text className="text-slate-500 text-xs">全站排名</Text>
              </div>
            </div>
            <div className="h-10 w-px bg-slate-700" />
            <div>
              <div className="flex items-baseline gap-1">
                <span className="text-2xl font-bold text-cyan-400 font-mono">
                  {reputation.ranking.percentile}%
                </span>
              </div>
              <Text className="text-slate-500 text-xs">超越的打工人</Text>
            </div>
          </div>
          {/* 可视化排名条 */}
          <div className="flex-1 max-w-xs">
            <div className="h-3 bg-slate-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-cyan-500 to-amber-500 rounded-full transition-all duration-500"
                style={{ width: `${reputation.ranking.percentile}%` }}
              />
            </div>
            <div className="flex justify-between mt-1 text-xs text-slate-600">
              <span>后 {100 - reputation.ranking.percentile}%</span>
              <span>前 {reputation.ranking.percentile}%</span>
            </div>
          </div>
        </div>
      </Card>

      {/* 分数构成 */}
      <Row gutter={16}>
        {/* 履约分 */}
        <Col span={8}>
          <Card className="glass-card h-full" bodyStyle={{ padding: 16 }}>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <CheckCircleOutlined className="text-emerald-400 text-lg" />
                <Text className="text-white">履约分</Text>
              </div>
              <Tag className="bg-emerald-500/20 text-emerald-400 border-0">
                {reputation.breakdown.fulfillment.score > 0 ? '+' : ''}{reputation.breakdown.fulfillment.score}
              </Tag>
            </div>
            <Progress
              percent={(Math.abs(reputation.breakdown.fulfillment.score) / reputation.breakdown.fulfillment.max) * 100}
              strokeColor={reputation.breakdown.fulfillment.score >= 0 ? '#10b981' : '#f43f5e'}
              trailColor="rgba(255,255,255,0.1)"
            />
            <div className="flex justify-between mt-3 text-xs">
              <div className="text-center">
                <Text className="text-emerald-400 block">{reputation.breakdown.fulfillment.completed_orders}</Text>
                <Text className="text-slate-500">已完成</Text>
              </div>
              <div className="text-center">
                <Text className="text-rose-400 block">{reputation.breakdown.fulfillment.cancelled_orders}</Text>
                <Text className="text-slate-500">已取消</Text>
              </div>
            </div>
          </Card>
        </Col>
        {/* 质量分 */}
        <Col span={8}>
          <Card className="glass-card h-full" bodyStyle={{ padding: 16 }}>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <StarOutlined className="text-amber-400 text-lg" />
                <Text className="text-white">质量分</Text>
              </div>
              <Tag className="bg-amber-500/20 text-amber-400 border-0">
                {reputation.breakdown.quality.score > 0 ? '+' : ''}{reputation.breakdown.quality.score}
              </Tag>
            </div>
            <Progress
              percent={(Math.abs(reputation.breakdown.quality.score) / reputation.breakdown.quality.max) * 100}
              strokeColor={reputation.breakdown.quality.score >= 0 ? '#f59e0b' : '#f43f5e'}
              trailColor="rgba(255,255,255,0.1)"
            />
            <div className="flex justify-between mt-3 text-xs">
              <div className="text-center">
                <Text className="text-amber-400 block">
                  {reputation.breakdown.quality.avg_rating?.toFixed(1) || '-'}
                </Text>
                <Text className="text-slate-500">平均评分</Text>
              </div>
              <div className="text-center">
                <Text className="text-slate-300 block">{reputation.breakdown.quality.rated_orders}</Text>
                <Text className="text-slate-500">评价数</Text>
              </div>
            </div>
          </Card>
        </Col>
        {/* 活跃分 */}
        <Col span={8}>
          <Card className="glass-card h-full" bodyStyle={{ padding: 16 }}>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <FireOutlined className="text-orange-400 text-lg" />
                <Text className="text-white">活跃分</Text>
              </div>
              <Tag className="bg-orange-500/20 text-orange-400 border-0">
                +{reputation.breakdown.activity.score}
              </Tag>
            </div>
            <Progress
              percent={(reputation.breakdown.activity.score / reputation.breakdown.activity.max) * 100}
              strokeColor="#f97316"
              trailColor="rgba(255,255,255,0.1)"
            />
            <div className="flex justify-between mt-3 text-xs">
              <div className="text-center">
                <Text className="text-orange-400 block">{reputation.breakdown.activity.recent_orders}</Text>
                <Text className="text-slate-500">近30天</Text>
              </div>
              <div className="text-center">
                <Text className="text-slate-400 block">{reputation.breakdown.activity.max}</Text>
                <Text className="text-slate-500">上限</Text>
              </div>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

// 流水 Tab
const LogsTab: React.FC<{ logs: ReputationLog[]; loading: boolean }> = ({ logs, loading }) => {
  if (loading) {
    return <div className="flex justify-center py-12"><Spin size="large" /></div>;
  }

  if (logs.length === 0) {
    return (
      <Empty
        description="暂无流水记录"
        image={Empty.PRESENTED_IMAGE_SIMPLE}
        className="py-12"
      />
    );
  }

  return (
    <Card className="glass-card">
      <Timeline
        items={logs.map((log) => {
          const config = CHANGE_TYPE_CONFIG[log.change_type] || CHANGE_TYPE_CONFIG.manual_adjustment;
          const isPositive = log.score_change >= 0;
          return {
            color: isPositive ? '#10b981' : '#f43f5e',
            dot: <span className={config.color}>{config.icon}</span>,
            children: (
              <div className="flex items-start justify-between py-1">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <Text className="text-white">{log.description}</Text>
                    <Tag
                      className={`${isPositive ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'} border-0`}
                    >
                      {isPositive ? <ArrowUpOutlined /> : <ArrowDownOutlined />} {isPositive ? '+' : ''}{log.score_change}
                    </Tag>
                  </div>
                  <Text className="text-slate-500 text-xs">
                    {log.score_before} → {log.score_after}
                  </Text>
                </div>
                <Text className="text-slate-600 text-xs">
                  {new Date(log.created_at).toLocaleDateString('zh-CN', {
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </Text>
              </div>
            ),
          };
        })}
      />
    </Card>
  );
};

// 主页面组件
const ReputationPage: React.FC = () => {
  const [reputation, setReputation] = useState<ReputationData | null>(null);
  const [logs, setLogs] = useState<ReputationLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('score');
  const [selectedAgentId] = useState('worker_001'); // TODO: 从路由或状态获取

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [repRes, logsRes] = await Promise.all([
          fetch(`http://localhost:8000/api/v1/agents/${selectedAgentId}/reputation`).then(r => r.json()),
          fetch(`http://localhost:8000/api/v1/agents/${selectedAgentId}/reputation/logs`).then(r => r.json()),
        ]);
        setReputation(repRes);
        setLogs(logsRes.logs || []);
      } catch (err) {
        console.error('Failed to fetch reputation data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [selectedAgentId]);

  const tabItems: TabsProps['items'] = [
    {
      key: 'score',
      label: (
        <span className="flex items-center gap-2">
          <TrophyOutlined />
          我的声誉
        </span>
      ),
      children: <ScoreTab reputation={reputation} loading={loading} />,
    },
    {
      key: 'logs',
      label: (
        <span className="flex items-center gap-2">
          <ClockCircleOutlined />
          变化记录
          {logs.length > 0 && (
            <Tag className="bg-slate-700 text-slate-300 border-0 ml-1">{logs.length}</Tag>
          )}
        </span>
      ),
      children: <LogsTab logs={logs} loading={loading} />,
    },
    {
      key: 'rules',
      label: (
        <span className="flex items-center gap-2">
          <QuestionCircleOutlined />
          规则说明
        </span>
      ),
      children: <RulesTab />,
    },
  ];

  return (
    <div className="p-4">
      <Title level={4} className="text-white mb-4 flex items-center gap-2">
        <StarOutlined className="text-amber-400" />
        声誉体系
      </Title>
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={tabItems}
        className="reputation-tabs"
      />
    </div>
  );
};

export default ReputationPage;