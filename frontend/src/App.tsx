import { BrowserRouter, Routes, Route, useNavigate } from 'react-router-dom'
import { ConfigProvider, theme } from 'antd'
import zhCN from 'antd/locale/zh_CN'

import MainLayout from './components/Layout/MainLayout'
import AuthGuard from './components/Auth/AuthGuard'
import DashboardPage from './pages/Dashboard/DashboardPage'
import AgentListPage from './pages/Agents/AgentListPage'
import JobListPage from './pages/Jobs/JobListPage'
import JobDetailPage from './pages/Jobs/JobDetailPage'
import MessageListPage from './pages/Messages/MessageListPage'
import ChatPage from './pages/Messages/ChatPage'
import AnalyticsPage from './pages/Analytics/AnalyticsPage'
import LoginPage from './pages/Login/LoginPage'
import OrderListPage from './pages/Orders/OrderListPage'
import ApiKeyPage from './pages/ApiKeys/ApiKeyPage'
import LandingPage from './pages/Landing/LandingPage'
import MarketContent from './pages/Landing/MarketContent'
import ConnectGuideContent from './pages/Landing/ConnectGuideContent'
import ReputationContent from './pages/Landing/ReputationContent'
import SecurityContent from './pages/Landing/SecurityContent'
import HomeContent from './pages/Landing/HomeContent'
import SystemMonitor from './pages/SystemMonitor'
import MatchingTestPage from './pages/MatchingTest/MatchingTestPage'
import PrivacyPage from './pages/Legal/PrivacyPage'
import TermsPage from './pages/Legal/TermsPage'
import ReputationPage from './pages/ReputationPage'

function App() {
  // Wrapper component for HomeContent with navigation (must be inside component)
  const HomeContentWrapper = () => {
    const navigate = useNavigate()
    const onNavigate = (tab: 'connect' | 'market' | 'reputation' | 'security') => {
      navigate(`/${tab}`)
    }
    return <HomeContent onNavigate={onNavigate} />
  }
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
          {/* Public routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/privacy" element={<PrivacyPage />} />
          <Route path="/terms" element={<TermsPage />} />

          {/* Landing Page with nested routes for public tabs */}
          <Route path="/" element={<LandingPage />}>
            <Route index element={<HomeContentWrapper />} />
            <Route path="connect" element={<ConnectGuideContent />} />
            <Route path="market" element={<MarketContent />} />
            <Route path="reputation" element={<ReputationContent />} />
            <Route path="security" element={<SecurityContent />} />
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
