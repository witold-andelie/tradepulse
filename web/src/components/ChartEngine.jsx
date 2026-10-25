import ReactEChartsCore from 'echarts-for-react/lib/core';
import * as echarts from 'echarts/core';
import { BarChart, LineChart, ScatterChart, TreemapChart } from 'echarts/charts';
import { AriaComponent, GridComponent, TooltipComponent, LegendComponent, VisualMapComponent, MarkAreaComponent, MarkLineComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import { accessibleChartOption } from '../lib/a11y.js';
echarts.use([BarChart, LineChart, ScatterChart, TreemapChart, AriaComponent, GridComponent, TooltipComponent, LegendComponent, VisualMapComponent, MarkAreaComponent, MarkLineComponent, CanvasRenderer]);

export default function ChartEngine({ option, height = 280, onEvents }) {
  const readableAxes = (axes) => Array.isArray(axes) ? axes.map(readableAxes) : axes && ({ ...axes, axisLabel: { hideOverlap: true, ...axes.axisLabel, fontSize: 13, color: '#526078' }, nameTextStyle: { ...axes.nameTextStyle, fontSize: 13, color: '#526078' } });
  return <div dir="ltr" aria-hidden="true" className="chart chart-visual"><ReactEChartsCore echarts={echarts} option={accessibleChartOption({
    animation: false, color: ['#5549e8', '#954b26', '#0b7068'], textStyle: { fontFamily: 'system-ui, sans-serif', color: '#526078', fontSize: 13 },
    tooltip: { trigger: 'axis', confine: true, renderMode: 'richText' },
    grid: { left: 52, right: 22, top: 36, bottom: 44, containLabel: true },
    aria: { enabled: true }, ...option, ...(option.legend ? { legend: { ...option.legend, textStyle: { ...option.legend.textStyle, fontSize: 13, color: '#526078' } } } : {}), series: option.series?.map((series) => ({ ...series, animation: false, animationDuration: 0, animationDurationUpdate: 0 })), ...(option.xAxis ? { xAxis: readableAxes(option.xAxis) } : {}), ...(option.yAxis ? { yAxis: readableAxes(option.yAxis) } : {}),
  }, { reducedMotion: true })} style={{ height, width: '100%' }} notMerge onEvents={onEvents} /></div>;
}
