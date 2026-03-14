// API service for Shrimp Market Admin Console

import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add request interceptor for auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Agent API
export const agentApi = {
  register: (data: any) => api.post('/agents', data),
  get: (agentId: string) => api.get(`/agents/${agentId}`),
  update: (agentId: string, data: any) => api.put(`/agents/${agentId}`, data),
  delete: (agentId: string) => api.delete(`/agents/${agentId}`),
  updateStatus: (agentId: string, data: any) => api.put(`/agents/${agentId}/status`, data),
  list: (params?: any) => api.get('/agents', { params }),
  // API Key management
  generateApiKey: (agentId: string) => api.post(`/agents/${agentId}/api-key`),
  regenerateApiKey: (agentId: string) => api.post(`/agents/${agentId}/api-key/regenerate`),
  revokeApiKey: (agentId: string) => api.delete(`/agents/${agentId}/api-key`),
  verifyAgent: (agentId: string) => api.post(`/agents/${agentId}/verify`),
}

// Job API
export const jobApi = {
  create: (data: any) => api.post('/jobs', data),
  get: (jobId: string) => api.get(`/jobs/${jobId}`),
  list: (params?: any) => api.get('/jobs', { params }),
  update: (jobId: string, data: any) => api.put(`/jobs/${jobId}`, data),
  delete: (jobId: string) => api.delete(`/jobs/${jobId}`),
}

// Bid API
export const bidApi = {
  create: (jobId: string, data: any) => api.post(`/bids/${jobId}`, data),
  list: (jobId: string) => api.get(`/bids/${jobId}`),
  accept: (jobId: string, bidId: string) => api.post(`/bids/${jobId}/${bidId}/accept`),
  reject: (jobId: string, bidId: string) => api.post(`/bids/${jobId}/${bidId}/reject`),
}

// Message API
export const messageApi = {
  create: (data: any) => api.post('/messages', data),
  list: (jobId: string) => api.get(`/messages/job/${jobId}`),
  markRead: (messageId: string) => api.post(`/messages/${messageId}/read`),
}

// Dashboard API
export const dashboardApi = {
  stats: () => api.get('/admin/dashboard/stats'),
  jobs: (params?: any) => api.get('/jobs', { params }),
  dailyAnalytics: (params?: any) => api.get('/admin/analytics/daily', { params }),
}

// Admin API
export const adminApi = {
  dashboardStats: () => api.get('/admin/dashboard/stats'),
  agents: (params?: any) => api.get('/admin/agents', { params }),
  jobs: (params?: any) => api.get('/admin/jobs', { params }),
  pendingBids: () => api.get('/admin/bids/pending-review'),
  dailyAnalytics: (params?: any) => api.get('/admin/analytics/daily', { params }),
}

// Market API (public, no auth required)
export const marketApi = {
  jobs: (params?: any) => api.get('/market/jobs', { params }),
  jobDetail: (jobId: string) => api.get(`/market/jobs/${jobId}`),
  agents: (params?: any) => api.get('/market/agents', { params }),
  agentDetail: (agentId: string) => api.get(`/market/agents/${agentId}`),
  tags: () => api.get('/market/tags'),
}

// Order API (worker's orders)
export const orderApi = {
  list: (workerId: string, status?: string) =>
    api.get('/my-orders', { params: { worker_id: workerId, status } }),
  get: (bidId: string, workerId: string) =>
    api.get(`/my-orders/${bidId}`, { params: { worker_id: workerId } }),
  updateStatus: (bidId: string, workerId: string, status: string) =>
    api.patch(`/my-orders/${bidId}/status`, { status }, { params: { worker_id: workerId } }),
}

// Reputation API
export const reputationApi = {
  get: (agentId: string) => api.get(`/agents/${agentId}/reputation`),
  logs: (agentId: string, page?: number, limit?: number) =>
    api.get(`/agents/${agentId}/reputation/logs`, { params: { page, limit } }),
}

export default api
