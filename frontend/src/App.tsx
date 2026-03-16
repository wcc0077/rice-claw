import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { ConfigProvider, theme } from 'antd'
import zhCN from 'antd/locale/zh_CN'

import MainLayout from './components/Layout/MainLayout'
import TabLayout from './components/Layout/TabLayout'
import AuthGuard from './components/Auth/AuthGuard'
import DashboardPage from './pages/Dashboard/DashboardPage'
import AgentListPage from './pages/Agents/AgentListPage'
import JobListPage from './pages/Jobs/JobListPage'
import JobDetailPage from './pages/Jobs/JobDetailPage'
import MessageListPage from './pages/Messages/MessageListPage'
import ChatPage from './pages/Messages/ChatPage'
import AnalyticsPage from './pages/Analytics/AnalyticsPage'
import LoginPage from './pages/Login/LoginPage'
import MarketPage from './pages/Market/MarketPage'
import OrderListPage from './pages/Orders/OrderListPage'
import ApiKeyPage from './pages/ApiKeys/ApiKeyPage'
import ReputationPage from './pages/ReputationPage'
import ConnectGuidePage from './pages/ConnectGuide/ConnectGuidePage'
import LandingPage from './pages/Landing/LandingPage'
import SystemMonitor from './pages/SystemMonitor'
import MatchingTestPage from './pages/MatchingTest/MatchingTestPage'
import SecurityPage from './pages/Security/SecurityPage'
import PrivacyPage from './pages/Legal/PrivacyPage'
import TermsPage from './pages/Legal/TermsPage'

function App() {
  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        algorithm: theme.darkAlgorithm,
        token: {
          colorBgContainer: '#0f172a',
          colorBgElevated: '#1e293b',
          colorBorder: 'rgba(255, 255, 255, 0.1)',
          colorText: '#e2e8f0',
          colorTextSecondary: '#94a3b8',
          colorPrimary: '#06b6d4',
        },
        components: {
          Table: {
            headerBg: '#1e293b',
            rowHoverBg: 'rgba(6, 182, 212, 0.1)',
            borderColor: 'rgba(255, 255, 255, 0.05)',
          },
          Popover: {
            colorBgElevated: '#1e293b',
          },
        },
      }}
    >
      <BrowserRouter>
        <Routes>
          {/* Public routes with Tab Layout */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />

          {/* Tab Layout pages (接入指南, 任务广场, 声誉体系, 安全防护) */}
          <Route element={<TabLayout />}>
            <Route path="/connect" element={<ConnectGuidePage />} />
            <Route path="/market" element={<MarketPage />} />
            <Route path="/reputation" element={<ReputationPage />} />
            <Route path="/security" element={<SecurityPage />} />
          </Route>

          {/* Protected routes with MainLayout */}
          <Route
            path="/dashboard"
            element={
              <AuthGuard>
                <MainLayout />
              </AuthGuard>
            }
          >
            <Route index element={<DashboardPage />} />
            <Route path="test-matching" element={<MatchingTestPage />} />
            <Route path="agents" element={<AgentListPage />} />
            <Route path="api-keys" element={<ApiKeyPage />} />
            <Route path="jobs" element={<JobListPage />} />
            <Route path="jobs/:jobId" element={<JobDetailPage />} />
            <Route path="orders" element={<OrderListPage />} />
            <Route path="reputation" element={<ReputationPage />} />
            <Route path="messages" element={<MessageListPage />} />
            <Route path="messages/:agentId" element={<ChatPage />} />
            <Route path="analytics" element={<AnalyticsPage />} />
            <Route path="monitoring" element={<SystemMonitor />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  )
}

export default App
