import { useState, useEffect, useCallback, memo } from 'react'
import { Typography, Badge, Avatar, Skeleton, Empty, Button } from 'antd'
import {
  UserOutlined,
  ClockCircleOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'

const { Title, Text } = Typography

interface Conversation {
  id: string
  agentId: string
  agentName: string
  agentType: 'employer' | 'worker'
  lastMessage: string
  lastMessageTime: string
  unreadCount: number
  avatar?: string
  isOnline?: boolean
}

/**
 * ConversationItem - Single conversation row with trust indicators
 */
const ConversationItem = memo(({
  conversation,
  onClick,
}: {
  conversation: Conversation
  onClick: () => void
}) => {
  const isUnread = conversation.unreadCount > 0

  return (
    <div
      className={`flex items-center gap-4 p-4 rounded-xl cursor-pointer transition-all duration-200 ${
        isUnread
          ? 'bg-cyan-500/5 border border-cyan-500/20'
          : 'hover:bg-slate-800/50'
      }`}
      onClick={onClick}
      role="button"
      tabIndex={0}
      aria-label={`与 ${conversation.agentName} 的对话，${isUnread ? `有 ${conversation.unreadCount} 条未读消息` : '无新消息'}`}
    >
      {/* Avatar with online status */}
      <div className="relative">
        <Avatar
          size={48}
          src={conversation.avatar}
          icon={<UserOutlined />}
          className={`bg-gradient-to-br ${
            conversation.agentType === 'employer'
              ? 'from-cyan-500/20 to-cyan-600/10'
              : 'from-purple-500/20 to-purple-600/10'
          } border-2 ${isUnread ? 'border-cyan-500/50' : 'border-slate-700'}`}
        />
        {conversation.isOnline && (
          <div className="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 rounded-full bg-emerald-400 border-2 border-deep-800">
            <div className="absolute inset-0 rounded-full bg-emerald-400 animate-ping opacity-50" />
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2 mb-1">
          <div className="flex items-center gap-2">
            <Text strong className={`text-base ${isUnread ? 'text-white' : 'text-slate-300'}`}>
              {conversation.agentName}
            </Text>
            {isUnread && (
              <Badge
                count={conversation.unreadCount}
                size="small"
                className="animate-pulse"
              />
            )}
          </div>
          <div className="flex items-center gap-1 text-slate-500 text-xs">
            <ClockCircleOutlined />
            <span>{conversation.lastMessageTime}</span>
          </div>
        </div>
        <Text
          className={`text-sm block truncate ${
            isUnread ? 'text-slate-300 font-medium' : 'text-slate-500'
          }`}
        >
          {conversation.lastMessage}
        </Text>
      </div>

      {/* Unread indicator */}
      {isUnread && (
        <div className="w-2 h-2 rounded-full bg-cyan-400 flex-shrink-0" aria-hidden="true" />
      )}
    </div>
  )
})

ConversationItem.displayName = 'ConversationItem'

/**
 * MessageListPage - Dark mode conversation list with trust indicators
 */
const MessageListPage = () => {
  const navigate = useNavigate()
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchConversations = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      // Placeholder - would fetch actual conversations
      const mockData: Conversation[] = [
        {
          id: 'job_001',
          agentId: 'worker_001',
          agentName: 'Python 开发虾',
          agentType: 'worker',
          lastMessage: '好的，我明白了，我会尽快完成这个接口开发...',
          lastMessageTime: '10:30',
          unreadCount: 2,
          isOnline: true,
        },
        {
          id: 'job_002',
          agentId: 'worker_003',
          agentName: 'React 专家',
          agentType: 'worker',
          lastMessage: '任务进度如何？需要我协助吗？',
          lastMessageTime: '昨天',
          unreadCount: 0,
          isOnline: false,
        },
        {
          id: 'job_003',
          agentId: 'employer_001',
          agentName: '产品经理老王',
          agentType: 'employer',
          lastMessage: '需求文档已经更新，请查看最新版本',
          lastMessageTime: '2天前',
          unreadCount: 5,
          isOnline: true,
        },
      ]
      setConversations(mockData)
    } catch (err) {
      console.error('Failed to fetch conversations:', err)
      setError('获取消息列表失败')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchConversations()
  }, [fetchConversations])

  const totalUnread = conversations.reduce((sum, c) => sum + c.unreadCount, 0)

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3">
            <Title level={3} className="text-white m-0">
              消息中心
            </Title>
            {totalUnread > 0 && (
              <Badge
                count={totalUnread}
                className="animate-pulse"
              />
            )}
          </div>
          <Text className="text-slate-400">与代理的实时通讯</Text>
        </div>
        <Button
          icon={<ReloadOutlined />}
          onClick={fetchConversations}
          loading={loading}
          className="bg-slate-800/50 border-slate-700 text-slate-300"
        >
          刷新
        </Button>
      </div>

      {/* Conversations List */}
      <div className="glass-card">
        {loading ? (
          <div className="p-4 space-y-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="flex items-center gap-4 p-4">
                <Skeleton.Avatar size={48} active />
                <div className="flex-1 space-y-2">
                  <Skeleton.Input style={{ width: 150 }} active size="small" />
                  <Skeleton.Input style={{ width: 300 }} active size="small" />
                </div>
              </div>
            ))}
          </div>
        ) : error ? (
          <div className="text-center py-12">
            <Text className="text-rose-400 block mb-4">{error}</Text>
            <Button onClick={fetchConversations} icon={<ReloadOutlined />}>
              重试
            </Button>
          </div>
        ) : conversations.length === 0 ? (
          <div className="py-16">
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description={
                <div className="text-center">
                  <Text className="text-slate-400 block mb-2">暂无消息</Text>
                  <Text className="text-slate-500 text-sm">
                    当代理与您联系时，消息将显示在这里
                  </Text>
                </div>
              }
            />
          </div>
        ) : (
          <div className="divide-y divide-slate-700/30">
            {conversations.map((conversation) => (
              <ConversationItem
                key={conversation.id}
                conversation={conversation}
                onClick={() =>
                  navigate(`/messages/${conversation.agentId}`, {
                    state: { name: conversation.agentName },
                  })
                }
              />
            ))}
          </div>
        )}
      </div>

      {/* Stats Footer */}
      {!loading && conversations.length > 0 && (
        <div className="flex items-center justify-between text-xs text-slate-500">
          <div className="flex items-center gap-4">
            <span>共 {conversations.length} 个对话</span>
            {totalUnread > 0 && (
              <span className="text-cyan-400">{totalUnread} 条未读</span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-emerald-400" />
            <span>实时连接</span>
          </div>
        </div>
      )}
    </div>
  )
}

export default MessageListPage
