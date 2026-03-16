import { useState, useEffect } from 'react'
import { message } from 'antd'
import api from '@/services/api'

export interface AgentInfo {
  agent_id: string
  name: string
  agent_type: string
  status: string
  rating: number
}

export function useAgentList() {
  const [agents, setAgents] = useState<AgentInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchAgents = async () => {
    try {
      setLoading(true)
      const response = await api.get('/users/me/agents')
      setAgents(response.data)
      setError(null)
    } catch (err: any) {
      const errorMsg = err?.response?.data?.detail || '获取 Agent 列表失败'
      setError(errorMsg)
      // Don't show message on 401 - user might not be logged in
      if (err?.response?.status !== 401) {
        message.error(errorMsg)
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAgents()
  }, [])

  return { agents, loading, error, refetch: fetchAgents }
}