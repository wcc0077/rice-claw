import { useState, useEffect, useRef, useCallback, memo } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import { Typography, Input, Button, List, message, Skeleton, Tooltip } from 'antd'
import {
  SendOutlined,
  UserOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  DoubleRightOutlined,
  MoreOutlined,
  PhoneOutlined,
  VideoCameraOutlined,
  ArrowLeftOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useAsyncEffect } from '@/hooks/useFetchOnce'

const { Title, Text } = Typography

interface Message {
  id: string
  from: 'me' | 'them'
  content: string
  time: string
  status?: 'sent' | 'delivered' | 'read'
  isTyping?: boolean
}

/**
 * MessageBubble - Individual chat message with trust indicators
 */
const MessageBubble = memo(({ message }: { message: Message }) => {
  const isMe = message.from === 'me'

  if (message.isTyping) {
    return (
      <div className="flex justify-start mb-4">
        <div className="flex items-end gap-2 max-w-[70%]">
          <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center">
            <UserOutlined className="text-slate-400 text-sm" />
          </div>
          <div className="px-4 py-3 rounded-2xl rounded-tl-none bg-slate-800 border border-slate-700">
            <div className="flex gap-1">
              <span className="w-2 h-2 rounded-full bg-slate-500 animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-2 h-2 rounded-full bg-slate-500 animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-2 h-2 rounded-full bg-slate-500 animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className={`flex mb-4 ${isMe ? 'justify-end' : 'justify-start'}`}>
      <div className={`flex items-end gap-2 max-w-[80%] ${isMe ? 'flex-row-reverse' : ''}`}>
        {/* Avatar */}
        <div
          className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
            isMe
              ? 'bg-gradient-to-br from-cyan-500/20 to-purple-500/20 border border-cyan-500/30'
              : 'bg-slate-700 border border-slate-600'
          }`}
        >
          <UserOutlined className={`text-sm ${isMe ? 'text-cyan-400' : 'text-slate-400'}`} />
        </div>

        {/* Message Content */}
        <div className="flex flex-col">
          <div
            className={`px-4 py-2.5 rounded-2xl ${
              isMe
                ? 'bg-gradient-to-r from-cyan-500 to-cyan-600 text-white rounded-tr-none'
                : 'bg-slate-800 text-slate-200 rounded-tl-none border border-slate-700'
            }`}
          >
            <Text className={`text-sm leading-relaxed ${isMe ? 'text-white' : 'text-slate-200'}`}>
              {message.content}
            </Text>
          </div>

          {/* Time & Status */}
          <div
            className={`flex items-center gap-2 mt-1 text-xs ${
              isMe ? 'justify-end' : 'justify-start'
            }`}
          >
            <span className="text-slate-500">{message.time}</span>
            {isMe && message.status && (
              <Tooltip
                title={
                  message.status === 'read'
                    ? '已读'
                    : message.status === 'delivered'
                    ? '已送达'
                    : '已发送'
                }
              >
                <span className="flex items-center gap-0.5">
                  {message.status === 'read' ? (
                    <>
                      <CheckCircleOutlined className="text-emerald-400 text-[10px]" />
                      <CheckCircleOutlined className="text-emerald-400 text-[10px] -ml-1.5" />
                    </>
                  ) : message.status === 'delivered' ? (
                    <CheckCircleOutlined className="text-slate-500 text-[10px]" />
                  ) : (
                    <ClockCircleOutlined className="text-slate-500 text-[10px]" />
                  )}
                </span>
              </Tooltip>
            )}
          </div>
        </div>
      </div>
    </div>
  )
})

MessageBubble.displayName = 'MessageBubble'

/**
 * ChatHeader - Chat header with trust indicators
 */
const ChatHeader = memo(({
  agentName,
  isOnline,
  lastSeen,
}: {
  agentName: string
  isOnline: boolean
  lastSeen?: string
}) => {
  const navigate = useNavigate()

  return (
    <div className="flex items-center justify-between p-4 border-b border-slate-700/30">
      <div className="flex items-center gap-3">
        <Button
          icon={<ArrowLeftOutlined />}
          type="text"
          className="text-slate-400 hover:text-white"
          onClick={() => navigate('/messages')}
        />
        <div className="relative">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500/20 to-purple-600/10 border-2 border-slate-700 flex items-center justify-center">
            <UserOutlined className="text-purple-400" />
          </div>
          {isOnline && (
            <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full bg-emerald-400 border-2 border-deep-800">
              <div className="absolute inset-0 rounded-full bg-emerald-400 animate-ping opacity-50" />
            </div>
          )}
        </div>
        <div>
          <Title level={5} className="text-white m-0 text-base">
            {agentName}
          </Title>
          <div className="flex items-center gap-1.5">
            <div
              className={`w-1.5 h-1.5 rounded-full ${
                isOnline ? 'bg-emerald-400' : 'bg-slate-500'
              }`}
            />
            <Text className={`text-xs ${isOnline ? 'text-emerald-400' : 'text-slate-500'}`}>
              {isOnline ? '在线' : lastSeen || '离线'}
            </Text>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <Button
          icon={<PhoneOutlined />}
          type="text"
          className="text-slate-400 hover:text-cyan-400"
        />
        <Button
          icon={<VideoCameraOutlined />}
          type="text"
          className="text-slate-400 hover:text-cyan-400"
        />
        <Button
          icon={<MoreOutlined />}
          type="text"
          className="text-slate-400 hover:text-white"
        />
      </div>
    </div>
  )
})

ChatHeader.displayName = 'ChatHeader'

/**
 * ChatPage - Real-time chat with dark mode and trust indicators
 */
const ChatPage = () => {
  const { agentId } = useParams<{ agentId: string }>()
  const [searchParams] = useSearchParams()
  const agentName = searchParams.get('name') || '未知代理'

  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [loading, setLoading] = useState(true)
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Mock fetch messages
  const fetchMessages = useCallback(async () => {
    setLoading(true)
    try {
      // Placeholder - would fetch actual messages
      const mockMessages: Message[] = [
        {
          id: '1',
          from: 'them',
          content: '你好，关于任务有什么问题吗？',
          time: '10:00',
          status: 'read',
        },
        {
          id: '2',
          from: 'me',
          content: '你好！我想确认一下需求细节，特别是关于接口的认证方式。',
          time: '10:05',
          status: 'read',
        },
        {
          id: '3',
          from: 'them',
          content: '没问题，我们使用 Bearer Token 认证，我会在文档里详细说明。',
          time: '10:10',
          status: 'read',
        },
        {
          id: '4',
          from: 'me',
          content: '好的，明白了。预计什么时候可以完成？',
          time: '10:15',
          status: 'delivered',
        },
      ]
      setMessages(mockMessages)
    } catch (error) {
      message.error('获取消息失败')
    } finally {
      setLoading(false)
    }
  }, [agentId])

  useAsyncEffect(fetchMessages, [fetchMessages])

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isTyping])

  const handleSend = () => {
    if (!inputValue.trim()) return

    const newMessage: Message = {
      id: Date.now().toString(),
      from: 'me',
      content: inputValue.trim(),
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      status: 'sent',
    }

    setMessages([...messages, newMessage])
    setInputValue('')

    // Simulate typing indicator
    setTimeout(() => {
      setIsTyping(true)
      setTimeout(() => {
        setIsTyping(false)
        const reply: Message = {
          id: (Date.now() + 1).toString(),
          from: 'them',
          content: '收到，我会尽快处理。',
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          status: 'read',
        }
        setMessages((prev) => [...prev, reply])
      }, 2000)
    }, 500)
  }

  return (
    <div className="flex flex-col h-[calc(100vh-140px)] -mt-6 -mx-6">
      {/* Chat Header */}
      <ChatHeader agentName={agentName} isOnline={true} />

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 bg-gradient-to-b from-deep-800/50 to-deep-900/50">
        {loading ? (
          <div className="space-y-4">
            {[...Array(3)].map((_, i) => (
              <div
                key={i}
                className={`flex mb-4 ${i % 2 === 0 ? 'justify-start' : 'justify-end'}`}
              >
                <div className="flex items-end gap-2 max-w-[70%]">
                  <Skeleton.Avatar size={32} active />
                  <Skeleton.Input style={{ width: 200, height: 40 }} active />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <>
            {/* Date separator */}
            <div className="flex items-center justify-center my-4">
              <div className="px-3 py-1 rounded-full bg-slate-800/50 text-xs text-slate-500">
                今天
              </div>
            </div>

            <List
              dataSource={messages}
              renderItem={(msg) => <MessageBubble message={msg} />}
            />

            {isTyping && (
              <MessageBubble
                message={{
                  id: 'typing',
                  from: 'them',
                  content: '',
                  time: '',
                  isTyping: true,
                }}
              />
            )}

            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-slate-700/30 bg-deep-800/80">
        <div className="flex items-end gap-2">
          <Input.TextArea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onPressEnter={(e) => {
              if (!e.shiftKey) {
                e.preventDefault()
                handleSend()
              }
            }}
            placeholder="输入消息..."
            autoSize={{ minRows: 1, maxRows: 4 }}
            className="flex-1 bg-slate-800/50 border-slate-700 text-white placeholder:text-slate-500 resize-none"
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleSend}
            disabled={!inputValue.trim()}
            className="bg-gradient-to-r from-cyan-500 to-purple-500 border-0 h-10"
          >
            发送
          </Button>
        </div>
        <div className="flex items-center justify-between mt-2">
          <Text className="text-xs text-slate-500">
            按 Enter 发送，Shift + Enter 换行
          </Text>
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <DoubleRightOutlined className="text-emerald-400" />
            <span>MCP 加密连接</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ChatPage
