import { useState, memo, useCallback, useEffect, useRef } from 'react'
import { Typography, Form, Input, Button, message, Alert, Spin, Tabs } from 'antd'
import { useNavigate, useSearchParams } from 'react-router-dom'
import {
  ThunderboltOutlined,
  SafetyCertificateOutlined,
  LockOutlined,
  UserOutlined,
  EyeOutlined,
  EyeInvisibleOutlined,
  CheckCircleOutlined,
  SecurityScanOutlined,
  MobileOutlined,
  MailOutlined,
} from '@ant-design/icons'
import { authApi } from '@/services/api'

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
 * LoginPage - Trust-focused authentication with phone SMS and password login
 */
const LoginPage = () => {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showPassword, setShowPassword] = useState(false)
  const [countdown, setCountdown] = useState(0)
  const [sendingCode, setSendingCode] = useState(false)
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [phoneForm] = Form.useForm()
  const [passwordForm] = Form.useForm()
  const timerRef = useRef<NodeJS.Timeout | null>(null)

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current)
      }
    }
  }, [])

  // Phone login with SMS code
  const handleSendCode = useCallback(async () => {
    try {
      const phone = phoneForm.getFieldValue('phone')
      if (!phone || !/^1[3-9]\d{9}$/.test(phone)) {
        message.error('请输入正确的手机号')
        return
      }

      setSendingCode(true)
      const response = await authApi.sendSmsCode(phone)

      if (response.data.success) {
        message.success('验证码已发送')
        // Start countdown
        setCountdown(60)
        timerRef.current = setInterval(() => {
          setCountdown((prev) => {
            if (prev <= 1) {
              if (timerRef.current) {
                clearInterval(timerRef.current)
              }
              return 0
            }
            return prev - 1
          })
        }, 1000)
      }
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || '发送验证码失败'
      message.error(errorMsg)
    } finally {
      setSendingCode(false)
    }
  }, [phoneForm])

  const handlePhoneLogin = useCallback(
    async (values: { phone: string; code: string }) => {
      setLoading(true)
      setError(null)

      try {
        const response = await authApi.smsLogin(values.phone, values.code)

        if (response.data.success) {
          localStorage.setItem('auth_token', response.data.token)
          localStorage.setItem('agent_id', response.data.user.user_id)
          localStorage.setItem('user_info', JSON.stringify(response.data.user))

          message.success({
            content: response.data.is_new_user ? '注册成功，欢迎加入！' : '登录成功',
            icon: <CheckCircleOutlined className="text-emerald-400" />,
          })

          const redirectTo = searchParams.get('redirect') || '/dashboard'
          navigate(redirectTo)
        }
      } catch (err: any) {
        const errorMsg = err.response?.data?.detail || '登录失败'
        setError(errorMsg)
        message.error(errorMsg)
      } finally {
        setLoading(false)
      }
    },
    [navigate, searchParams]
  )

  // Password login (legacy)
  const handlePasswordLogin = useCallback(
    async (values: { username: string; password: string }) => {
      setLoading(true)
      setError(null)

      try {
        const response = await authApi.passwordLogin(values.username, values.password)

        if (response.data.access_token) {
          localStorage.setItem('auth_token', response.data.access_token)
          localStorage.setItem('agent_id', response.data.agent_id)

          message.success({
            content: '登录成功',
            icon: <CheckCircleOutlined className="text-emerald-400" />,
          })

          const redirectTo = searchParams.get('redirect') || '/dashboard'
          navigate(redirectTo)
        }
      } catch (err: any) {
        const errorMsg = err.response?.data?.detail || '用户名或密码错误'
        setError(errorMsg)
        message.error(errorMsg)
      } finally {
        setLoading(false)
      }
    },
    [navigate, searchParams]
  )

  // Tab items
  const tabItems = [
    {
      key: 'phone',
      label: (
        <span className="flex items-center gap-2">
          <MobileOutlined />
          短信登录
        </span>
      ),
      children: (
        <Form
          form={phoneForm}
          name="phoneLogin"
          onFinish={handlePhoneLogin}
          layout="vertical"
          className="space-y-4"
        >
          <Form.Item
            name="phone"
            rules={[
              { required: true, message: '请输入手机号' },
              { pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确' },
            ]}
          >
            <Input
              prefix={<MobileOutlined className="text-slate-500 mr-2" />}
              placeholder="手机号"
              size="large"
              maxLength={11}
              className="h-12 bg-slate-800/50 border-slate-700 text-white placeholder:text-slate-500 focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20"
              disabled={loading}
            />
          </Form.Item>

          <Form.Item
            name="code"
            rules={[
              { required: true, message: '请输入验证码' },
              { pattern: /^\d{6}$/, message: '验证码为6位数字' },
            ]}
          >
            <Input
              prefix={<MailOutlined className="text-slate-500 mr-2" />}
              placeholder="验证码"
              size="large"
              maxLength={6}
              className="h-12 bg-slate-800/50 border-slate-700 text-white placeholder:text-slate-500 focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20"
              disabled={loading}
              suffix={
                <Button
                  type="link"
                  size="small"
                  onClick={handleSendCode}
                  disabled={countdown > 0 || sendingCode}
                  className="text-cyan-400"
                >
                  {sendingCode ? (
                    <Spin size="small" />
                  ) : countdown > 0 ? (
                    `重新发送 (${countdown}s)`
                  ) : (
                    '发送验证码'
                  )}
                </Button>
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
              className="h-12 text-base font-medium bg-gradient-to-r from-cyan-500 to-purple-500 border-0 hover:opacity-90 hover:shadow-[0_0_20px_rgba(0,212,255,0.4)] transition-all duration-300"
            >
              {loading ? '登录中...' : '安全登录'}
            </Button>
          </Form.Item>
        </Form>
      ),
    },
    {
      key: 'password',
      label: (
        <span className="flex items-center gap-2">
          <LockOutlined />
          密码登录
        </span>
      ),
      children: (
        <Form
          form={passwordForm}
          name="passwordLogin"
          onFinish={handlePasswordLogin}
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

          {/* Demo Credentials */}
          <div className="text-center mt-4">
            <Text className="text-xs text-slate-500">
              默认账号: <span className="text-cyan-400">admin</span> /{' '}
              <span className="text-purple-400">admin123</span>
            </Text>
          </div>
        </Form>
      ),
    },
  ]

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
              虾有钳
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

          {/* Login Tabs */}
          <Tabs
            defaultActiveKey="phone"
            items={tabItems}
            className="login-tabs"
            onChange={() => setError(null)}
          />

          {/* Trust Indicators */}
          <div className="mt-6 pt-6 border-t border-slate-700/50">
            <div className="grid grid-cols-2 gap-3">
              <FeatureItem icon={<SecurityScanOutlined />} text="MCP 协议加密" />
              <FeatureItem icon={<LockOutlined />} text="端到端安全" />
            </div>
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