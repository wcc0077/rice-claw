import { Layout as AntdLayout } from 'antd'
import { Outlet } from 'react-router-dom'
import Header from './Header'
import Sidebar from './Sidebar'
import MobileNav from './MobileNav'

const { Content, Sider } = AntdLayout

const MainLayout = () => {
  return (
    <AntdLayout className="min-h-screen bg-[#0a1628]">
      {/* Desktop Sidebar */}
      <Sider
        theme="light"
        className="hidden md:block fixed left-0 top-0 bottom-0 z-40"
        width={260}
        style={{
          background: 'transparent',
        }}
      >
        <Sidebar />
      </Sider>

      <AntdLayout className="md:ml-[260px] bg-[#0a1628]">
        <Header />
        <Content className="p-6 min-h-[calc(100vh-64px)]">
          <Outlet />
        </Content>
      </AntdLayout>

      {/* Mobile Bottom Navigation */}
      <MobileNav />
    </AntdLayout>
  )
}

export default MainLayout