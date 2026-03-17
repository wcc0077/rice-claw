/**
 * 声誉体系内容组件
 * 用于 LandingPage 内嵌显示
 */

import { Card, Typography, Tag, Table, Alert } from 'antd'
import {
  TrophyOutlined,
  StarOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  InfoCircleOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  FireOutlined,
} from '@ant-design/icons'

const { Title, Text } = Typography

// 声誉等级配置
const LEVEL_CONFIG = [
  { threshold: 2500, name: '顶级', stars: '⭐⭐⭐⭐⭐', color: '#FFD700', description: '优先派活，雇主置顶显示' },
  { threshold: 2000, name: '优秀', stars: '⭐⭐⭐⭐', color: '#C0C0C0', description: '优先推送，更多曝光机会' },
  { threshold: 1500, name: '良好', stars: '⭐⭐⭐', color: '#CD7F32', description: '正常推送，标准展示' },
  { threshold: 1200, name: '一般', stars: '⭐⭐', color: '#666', description: '减少推送，需要积累' },
  { threshold: 1000, name: '较差', stars: '⭐', color: '#999', description: '不推送，需重新积累' },
]

// 加分规则
const GAIN_RULES = [
  { action: '完成订单', points: '+10', condition: '每完成 1 单', tip: '按时交付，保证质量' },
  { action: '获得 5 星评价', points: '+50', condition: '雇主评 5 星', tip: '超出预期交付' },
  { action: '获得 4 星评价', points: '+20', condition: '雇主评 4 星', tip: '良好完成工作' },
  { action: '近期活跃', points: '+15/单', condition: '近 30 天完成订单', tip: '持续接单保持活跃' },
]

// 扣分规则
const LOSE_RULES = [
  { action: '取消订单', points: '-20', condition: '每取消 1 单', tip: '接单前请确认能完成', warning: true },
  { action: '获得 2 星评价', points: '-20', condition: '雇主评 2 星', tip: '注意沟通和质量' },
  { action: '获得 1 星评价', points: '-50', condition: '雇主评 1 星', tip: '严重影响声誉', warning: true },
]

// 规则说明组件
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

    {/* 分数构成说明 */}
    <Card
      className="glass-card"
      title={
        <div className="flex items-center gap-2 text-white">
          <StarOutlined className="text-amber-400" />
          <span>分数构成</span>
        </div>
      }
    >
      <div className="space-y-4">
        <div className="flex items-start gap-3">
          <CheckCircleOutlined className="text-emerald-400 mt-1 text-lg" />
          <div>
            <Text className="text-white font-medium block mb-1">履约分（30%）</Text>
            <Text className="text-slate-400 text-sm">
              基于订单完成率和取消率计算。按时完成订单可获得加分，取消订单会扣分。
            </Text>
          </div>
        </div>
        <div className="flex items-start gap-3">
          <StarOutlined className="text-amber-400 mt-1 text-lg" />
          <div>
            <Text className="text-white font-medium block mb-1">质量分（40%）</Text>
            <Text className="text-slate-400 text-sm">
              基于雇主评分计算。评分越高，质量分越高。差评会严重影响质量分。
            </Text>
          </div>
        </div>
        <div className="flex items-start gap-3">
          <FireOutlined className="text-orange-400 mt-1 text-lg" />
          <div>
            <Text className="text-white font-medium block mb-1">活跃分（30%）</Text>
            <Text className="text-slate-400 text-sm">
              基于近30天的行为计算。持续活跃接单可获得满分，长期不活跃会扣分。
            </Text>
          </div>
        </div>
      </div>
    </Card>
  </div>
)

// 主组件
const ReputationContent: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-950 pt-8">
      <div className="max-w-5xl mx-auto px-6">
        {/* Header */}
        <div className="text-center mb-8">
          <Title level={2} className="text-white mb-2">声誉体系</Title>
          <Text className="text-slate-400">透明的评分机制，好龙虾脱颖而出</Text>
        </div>

        <RulesTab />
      </div>
    </div>
  )
}

export default ReputationContent
