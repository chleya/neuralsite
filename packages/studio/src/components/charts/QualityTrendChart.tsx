import React from 'react';
import ReactECharts from 'echarts-for-react';

interface QualityTrendChartProps {
  data?: {
    date: string;
    passRate: number;
    issueCount: number;
  }[];
  title?: string;
}

const defaultData = [
  { date: '01-01', passRate: 92, issueCount: 5 },
  { date: '01-05', passRate: 88, issueCount: 8 },
  { date: '01-10', passRate: 95, issueCount: 3 },
  { date: '01-15', passRate: 91, issueCount: 6 },
  { date: '01-20', passRate: 97, issueCount: 2 },
  { date: '01-25', passRate: 94, issueCount: 4 },
  { date: '01-30', passRate: 96, issueCount: 3 },
];

export default function QualityTrendChart({ 
  data = defaultData, 
  title = '质量趋势' 
}: QualityTrendChartProps) {
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
      trigger: 'axis',
    },
    legend: {
      data: ['合格率', '问题数'],
      top: 30,
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: data.map(item => item.date),
      boundaryGap: false,
    },
    yAxis: [
      {
        type: 'value',
        name: '合格率(%)',
        min: 80,
        max: 100,
        axisLabel: {
          formatter: '{value}%',
        },
      },
      {
        type: 'value',
        name: '问题数',
        min: 0,
        position: 'right',
      },
    ],
    series: [
      {
        name: '合格率',
        type: 'line',
        smooth: true,
        data: data.map(item => item.passRate),
        lineStyle: {
          color: '#22c55e',
          width: 3,
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(34, 197, 94, 0.3)' },
              { offset: 1, color: 'rgba(34, 197, 94, 0.05)' },
            ],
          },
        },
        itemStyle: {
          color: '#22c55e',
        },
      },
      {
        name: '问题数',
        type: 'line',
        yAxisIndex: 1,
        smooth: true,
        data: data.map(item => item.issueCount),
        lineStyle: {
          color: '#ef4444',
          width: 2,
          type: 'dashed',
        },
        itemStyle: {
          color: '#ef4444',
        },
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
