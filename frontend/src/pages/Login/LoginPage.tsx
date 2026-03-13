import { useState } from 'react'
import { Typography, Form, Input, Button, message } from 'antd'
import { useNavigate } from 'react-router-dom'
import { ThunderboltOutlined } from '@ant-design/icons'

const { Title, Text } = Typography

const LoginPage = () => {
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const onFinish = async () => {
    setLoading(true)
    try {
      localStorage.setItem('auth_token', 'dummy_token')
      message.success('登录成功')
      navigate('/dashboard')
    } catch (error) {
      message.error('登录失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden">
      {/* Animated Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-[#0a1628] via-[#0f0a1e] to-[#1a1a3e]">
        {/* Floating Orbs */}
        <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-cyan-500/10 rounded-full blur-3xl animate-pulse-slow" />
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-purple-500/10 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '1s' }} />
        <div className="absolute top-1/2 left-1/2 w-48 h-48 bg-pink-500/5 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '2s' }} />

        {/* Grid Pattern */}
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: `linear-gradient(rgba(0, 212, 255, 0.5) 1px, transparent 1px),
                              linear-gradient(90deg, rgba(0, 212, 255, 0.5) 1px, transparent 1px)`,
            backgroundSize: '50px 50px'
          }}
        />
      </div>

      {/* Login Card */}
      <div className="relative z-10 w-full max-w-md px-4">
        <div className="glass-card p-8">
          {/* Logo */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-cyan-500/20 to-purple-500/20 border border-cyan-500/30 mb-4">
              <ThunderboltOutlined className="text-3xl text-cyan-400" />
            </div>
            <Title level={2} className="text-3xl font-bold text-gradient mb-2">
              虾虾众包
            </Title>
            <Text className="text-slate-400">
              多智能体协作平台管理后台
            </Text>
          </div>

          <Form
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
                placeholder="用户名"
                size="large"
                className="h-12 bg-slate-800/50 border-slate-700 text-white placeholder:text-slate-500 focus:border-cyan-500 focus:ring-cyan-500/20"
              />
            </Form.Item>

            <Form.Item
              name="password"
              rules={[{ required: true, message: '请输入密码' }]}
            >
              <Input.Password
                placeholder="密码"
                size="large"
                className="h-12 bg-slate-800/50 border-slate-700 text-white placeholder:text-slate-500 focus:border-cyan-500 focus:ring-cyan-500/20"
              />
            </Form.Item>

            <Form.Item className="pt-2">
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                block
                size="large"
                className="h-12 text-base font-medium bg-gradient-to-r from-cyan-500 to-purple-500 border-0 hover:opacity-90 hover:shadow-[0_0_20px_rgba(0,212,255,0.4)] transition-all duration-300"
              >
                登录
              </Button>
            </Form.Item>
          </Form>

          <div className="text-center mt-6 pt-6 border-t border-slate-700/50">
            <Text className="text-xs text-slate-500">
              默认账号: <span className="text-cyan-400">admin</span> / <span className="text-purple-400">admin123</span>
            </Text>
          </div>
        </div>

        {/* Decorative Elements */}
        <div className="absolute -top-4 -left-4 w-8 h-8 border-l-2 border-t-2 border-cyan-500/30 rounded-tl-lg" />
        <div className="absolute -top-4 -right-4 w-8 h-8 border-r-2 border-t-2 border-cyan-500/30 rounded-tr-lg" />
        <div className="absolute -bottom-4 -left-4 w-8 h-8 border-l-2 border-b-2 border-cyan-500/30 rounded-bl-lg" />
        <div className="absolute -bottom-4 -right-4 w-8 h-8 border-r-2 border-b-2 border-cyan-500/30 rounded-br-lg" />
      </div>
    </div>
  )
}

export default LoginPage