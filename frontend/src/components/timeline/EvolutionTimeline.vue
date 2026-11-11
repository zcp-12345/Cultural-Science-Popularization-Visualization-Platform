<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { scalePoint, select } from 'd3'
import type { Era } from '@/types/character'

const props = defineProps<{
  eras: Era[]
  selectedId: string
}>()

const emit = defineEmits<{ select: [id: string] }>()

const svgEl = ref<SVGSVGElement | null>(null)

const WIDTH = 960
const HEIGHT = 236
const BASELINE = 124

function applySelection() {
  if (!svgEl.value) return
  select(svgEl.value)
    .selectAll<SVGGElement, Era>('g.era')
    .classed('is-selected', (era) => era.id === props.selectedId)
}

function render() {
  if (!svgEl.value) return

  const svg = select(svgEl.value)
  svg.selectAll('*').remove()

  const x = scalePoint<string>()
    .domain(props.eras.map((era) => era.id))
    .range([72, WIDTH - 72])
    .padding(0.2)

  const defs = svg.append('defs')
  const gradient = defs
    .append('linearGradient')
    .attr('id', 'timeline-line')
    .attr('x1', '0%')
    .attr('x2', '100%')

  gradient.append('stop').attr('offset', '0%').attr('stop-color', '#00f0ff').attr('stop-opacity', 0.15)
  gradient.append('stop').attr('offset', '45%').attr('stop-color', '#00f0ff').attr('stop-opacity', 0.75)
  gradient.append('stop').attr('offset', '100%').attr('stop-color', '#ffcc00').attr('stop-opacity', 0.85)

  svg
    .append('line')
    .attr('x1', 40)
    .attr('x2', WIDTH - 40)
    .attr('y1', BASELINE)
    .attr('y2', BASELINE)
    .attr('stroke', 'url(#timeline-line)')
    .attr('stroke-width', 1.5)
    .attr('stroke-linecap', 'round')

  const groups = svg
    .selectAll<SVGGElement, Era>('g.era')
    .data(props.eras)
    .join('g')
    .attr('class', 'era')
    .attr('transform', (era) => `translate(${x(era.id) ?? 0}, ${BASELINE})`)
    .attr('tabindex', 0)
    .attr('role', 'button')
    .attr('aria-label', (era) => `${era.name}，${era.dynasty}，${era.period}`)
    .on('click', (_event, era) => emit('select', era.id))
    .on('keydown', (event: KeyboardEvent, era) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault()
        emit('select', era.id)
      }
    })

  groups.each(function (era, index) {
    const group = select(this)
    const above = index % 2 === 0
    const direction = above ? -1 : 1

    group
      .append('line')
      .attr('class', 'era-connector')
      .attr('y1', 9 * direction)
      .attr('y2', 40 * direction)
      .attr('stroke', 'rgba(0, 240, 255, 0.3)')
      .attr('stroke-width', 1)

    group
      .append('circle')
      .attr('class', 'era-dot')
      .attr('r', 7)
      .attr('style', `animation-delay: ${index * 90}ms`)

    group
      .append('circle')
      .attr('class', 'era-halo')
      .attr('r', 14)
      .attr('style', `animation-delay: ${index * 90}ms`)

    group
      .append('text')
      .attr('class', 'era-name')
      .attr('text-anchor', 'middle')
      .attr('y', above ? -72 : 66)
      .text(era.name)

    group
      .append('text')
      .attr('class', 'era-period')
      .attr('text-anchor', 'middle')
      .attr('y', above ? -52 : 86)
      .text(era.period)

    group
      .append('text')
      .attr('class', 'era-dynasty')
      .attr('text-anchor', 'middle')
      .attr('y', above ? -92 : 46)
      .text(era.dynasty)
  })

  applySelection()
}

onMounted(render)

watch(
  () => props.eras,
  () => render(),
)

watch(
  () => props.selectedId,
  () => applySelection(),
)
</script>

<template>
  <div class="timeline-scroll">
    <svg
      ref="svgEl"
      class="timeline"
      :viewBox="`0 0 ${WIDTH} ${HEIGHT}`"
      role="group"
      aria-label="汉字字体演变时间轴，从甲骨文到简体字"
    ></svg>
  </div>
</template>

<style scoped>
.timeline-scroll {
  width: 100%;
  overflow-x: auto;
  overflow-y: hidden;
  padding: 6px 0 2px;
}

.timeline {
  width: 100%;
  min-width: 760px;
  height: auto;
  display: block;
}

:deep(.era) {
  cursor: pointer;
  outline: none;
}

:deep(.era-dot) {
  fill: #0b1120;
  stroke: rgba(0, 240, 255, 0.6);
  stroke-width: 2;
  transition:
    fill 0.25s ease,
    stroke 0.25s ease;
  animation: dot-in 0.7s var(--ease-out) both;
}

:deep(.era-halo) {
  fill: none;
  stroke: rgba(0, 240, 255, 0.16);
  stroke-width: 1;
  opacity: 0;
  transition: opacity 0.25s ease;
  animation: halo-in 0.8s var(--ease-out) both;
}

:deep(.era:hover .era-dot),
:deep(.era:focus-visible .era-dot) {
  stroke: var(--c-cyan);
  fill: rgba(0, 240, 255, 0.18);
}

:deep(.era.is-selected .era-dot) {
  fill: var(--c-gold);
  stroke: var(--c-gold);
  filter: drop-shadow(0 0 8px rgba(255, 204, 0, 0.8));
}

:deep(.era.is-selected .era-halo) {
  opacity: 1;
  stroke: rgba(255, 204, 0, 0.5);
}

:deep(.era-connector) {
  transition: stroke 0.25s ease;
}

:deep(.era.is-selected .era-connector) {
  stroke: rgba(255, 204, 0, 0.65);
}

:deep(.era-name) {
  fill: var(--c-text);
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.05em;
  transition: fill 0.25s ease;
}

:deep(.era:hover .era-name),
:deep(.era:focus-visible .era-name) {
  fill: var(--c-cyan);
}

:deep(.era.is-selected .era-name) {
  fill: var(--c-gold);
}

:deep(.era-period) {
  fill: var(--c-text-faint);
  font-size: 9.5px;
  letter-spacing: 0.02em;
}

:deep(.era-dynasty) {
  fill: var(--c-cyan);
  font-size: 9.5px;
  letter-spacing: 0.14em;
  opacity: 0.7;
}

@keyframes dot-in {
  from {
    transform: scale(0);
    opacity: 0;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}

@keyframes halo-in {
  from {
    transform: scale(0.4);
    opacity: 0;
  }
  to {
    transform: scale(1);
    opacity: 0;
  }
}

@media (max-width: 720px) {
  .timeline {
    min-width: 700px;
  }
}
</style>
