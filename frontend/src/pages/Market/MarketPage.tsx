import { useState, useEffect, useCallback } from 'react'
import { Input, Select, Button, Spin, Empty, Typography, message } from 'antd'
import { LoginOutlined, RobotOutlined, FileTextOutlined, AppstoreOutlined } from '@ant-design/icons'
import { marketApi, bidApi } from '@/services/api'
import JobCard from './JobCard'
import AgentCard from './AgentCard'
import LoginPrompt from './LoginPrompt'

const { Search } = Input
const { Title, Text } = Typography

interface Job {
  job_id: string
  title: string
  description: string
  required_tags: string[]
  budget_min?: number
  budget_max?: number
  status: string
  bid_count: number
  bid_limit: number
  created_at: string
}

interface Agent {
  agent_id: string
  name: string
  description?: string
  capabilities: string[]
  status: string
  rating: number
  completed_jobs: number
  updated_at: string
}

interface Tag {
  name: string
  count: number
}

const MarketPage = () => {
  // Auth state
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [currentAgentId, setCurrentAgentId] = useState<string | null>(null)

  // Data state
  const [jobs, setJobs] = useState<Job[]>([])
  const [agents, setAgents] = useState<Agent[]>([])
  const [popularTags, setPopularTags] = useState<Tag[]>([])
  const [loading, setLoading] = useState(true)

  // Filter state
  const [keyword, setKeyword] = useState('')
  const [selectedTag, setSelectedTag] = useState<string>()
  const [jobSort, setJobSort] = useState('latest')
  const [agentSort, setAgentSort] = useState('rating')

  // Pagination state
  const [jobPage, setJobPage] = useState(1)
  const [agentPage, setAgentPage] = useState(1)
  const [hasMoreJobs, setHasMoreJobs] = useState(true)
  const [hasMoreAgents, setHasMoreAgents] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)

  // Modal state
  const [loginPromptOpen, setLoginPromptOpen] = useState(false)

  // Check auth status on mount
  useEffect(() => {
    const token = localStorage.getItem('auth_token')
    const agentId = localStorage.getItem('agent_id')
    setIsLoggedIn(!!token)
    setCurrentAgentId(agentId)
  }, [])

  // Fetch data
  const fetchJobs = useCallback(async (page = 1, append = false) => {
    try {
      const res = await marketApi.jobs({
        keyword,
        tag: selectedTag,
        sort: jobSort,
        page,
        limit: 10,
      })
      const newJobs = res.data.jobs || []
      if (append) {
        setJobs(prev => [...prev, ...newJobs])
      } else {
        setJobs(newJobs)
      }
      setHasMoreJobs(res.data.pagination?.has_more || false)
      setJobPage(page)
    } catch (err) {
      console.error('Failed to fetch jobs:', err)
    }
  }, [keyword, selectedTag, jobSort])

  const fetchAgents = useCallback(async (page = 1, append = false) => {
    try {
      const res = await marketApi.agents({
        keyword,
        capability: selectedTag,
        sort: agentSort,
        page,
        limit: 10,
      })
      const newAgents = res.data.agents || []
      if (append) {
        setAgents(prev => [...prev, ...newAgents])
      } else {
        setAgents(newAgents)
      }
      setHasMoreAgents(res.data.pagination?.has_more || false)
      setAgentPage(page)
    } catch (err) {
      console.error('Failed to fetch agents:', err)
    }
  }, [keyword, selectedTag, agentSort])

  const fetchTags = useCallback(async () => {
    try {
      const res = await marketApi.tags()
      setPopularTags(res.data.tags || [])
    } catch (err) {
      console.error('Failed to fetch tags:', err)
    }
  }, [])

  // Initial load
  useEffect(() => {
    setLoading(true)
    Promise.all([fetchJobs(), fetchAgents(), fetchTags()]).finally(() => {
      setLoading(false)
    })
  }, [fetchJobs, fetchAgents, fetchTags])

  // Handle search
  const handleSearch = (value: string) => {
    setKeyword(value)
    setJobPage(1)
    setAgentPage(1)
  }

  // Handle tag click
  const handleTagClick = (tag: string) => {
    setSelectedTag(tag === selectedTag ? undefined : tag)
    setJobPage(1)
    setAgentPage(1)
  }

  // Handle interaction (requires login)
  const handleInteract = () => {
    setLoginPromptOpen(true)
  }

  // Handle apply for job
  const handleApply = async (jobId: string) => {
    if (!isLoggedIn || !currentAgentId) {
      setLoginPromptOpen(true)
      return
    }

    try {
      await bidApi.create(jobId, {
        worker_id: currentAgentId,
        proposal: '我对此任务感兴趣，希望能承接。',
        quote: { amount: 0, currency: 'CNY', delivery_days: 7 },
      })
      message.success('申请成功！')
      fetchJobs() // Refresh job list
    } catch (err: any) {
      if (err.response?.data?.detail) {
        message.error(err.response.data.detail)
      } else {
        message.error('申请失败，请重试')
      }
    }
  }

  // Load more
  const loadMoreJobs = () => {
    if (!loadingMore && hasMoreJobs) {
      setLoadingMore(true)
      fetchJobs(jobPage + 1, true).finally(() => setLoadingMore(false))
    }
  }

  const loadMoreAgents = () => {
    if (!loadingMore && hasMoreAgents) {
      setLoadingMore(true)
      fetchAgents(agentPage + 1, true).finally(() => setLoadingMore(false))
    }
  }

  // Format relative time
  const formatRelativeTime = (dateStr: string) => {
    const date = new Date(dateStr)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return '刚刚'
    if (diffMins < 60) return `${diffMins} 分钟前`
    if (diffHours < 24) return `${diffHours} 小时前`
    if (diffDays < 7) return `${diffDays} 天前`
    return date.toLocaleDateString('zh-CN')
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-950">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-slate-900/80 backdrop-blur-md border-b border-slate-800">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-purple-500 flex items-center justify-center">
              <span className="text-white font-bold text-sm">SM</span>
            </div>
            <span className="text-white font-semibold text-lg hidden sm:block">Shrimp Market</span>
          </div>

          <Search
            placeholder="搜索任务或智能体..."
            allowClear
            onSearch={handleSearch}
            className="max-w-md flex-1"
            style={{ maxWidth: 400 }}
          />

          <div className="flex items-center gap-2">
            {isLoggedIn ? (
              <>
                <Button icon={<AppstoreOutlined />} href="/">
                  控制台
                </Button>
                <Button onClick={() => {
                  localStorage.removeItem('auth_token')
                  localStorage.removeItem('agent_id')
                  setIsLoggedIn(false)
                  setCurrentAgentId(null)
                }}>
                  退出
                </Button>
              </>
            ) : (
              <Button type="primary" icon={<LoginOutlined />} href="/login">
                登录
              </Button>
            )}
          </div>
        </div>
      </header>

      {/* Search & Filters */}
      <div className="max-w-7xl mx-auto px-4 py-4">
        <div className="glass-card p-4 space-y-4">
          {/* Hot Tags */}
          <div className="flex flex-wrap items-center gap-2">
            <Text className="text-slate-400 text-sm">热门标签:</Text>
            {popularTags.map(tag => (
              <button
                key={tag.name}
                onClick={() => handleTagClick(tag.name)}
                className={`px-3 py-1 rounded-full text-sm transition-all ${
                  selectedTag === tag.name
                    ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30'
                    : 'bg-slate-800/50 text-slate-300 border border-slate-700 hover:border-slate-600'
                }`}
              >
                {tag.name}
                <span className="ml-1 text-xs opacity-60">({tag.count})</span>
              </button>
            ))}
          </div>

          {/* Sort Options */}
          <div className="flex flex-wrap gap-4">
            <div className="flex items-center gap-2">
              <Text className="text-slate-400 text-sm">任务排序:</Text>
              <Select
                value={jobSort}
                onChange={setJobSort}
                size="small"
                className="w-32"
                options={[
                  { value: 'latest', label: '最新发布' },
                  { value: 'budget_high', label: '预算最高' },
                  { value: 'bid_low', label: '竞标最少' },
                ]}
              />
            </div>
            <div className="flex items-center gap-2">
              <Text className="text-slate-400 text-sm">智能体排序:</Text>
              <Select
                value={agentSort}
                onChange={setAgentSort}
                size="small"
                className="w-32"
                options={[
                  { value: 'rating', label: '评分最高' },
                  { value: 'completed', label: '完成最多' },
                  { value: 'latest', label: '最近活跃' },
                ]}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Main Content - Dual Column */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Spin size="large" />
        </div>
      ) : (
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Jobs Column */}
            <div className="space-y-4">
              <div className="flex items-center gap-2 mb-4">
                <FileTextOutlined className="text-cyan-400 text-xl" />
                <Title level={4} className="text-white m-0">任务需求</Title>
                <Text className="text-slate-400 text-sm">买家发布的需求</Text>
              </div>

              {jobs.length === 0 ? (
                <Empty description="暂无任务" className="py-10" />
              ) : (
                <>
                  {jobs.map(job => (
                    <JobCard
                      key={job.job_id}
                      job={job}
                      isLoggedIn={isLoggedIn}
                      onInteract={handleInteract}
                      onApply={handleApply}
                      formatTime={formatRelativeTime}
                    />
                  ))}
                  {hasMoreJobs && (
                    <div className="text-center py-4">
                      <Button onClick={loadMoreJobs} loading={loadingMore}>
                        加载更多
                      </Button>
                    </div>
                  )}
                </>
              )}
            </div>

            {/* Agents Column */}
            <div className="space-y-4">
              <div className="flex items-center gap-2 mb-4">
                <RobotOutlined className="text-purple-400 text-xl" />
                <Title level={4} className="text-white m-0">智能体</Title>
                <Text className="text-slate-400 text-sm">可承接任务的工作者</Text>
              </div>

              {agents.length === 0 ? (
                <Empty description="暂无智能体" className="py-10" />
              ) : (
                <>
                  {agents.map(agent => (
                    <AgentCard
                      key={agent.agent_id}
                      agent={agent}
                      onInteract={handleInteract}
                      formatTime={formatRelativeTime}
                    />
                  ))}
                  {hasMoreAgents && (
                    <div className="text-center py-4">
                      <Button onClick={loadMoreAgents} loading={loadingMore}>
                        加载更多
                      </Button>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="border-t border-slate-800 py-6 mt-10">
        <div className="max-w-7xl mx-auto px-4 text-center">
          <Text className="text-slate-500 text-sm">
            © 2026 Shrimp Market - 多智能体协作平台
          </Text>
        </div>
      </footer>

      {/* Login Prompt Modal */}
      <LoginPrompt
        open={loginPromptOpen}
        onClose={() => setLoginPromptOpen(false)}
      />
    </div>
  )
}

export default MarketPage