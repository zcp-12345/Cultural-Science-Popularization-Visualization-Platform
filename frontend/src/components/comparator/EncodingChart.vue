<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { echarts, type EChartsInstance } from '@/lib/echarts'
import type { CharDescription } from '@/types/encoding'

const props = defineProps<{ description: CharDescription }>()

const chartEl = ref<HTMLDivElement | null>(null)
let chart: EChartsInstance | null = null
let observer: ResizeObserver | null = null

const reduceMotion =
  typeof window !== 'undefined' && window.matchMedia
    ? window.matchMedia('(prefers-reduced-motion: reduce)').matches
    : false

interface Row {
  label: string
  bytes: number[] | null
  note: string
}

const rows = computed<Row[]>(() => {
  const description = props.description
  return [
    { label: 'UTF-8', bytes: description.utf8.bytes, note: '互联网通用变长编码' },
    { label: 'UTF-16', bytes: description.utf16.bytesLE, note: '按 UTF-16 码元存储（小端）' },
    {
      label: 'GB2312',
      bytes: description.legacy.gb2312.bytes,
      note: description.legacy.gb2312.note ?? '1980 年国标，收录 6763 个汉字',
    },
    {
      label: 'GBK',
      bytes: description.legacy.gbk.bytes,
      note: description.legacy.gbk.note ?? '1995 年扩展，收录 21003 个汉字',
    },
    {
      label: 'Big5',
      bytes: description.legacy.big5.bytes,
      note: description.legacy.big5.note ?? '繁体中文常用字符集',
    },
  ]
})

const ariaSummary = computed(() =>
  rows.value
    .map((row) => `${row.label}：${row.bytes ? `${row.bytes.length} 字节` : '不支持该字符'}`)
    .join('；'),
)

function hexOf(bytes: number[]): string {
  return bytes.map((byte) => byte.toString(16).toUpperCase().padStart(2, '0')).join(' ')
}

function render() {
  if (!chart) return

  const list = rows.value
  const option: any = {
    animation: !reduceMotion,
    animationDuration: 520,
    animationEasing: 'cubicOut',
    grid: { left: 6, right: 64, top: 8, bottom: 6, containLabel: true },
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(8, 13, 24, 0.96)',
      borderColor: 'rgba(0, 240, 255, 0.3)',
      borderWidth: 1,
      padding: [8, 12],
      textStyle: { color: '#e9f2fb', fontSize: 12 },
      formatter: (params: any) => {
        const row = list[params.dataIndex]
        if (!row) return ''
        if (!row.bytes) {
          return `<b>${row.label}</b><br/><span style="color:#8b93a7">不支持该字符</span><br/><span style="color:#8b93a7;font-size:11px">${row.note}</span>`
        }
        return `<b>${row.label}</b><br/>${row.bytes.length} 字节 · <span style="font-family:monospace;color:#00ff88">${hexOf(row.bytes)}</span><br/><span style="color:#8b93a7;font-size:11px">${row.note}</span>`
      },
    },
    xAxis: {
      type: 'value',
      minInterval: 1,
      axisLabel: { color: '#8b93a7', fontSize: 11, formatter: '{value} B' },
      splitLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.06)' } },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'category',
      data: list.map((row) => row.label),
      inverse: true,
      axisLabel: {
        color: '#c3c9d4',
        fontSize: 12,
        fontFamily: "'Cascadia Code', Consolas, monospace",
      },
      axisLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.12)' } },
      axisTick: { show: false },
    },
    series: [
      {
        type: 'bar',
        barWidth: 16,
        showBackground: true,
        backgroundStyle: {
          color: 'rgba(255, 255, 255, 0.025)',
          borderRadius: [0, 4, 4, 0],
        },
        data: list.map((row) => ({
          value: row.bytes ? row.bytes.length : 0,
          itemStyle: {
            color: row.bytes ? '#00f0ff' : 'rgba(255, 255, 255, 0.05)',
            borderRadius: [0, 4, 4, 0],
          },
        })),
        label: {
          show: true,
          position: 'right',
          distance: 8,
          color: '#c3c9d4',
          fontSize: 11,
          formatter: (params: any) => (params.value > 0 ? `${params.value} B` : '不支持'),
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 16,
            shadowColor: 'rgba(0, 240, 255, 0.45)',
          },
        },
      },
    ],
  }

  chart.setOption(option, true)
}

onMounted(() => {
  if (!chartEl.value) return
  chart = echarts.init(chartEl.value)
  render()
  observer = new ResizeObserver(() => chart?.resize())
  observer.observe(chartEl.value)
})

watch(() => props.description, render)

onBeforeUnmount(() => {
  observer?.disconnect()
  chart?.dispose()
  chart = null
})
</script>

<template>
  <div class="chart">
    <header class="chart__head">
      <h3>字节开销对比</h3>
      <span class="chart__unit">单位：字节</span>
    </header>
    <div ref="chartEl" class="chart__canvas" role="img" :aria-label="ariaSummary"></div>
  </div>
</template>

<style scoped>
.chart {
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.chart__head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 4px;
}

.chart__head h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: var(--c-text);
}

.chart__unit {
  font-size: 11px;
  color: var(--c-text-faint);
}

.chart__canvas {
  width: 100%;
  height: 196px;
}
</style>
