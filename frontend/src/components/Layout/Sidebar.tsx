import { Menu, Typography } from 'antd'
import type { MenuProps } from 'antd'
import {
  HomeOutlined,
  TeamOutlined,
  FileOutlined,
  MessageOutlined,
  BarChartOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons'
import { useNavigate, useLocation } from 'react-router-dom'

const { Text } = Typography

type MenuItem = Required<MenuProps>['items'][number]

const Sidebar = () => {
  const navigate = useNavigate()
  const location = useLocation()

  const menuItems: MenuItem[] = [
    { key: '/dashboard', icon: <HomeOutlined />, label: '仪表盘' },
    { key: '/agents', icon: <TeamOutlined />, label: '代理管理' },
    { key: '/jobs', icon: <FileOutlined />, label: '任务管理' },
    { key: '/messages', icon: <MessageOutlined />, label: '消息中心' },
    { key: '/analytics', icon: <BarChartOutlined />, label: '数据分析' },
  ]

  const activeKey = location.pathname

  const handleMenuClick: MenuProps['onClick'] = (e) => {
    navigate(e.key)
  }

  return (
    <div className="h-full flex flex-col bg-gradient-to-b from-[#0f1a2e] to-[#0a1628]">
      {/* Logo */}
      <div className="p-6 flex items-center gap-3 border-b border-slate-700/30">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500/20 to-purple-500/20 border border-cyan-500/30 flex items-center justify-center">
          <ThunderboltOutlined className="text-xl text-cyan-400" />
        </div>
        <div>
          <Text className="text-lg font-bold text-white block leading-tight">虾虾众包</Text>
          <Text className="text-xs text-slate-500 block">Shrimp Market</Text>
        </div>
      </div>

      {/* Menu */}
      <div className="flex-1 py-4 px-3">
        <Text className="text-xs text-slate-500 px-3 mb-3 block uppercase tracking-wider">主菜单</Text>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[activeKey]}
          items={menuItems}
          onClick={handleMenuClick}
          className="bg-transparent border-0"
          style={{
            background: 'transparent',
          }}
        />
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-slate-700/30">
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
          <span>系统运行正常</span>
        </div>
        <div className="text-xs text-slate-600 mt-1">v1.0.0</div>
      </div>
    </div>
  )
}

export default Sidebar