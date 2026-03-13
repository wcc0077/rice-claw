import { Card, List, Typography } from 'antd'
import { Agent } from '@/types/agent'

const { Text } = Typography

const AgentStatusChart = ({ agents }: { agents: Agent[] }) => {
  const statusCounts = agents.reduce(
    (acc, agent) => {
      acc[agent.status] = (acc[agent.status] || 0) + 1
      return acc
    },
    { idle: 0, busy: 0, offline: 0 }
  )

  const statusData = [
    { key: 'idle', label: '空闲', value: statusCounts.idle, color: '#52c41a' },
    { key: 'busy', label: '工作中', value: statusCounts.busy, color: '#faad14' },
    { key: 'offline', label: '离线', value: statusCounts.offline, color: '#8c8c8c' },
  ]

  return (
    <Card title="代理状态分布">
      <List
        dataSource={statusData}
        renderItem={(item) => (
          <List.Item>
            <div className="flex items-center justify-between w-full">
              <div className="flex items-center">
                <div
                  className="w-3 h-3 rounded-full mr-2"
                  style={{ backgroundColor: item.color }}
                />
                <span>{item.label}</span>
              </div>
              <Text strong>{item.value} 个</Text>
            </div>
          </List.Item>
        )}
      />
    </Card>
  )
}

export default AgentStatusChart
