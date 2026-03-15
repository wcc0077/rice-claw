/** Agent types and interfaces. */

export type AgentType = 'employer' | 'worker' | 'all'

export interface Agent {
  agent_id: string
  agent_type: AgentType
  name: string
  capabilities: string[]
  description?: string
  status: 'idle' | 'busy' | 'offline'
  rating: number
  completed_jobs: number
  created_at: string
  updated_at: string
}

export interface AgentFormValues {
  agent_id: string
  agent_type: AgentType
  name: string
  capabilities: string[]
  description?: string
}

export interface AgentStats {
  id: string
  name: string
  type: string
  status: string
  rating: number
  jobs: number
}