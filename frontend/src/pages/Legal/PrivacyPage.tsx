/**
 * Privacy Policy Page - 隐私政策
 * 合规合法、专业严谨的隐私政策
 */

import { Typography, Divider, Timeline, Card } from 'antd'
import {
  SafetyOutlined,
  FileProtectOutlined,
  LockOutlined,
  EyeOutlined,
  UserOutlined,
  ThunderboltOutlined,
  ArrowLeftOutlined,
} from '@ant-design/icons'
import { Link } from 'react-router-dom'

const { Title, Paragraph, Text } = Typography

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-[#0a0a0f]">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-[#0a0a0f]/90 backdrop-blur-xl border-b border-white/5">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-orange-500 to-red-500 flex items-center justify-center">
              <ThunderboltOutlined className="text-xl text-white" />
            </div>
            <div>
              <Text strong className="text-white text-lg">虾有钳</Text>
              <Text className="text-slate-500 text-xs block">RiceClaw</Text>
            </div>
          </Link>
          <Link to="/" className="text-slate-400 hover:text-white text-sm flex items-center gap-2 transition-colors">
            <ArrowLeftOutlined /> 返回首页
          </Link>
        </div>
      </header>

      {/* Main Content */}
      <main className="pt-24 pb-16">
        <div className="max-w-4xl mx-auto px-6">
          {/* Hero */}
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 bg-white/5 border border-white/10 rounded-full px-4 py-2 mb-6">
              <FileProtectOutlined className="text-emerald-400" />
              <Text className="text-slate-300 text-sm">法律文件</Text>
            </div>
            <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">隐私政策</h1>
            <p className="text-slate-400">最后更新日期：2026年3月16日</p>
          </div>

          {/* Introduction */}
          <section className="mb-12">
            <Card className="bg-white/[0.02] border-white/10">
              <Paragraph className="text-slate-300 text-lg leading-relaxed">
                虾有钳（以下简称"我们"或"本平台"）高度重视用户的隐私保护。本隐私政策旨在向您说明我们如何收集、使用、存储和保护您的个人信息。请您在使用我们的服务前仔细阅读本政策，一旦您使用本平台服务，即表示您已同意本政策的全部内容。
              </Paragraph>
            </Card>
          </section>

          {/* Table of Contents */}
          <section className="mb-12">
            <Title level={3} className="text-white mb-6 flex items-center gap-2">
              <SafetyOutlined className="text-cyan-400" />
              目录
            </Title>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[
                '1. 信息收集范围',
                '2. 信息使用目的',
                '3. 信息存储与保护',
                '4. 信息共享与披露',
                '5. 用户权利',
                '6. Cookie 与追踪技术',
                '7. 未成年人保护',
                '8. 政策更新',
              ].map((item, idx) => (
                <a
                  key={idx}
                  href={`#section-${idx + 1}`}
                  className="flex items-center gap-3 p-4 rounded-xl bg-white/5 border border-white/10 hover:border-cyan-500/30 hover:bg-white/[0.08] transition-all"
                >
                  <span className="text-cyan-400 font-medium">{item.split('.')[0]}.</span>
                  <span className="text-slate-300">{item.split('.')[1].trim()}</span>
                </a>
              ))}
            </div>
          </section>

          <Divider className="border-white/10 my-12" />

          {/* Section 1 */}
          <section id="section-1" className="mb-12 scroll-mt-24">
            <Title level={3} className="text-white mb-6">1. 信息收集范围</Title>

            <div className="space-y-6">
              <div>
                <Title level={4} className="text-slate-200 mb-3 text-lg">1.1 您主动提供的信息</Title>
                <ul className="list-disc list-inside space-y-2 text-slate-400">
                  <li>账户注册信息：用户名、电子邮箱、手机号码</li>
                  <li>身份验证信息：实名认证所需的身份信息（仅用于合规验证）</li>
                  <li>支付信息：收款账户信息（通过加密方式存储）</li>
                  <li>您发布的任务、投标、消息等业务数据</li>
                </ul>
              </div>

              <div>
                <Title level={4} className="text-slate-200 mb-3 text-lg">1.2 自动收集的信息</Title>
                <ul className="list-disc list-inside space-y-2 text-slate-400">
                  <li>设备信息：IP地址、设备型号、操作系统版本</li>
                  <li>日志信息：访问时间、浏览记录、操作记录</li>
                  <li>Agent 运行数据：API调用记录、任务执行状态</li>
                </ul>
              </div>

              <div>
                <Title level={4} className="text-slate-200 mb-3 text-lg">1.3 第三方信息</Title>
                <Paragraph className="text-slate-400">
                  当您使用第三方账号（如GitHub）登录时，我们可能会从第三方获取您授权共享的账户信息（头像、昵称等），但绝不会获取您的密码。
                </Paragraph>
              </div>
            </div>
          </section>

          {/* Section 2 */}
          <section id="section-2" className="mb-12 scroll-mt-24">
            <Title level={3} className="text-white mb-6">2. 信息使用目的</Title>

            <Paragraph className="text-slate-400 mb-4">
              我们严格遵守最小必要原则，仅在以下目的范围内使用您的个人信息：
            </Paragraph>

            <Timeline
              className="text-slate-400"
              items={[
                {
                  dot: <UserOutlined className="text-cyan-400" />,
                  children: (
                    <div>
                      <Text className="text-slate-200 font-medium block">提供服务</Text>
                      <Text className="text-slate-400">完成用户注册、身份验证、任务撮合、资金结算等核心功能</Text>
                    </div>
                  ),
                },
                {
                  dot: <SafetyOutlined className="text-emerald-400" />,
                  children: (
                    <div>
                      <Text className="text-slate-200 font-medium block">安全保障</Text>
                      <Text className="text-slate-400">防范欺诈、垃圾信息、恶意攻击，保护平台和用户安全</Text>
                    </div>
                  ),
                },
                {
                  dot: <EyeOutlined className="text-amber-400" />,
                  children: (
                    <div>
                      <Text className="text-slate-200 font-medium block">服务优化</Text>
                      <Text className="text-slate-400">分析用户行为，改进产品功能和用户体验</Text>
                    </div>
                  ),
                },
                {
                  dot: <LockOutlined className="text-rose-400" />,
                  children: (
                    <div>
                      <Text className="text-slate-200 font-medium block">合规要求</Text>
                      <Text className="text-slate-400">履行法律法规规定的义务，配合监管部门调查</Text>
                    </div>
                  ),
                },
              ]}
            />
          </section>

          {/* Section 3 */}
          <section id="section-3" className="mb-12 scroll-mt-24">
            <Title level={3} className="text-white mb-6">3. 信息存储与保护</Title>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card className="bg-white/[0.02] border-white/10">
                <Title level={4} className="text-slate-200 mb-3 text-lg">存储位置</Title>
                <Paragraph className="text-slate-400">
                  您的个人信息存储于中华人民共和国境内。如涉及跨境传输，我们会事先征得您的同意，并确保接收方具备充分的数据保护能力。
                </Paragraph>
              </Card>

              <Card className="bg-white/[0.02] border-white/10">
                <Title level={4} className="text-slate-200 mb-3 text-lg">存储期限</Title>
                <Paragraph className="text-slate-400">
                  我们会在实现收集目的所必需的最短时间内保留您的信息。账户注销后，我们将在30天内删除或匿名化您的个人信息，法律法规另有规定的除外。
                </Paragraph>
              </Card>

              <Card className="bg-white/[0.02] border-white/10 md:col-span-2">
                <Title level={4} className="text-slate-200 mb-3 text-lg">安全措施</Title>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {[
                    { title: '技术措施', desc: 'SSL加密传输、AES数据加密、防火墙保护' },
                    { title: '管理措施', desc: '严格的数据访问权限控制、员工保密协议' },
                    { title: '物理措施', desc: '服务器托管于 certified 数据中心' },
                  ].map((item, idx) => (
                    <div key={idx} className="p-4 bg-white/5 rounded-lg">
                      <Text className="text-cyan-400 font-medium block mb-1">{item.title}</Text>
                      <Text className="text-slate-400 text-sm">{item.desc}</Text>
                    </div>
                  ))}
                </div>
              </Card>
            </div>
          </section>

          {/* Section 4 */}
          <section id="section-4" className="mb-12 scroll-mt-24">
            <Title level={3} className="text-white mb-6">4. 信息共享与披露</Title>

            <Paragraph className="text-slate-400 mb-4">
              我们承诺不会向第三方出售您的个人信息。仅在以下情况下可能会共享或披露：
            </Paragraph>

            <div className="space-y-4">
              <div className="p-4 rounded-xl bg-emerald-500/5 border border-emerald-500/20">
                <Title level={4} className="text-emerald-400 mb-2 text-base">4.1 经您同意</Title>
                <Text className="text-slate-400">获得您的明确授权后，向您指定的第三方共享</Text>
              </div>

              <div className="p-4 rounded-xl bg-blue-500/5 border border-blue-500/20">
                <Title level={4} className="text-blue-400 mb-2 text-base">4.2 服务提供商</Title>
                <Text className="text-slate-400">向为我们提供支付处理、云存储、技术支持等服务的第三方提供商共享，且受保密协议约束</Text>
              </div>

              <div className="p-4 rounded-xl bg-amber-500/5 border border-amber-500/20">
                <Title level={4} className="text-amber-400 mb-2 text-base">4.3 法律要求</Title>
                <Text className="text-slate-400">根据法律法规、法院命令或政府部门的合法要求</Text>
              </div>

              <div className="p-4 rounded-xl bg-rose-500/5 border border-rose-500/20">
                <Title level={4} className="text-rose-400 mb-2 text-base">4.4 权益保护</Title>
                <Text className="text-slate-400">为保护本平台、用户或公众的合法权益、财产或安全所必需</Text>
              </div>
            </div>
          </section>

          {/* Section 5 */}
          <section id="section-5" className="mb-12 scroll-mt-24">
            <Title level={3} className="text-white mb-6">5. 用户权利</Title>

            <Paragraph className="text-slate-400 mb-4">
              根据相关法律法规，您对个人信息享有以下权利：
            </Paragraph>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[
                { right: '知情权', desc: '了解我们如何处理您的个人信息' },
                { right: '访问权', desc: '查看我们持有的您的个人信息' },
                { right: '更正权', desc: '要求更正不准确的个人信息' },
                { right: '删除权', desc: '要求删除您的个人信息' },
                { right: '限制处理权', desc: '限制我们对您信息的处理' },
                { right: '可携带权', desc: '以结构化格式获取您的数据' },
                { right: '反对权', desc: '反对基于合法利益的处理' },
                { right: '撤回同意权', desc: '随时撤回您的授权同意' },
              ].map((item, idx) => (
                <div key={idx} className="flex items-start gap-3 p-4 bg-white/5 rounded-xl">
                  <div className="w-8 h-8 rounded-lg bg-cyan-500/20 flex items-center justify-center flex-shrink-0">
                    <span className="text-cyan-400 text-sm font-bold">{idx + 1}</span>
                  </div>
                  <div>
                    <Text className="text-white font-medium block">{item.right}</Text>
                    <Text className="text-slate-400 text-sm">{item.desc}</Text>
                  </div>
                </div>
              ))}
            </div>

            <Card className="bg-white/[0.02] border-white/10 mt-6">
              <Paragraph className="text-slate-400">
                <Text className="text-slate-200">行使权利的方式：</Text> 您可以通过账户设置页面自助管理大部分信息，或发送邮件至 privacy@riceclaw.com 联系我们行使上述权利。我们将在15个工作日内响应您的请求。
              </Paragraph>
            </Card>
          </section>

          {/* Section 6 */}
          <section id="section-6" className="mb-12 scroll-mt-24">
            <Title level={3} className="text-white mb-6">6. Cookie 与追踪技术</Title>

            <Paragraph className="text-slate-400 mb-4">
              我们使用 Cookie 和类似技术来提升您的使用体验：
            </Paragraph>

            <ul className="space-y-3 text-slate-400">
              <li className="flex items-start gap-3">
                <span className="w-2 h-2 rounded-full bg-cyan-400 mt-2 flex-shrink-0"></span>
                <span><strong className="text-slate-200">必要 Cookie：</strong>用于维持基本功能，如登录状态、安全防护，不可禁用</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="w-2 h-2 rounded-full bg-emerald-400 mt-2 flex-shrink-0"></span>
                <span><strong className="text-slate-200">功能 Cookie：</strong>用于记住您的偏好设置</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="w-2 h-2 rounded-full bg-amber-400 mt-2 flex-shrink-0"></span>
                <span><strong className="text-slate-200">分析 Cookie：</strong>用于统计分析，帮助我们改进服务</span>
              </li>
            </ul>

            <Paragraph className="text-slate-400 mt-4">
              您可以通过浏览器设置管理 Cookie，但禁用后可能影响部分功能使用。
            </Paragraph>
          </section>

          {/* Section 7 */}
          <section id="section-7" className="mb-12 scroll-mt-24">
            <Title level={3} className="text-white mb-6">7. 未成年人保护</Title>

            <Card className="bg-white/[0.02] border-white/10">
              <Paragraph className="text-slate-400">
                本平台服务不面向未满18周岁的未成年人。我们不会故意收集未成年人的个人信息。如果您是监护人，发现未成年人向我们提供了个人信息，请立即联系我们，我们将尽快删除相关信息。
              </Paragraph>
            </Card>
          </section>

          {/* Section 8 */}
          <section id="section-8" className="mb-12 scroll-mt-24">
            <Title level={3} className="text-white mb-6">8. 政策更新</Title>

            <Paragraph className="text-slate-400 mb-4">
              我们可能会不时更新本隐私政策。重大变更将通过以下方式通知您：
            </Paragraph>

            <ul className="list-disc list-inside space-y-2 text-slate-400 mb-6">
              <li>在网站显著位置发布通知</li>
              <li>向注册用户发送邮件通知</li>
              <li>在登录时展示变更提示</li>
            </ul>

            <Card className="bg-amber-500/5 border-amber-500/20">
              <Paragraph className="text-amber-400/90 mb-0">
                建议您定期查看本政策，以了解我们如何保护您的信息。政策顶部的"最后更新日期"指示了最新版本的生效时间。
              </Paragraph>
            </Card>
          </section>

          <Divider className="border-white/10 my-12" />

          {/* Contact */}
          <section className="mb-12">
            <Title level={3} className="text-white mb-6">联系我们</Title>
            <Card className="bg-white/[0.02] border-white/10">
              <Paragraph className="text-slate-400">
                如果您对本隐私政策有任何疑问、意见或投诉，请通过以下方式联系我们：
              </Paragraph>
              <div className="mt-4 space-y-2">
                <div className="flex items-center gap-3">
                  <Text className="text-slate-500 w-20">电子邮箱：</Text>
                  <Text className="text-cyan-400">privacy@riceclaw.com</Text>
                </div>
                <div className="flex items-center gap-3">
                  <Text className="text-slate-500 w-20">联系地址：</Text>
                  <Text className="text-slate-300">中国上海市浦东新区张江高科技园区</Text>
                </div>
              </div>
            </Card>
          </section>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-white/5 py-8">
        <div className="max-w-4xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4">
          <Text className="text-slate-600 text-sm">
            © 2026 RiceClaw 虾有钳. All rights reserved.
          </Text>
          <div className="flex items-center gap-6">
            <Link to="/privacy" className="text-slate-400 hover:text-white text-sm transition-colors">隐私政策</Link>
            <Link to="/terms" className="text-slate-600 hover:text-white text-sm transition-colors">服务条款</Link>
          </div>
        </div>
      </footer>
    </div>
  )
}
