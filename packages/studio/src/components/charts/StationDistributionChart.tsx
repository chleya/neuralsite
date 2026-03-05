import React from 'react';
import ReactECharts from 'echarts-for-react';

interface StationDistributionChartProps {
  data?: {
    station: string;
    count: number;
  }[];
  title?: string;
}

const defaultData = [
  { station: 'K0+000', count: 12 },
  { station: 'K0+100', count: 8 },
  { station: 'K0+200', count: 15 },
  { station: 'K0+300', count: 6 },
  { station: 'K0+400', count: 10 },
  { station: 'K0+500', count: 14 },
  { station: 'K0+600', count: 9 },
  { station: 'K0+700', count: 11 },
];

export default function StationDistributionChart({ 
  data = defaultData, 
  title = '桩号分布' 
}: StationDistributionChartProps) {
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
      axisPointer: {
        type: 'shadow',
      },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: data.map(item => item.station),
      axisLabel: {
        rotate: 45,
        fontSize: 11,
      },
    },
    yAxis: {
      type: 'value',
      name: '数量',
    },
    series: [
      {
        name: '桩点数',
        type: 'bar',
        barWidth: '60%',
        data: data.map(item => ({
          value: item.count,
          itemStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: '#3b82f6' },
                { offset: 1, color: '#60a5fa' },
              ],
            },
          },
        })),
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
