import { TabBar } from 'antd-mobile'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  HomeOutlined,
  UserOutlined,
  AppstoreOutlined,
  MessageOutlined,
  BarChartOutlined,
  ThunderboltOutlined,
  StarOutlined,
} from '@ant-design/icons'

const MobileNav = () => {
  const navigate = useNavigate()
  const location = useLocation()

  const items = [
    { key: '/dashboard', title: '首页', icon: <HomeOutlined /> },
    { key: '/agents', title: '代理', icon: <UserOutlined /> },
    { key: '/jobs', title: '任务', icon: <AppstoreOutlined /> },
    { key: '/orders', title: '接单', icon: <ThunderboltOutlined /> },
    { key: '/messages', title: '消息', icon: <MessageOutlined /> },
    { key: '/market', title: '广场', icon: <StarOutlined /> },
    { key: '/reputation', title: '声誉', icon: <StarOutlined /> },
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
