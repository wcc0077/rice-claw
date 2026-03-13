import { Menu } from 'antd'
import type { MenuProps } from 'antd'
import {
  HomeOutlined,
  TeamOutlined,
  FileOutlined,
  MessageOutlined,
  BarChartOutlined,
} from '@ant-design/icons'
import { useNavigate, useLocation } from 'react-router-dom'

type MenuItem = Required<MenuProps>['items'][number]

const Sidebar = () => {
  const navigate = useNavigate()
  const location = useLocation()

  const menuItems: MenuItem[] = [
    { key: '/dashboard', icon: <HomeOutlined />, label: 'Dashboard' },
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
    <div className="h-full flex flex-col">
      <div className="p-4 text-center font-bold text-xl text-blue-600">
        虾虾众包
      </div>
      <Menu
        theme="light"
        mode="inline"
        selectedKeys={[activeKey]}
        items={menuItems}
        className="flex-1"
        onClick={handleMenuClick}
      />
    </div>
  )
}

export default Sidebar
