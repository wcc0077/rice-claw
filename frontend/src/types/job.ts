/** Job types and interfaces. */

export interface Job {
  job_id: string
  employer_id: string
  title: string
  description: string
  required_tags: string[]
  budget_min?: number
  budget_max?: number
  currency: string
  deadline?: string
  bid_limit: number
  bid_count: number
  status: 'OPEN' | 'ACTIVE' | 'REVIEW' | 'CLOSED'
  created_at: string
  updated_at: string
}

export interface JobFormValues {
  employer_id: string
  title: string
  description: string
  required_tags: string[]
  budget_min?: number
  budget_max?: number
  deadline?: string
  bid_limit?: number
  priority?: string
}

export interface JobStats {
  id: string
  title: string
  employer: string
  status: string
  bidCount: number
  budget: string
  deadline: string
}
