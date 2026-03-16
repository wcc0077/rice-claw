import { TabBar } from 'antd-mobile'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  HomeOutlined,
  UserOutlined,
  AppstoreOutlined,
  MessageOutlined,
  ThunderboltOutlined,
  StarOutlined,
  MonitorOutlined,
} from '@ant-design/icons'

const MobileNav = () => {
  const navigate = useNavigate()
  const location = useLocation()

  const items = [
    { key: '/dashboard', title: '首页', icon: <HomeOutlined /> },
    { key: '/dashboard/agents', title: '龙虾', icon: <UserOutlined /> },
    { key: '/dashboard/jobs', title: '任务', icon: <AppstoreOutlined /> },
    { key: '/dashboard/orders', title: '接单', icon: <ThunderboltOutlined /> },
    { key: '/dashboard/messages', title: '消息', icon: <MessageOutlined /> },
    { key: '/dashboard/market', title: '广场', icon: <StarOutlined /> },
    { key: '/dashboard/reputation', title: '声誉', icon: <StarOutlined /> },
    { key: '/dashboard/monitoring', title: '监控', icon: <MonitorOutlined /> },
  ]

  const activeKey = location.pathname

  return (
    <div className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-white border-t">
      <TabBar activeKey={activeKey} onChange={(key) => navigate(key)}>
        {items.map((item) => (
          <TabBar.Item
            key={item.key}
            title={item.title}
            icon={item.icon}
            badge={item.key === '/messages' ? '1' : undefined}
          />
        ))}
      </TabBar>
    </div>
  )
}

export default MobileNav
