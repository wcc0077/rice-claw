import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'

import MainLayout from './components/Layout/MainLayout'
import DashboardPage from './pages/Dashboard/DashboardPage'
import AgentListPage from './pages/Agents/AgentListPage'
import JobListPage from './pages/Jobs/JobListPage'
import JobDetailPage from './pages/Jobs/JobDetailPage'
import MessageListPage from './pages/Messages/MessageListPage'
import ChatPage from './pages/Messages/ChatPage'
import AnalyticsPage from './pages/Analytics/AnalyticsPage'
import LoginPage from './pages/Login/LoginPage'

function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <BrowserRouter>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<LoginPage />} />

          {/* Protected routes with layout */}
          <Route path="/" element={<MainLayout />}>
            <Route index element={<DashboardPage />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="agents" element={<AgentListPage />} />
            <Route path="jobs" element={<JobListPage />} />
            <Route path="jobs/:jobId" element={<JobDetailPage />} />
            <Route path="messages" element={<MessageListPage />} />
            <Route path="messages/:agentId" element={<ChatPage />} />
            <Route path="analytics" element={<AnalyticsPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  )
}

export default App
