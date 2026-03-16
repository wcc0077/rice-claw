import { Select, Tag, Space, Empty } from 'antd'
import { UserOutlined } from '@ant-design/icons'
import { useAgentList } from './useAgentList'

interface AgentSelectorProps {
  value?: string
  onChange?: (agentId: string) => void
  placeholder?: string
  disabled?: boolean
  className?: string
}

const statusColorMap: Record<string, string> = {
  idle: 'green',
  busy: 'orange',
  offline: 'default',
}

/**
 * AgentSelector - Agent 选择下拉框
 *
 * 用于接单时选择要使用的 Agent
 */
export function AgentSelector({
  value,
  onChange,
  placeholder = '选择接单 Agent',
  disabled = false,
  className,
}: AgentSelectorProps) {
  const { agents, loading, error } = useAgentList()

  // No agents available
  if (!loading && agents.length === 0 && !error) {
    return (
      <Empty
        image={Empty.PRESENTED_IMAGE_SIMPLE}
        description={
          <span className="text-gray-400">
            暂无可用 Agent，请先创建
          </span>
        }
      />
    )
  }

  return (
    <Select
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      disabled={disabled || !!error}
      loading={loading}
      className={className}
      style={{ minWidth: 200 }}
      optionLabelProp="label"
    >
      {agents.map((agent) => (
        <Select.Option
          key={agent.agent_id}
          value={agent.agent_id}
          label={
            <Space>
              <UserOutlined />
              {agent.name}
            </Space>
          }
        >
          <div className="flex justify-between items-center">
            <span>{agent.name}</span>
            <Space>
              <Tag color={statusColorMap[agent.status] || 'default'}>
                {agent.status}
              </Tag>
              {agent.rating > 0 && (
                <span className="text-yellow-500">
                  ★ {agent.rating.toFixed(1)}
                </span>
              )}
            </Space>
          </div>
        </Select.Option>
      ))}
    </Select>
  )
}

export default AgentSelector