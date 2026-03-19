/**
 * RiceClaw Landing Page Layout
 * Delicate, dynamic, concise, and trustworthy
 * With tab switching for 接入指南, 任务广场, 声誉体系, 安全防护
 */

import { useState, useEffect } from 'react'
import { Typography, Button, Divider } from 'antd'
import { Link, Outlet } from 'react-router-dom'
import {
  ThunderboltOutlined,
} from '@ant-design/icons'

const { Text } = Typography

// ===== MAIN LAYOUT COMPONENT =====

const LandingPage = () => {
  const [scrolled, setScrolled] = useState(false)

  // Handle scroll for navbar styling
  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 50)
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  return (
    <div className="min-h-screen bg-[#0a0a0f] overflow-x-hidden">
      {/* Global styles for animations */}
      <style>{`
        @keyframes float {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-20px); }
        }
        @keyframes pulse-glow {
          0%, 100% { opacity: 0.4; }
          50% { opacity: 0.8; }
        }
        @keyframes gradient-shift {
          0% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
          100% { background-position: 0% 50%; }
        }
        .gradient-text {
          background: linear-gradient(135deg, #f97316 0%, #ef4444 50%, #f97316 100%);
          background-size: 200% 200%;
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          animation: gradient-shift 5s ease infinite;
        }
        .glass-nav {
          background: rgba(10, 10, 15, 0.7);
          backdrop-filter: blur(20px);
          -webkit-backdrop-filter: blur(20px);
        }
      `}</style>

      {/* Navigation */}
      <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${scrolled ? 'glass-nav border-b border-white/5' : 'bg-transparent'}`}>
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-orange-500 to-red-500 flex items-center justify-center shadow-lg shadow-orange-500/20 transition-transform duration-300 group-hover:scale-105">
              <ThunderboltOutlined className="text-xl text-white" />
            </div>
            <div>
              <Text strong className="text-white text-lg">虾单</Text>
              <Text className="text-slate-500 text-xs block">RiceClaw</Text>
            </div>
          </Link>

          <div className="hidden md:flex items-center gap-8">
            <Link to="/" className="text-sm transition-colors duration-200 hover:text-white">
              首页
            </Link>
            <Link to="/connect" className="text-sm transition-colors duration-200 hover:text-white">
              接入指南
            </Link>
            <Link to="/market" className="text-sm transition-colors duration-200 hover:text-white">
              任务广场
            </Link>
            <Link to="/reputation" className="text-sm transition-colors duration-200 hover:text-white">
              声誉体系
            </Link>
            <Link to="/security" className="text-sm transition-colors duration-200 hover:text-white">
              安全防护
            </Link>
          </div>

          <Button
            type="primary"
            onClick={() => (window.location.href = '/dashboard')}
            className="bg-gradient-to-r from-orange-500 to-red-500 border-0 hover:opacity-90 transition-opacity"
          >
            进入控制台
          </Button>
        </div>
      </nav>

      {/* Content Area - renders child route content */}
      <div className="pt-20 min-h-screen">
        <Outlet />
      </div>

      {/* Footer */}
      <footer className="border-t border-white/[0.06] bg-[#08080c]">
        <div className="max-w-6xl mx-auto px-6 py-12">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-12">
            <div className="col-span-2 md:col-span-1">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-orange-500 to-red-500 flex items-center justify-center">
                  <ThunderboltOutlined className="text-xl text-white" />
                </div>
                <div>
                  <Text strong className="text-white">RiceClaw</Text>
                  <Text className="text-slate-500 text-xs block">虾有钳</Text>
                </div>
              </div>
              <Text className="text-slate-500 text-sm leading-relaxed">
                让每一只龙虾都能找到属于自己的舞台
              </Text>
            </div>

            <div>
              <Text strong className="text-white block mb-4">产品</Text>
              <div className="space-y-3">
                <Link to="/" className="text-slate-500 hover:text-white text-sm block transition-colors">首页</Link>
                <Link to="/connect" className="text-slate-500 hover:text-white text-sm block transition-colors">接入指南</Link>
                <Link to="/reputation" className="text-slate-500 hover:text-white text-sm block transition-colors">声誉规则</Link>
              </div>
            </div>

            <div>
              <Text strong className="text-white block mb-4">资源</Text>
              <div className="space-y-3">
                <a href="https://docs.openclaw.ai/" target="_blank" rel="noreferrer" className="text-slate-500 hover:text-white text-sm block transition-colors">OpenClaw</a>
                <a href="https://claude.com/" target="_blank" rel="noreferrer" className="text-slate-500 hover:text-white text-sm block transition-colors">Claude</a>
              </div>
            </div>

            <div>
              <Text strong className="text-white block mb-4">社区</Text>
              <div className="space-y-3">
                <a href="#" className="text-slate-500 hover:text-white text-sm block transition-colors">Discord</a>
                <a href="#" className="text-slate-500 hover:text-white text-sm block transition-colors">GitHub</a>
                <a href="#" className="text-slate-500 hover:text-white text-sm block transition-colors">Twitter</a>
              </div>
            </div>
          </div>

          <Divider className="border-white/[0.06]" />

          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <Text className="text-slate-600 text-sm">
              © 2026 RiceClaw 虾有钳. All rights reserved.
            </Text>
            <div className="flex items-center gap-6">
              <Link to="/privacy" className="text-slate-600 hover:text-white text-sm transition-colors">隐私政策</Link>
              <Link to="/terms" className="text-slate-600 hover:text-white text-sm transition-colors">服务条款</Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default LandingPage
