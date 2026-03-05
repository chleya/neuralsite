import React from 'react';
import ReactECharts from 'echarts-for-react';

interface ProgressChartProps {
  data?: {
    name: string;
    value: number;
  }[];
  title?: string;
}

const defaultData = [
  { name: '已完成', value: 35 },
  { name: '进行中', value: 28 },
  { name: '未开始', value: 15 },
  { name: '延期', value: 8 },
];

export default function ProgressChart({ 
  data = defaultData, 
  title = '施工进度' 
}: ProgressChartProps) {
  const option = {
    title: {
      text: title,
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'bold',
      },
    },
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)',
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      top: 'middle',
    },
    color: ['#22c55e', '#3b82f6', '#94a3b8', '#ef4444'],
    series: [
      {
        name: '进度',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2,
        },
        label: {
          show: true,
          formatter: '{b}: {d}%',
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 14,
            fontWeight: 'bold',
          },
        },
        data: data,
      },
    ],
  };

  return (
    <div className="chart-container">
      <ReactECharts 
        option={option} 
        style={{ height: '300px', width: '100%' }}
        opts={{ renderer: 'svg' }}
      />
    </div>
  );
}
