import { useState, useEffect } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import { Card, Typography, Input, Button, List, message } from 'antd'
import { SendOutlined } from '@ant-design/icons'

const { Title, Text } = Typography

const ChatPage = () => {
  const { agentId } = useParams<{ agentId: string }>()
  const [searchParams] = useSearchParams()
  const agentName = searchParams.get('name') || 'Unknown Agent'
  const [messages, setMessages] = useState<any[]>([])
  const [inputValue, setInputValue] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchMessages()
  }, [agentId])

  const fetchMessages = async () => {
    setLoading(true)
    try {
      // Placeholder - would fetch actual messages
      const mockMessages = [
        { from: 'them', content: '你好，关于任务有什么问题吗？', time: '10:00' },
        { from: 'me', content: '你好，我想确认一下需求细节...', time: '10:05' },
        { from: 'them', content: '好的，我明白了...', time: '10:10' },
      ]
      setMessages(mockMessages)
    } catch (error) {
      message.error('获取消息失败')
    } finally {
      setLoading(false)
    }
  }

  const handleSend = () => {
    if (!inputValue.trim()) return

    const newMessage = { from: 'me', content: inputValue, time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }
    setMessages([...messages, newMessage])
    setInputValue('')
  }

  return (
    <div className="flex flex-col h-[calc(100vh-120px)]">
      <Card className="mb-2">
        <div className="flex items-center">
          <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold mr-3">
            {agentName.charAt(0)}
          </div>
          <div>
            <Title level={4} className="m-0">{agentName}</Title>
            <Text type="success" className="text-sm">在线</Text>
          </div>
        </div>
      </Card>

      <div className="flex-1 overflow-y-auto p-4 bg-gray-50">
        {loading ? (
          <Text type="secondary">加载中...</Text>
        ) : (
          <List
            dataSource={messages}
            renderItem={(msg) => (
              <List.Item style={{ justifyContent: msg.from === 'me' ? 'flex-end' : 'flex-start' }}>
                <div
                  className={`max-w-[70%] p-3 rounded-lg ${
                    msg.from === 'me'
                      ? 'bg-blue-500 text-white rounded-tr-none'
                      : 'bg-white text-gray-800 shadow-sm rounded-tl-none'
                  }`}
                >
                  <Text>{msg.content}</Text>
                  <div className={`text-[10px] mt-1 text-right ${msg.from === 'me' ? 'text-blue-100' : 'text-gray-400'}`}>
                    {msg.time}
                  </div>
                </div>
              </List.Item>
            )}
          />
        )}
      </div>

      <Card className="mt-2">
        <div className="flex items-center">
          <Input
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onPressEnter={handleSend}
            placeholder="输入消息..."
            className="flex-1"
          />
          <Button type="primary" icon={<SendOutlined />} onClick={handleSend} className="ml-2">
            发送
          </Button>
        </div>
      </Card>
    </div>
  )
}

export default ChatPage
