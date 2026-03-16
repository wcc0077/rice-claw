import { CheckCircleFilled, ClockCircleFilled, CloseCircleFilled } from '@ant-design/icons'
import { Steps } from 'antd'
import { JobStatus } from '@/types/job-status'

interface StateTimelineProps {
  currentStatus: string
}

// Status flow order (matches the state machine)
const STATUS_FLOW: { key: JobStatus; title: string; description: string }[] = [
  { key: JobStatus.OPEN, title: '开放中', description: '任务已发布，等待抢单' },
  { key: JobStatus.BIDDING, title: '抢单中', description: '工人正在抢单' },
  { key: JobStatus.LOCKED, title: '已锁单', description: '已选中标的，等待支付订金' },
  { key: JobStatus.WORKING, title: '进行中', description: '工人正在执行任务' },
  { key: JobStatus.SELECTED, title: '已交付', description: '任务已完成，等待确认' },
  { key: JobStatus.CLOSED, title: '已关闭', description: '任务已结束' },
]

/**
 * 状态时间线 - 可视化展示任务状态流转
 * 状态流程：OPEN → BIDDING → LOCKED → WORKING → SELECTED → CLOSED
 */
const StateTimeline = ({ currentStatus }: StateTimelineProps) => {
  // Map current status to progress
  const getCurrentStep = () => {
    const statusIndex: Record<string, number> = {
      OPEN: 0,
      BIDDING: 1,
      LOCKED: 2,
      WORKING: 3,
      SELECTED: 4,
      CLOSED: 5,
    }
    return statusIndex[currentStatus] ?? 0
  }

  const currentStep = getCurrentStep()

  // Custom status render
  const renderStatusIcon = (index: number) => {
    if (index < currentStep) {
      return <CheckCircleFilled style={{ color: '#52c41a' }} />
    }
    if (index === currentStep) {
      return <ClockCircleFilled style={{ color: '#1890ff' }} />
    }
    return <CloseCircleFilled style={{ color: 'rgba(255, 255, 255, 0.3)' }} />
  }

  return (
    <div className="glass-card p-6">
      <h3 className="text-lg font-semibold text-white mb-4">任务状态</h3>
      <Steps
        current={currentStep}
        items={STATUS_FLOW.map((step, index) => ({
          key: step.key,
          title: (
            <span className={index <= currentStep ? 'text-white' : 'text-slate-500'}>
              {step.title}
            </span>
          ),
          description: (
            <span className={index <= currentStep ? 'text-slate-300' : 'text-slate-600'}>
              {step.description}
            </span>
          ),
          icon: renderStatusIcon(index),
          status: index < currentStep ? 'finish' : index === currentStep ? 'process' : 'wait',
        }))}
        responsive={false}
        size="small"
        className="state-timeline-steps"
      />
      <style>{`
        .state-timeline-steps .ant-steps-item-tail {
          background-color: rgba(255, 255, 255, 0.1);
        }
        .state-timeline-steps .ant-steps-item-finish .ant-steps-item-tail {
          background-color: #52c41a;
        }
        .state-timeline-steps .ant-steps-item-icon {
          background-color: rgba(255, 255, 255, 0.1);
          border: 2px solid rgba(255, 255, 255, 0.3);
        }
        .state-timeline-steps .ant-steps-item-finish .ant-steps-item-icon {
          background-color: #52c41a;
          border-color: #52c41a;
        }
        .state-timeline-steps .ant-steps-item-process .ant-steps-item-icon {
          background-color: #1890ff;
          border-color: #1890ff;
        }
      `}</style>
    </div>
  )
}

export default StateTimeline
