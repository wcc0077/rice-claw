import { memo } from 'react'
import { Pie } from '@ant-design/plots'

interface JobStatusChartProps {
  data: Record<string, number>
}

/**
 * JobStatusChart - Dark mode pie chart for job distribution
 */
const JobStatusChart = memo(({ data }: JobStatusChartProps) => {
  const statusColors = {
    OPEN: '#34d399',
    ACTIVE: '#00d4ff',
    REVIEW: '#fbbf24',
    CLOSED: '#64748b',
  }

  const statusLabels: Record<string, string> = {
    OPEN: '开放中',
    ACTIVE: '进行中',
    REVIEW: '审核中',
    CLOSED: '已关闭',
  }

  const config = {
    angleField: 'value',
    colorField: 'type',
    radius: 0.8,
    color: ({ type }: { type: string }) => statusColors[type as keyof typeof statusColors] || '#94a3b8',
    label: {
      text: (d: { type: string; value: number }) => `${d.type}\n${d.value}个`,
      style: {
        fontWeight: 'bold',
        fill: '#f8fafc',
        fontSize: 12,
      },
    },
    legend: {
      position: 'bottom',
      itemName: {
        style: {
          fill: '#e2e8f0',
          fontSize: 12,
        },
        formatter: (text: string) => statusLabels[text] || text,
      },
      itemValue: {
        style: {
          fill: '#94a3b8',
          fontSize: 12,
        },
      },
    },
    interactions: [
      { type: 'element-selected' },
      { type: 'element-active' },
    ],
    tooltip: {
      title: (d: { type: string; value: number }) => statusLabels[d.type] || d.type,
      customItems: (items: any[]) => {
        return items.map((item) => ({
          ...item,
          name: statusLabels[item.name] || item.name,
        }))
      },
    },
  }

  const chartData = Object.entries(data).map(([type, value]) => ({
    type,
    value,
  }))

  if (chartData.length === 0 || chartData.every((d) => d.value === 0)) {
    return (
      <div className="h-[250px] flex items-center justify-center">
        <div className="text-center">
          <div className="text-slate-500 text-sm">暂无数据</div>
          <div className="text-slate-600 text-xs mt-1">等待任务创建</div>
        </div>
      </div>
    )
  }

  return (
    <div className="h-[250px]">
      <Pie {...config} data={chartData} />
    </div>
  )
})

JobStatusChart.displayName = 'JobStatusChart'

export default JobStatusChart
