import { useState } from 'react'
import { Layout as AntdLayout, Typography, Space, Dropdown, Avatar, Badge } from 'antd'
import type { MenuProps } from 'antd'
import {
  BellOutlined,
  DownOutlined,
  UserOutlined,
  LogoutOutlined,
  SettingOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'

const { Header: AntdHeader } = AntdLayout
const { Text } = Typography

const Header = () => {
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
    <AntdHeader className="bg-[#0a1628]/80 backdrop-blur-md border-b border-slate-700/30 flex items-center justify-between px-6 sticky top-0 z-50">
      {/* Breadcrumb / Page Title */}
      <div className="flex items-center">
        <Text className="text-slate-400 text-sm">
          欢迎回来，<span className="text-cyan-400">管理员</span>
        </Text>
      </div>

      {/* Right Side Actions */}
      <Space size="large" className="flex items-center">
        {/* Notification Bell */}
        <Badge count={3} size="small" className="cursor-pointer">
          <div className="w-10 h-10 rounded-xl bg-slate-800/50 border border-slate-700/50 flex items-center justify-center hover:border-cyan-500/30 hover:bg-slate-800 transition-all duration-300">
            <BellOutlined className="text-lg text-slate-400 hover:text-cyan-400" />
          </div>
        </Badge>

        {/* User Dropdown */}
        <Dropdown
          menu={{ items, onClick: handleMenuClick }}
          trigger={['click']}
          open={menuOpen}
          onOpenChange={setMenuOpen}
          placement="bottomRight"
        >
          <div className="flex items-center gap-3 cursor-pointer group">
            <div className="text-right hidden md:block">
              <Text className="text-sm text-white font-medium block leading-tight group-hover:text-cyan-400 transition-colors">管理员</Text>
              <Text className="text-xs text-slate-500 block">admin@shrimp.market</Text>
            </div>
            <div className="relative">
              <Avatar
                size={40}
                icon={<UserOutlined />}
                className="bg-gradient-to-br from-cyan-500/20 to-purple-500/20 border-2 border-slate-700 group-hover:border-cyan-500/30 transition-all duration-300"
              />
              <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full bg-green-400 border-2 border-[#0a1628]" />
            </div>
            <DownOutlined className="text-xs text-slate-500 group-hover:text-cyan-400 transition-colors" />
          </div>
        </Dropdown>
      </Space>
    </AntdHeader>
  )
}

export default Header