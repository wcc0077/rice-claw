import { useState, memo } from 'react'
import { Layout as AntdLayout, Typography, Space, Dropdown, Avatar, Badge, Tooltip } from 'antd'
import type { MenuProps } from 'antd'
import {
  BellOutlined,
  DownOutlined,
  UserOutlined,
  LogoutOutlined,
  SettingOutlined,
  SecurityScanOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'

const { Header: AntdHeader } = AntdLayout
const { Text } = Typography

interface HeaderProps {
  /** User's display name */
  userName?: string
  /** User's email */
  userEmail?: string
  /** Number of unread notifications */
  notificationCount?: number
  /** Security status for trust indicator */
  securityStatus?: 'secure' | 'warning' | 'unverified'
}

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
 * Header - Top navigation with trust indicators and accessibility
 * Features: Security badges, notification management, user menu
 */
const Header = memo(({
  userName = '管理员',
  userEmail = 'admin@shrimp.market',
  notificationCount = 0,
  securityStatus = 'secure',
}: HeaderProps) => {
  const [menuOpen, setMenuOpen] = useState(false)
  const navigate = useNavigate()

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
      key: 'logout',
      label: '退出登录',
      icon: <LogoutOutlined />,
      danger: true,
    },
  ]

  const handleMenuClick: MenuProps['onClick'] = ({ key }) => {
    setMenuOpen(false)
    if (key === 'logout') {
      navigate('/login')
    }
  }

  return (
    <AntdHeader
      className="bg-deep-800/80 backdrop-blur-md border-b border-slate-700/30 flex items-center justify-between px-6 sticky top-0 z-50"
      role="banner"
    >
      {/* Left: Welcome message with trust indicator */}
      <div className="flex items-center gap-4">
        <div className="flex items-center">
          <Text className="text-slate-400 text-sm">
            欢迎回来，<span className="text-cyan-400 font-medium">{userName}</span>
          </Text>
        </div>
        <SecurityIndicator status={securityStatus} />
      </div>

      {/* Right: Actions */}
      <Space size="large" className="flex items-center">
        {/* Notification Bell with accessibility */}
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

        {/* User Dropdown with trust indicators */}
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
              {/* Online status indicator */}
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
  )
})

Header.displayName = 'Header'

export default Header
