import { useState, useEffect } from 'react'
import { useMatchingState } from '@/hooks/useMatchingState'
import { jobApi } from '@/services/api'
import StateTimeline from './components/StateTimeline'
import TaskList from './components/TaskList'
import BidList from './components/BidList'
import ActionPanel from './components/ActionPanel'
import { message } from 'antd'

interface Job {
  job_id: string
  title: string
  status: string
  required_tags: string[]
  budget_min?: number | null
  budget_max?: number | null
  bid_count: number
  created_at: string
}

interface Bid {
  bid_id: string
  job_id: string
  worker_id: string
  proposal: string
  quote: { amount: number; currency: string; delivery_days: number }
  is_hired: boolean
  status: string
  submitted_at: string
  worker_name?: string | null
  worker_rating?: number | null
}

interface Worker {
  job_worker_id: string
  bid_id: string
  worker_id: string
  worker_name?: string | null
  worker_rating?: number | null
  status: string
  is_confirmed: boolean
  is_winner: boolean
  quote_amount?: number | null
  proposal?: string | null
}

const MatchingTestPage = () => {
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null)
  const [selectedBidId, setSelectedBidId] = useState<string | null>(null)
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null)
  const [jobs, setJobs] = useState<Job[]>([])
  const [jobsLoading, setJobsLoading] = useState(false)

  // Fetch job list
  const fetchJobs = async () => {
    try {
      setJobsLoading(true)
      const res = await jobApi.list()
      setJobs(res.data.jobs || [])
    } catch (err: any) {
      console.error('Failed to fetch jobs:', err)
      const errorMsg = err?.response?.data?.detail || '获取任务列表失败'
      message.error(errorMsg)
    } finally {
      setJobsLoading(false)
    }
  }

  // Initial fetch
  useEffect(() => {
    fetchJobs()
  }, [])

  // Use polling hook for selected job state
  const { data: jobState, loading: stateLoading } = useMatchingState(selectedJobId, {
    pollInterval: 3000,
    autoStart: !!selectedJobId,
  })

  // Extract data from jobState
  const currentJob = jobState?.job
  const bids: Bid[] = jobState?.bids || []
  const workers: Worker[] = jobState?.workers || []
  const currentStatus = jobState?.state_summary?.current_status || currentJob?.status || ''

  // Get worker_id from selected bid
  const selectedWorkerId = selectedBidId
    ? workers.find((w) => w.bid_id === selectedBidId)?.worker_id || null
    : null

  // Handle job selection
  const handleSelectJob = (jobId: string) => {
    setSelectedJobId(jobId)
    setSelectedBidId(null) // Reset bid selection when changing jobs
  }

  // Handle bid selection
  const handleSelectBid = (bidId: string) => {
    setSelectedBidId(bidId)
  }

  // Handle action complete (refresh state)
  const handleActionComplete = () => {
    // Refresh job list if job was created
    if (!selectedJobId) {
      fetchJobs()
    }
    // useMatchingState will auto-refresh via polling
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-cyan-900/20 to-purple-900/20 p-6">
      <div className="max-w-[1600px] mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-white mb-2">撮合测试页面</h1>
          <p className="text-slate-400">
            手动测试撮合平台核心逻辑：任务创建 → 抢单 → 撮合 → 选择 → 锁单 → 交付
          </p>
        </div>

        {/* State Timeline - Full width at top */}
        {selectedJobId && currentStatus && (
          <div className="mb-6">
            <StateTimeline currentStatus={currentStatus} />
          </div>
        )}

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Column */}
          <div className="space-y-6">
            {/* Task List */}
            <TaskList
              jobs={jobs}
              selectedJobId={selectedJobId}
              onSelectJob={handleSelectJob}
              loading={jobsLoading}
            />

            {/* Bid List */}
            {selectedJobId && (
              <BidList
                bids={bids}
                workers={workers}
                selectedBidId={selectedBidId}
                onSelectBid={handleSelectBid}
                loading={stateLoading}
              />
            )}
          </div>

          {/* Right Column */}
          <div className="space-y-6">
            {/* Action Panel */}
            <ActionPanel
              jobId={selectedJobId}
              jobStatus={currentStatus}
              selectedBidId={selectedBidId}
              workerId={selectedWorkerId}
              selectedAgentId={selectedAgentId}
              onAgentChange={setSelectedAgentId}
              onActionComplete={handleActionComplete}
            />

            {/* State Summary Card */}
            {selectedJobId && jobState && (
              <div className="glass-card p-4">
                <h3 className="text-lg font-semibold text-white mb-4">状态摘要</h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-slate-400">总竞标数</span>
                    <span className="text-white font-mono">{jobState.state_summary.total_bids}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-400">已确认工人</span>
                    <span className="text-white font-mono">{jobState.state_summary.confirmed_workers}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-400">中标者数</span>
                    <span className="text-white font-mono">{jobState.state_summary.winner_count}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-400">支付记录</span>
                    <span className="text-white font-mono">{jobState.state_summary.total_payments}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-400">已支付金额</span>
                    <span className="text-cyan-400 font-mono">
                      ¥{jobState.state_summary.total_paid_amount.toLocaleString('zh-CN')}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default MatchingTestPage
