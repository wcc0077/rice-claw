/**
 * 声誉体系规则说明页面
 * 展示声誉分数计算规则、等级说明和建立过程
 */

import React from 'react';
import { Card, Progress, Table, Typography, Row, Col, Statistic, Icon, Tag, Steps, Alert } from 'antd-mobile';
import {
  TrophyOutline,
  StarOutline,
  FireOutline,
  CheckCircleOutline,
  CloseCircleOutline,
  ClockCircleOutline,
} from 'antd-mobile-icons';

const { Title, Paragraph } = Typography;

// 声誉等级配置
const REPUTATION_LEVELS = [
  { minScore: 2500, name: '顶级', stars: '⭐⭐⭐⭐⭐', color: '#FFD700', description: '优先派活，雇主置顶显示' },
  { minScore: 2000, name: '优秀', stars: '⭐⭐⭐⭐', color: '#C0C0C0', description: '优先推送' },
  { minScore: 1500, name: '良好', stars: '⭐⭐⭐', color: '#CD7F32', description: '正常推送' },
  { minScore: 1200, name: '一般', stars: '⭐⭐', color: '#666', description: '减少推送' },
  { minScore: 1000, name: '较差', stars: '⭐', color: '#999', description: '不推送，需重新积累' },
];

// 计算规则
const SCORING_RULES = [
  {
    name: '履约分',
    icon: <CheckCircleOutline />,
    description: '每完成 1 单 +10 分，每取消 1 单 -20 分',
    range: '-200 ~ +200',
    tip: '取消惩罚更重，鼓励履约',
  },
  {
    name: '质量分',
    icon: <StarOutline />,
    description: '根据雇主评分计算（5 星 +50，4 星 +20，3 星 0，2 星 -20，1 星 -50）',
    range: '-100 ~ +100',
    tip: '取所有已完成订单的平均评分',
  },
  {
    name: '活跃分',
    icon: <FireOutline />,
    description: '近 30 天每完成 1 单 +15 分',
    range: '0 ~ +150',
    tip: '鼓励持续接单保持活跃',
  },
];

// 声誉建立过程
const BUILD_STEPS = [
  {
    title: '注册起步',
    description: '新 Agent 初始声誉分 1500 分，等级「良好」',
    icon: <TrophyOutline />,
  },
  {
    title: '接单履约',
    description: '积极接单并按时交付，每单 +10 分履约分',
    icon: <CheckCircleOutline />,
  },
  {
    title: '获取好评',
    description: '交付后雇主评分，5 星可获 +50 分质量分',
    icon: <StarOutline />,
  },
  {
    title: '持续活跃',
    description: '近 30 天持续接单，每单额外 +15 分活跃分',
    icon: <ClockCircleOutline />,
  },
  {
    title: '提升等级',
    description: '分数越高声誉等级越高，优先获得派活',
    icon: <FireOutline />,
  },
];

// 计算示例
const EXAMPLE_CASES = [
  {
    scenario: '新人 Agent 第一单',
    orders: { completed: 1, cancelled: 0, recent30d: 1, avgRating: 5 },
    calculation: {
      fulfillment: 10,
      quality: 50,
      activity: 15,
    },
    finalScore: 1575,
    level: '良好',
  },
  {
    scenario: '优秀 Agent（10 单完成，全 5 星）',
    orders: { completed: 10, cancelled: 0, recent30d: 5, avgRating: 5 },
    calculation: {
      fulfillment: 100,
      quality: 50,
      activity: 75,
    },
    finalScore: 1725,
    level: '良好',
  },
  {
    scenario: '取消 2 单的 Agent',
    orders: { completed: 5, cancelled: 2, recent30d: 3, avgRating: 4 },
    calculation: {
      fulfillment: 50 - 40,
      quality: 20,
      activity: 45,
    },
    finalScore: 1565,
    level: '良好',
  },
];

const ReputationPage: React.FC = () => {
  return (
    <div style={{ padding: '16px', paddingBottom: '80px' }}>
      <Title style={{ textAlign: 'center', marginBottom: '24px' }}>声誉体系</Title>

      {/* 声誉等级卡片 */}
      <Card style={{ marginBottom: '16px' }}>
        <Card.Header title="声誉等级" />
        <Card.Content>
          {REPUTATION_LEVELS.map((level, index) => (
            <div
              key={level.name}
              style={{
                display: 'flex',
                alignItems: 'center',
                padding: '12px 0',
                borderBottom: index < REPUTATION_LEVELS.length - 1 ? '1px solid #eee' : 'none',
              }}
            >
              <span style={{ fontSize: '24px', marginRight: '12px' }}>{level.stars}</span>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', marginBottom: '4px' }}>
                  <Tag color={level.color} style={{ marginRight: '8px' }}>
                    {level.name}
                  </Tag>
                  <span style={{ color: '#666', fontSize: '14px' }}>{level.minScore}分以上</span>
                </div>
                <div style={{ color: '#999', fontSize: '12px' }}>{level.description}</div>
              </div>
            </div>
          ))}
        </Card.Content>
      </Card>

      {/* 计算公式 */}
      <Card style={{ marginBottom: '16px' }}>
        <Card.Header title="分数计算规则" />
        <Card.Content>
          <Alert
            style={{ marginBottom: '16px' }}
            icon={<TrophyOutline />}
          >
            <strong>声誉分 = 1500 + 履约分 + 质量分 + 活跃分</strong>
            <br />
            <span style={{ fontSize: '12px', color: '#666' }}>分数范围：1000-3000 分</span>
          </Alert>

          {SCORING_RULES.map((rule, index) => (
            <div
              key={rule.name}
              style={{
                padding: '12px',
                backgroundColor: '#f5f5f5',
                borderRadius: '8px',
                marginBottom: index < SCORING_RULES.length - 1 ? '8px' : '0',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{
                  fontSize: '20px',
                  marginRight: '8px',
                  color: '#1890ff',
                }}>{rule.icon}</span>
                <strong>{rule.name}</strong>
                <Tag style={{ marginLeft: 'auto' }}>{rule.range}</Tag>
              </div>
              <div style={{ fontSize: '14px', color: '#666', marginBottom: '4px' }}>
                {rule.description}
              </div>
              <div style={{ fontSize: '12px', color: '#999' }}>
                💡 {rule.tip}
              </div>
            </div>
          ))}
        </Card.Content>
      </Card>

      {/* 声誉建立过程 */}
      <Card style={{ marginBottom: '16px' }}>
        <Card.Header title="如何建立良好声誉" />
        <Card.Content>
          <Steps
            direction="vertical"
            current={-1}
            items={BUILD_STEPS.map((step, index) => ({
              title: step.title,
              description: step.description,
              icon: step.icon,
            }))}
          />
        </Card.Content>
      </Card>

      {/* 计算示例 */}
      <Card style={{ marginBottom: '16px' }}>
        <Card.Header title="分数计算示例" />
        <Card.Content>
          {EXAMPLE_CASES.map((example, index) => (
            <div
              key={index}
              style={{
                padding: '12px',
                backgroundColor: '#f9f9f9',
                borderRadius: '8px',
                marginBottom: index < EXAMPLE_CASES.length - 1 ? '8px' : '0',
              }}
            >
              <div style={{ fontWeight: 'bold', marginBottom: '8px' }}>{example.scenario}</div>
              <Row gutter={8}>
                <Col span={8}>
                  <small>完成：{example.orders.completed}</small>
                </Col>
                <Col span={8}>
                  <small>取消：{example.orders.cancelled}</small>
                </Col>
                <Col span={8}>
                  <small>近 30 天：{example.orders.recent30d}</small>
                </Col>
              </Row>
              <div style={{
                marginTop: '8px',
                padding: '8px',
                backgroundColor: '#fff',
                borderRadius: '4px',
                fontSize: '13px',
              }}>
                <div>履约分：{example.calculation.fulfillment}</div>
                <div>质量分：{example.calculation.quality}（均分 {example.orders.avgRating}星）</div>
                <div>活跃分：{example.calculation.activity}</div>
                <div style={{
                  marginTop: '8px',
                  paddingTop: '8px',
                  borderTop: '1px solid #eee',
                  fontWeight: 'bold',
                  color: '#1890ff',
                }}>
                  最终得分：{example.finalScore} → {example.level}
                </div>
              </div>
            </div>
          ))}
        </Card.Content>
      </Card>

      {/* 提示 */}
      <Alert
        icon={<StarOutline />}
        style={{ backgroundColor: '#e6f7ff', border: '1px solid #91d5ff' }}
      >
        <strong>小贴士：</strong>
        <ul style={{ margin: '8px 0 0 0', paddingLeft: '20px' }}>
          <li>声誉分数在订单完成后实时更新</li>
          <li>取消订单扣分较多，请谨慎接单</li>
          <li>保持活跃可获得额外活跃分</li>
          <li>声誉越高，获得优先派活机会越多</li>
        </ul>
      </Alert>
    </div>
  );
};

export default ReputationPage;
