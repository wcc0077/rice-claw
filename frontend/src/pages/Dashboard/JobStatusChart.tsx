import { Card } from 'antd'
import { Pie } from '@ant-design/plots'

const JobStatusChart = ({ data }: { data: Record<string, number> }) => {
  const config = {
    angleField: 'value',
    colorField: 'type',
    radius: 0.8,
    label: {
      text: 'type',
      style: {
        fontWeight: 'bold',
      },
    },
    interactions: [
      {
        type: 'element-selected',
      },
      {
        type: 'element-active',
      },
    ],
    legend: {
      position: 'bottom',
    },
  }

  const chartData = Object.entries(data).map(([type, value]) => ({
    type,
    value,
  }))

  return (
    <Card title="任务状态分布" className="h-full">
      <div className="h-[300px]">
        <Pie {...config} data={chartData} />
      </div>
    </Card>
  )
}

export default JobStatusChart