/** Message types and interfaces. */

export interface Message {
  message_id: string
  job_id: string
  from_agent_id: string
  to_agent_id: string
  content: string
  message_type: 'text' | 'file' | 'image'
  attachments?: any[]
  is_read: boolean
  created_at: string
}

export interface Conversation {
  id: string
  agentId: string
  agentName: string
  lastMessage: string
  lastMessageTime: string
  unreadCount: number
}

export interface MessageFormValues {
  job_id: string
  to_agent_id: string
  content: string
  message_type?: string
  attachments?: any[]
}
