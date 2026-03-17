import { useState, memo } from 'react'
import { Layout as AntdLayout, Tabs, Typography, Space, Dropdown, Avatar, Badge, Tooltip, Button } from 'antd'
import type { MenuProps, TabsProps } from 'antd'
import {
  BellOutlined,
  DownOutlined,
  UserOutlined,
  LogoutOutlined,
  SettingOutlined,
  SecurityScanOutlined,
  CheckCircleOutlined,
  ShopOutlined,
  ApiOutlined,
  TrophyOutlined,
  SafetyCertificateOutlined,
  RocketOutlined,
} from '@ant-design/icons'
import { useNavigate, useLocation, Outlet } from 'react-router-dom'
import { useAuthStore } from '@/stores/auth'

const { Header: AntdHeader, Content } = AntdLayout
const { Text } = Typography

// Security status configuration
const securityConfig = {
  secure: {
    icon: <CheckCircleOutlined className="text-emerald-400" />,
    label: '已安全连接',
    tooltip: '您的连接已加密，系统安全',
  },
  warning: {
    icon: <SecurityScanOutlined className="text-amber-400" />,
    label: '安全检查中',
    tooltip: '正在进行安全验证',
  },
  unverified: {
    icon: <SecurityScanOutlined className="text-rose-400" />,
    label: '未验证',
    tooltip: '请完成安全验证',
  },
}

// Tab configuration
const tabItems: TabsProps['items'] = [
  {
    key: '/connect',
    label: (
      <span className="flex items-center gap-2">
        <RocketOutlined />
        接入指南
      </span>
    ),
  },
  {
    key: '/market',
    label: (
      <span className="flex items-center gap-2">
        <ShopOutlined />
        任务广场
      </span>
    ),
  },
  {
    key: '/reputation',
    label: (
      <span className="flex items-center gap-2">
        <TrophyOutlined />
        声誉体系
      </span>
    ),
  },
  {
    key: '/security',
    label: (
      <span className="flex items-center gap-2">
        <SafetyCertificateOutlined />
        安全防护
      </span>
    ),
  },
]

/**
 * SecurityIndicator - Trust badge showing connection security
 */
const SecurityIndicator = memo(({ status }: { status: 'secure' | 'warning' | 'unverified' }) => {
  const config = securityConfig[status]

  return (
    <Tooltip title={config.tooltip} placement="bottom">
      <div
        className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/50 border border-slate-700/50 cursor-help transition-colors hover:border-emerald-500/30"
        role="status"
        aria-label={`安全状态: ${config.label}`}
      >
        {config.icon}
        <span className="text-xs text-slate-400">{config.label}</span>
      </div>
    </Tooltip>
  )
})

SecurityIndicator.displayName = 'SecurityIndicator'

/**
 * TabLayout - Layout with header and tabs for public pages
 */
const TabLayout = memo(() => {
  const [menuOpen, setMenuOpen] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const { logout } = useAuthStore()

  const userName = '用户'
  const userEmail = 'user@shrimp.market'
  const notificationCount = 0
  const securityStatus = 'secure' as const

  const items: MenuProps['items'] = [
    {
      key: 'profile',
      label: '个人资料',
      icon: <UserOutlined />,
    },
    {
      key: 'settings',
      label: '系统设置',
      icon: <SettingOutlined />,
    },
    {
      type: 'divider',
    },
    {
      key: 'login',
      label: '登录控制台',
      icon: <ApiOutlined />,
    },
    {
      key: 'logout',
      label: '退出登录',
      icon: <LogoutOutlined />,
      danger: true,
    },
  ]

  const handleMenuClick: MenuProps['onClick'] = ({ key }) => {
    setMenuOpen(false)
    if (key === 'logout') {
      logout()
    }
    if (key === 'logout' || key === 'login') {
      navigate('/login')
    }
  }

  const handleTabChange = (key: string) => {
    navigate(key)
  }

  return (
    <AntdLayout className="min-h-screen bg-deep-800">
      {/* Header */}
      <AntdHeader
        className="bg-deep-800/80 backdrop-blur-md border-b border-slate-700/30 flex items-center justify-between px-6 sticky top-0 z-50"
        role="banner"
      >
        {/* Left: Logo and Title */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-purple-500 flex items-center justify-center">
              <span className="text-white font-bold text-sm">R</span>
            </div>
            <Text className="text-white font-medium text-lg">Shrimp Market</Text>
          </div>
          <SecurityIndicator status={securityStatus} />
        </div>

        {/* Right: Actions */}
        <Space size="large" className="flex items-center">
          {/* Dashboard Link */}
          <Tooltip title="进入控制台" placement="bottom">
            <Button
              type="text"
              icon={<ApiOutlined />}
              onClick={() => navigate('/dashboard')}
              className="flex items-center gap-2 text-slate-400 hover:text-cyan-400 border border-slate-700/50 hover:border-cyan-500/30 rounded-lg px-3"
            >
              <span className="hidden sm:inline">控制台</span>
            </Button>
          </Tooltip>

          {/* Notification Bell */}
          <Tooltip title="通知" placement="bottom">
            <Badge
              count={notificationCount}
              size="small"
              className="cursor-pointer"
              aria-label={`${notificationCount} 条未读通知`}
            >
              <div
                className="w-10 h-10 rounded-xl bg-slate-800/50 border border-slate-700/50 flex items-center justify-center hover:border-cyan-500/30 hover:bg-slate-800 transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
                tabIndex={0}
                role="button"
                aria-label="查看通知"
              >
                <BellOutlined className="text-lg text-slate-400 hover:text-cyan-400 transition-colors" />
              </div>
            </Badge>
          </Tooltip>

          {/* User Dropdown */}
          <Dropdown
            menu={{ items, onClick: handleMenuClick }}
            trigger={['click']}
            open={menuOpen}
            onOpenChange={setMenuOpen}
            placement="bottomRight"
            aria-label="用户菜单"
          >
            <div
              className="flex items-center gap-3 cursor-pointer group focus:outline-none focus:ring-2 focus:ring-cyan-500/50 rounded-lg px-2 py-1 -mx-2 -my-1"
              tabIndex={0}
              role="button"
              aria-expanded={menuOpen}
              aria-haspopup="true"
            >
              <div className="text-right hidden md:block">
                <Text className="text-sm text-white font-medium block leading-tight group-hover:text-cyan-400 transition-colors">
                  {userName}
                </Text>
                <Text className="text-xs text-slate-500 block">{userEmail}</Text>
              </div>
              <div className="relative">
                <Avatar
                  size={40}
                  icon={<UserOutlined />}
                  className="bg-gradient-to-br from-cyan-500/20 to-purple-500/20 border-2 border-slate-700 group-hover:border-cyan-500/30 transition-all duration-300"
                  aria-hidden="true"
                />
                <div
                  className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full bg-emerald-400 border-2 border-deep-800"
                  aria-hidden="true"
                >
                  <div className="absolute inset-0 rounded-full bg-emerald-400 animate-ping opacity-50" />
                </div>
              </div>
              <DownOutlined className="text-xs text-slate-500 group-hover:text-cyan-400 transition-colors" />
            </div>
          </Dropdown>
        </Space>
      </AntdHeader>

      {/* Tab Bar */}
      <div className="bg-deep-800/80 border-b border-slate-700/30 sticky top-16 z-40">
        <Tabs
          activeKey={location.pathname}
          items={tabItems}
          onChange={handleTabChange}
          className="px-6 [&_.ant-tabs-nav]:mb-0 [&_.ant-tabs-nav]:before\:border-none [&_.ant-tabs-tab]:px-4 [&_.ant-tabs-tab]:py-3"
          tabBarStyle={{
            marginBottom: 0,
          }}
        />
      </div>

      {/* Content */}
      <Content
        id="main-content"
        className="p-6 min-h-[calc(100vh-120px)]"
        role="main"
        aria-label="主要内容区域"
      >
        <Outlet />
      </Content>
    </AntdLayout>
  )
})

TabLayout.displayName = 'TabLayout'

export default TabLayout