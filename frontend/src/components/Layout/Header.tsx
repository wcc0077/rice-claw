import { useState } from 'react'
import { Layout as AntdLayout, Typography, Space, Dropdown, Avatar } from 'antd'
import type { MenuProps } from 'antd'
import {
  BellOutlined,
  DownOutlined,
  UserOutlined,
  LogoutOutlined,
  MenuOutlined,
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
      key: 'logout',
      label: '退出登录',
      icon: <LogoutOutlined />,
      danger: true,
    },
  ]

  const handleMenuClick: MenuProps['onClick'] = ({ key }) => {
    setMenuOpen(false)
    if (key === 'logout') {
      // Handle logout
      navigate('/login')
    }
  }

  return (
    <AntdHeader className="bg-white shadow-sm flex items-center justify-between px-4 md:px-6">
      <div className="flex items-center md:hidden">
        <MenuOutlined className="text-xl" />
        <Text className="ml-2 font-bold text-lg">虾虾众包</Text>
      </div>

      <Space className="ml-auto flex items-center">
        <BellOutlined className="text-xl cursor-pointer" />
        <Dropdown
          menu={{
            items,
            onClick: handleMenuClick,
          }}
          trigger={['click']}
          open={menuOpen}
          onOpenChange={setMenuOpen}
        >
          <div className="flex items-center cursor-pointer">
            <Avatar icon={<UserOutlined />} />
            <DownOutlined className="ml-1 text-sm" />
          </div>
        </Dropdown>
      </Space>
    </AntdHeader>
  )
}

export default Header
