/**
 * Job status types and configuration
 * Shared across all components to avoid stringly-typed code
 */

export enum JobStatus {
  OPEN = 'OPEN',
  BIDDING = 'BIDDING',
  LOCKED = 'LOCKED',
  WORKING = 'WORKING',
  SELECTED = 'SELECTED',
  CLOSED = 'CLOSED',
}

export interface JobStatusConfig {
  label: string
  color: string
  icon: React.ReactNode
}

export const jobStatusConfig: Record<JobStatus, JobStatusConfig> = {
  [JobStatus.OPEN]: {
    label: '开放中',
    color: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    icon: null,
  },
  [JobStatus.BIDDING]: {
    label: '抢单中',
    color: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
    icon: null,
  },
  [JobStatus.LOCKED]: {
    label: '已锁单',
    color: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
    icon: null,
  },
  [JobStatus.WORKING]: {
    label: '进行中',
    color: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
    icon: null,
  },
  [JobStatus.SELECTED]: {
    label: '已交付',
    color: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    icon: null,
  },
  [JobStatus.CLOSED]: {
    label: '已关闭',
    color: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
    icon: null,
  },
}

export const bidStatusConfig: Record<string, { label: string; color: string }> = {
  BIDDING: { label: '抢单中', color: 'cyan' },
  PENDING: { label: '待处理', color: 'orange' },
  ACCEPTED: { label: '已接受', color: 'green' },
  REJECTED: { label: '已拒绝', color: 'red' },
  WORKING: { label: '进行中', color: 'blue' },
  COMPLETED: { label: '已完成', color: 'purple' },
}
