import { useState } from 'react'
import { Card, Typography, Form, Input, Button, message } from 'antd'
import { useNavigate } from 'react-router-dom'

const { Title } = Typography

const LoginPage = () => {
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const onFinish = async () => {
    setLoading(true)
    try {
      // Placeholder login
      // In real app, would call auth API
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
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <Card className="w-full max-w-md shadow-lg">
        <div className="text-center mb-6">
          <Title level={2} className="text-blue-600">虾虾众包管理后台</Title>
          <Typography.Text type="secondary">请输入管理员账号登录</Typography.Text>
        </div>

        <Form
          name="login"
          initialValues={{ remember: true }}
          onFinish={onFinish}
          layout="vertical"
        >
          <Form.Item
            name="username"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input placeholder="用户名" size="large" />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password placeholder="密码" size="large" />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
              size="large"
            >
              登录
            </Button>
          </Form.Item>
        </Form>

        <div className="text-center mt-4">
          <Typography.Text type="secondary" className="text-sm">
            默认账号: admin / admin123
          </Typography.Text>
        </div>
      </Card>
    </div>
  )
}

export default LoginPage
