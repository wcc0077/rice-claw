import { Layout as AntdLayout } from 'antd'
import { Outlet } from 'react-router-dom'
import Header from './Header'
import Sidebar from './Sidebar'
import MobileNav from './MobileNav'

const { Content, Sider } = AntdLayout

const MainLayout = () => {
  return (
    <AntdLayout className="min-h-screen">
      {/* Desktop Sidebar */}
      <Sider theme="light" className="hidden md:block" width={240}>
        <Sidebar />
      </Sider>

      <AntdLayout>
        <Header />
        <Content className="p-4 md:p-6">
          <Outlet />
        </Content>
      </AntdLayout>

      {/* Mobile Bottom Navigation */}
      <MobileNav />
    </AntdLayout>
  )
}

export default MainLayout
