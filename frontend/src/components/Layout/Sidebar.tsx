import { Menu, Typography, Badge, Tooltip } from 'antd'
import type { MenuProps } from 'antd'
import {
  HomeOutlined,
  TeamOutlined,
  FileOutlined,
  MessageOutlined,
  BarChartOutlined,
  ThunderboltOutlined,
  SafetyCertificateOutlined,
} from '@ant-design/icons'
import { useNavigate, useLocation } from 'react-router-dom'
import { memo } from 'react'

const { Text } = Typography

type MenuItem = Required<MenuProps>['items'][number]

interface SidebarProps {
  /** Number of unread messages for badge */
  unreadMessages?: number
  /** System health status */
  systemHealth?: 'healthy' | 'degraded' | 'unhealthy'
}

// Trust badge configuration
const trustConfig = {
  healthy: {
    color: 'bg-emerald-400',
    pulseColor: 'bg-emerald-400/30',
    label: '安全',
  },
  degraded: {
    color: 'bg-amber-400',
    pulseColor: 'bg-amber-400/30',
    label: '注意',
  },
  unhealthy: {
    color: 'bg-rose-400',
    pulseColor: 'bg-rose-400/30',
    label: '异常',
  },
}

/**
 * TrustBadge - Security/trust indicator for the sidebar
 */
const TrustBadge = memo(({ status }: { status: 'healthy' | 'degraded' | 'unhealthy' }) => {
  const config = trustConfig[status]

  return (
    <Tooltip title={`系统状态: ${config.label}`} placement="right">
      <div
        className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/50 border border-slate-700/50 cursor-help transition-colors hover:border-slate-600/50"
        role="status"
        aria-label={`系统安全状态: ${config.label}`}
      >
        <div className="relative flex items-center justify-center">
          <div className={`absolute w-2.5 h-2.5 rounded-full ${config.pulseColor} animate-ping`} />
          <div className={`relative w-2 h-2 rounded-full ${config.color}`} />
        </div>
        <SafetyCertificateOutlined className="text-slate-400 text-xs" />
        <span className="text-xs text-slate-400 font-medium">{config.label}</span>
      </div>
    </Tooltip>
  )
})

TrustBadge.displayName = 'TrustBadge'

/**
 * Sidebar - Navigation with trust indicators and accessibility
 * Features: Active state indicators, trust badges, keyboard navigation
 */
const Sidebar = memo(({ unreadMessages = 0, systemHealth = 'healthy' }: SidebarProps) => {
  const navigate = useNavigate()
  const location = useLocation()

  const menuItems: MenuItem[] = [
    {
      key: '/dashboard',
      icon: <HomeOutlined aria-hidden="true" />,
      label: '仪表盘',
    },
    {
      key: '/agents',
      icon: <TeamOutlined aria-hidden="true" />,
      label: '代理管理',
    },
    {
      key: '/jobs',
      icon: <FileOutlined aria-hidden="true" />,
      label: '任务管理',
    },
    {
      key: '/orders',
      icon: <ThunderboltOutlined aria-hidden="true" />,
      label: '接单管理',
    },
    {
      key: '/messages',
      icon: <MessageOutlined aria-hidden="true" />,
      label: (
        <span className="flex items-center gap-2">
          消息中心
          {unreadMessages > 0 && (
            <Badge
              count={unreadMessages > 99 ? '99+' : unreadMessages}
              size="small"
              className="ml-1"
            />
          )}
        </span>
      ),
    },
    {
      key: '/analytics',
      icon: <BarChartOutlined aria-hidden="true" />,
      label: '数据分析',
    },
  ]

  const activeKey = location.pathname

  const handleMenuClick: MenuProps['onClick'] = (e) => {
    navigate(e.key)
  }

  return (
    <div className="h-full flex flex-col bg-gradient-to-b from-deep-700 to-deep-800">
      {/* Logo with trust indicator */}
      <div className="p-6 flex items-center gap-3 border-b border-slate-700/30">
        <div
          className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500/20 to-purple-500/20 border border-cyan-500/30 flex items-center justify-center transition-transform duration-300 hover:scale-105"
          aria-hidden="true"
        >
          <ThunderboltOutlined className="text-xl text-cyan-400" />
        </div>
        <div className="flex-1">
          <Text className="text-lg font-bold text-white block leading-tight">
            虾虾众包
          </Text>
          <Text className="text-xs text-slate-500 block">Shrimp Market</Text>
        </div>
      </div>

      {/* Trust indicator banner */}
      <div className="px-4 py-3 border-b border-slate-700/30">
        <TrustBadge status={systemHealth} />
      </div>

      {/* Navigation Menu with improved accessibility */}
      <div className="flex-1 py-4 px-3">
        <Text className="text-xs text-slate-500 px-3 mb-3 block uppercase tracking-wider font-medium">
          主菜单
        </Text>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[activeKey]}
          items={menuItems}
          onClick={handleMenuClick}
          className="bg-transparent border-0 sidebar-menu"
          style={{ background: 'transparent' }}
          aria-label="主导航菜单"
        />
      </div>

      {/* Footer with version and status */}
      <div className="p-4 border-t border-slate-700/30 space-y-3">
        {/* System status */}
        <div
          className="flex items-center gap-2 text-xs text-slate-500"
          role="status"
          aria-label="系统运行正常"
        >
          <div className="relative flex items-center justify-center">
            <div className="absolute w-2.5 h-2.5 rounded-full bg-emerald-400/30 animate-ping" />
            <div className="relative w-2 h-2 rounded-full bg-emerald-400" />
          </div>
          <span>系统运行正常</span>
        </div>

        {/* Version info */}
        <div className="flex items-center justify-between">
          <div className="text-xs text-slate-600">v1.0.0</div>
          <div className="text-xs text-slate-600">MCP协议</div>
        </div>
      </div>
    </div>
  )
})

Sidebar.displayName = 'Sidebar'

export default Sidebar
