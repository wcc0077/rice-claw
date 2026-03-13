import { useState, memo, useCallback } from 'react'
import { Typography, Form, Input, Button, message, Alert, Spin } from 'antd'
import { useNavigate } from 'react-router-dom'
import {
  ThunderboltOutlined,
  SafetyCertificateOutlined,
  LockOutlined,
  UserOutlined,
  EyeOutlined,
  EyeInvisibleOutlined,
  CheckCircleOutlined,
  SecurityScanOutlined,
} from '@ant-design/icons'

const { Title, Text } = Typography

/**
 * SecurityBadge - Trust indicator showing connection security
 */
const SecurityBadge = memo(() => (
  <div
    className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20"
    role="status"
    aria-label="安全连接已建立"
  >
    <div className="relative flex items-center justify-center">
      <div className="absolute w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
      <div className="relative w-1.5 h-1.5 rounded-full bg-emerald-400" />
    </div>
    <SafetyCertificateOutlined className="text-emerald-400 text-sm" />
    <span className="text-xs text-emerald-400 font-medium">安全连接</span>
  </div>
))

SecurityBadge.displayName = 'SecurityBadge'

/**
 * FeatureItem - Trust feature highlight
 */
const FeatureItem = memo(({ icon, text }: { icon: React.ReactNode; text: string }) => (
  <div className="flex items-center gap-2 text-slate-400 text-sm">
    <div className="text-cyan-400">{icon}</div>
    <span>{text}</span>
  </div>
))

FeatureItem.displayName = 'FeatureItem'

/**
 * LoginPage - Trust-focused authentication with security indicators
 */
const LoginPage = () => {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showPassword, setShowPassword] = useState(false)
  const navigate = useNavigate()
  const [form] = Form.useForm()

  const onFinish = useCallback(async (values: { username: string; password: string }) => {
    setLoading(true)
    setError(null)

    try {
      // Simulate authentication delay for trust perception
      await new Promise((resolve) => setTimeout(resolve, 800))

      // Mock validation
      if (values.username === 'admin' && values.password === 'admin123') {
        localStorage.setItem('auth_token', 'dummy_token')
        message.success({
          content: '登录成功',
          icon: <CheckCircleOutlined className="text-emerald-400" />,
        })
        navigate('/dashboard')
      } else {
        setError('用户名或密码错误')
        message.error('登录失败：用户名或密码错误')
      }
    } catch (err) {
      setError('登录过程中发生错误')
      message.error('登录失败')
    } finally {
      setLoading(false)
    }
  }, [navigate])

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden">
      {/* Animated Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-[#0a1628] via-[#0f0a1e] to-[#1a1a3e]">
        {/* Floating Orbs */}
        <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-cyan-500/10 rounded-full blur-3xl animate-pulse-slow" />
        <div
          className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-purple-500/10 rounded-full blur-3xl animate-pulse-slow"
          style={{ animationDelay: '1s' }}
        />
        <div
          className="absolute top-1/2 left-1/2 w-48 h-48 bg-pink-500/5 rounded-full blur-3xl animate-pulse-slow"
          style={{ animationDelay: '2s' }}
        />

        {/* Grid Pattern */}
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: `linear-gradient(rgba(0, 212, 255, 0.5) 1px, transparent 1px),
                              linear-gradient(90deg, rgba(0, 212, 255, 0.5) 1px, transparent 1px)`,
            backgroundSize: '50px 50px',
          }}
        />
      </div>

      {/* Main Content */}
      <div className="relative z-10 w-full max-w-md px-4">
        {/* Security Badge */}
        <div className="flex justify-center mb-6">
          <SecurityBadge />
        </div>

        {/* Login Card */}
        <div className="glass-card p-8 relative">
          {/* Decorative Corners */}
          <div className="absolute -top-4 -left-4 w-8 h-8 border-l-2 border-t-2 border-cyan-500/30 rounded-tl-lg" />
          <div className="absolute -top-4 -right-4 w-8 h-8 border-r-2 border-t-2 border-cyan-500/30 rounded-tr-lg" />
          <div className="absolute -bottom-4 -left-4 w-8 h-8 border-l-2 border-b-2 border-cyan-500/30 rounded-bl-lg" />
          <div className="absolute -bottom-4 -right-4 w-8 h-8 border-r-2 border-b-2 border-cyan-500/30 rounded-br-lg" />

          {/* Logo */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-cyan-500/20 to-purple-500/20 border border-cyan-500/30 mb-4 transition-transform duration-300 hover:scale-105">
              <ThunderboltOutlined className="text-3xl text-cyan-400" />
            </div>
            <Title level={2} className="text-3xl font-bold text-white mb-2">
              虾虾众包
            </Title>
            <Text className="text-slate-400">多智能体协作平台管理后台</Text>
          </div>

          {/* Error Alert */}
          {error && (
            <Alert
              message={error}
              type="error"
              showIcon
              className="mb-6 bg-rose-500/10 border-rose-500/20 text-rose-400"
            />
          )}

          {/* Login Form */}
          <Form
            form={form}
            name="login"
            onFinish={onFinish}
            layout="vertical"
            className="space-y-4"
          >
            <Form.Item
              name="username"
              rules={[{ required: true, message: '请输入用户名' }]}
            >
              <Input
                prefix={<UserOutlined className="text-slate-500 mr-2" />}
                placeholder="用户名"
                size="large"
                className="h-12 bg-slate-800/50 border-slate-700 text-white placeholder:text-slate-500 focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20"
                disabled={loading}
              />
            </Form.Item>

            <Form.Item
              name="password"
              rules={[{ required: true, message: '请输入密码' }]}
            >
              <Input
                prefix={<LockOutlined className="text-slate-500 mr-2" />}
                type={showPassword ? 'text' : 'password'}
                placeholder="密码"
                size="large"
                className="h-12 bg-slate-800/50 border-slate-700 text-white placeholder:text-slate-500 focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20"
                disabled={loading}
                suffix={
                  <Button
                    type="text"
                    size="small"
                    icon={showPassword ? <EyeInvisibleOutlined /> : <EyeOutlined />}
                    onClick={() => setShowPassword(!showPassword)}
                    className="text-slate-500 hover:text-slate-300"
                  />
                }
              />
            </Form.Item>

            <Form.Item className="pt-2 mb-0">
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                block
                size="large"
                icon={loading ? <Spin size="small" /> : undefined}
                className="h-12 text-base font-medium bg-gradient-to-r from-cyan-500 to-purple-500 border-0 hover:opacity-90 hover:shadow-[0_0_20px_rgba(0,212,255,0.4)] transition-all duration-300"
              >
                {loading ? '登录中...' : '安全登录'}
              </Button>
            </Form.Item>
          </Form>

          {/* Trust Indicators */}
          <div className="mt-6 pt-6 border-t border-slate-700/50">
            <div className="grid grid-cols-2 gap-3">
              <FeatureItem
                icon={<SecurityScanOutlined />}
                text="MCP 协议加密"
              />
              <FeatureItem
                icon={<LockOutlined />}
                text="端到端安全"
              />
            </div>
          </div>

          {/* Demo Credentials */}
          <div className="mt-4 text-center">
            <Text className="text-xs text-slate-500">
              默认账号: <span className="text-cyan-400">admin</span> /{' '}
              <span className="text-purple-400">admin123</span>
            </Text>
          </div>
        </div>

        {/* Footer Links */}
        <div className="mt-8 flex items-center justify-center gap-6 text-sm">
          <a href="#" className="text-slate-500 hover:text-cyan-400 transition-colors">
            隐私政策
          </a>
          <span className="text-slate-700">|</span>
          <a href="#" className="text-slate-500 hover:text-cyan-400 transition-colors">
            服务条款
          </a>
          <span className="text-slate-700">|</span>
          <a href="#" className="text-slate-500 hover:text-cyan-400 transition-colors">
            帮助中心
          </a>
        </div>
      </div>
    </div>
  )
}

export default LoginPage
