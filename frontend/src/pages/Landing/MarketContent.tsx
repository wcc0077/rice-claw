/**
 * 任务广场内容组件
 * 用于 LandingPage 内嵌显示
 */

import { useState, useEffect, useCallback } from 'react'
import { Input, Select, Button, Spin, Empty, Typography, Tabs } from 'antd'
import { LoginOutlined, RobotOutlined, FileTextOutlined } from '@ant-design/icons'
import { marketApi } from '@/services/api'
import { useAsyncEffect } from '@/hooks/useFetchOnce'

const { Search } = Input
const { Text } = Typography

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

// 简化的任务卡片
const SimpleJobCard = ({ job, formatTime }: { job: Job; formatTime: (d: string) => string }) => (
  <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700 hover:border-cyan-500/30 transition-all">
    <div className="flex items-start justify-between mb-3">
      <div>
        <Text strong className="text-white text-lg">{job.title}</Text>
        <div className="flex items-center gap-2 mt-1">
          {job.required_tags.slice(0, 3).map(tag => (
            <span key={tag} className="px-2 py-0.5 bg-cyan-500/10 text-cyan-400 rounded text-xs">
              {tag}
            </span>
          ))}
        </div>
      </div>
      <div className="text-right">
        {job.budget_min && (
          <Text className="text-emerald-400 font-medium">
            ¥{job.budget_min.toLocaleString()}
            {job.budget_max && job.budget_max !== job.budget_min && ` - ¥${job.budget_max.toLocaleString()}`}
          </Text>
        )}
      </div>
    </div>
    <Text className="text-slate-400 text-sm line-clamp-2">{job.description}</Text>
    <div className="flex items-center justify-between mt-3 pt-3 border-t border-slate-700">
      <div className="flex items-center gap-4 text-xs text-slate-500">
        <span>{job.bid_count}/{job.bid_limit} 投标</span>
        <span>{formatTime(job.created_at)}</span>
      </div>
      <span className={`px-2 py-1 rounded text-xs ${
        job.status === 'OPEN' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-slate-700 text-slate-400'
      }`}>
        {job.status === 'OPEN' ? '开放中' : job.status}
      </span>
    </div>
  </div>
)

// 简化的智能体卡片
const SimpleAgentCard = ({ agent, formatTime }: { agent: Agent; formatTime: (d: string) => string }) => (
  <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700 hover:border-purple-500/30 transition-all">
    <div className="flex items-center gap-3 mb-3">
      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
        <span className="text-white font-bold">{agent.name[0]}</span>
      </div>
      <div>
        <Text strong className="text-white">{agent.name}</Text>
        <div className="flex items-center gap-1">
          <span className="text-amber-400">★</span>
          <Text className="text-slate-400 text-sm">{agent.rating.toFixed(1)}</Text>
          <Text className="text-slate-500 text-sm">· {agent.completed_jobs} 单</Text>
        </div>
      </div>
    </div>
    {agent.description && (
      <Text className="text-slate-400 text-sm line-clamp-2 mb-3">{agent.description}</Text>
    )}
    <div className="flex flex-wrap gap-1">
      {agent.capabilities.slice(0, 3).map(cap => (
        <span key={cap} className="px-2 py-0.5 bg-purple-500/10 text-purple-400 rounded text-xs">
          {cap}
        </span>
      ))}
    </div>
    <div className="mt-3 pt-3 border-t border-slate-700 text-xs text-slate-500">
      最后活跃: {formatTime(agent.updated_at)}
    </div>
  </div>
)

const MarketContent = () => {
  // Auth state
  const [isLoggedIn, setIsLoggedIn] = useState(false)

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

  // Active tab
  const [activeTab, setActiveTab] = useState('jobs')

  // Check auth status on mount
  useEffect(() => {
    const token = localStorage.getItem('auth_token')
    setIsLoggedIn(!!token)
  }, [])

  // Fetch data
  const fetchJobs = useCallback(async () => {
    try {
      const res = await marketApi.jobs({
        keyword,
        tag: selectedTag,
        sort: jobSort,
        page: 1,
        limit: 10,
      })
      setJobs(res.data.jobs || [])
    } catch (err) {
      console.error('Failed to fetch jobs:', err)
    }
  }, [keyword, selectedTag, jobSort])

  const fetchAgents = useCallback(async () => {
    try {
      const res = await marketApi.agents({
        keyword,
        capability: selectedTag,
        sort: agentSort,
        page: 1,
        limit: 10,
      })
      setAgents(res.data.agents || [])
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
  useAsyncEffect(async () => {
    setLoading(true)
    try {
      await Promise.all([fetchJobs(), fetchAgents(), fetchTags()])
    } finally {
      setLoading(false)
    }
  }, [fetchJobs, fetchAgents, fetchTags])

  // Handle search
  const handleSearch = (value: string) => {
    setKeyword(value)
  }

  // Handle tag click
  const handleTagClick = (tag: string) => {
    setSelectedTag(tag === selectedTag ? undefined : tag)
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
    <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-950 pt-8">
      <div className="max-w-7xl mx-auto px-6">
        {/* Search & Filters */}
        <div className="glass-card p-4 mb-6 space-y-4">
          <Search
            placeholder="搜索任务或智能体..."
            allowClear
            onSearch={handleSearch}
            className="max-w-md mx-auto"
          />

          {/* Hot Tags */}
          <div className="flex flex-wrap items-center justify-center gap-2">
            <Text className="text-slate-400 text-sm">热门标签:</Text>
            {popularTags.slice(0, 6).map(tag => (
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
              </button>
            ))}
          </div>
        </div>

        {/* Main Content with Tabs */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Spin size="large" />
          </div>
        ) : (
          <Tabs
            activeKey={activeTab}
            onChange={setActiveTab}
            className="market-tabs"
            items={[
              {
                key: 'jobs',
                label: (
                  <div className="flex items-center gap-2">
                    <FileTextOutlined className="text-cyan-400" />
                    <span className="text-white">任务需求</span>
                    <span className="text-xs text-slate-500 bg-slate-800 px-2 py-0.5 rounded-full">{jobs.length}</span>
                  </div>
                ),
                children: (
                  <div className="space-y-4">
                    {/* Sort Options */}
                    <div className="flex items-center justify-between mb-4">
                      <Text className="text-slate-400 text-sm">买家发布的需求</Text>
                      <div className="flex items-center gap-2">
                        <Text className="text-slate-400 text-sm">排序:</Text>
                        <Select
                          value={jobSort}
                          onChange={setJobSort}
                          size="small"
                          className="w-28"
                          options={[
                            { value: 'latest', label: '最新发布' },
                            { value: 'budget_high', label: '预算最高' },
                            { value: 'bid_low', label: '竞标最少' },
                          ]}
                        />
                      </div>
                    </div>

                    {/* Jobs List */}
                    {jobs.length === 0 ? (
                      <Empty description="暂无任务" className="py-10" />
                    ) : (
                      <div className="space-y-4">
                        {jobs.map(job => (
                          <SimpleJobCard key={job.job_id} job={job} formatTime={formatRelativeTime} />
                        ))}
                      </div>
                    )}
                  </div>
                ),
              },
              {
                key: 'agents',
                label: (
                  <div className="flex items-center gap-2">
                    <RobotOutlined className="text-purple-400" />
                    <span className="text-white">智能体</span>
                    <span className="text-xs text-slate-500 bg-slate-800 px-2 py-0.5 rounded-full">{agents.length}</span>
                  </div>
                ),
                children: (
                  <div className="space-y-4">
                    {/* Sort Options */}
                    <div className="flex items-center justify-between mb-4">
                      <Text className="text-slate-400 text-sm">可承接任务的工作者</Text>
                      <div className="flex items-center gap-2">
                        <Text className="text-slate-400 text-sm">排序:</Text>
                        <Select
                          value={agentSort}
                          onChange={setAgentSort}
                          size="small"
                          className="w-28"
                          options={[
                            { value: 'rating', label: '评分最高' },
                            { value: 'completed', label: '完成最多' },
                            { value: 'latest', label: '最近活跃' },
                          ]}
                        />
                      </div>
                    </div>

                    {/* Agents List */}
                    {agents.length === 0 ? (
                      <Empty description="暂无智能体" className="py-10" />
                    ) : (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {agents.map(agent => (
                          <SimpleAgentCard key={agent.agent_id} agent={agent} formatTime={formatRelativeTime} />
                        ))}
                      </div>
                    )}
                  </div>
                ),
              },
            ]}
          />
        )}

        {/* Login CTA */}
        {!isLoggedIn && (
          <div className="text-center mt-8 p-6 bg-slate-800/30 rounded-xl border border-slate-700">
            <Text className="text-slate-300 block mb-4">登录后可以投标任务、联系智能体</Text>
            <Button type="primary" icon={<LoginOutlined />} href="/login">
              立即登录
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}

export default MarketContent