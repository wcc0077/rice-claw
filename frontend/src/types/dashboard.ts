/** Dashboard data interfaces. */

export interface DashboardStats {
  total_agents: number
  active_jobs: number
  pending_bids: number
  completed_today: number
  revenue_today: number
  agent_status_breakdown: {
    idle: number
    busy: number
    offline: number
  }
  job_status_breakdown: {
    OPEN: number
    ACTIVE: number
    REVIEW: number
    CLOSED: number
  }
}

export interface DailyAnalytics {
  date: string
  new_agents: number
  new_jobs: number
  completed_jobs: number
  total_revenue: number
}
