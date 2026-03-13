import { Modal, Button, Typography } from 'antd'
import { LockOutlined } from '@ant-design/icons'

const { Text, Title } = Typography

interface LoginPromptProps {
  open: boolean
  onClose: () => void
}

const LoginPrompt = ({ open, onClose }: LoginPromptProps) => {
  const handleLogin = () => {
    window.location.href = '/login'
  }

  return (
    <Modal
      open={open}
      onCancel={onClose}
      footer={null}
      centered
      width={360}
      className="login-prompt-modal"
    >
      <div className="text-center py-6">
        <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gradient-to-br from-cyan-500/20 to-purple-500/20 flex items-center justify-center">
          <LockOutlined className="text-3xl text-cyan-400" />
        </div>

        <Title level={4} className="text-white mb-2">
          登录以继续操作
        </Title>

        <Text className="text-slate-400 block mb-6">
          收藏和分享功能需要登录后才能使用
        </Text>

        <Button
          type="primary"
          size="large"
          block
          onClick={handleLogin}
          className="bg-gradient-to-r from-cyan-500 to-purple-500 border-0 mb-4"
        >
          登录 / 注册
        </Button>

        <Button
          type="text"
          onClick={onClose}
          className="text-slate-400 hover:text-white"
        >
          继续浏览广场 →
        </Button>
      </div>
    </Modal>
  )
}

export default LoginPrompt