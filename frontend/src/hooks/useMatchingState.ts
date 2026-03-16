import { useState, useEffect, useCallback, useRef } from 'react'
import { matchingApi } from '@/services/api'
import { message } from 'antd'

export interface JobFullStatus {
  job: {
    job_id: string
    employer_id: string
    title: string
    description: string
    required_tags: string[]
    budget?: { min: number; max: number } | null
    deadline?: string
    bid_limit: number
    priority: string
    status: string
    budget_min?: number | null
    budget_max?: number | null
    bid_count: number
    created_at: string
    updated_at: string
    closed_at?: string | null
  }
  bids: Array<{
    bid_id: string
    job_id: string
    worker_id: string
    proposal: string
    quote: { amount: number; currency: string; delivery_days: number }
    portfolio_links?: string[] | null
    is_hired: boolean
    status: string
    submitted_at: string
    worker_name?: string | null
    worker_rating?: number | null
  }>
  workers: Array<{
    job_worker_id: string
    bid_id: string
    worker_id: string
    worker_name?: string | null
    worker_rating?: number | null
    status: string
    is_confirmed: boolean
    is_winner: boolean
    subsidy_amount?: number | null
    quote_amount?: number | null
    proposal?: string | null
    confirmed_at?: string | null
  }>
  payments: Array<{
    payment_id: string
    job_id: string
    payer_id: string
    payee_id: string
    amount: number
    type: string
    status: string
    transaction_id?: string | null
    description?: string | null
    created_at: string
  }>
  state_summary: {
    current_status: string
    total_bids: number
    confirmed_workers: number
    winner_count: number
    total_payments: number
    total_paid_amount: number
  }
}

interface UseMatchingStateOptions {
  pollInterval?: number // 轮询间隔（毫秒），默认 3000
  autoStart?: boolean // 是否自动开始轮询，默认 true
}

/**
 * 撮合状态轮询 Hook
 * 用于定期获取任务完整状态，支持开始/停止轮询
 */
export function useMatchingState(
  jobId: string | null,
  options: UseMatchingStateOptions = {}
) {
  const { pollInterval = 3000, autoStart = true } = options

  const [data, setData] = useState<JobFullStatus | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const pollTimerRef = useRef<NodeJS.Timeout | null>(null)
  const lastErrorRef = useRef<string | null>(null)

  // Fetch job full status
  const fetchStatus = useCallback(async () => {
    if (!jobId) return

    try {
      setLoading(true)
      setError(null)
      lastErrorRef.current = null
      const res = await matchingApi.getJobFullStatus(jobId)
      setData(res.data)
    } catch (err: any) {
      console.error('Failed to fetch job full status:', err)
      const errorMsg = err?.response?.data?.detail || '获取任务状态失败'
      setError(errorMsg)
      // Don't show error message for every poll failure (too noisy)
      // Use ref to track last error instead of depending on state
      if (lastErrorRef.current !== errorMsg) {
        lastErrorRef.current = errorMsg
        message.error(errorMsg)
      }
    } finally {
      setLoading(false)
    }
  }, [jobId])

  // Start polling
  const startPolling = useCallback(() => {
    if (pollTimerRef.current) {
      clearInterval(pollTimerRef.current)
    }
    pollTimerRef.current = setInterval(() => {
      fetchStatus()
    }, pollInterval)
    // Also fetch immediately when starting
    fetchStatus()
  }, [fetchStatus, pollInterval])

  // Stop polling
  const stopPolling = useCallback(() => {
    if (pollTimerRef.current) {
      clearInterval(pollTimerRef.current)
      pollTimerRef.current = null
    }
  }, [])

  // Auto-start polling when jobId changes
  useEffect(() => {
    if (autoStart && jobId) {
      startPolling()
    } else {
      stopPolling()
    }

    return () => {
      stopPolling()
    }
  }, [jobId, autoStart, startPolling, stopPolling])

  // Manual refresh function
  const refresh = useCallback(() => {
    return fetchStatus()
  }, [fetchStatus])

  return {
    data,
    loading,
    error,
    refresh,
    startPolling,
    stopPolling,
  }
}
