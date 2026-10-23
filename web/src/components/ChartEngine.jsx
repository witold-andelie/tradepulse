import ReactEChartsCore from 'echarts-for-react/lib/core';
import * as echarts from 'echarts/core';
import { BarChart, LineChart, ScatterChart, TreemapChart } from 'echarts/charts';
import { AriaComponent, GridComponent, TooltipComponent, LegendComponent, VisualMapComponent, MarkAreaComponent, MarkLineComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
echarts.use([BarChart, LineChart, ScatterChart, TreemapChart, AriaComponent, GridComponent, TooltipComponent, LegendComponent, VisualMapComponent, MarkAreaComponent, MarkLineComponent, CanvasRenderer]);

export default function ChartEngine({ option, label, height = 280, onEvents }) {
  return <div role="img" aria-label={label} className="chart"><ReactEChartsCore echarts={echarts} option={{
    animation: false, color: ['#166b65', '#bd6c36', '#526d9e'], textStyle: { fontFamily: 'system-ui, sans-serif', color: '#526273' },
    tooltip: { trigger: 'axis', confine: true, renderMode: 'richText' },
    grid: { left: 52, right: 22, top: 36, bottom: 44, containLabel: true },
    aria: { enabled: true }, ...option,
  }} style={{ height, width: '100%' }} notMerge onEvents={onEvents} /></div>;
}
