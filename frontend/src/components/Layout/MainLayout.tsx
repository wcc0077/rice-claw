import { Layout as AntdLayout } from 'antd'
import { Outlet } from 'react-router-dom'
import Header from './Header'
import Sidebar from './Sidebar'
import MobileNav from './MobileNav'
import { memo, useState, useEffect } from 'react'

const { Content, Sider } = AntdLayout

interface MainLayoutProps {
  /** Optional system health status */
  systemHealth?: 'healthy' | 'degraded' | 'unhealthy'
}

/**
 * SkipLink - Accessibility feature for keyboard navigation
 * Allows users to skip to main content
 */
const SkipLink = memo(() => (
  <a
    href="#main-content"
    className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-[100] focus:px-4 focus:py-2 focus:bg-cyan-500 focus:text-white focus:rounded-lg focus:font-medium"
  >
    跳转到主要内容
  </a>
))

SkipLink.displayName = 'SkipLink'

/**
 * MainLayout - Root layout with trust indicators and accessibility
 * Features: Skip links, system health monitoring, responsive design
 */
const MainLayout = memo(({ systemHealth = 'healthy' }: MainLayoutProps) => {
  const [scrolled, setScrolled] = useState(false)

  // Track scroll for header shadow effect
  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 10)
    }

    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  return (
    <AntdLayout className="min-h-screen bg-deep-800">
      {/* Accessibility skip link */}
      <SkipLink />

      {/* Desktop Sidebar */}
      <Sider
        theme="light"
        className="hidden md:block fixed left-0 top-0 bottom-0 z-40"
        width={260}
        style={{
          background: 'transparent',
        }}
        role="complementary"
        aria-label="侧边导航"
      >
        <Sidebar systemHealth={systemHealth} />
      </Sider>

      <AntdLayout className="md:ml-[260px] bg-deep-800">
        <div
          className={`sticky top-0 z-50 transition-shadow duration-300 ${
            scrolled ? 'shadow-lg shadow-black/20' : ''
          }`}
        >
          <Header securityStatus="secure" />
        </div>

        <Content
          id="main-content"
          className="p-6 min-h-[calc(100vh-64px)]"
          role="main"
          aria-label="主要内容区域"
        >
          <Outlet />
        </Content>
      </AntdLayout>

      {/* Mobile Bottom Navigation */}
      <MobileNav />
    </AntdLayout>
  )
})

MainLayout.displayName = 'MainLayout'

export default MainLayout
