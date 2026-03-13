import { useState, useEffect } from 'react'
import { Card, Typography, List, message } from 'antd'

const { Title, Text } = Typography

const MessageListPage = () => {
  const [conversations, setConversations] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchConversations()
  }, [])

  const fetchConversations = async () => {
    setLoading(true)
    try {
      // Placeholder - would fetch actual conversations
      const mockData = [
        {
          id: 'job_001',
          agentId: 'worker_001',
          agentName: 'Python 开发虾',
          lastMessage: '好的，我明白了...',
          lastMessageTime: '10:30',
          unreadCount: 2,
        },
        {
          id: 'job_002',
          agentId: 'worker_003',
          agentName: 'React 专家',
          lastMessage: '任务进度如何？',
          lastMessageTime: '昨天',
          unreadCount: 0,
        },
      ]
      setConversations(mockData)
    } catch (error) {
      message.error('获取消息失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card>
      <Title level={3} className="m-0">
        消息中心
      </Title>

      <List
        dataSource={conversations}
        loading={loading}
        renderItem={(item) => (
          <List.Item
            className={`cursor-pointer hover:bg-gray-50 ${item.unreadCount > 0 ? 'bg-blue-50' : ''}`}
            onClick={() => {
              // Navigate to chat
              console.log('Navigate to chat with', item.agentId)
            }}
          >
            <List.Item.Meta
              avatar={
                <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold">
                  {item.agentName.charAt(0)}
                </div>
              }
              title={
                <div className="flex justify-between items-center">
                  <Text strong>{item.agentName}</Text>
                  <Text type="secondary" className="text-xs">
                    {item.lastMessageTime}
                  </Text>
                </div>
              }
              description={
                <>
                  <Text type="secondary" className="text-sm">
                    {item.lastMessage}
                  </Text>
                  {item.unreadCount > 0 && (
                    <div className="inline-block ml-2 px-2 py-0.5 bg-red-500 text-white text-xs rounded-full">
                      {item.unreadCount}
                    </div>
                  )}
                </>
              }
            />
          </List.Item>
        )}
      />
    </Card>
  )
}

export default MessageListPage
