import { Card, Statistic } from 'antd'

const StatCard = ({ title, value, suffix, trend, color = 'blue' }: any) => {
  return (
    <Card size="small" className="hover:shadow-md transition-shadow">
      <Statistic
        title={title}
        value={value}
        suffix={suffix}
        valueStyle={{ color: color === 'green' ? '#52c41a' : color === 'red' ? '#f5222d' : '#1890ff' }}
      />
      {trend && (
        <div className="text-xs text-gray-500 mt-1">
          {trend} vs yesterday
        </div>
      )}
    </Card>
  )
}

export default StatCard
