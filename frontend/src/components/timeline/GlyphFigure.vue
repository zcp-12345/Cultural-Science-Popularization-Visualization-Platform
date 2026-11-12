<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { glyphSrc } from '@/services/glyphs'

const props = withDefaults(
  defineProps<{ char: string; era: string; size?: number }>(),
  { size: 96 },
)

const svg = ref<string | null>(null)
const failed = ref(false)

const cache = new Map<string, string>()
const box = computed(() => `${props.size}px`)
let controller: AbortController | null = null

async function load() {
  controller?.abort()
  const ctrl = new AbortController()
  controller = ctrl
  failed.value = false

  const url = glyphSrc(props.char, props.era)
  if (cache.has(url)) {
    svg.value = cache.get(url) ?? null
    return
  }
  try {
    const res = await fetch(url, { signal: ctrl.signal })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const text = await res.text()
    cache.set(url, text)
    svg.value = text
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') return
    svg.value = null
    failed.value = true
  }
}

watch(() => [props.char, props.era], load, { immediate: true })
</script>

<template>
  <span
    class="glyph-figure"
    :class="[`glyph--${era}`, { 'glyph-figure--fallback': failed }]"
    :style="{ width: box, height: box }"
    role="img"
    :aria-label="`${char} · ${era}`"
  >
    <span v-if="svg" class="glyph-figure__svg" v-html="svg" />
    <span v-else class="glyph-figure__char" :style="{ fontSize: `${size}px` }">{{ char }}</span>
  </span>
</template>

<style scoped>
.glyph-figure {
  position: relative;
  z-index: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.glyph-figure__svg {
  display: block;
  width: 100%;
  height: 100%;
}

.glyph-figure__svg :deep(svg) {
  display: block;
  width: 100%;
  height: 100%;
  filter: drop-shadow(0 0 26px var(--glyph-glow, transparent));
}

.glyph-figure__char {
  font-family: var(--font-serif);
  font-weight: 700;
  line-height: 1;
  text-shadow: 0 0 26px var(--glyph-glow, transparent);
}

/* 时期配色（与原 TimelineView 一致），同时供文字回退与 SVG currentColor 使用 */
.glyph--oracle {
  color: #d8a25b;
  --glyph-glow: rgba(216, 162, 91, 0.4);
}

.glyph--bronze {
  color: #b98a4e;
  --glyph-glow: rgba(185, 138, 78, 0.4);
}

.glyph--seal {
  color: #8fd3c7;
  --glyph-glow: rgba(143, 211, 199, 0.36);
}

.glyph--clerical {
  color: #e0b85c;
  --glyph-glow: rgba(224, 184, 92, 0.38);
}

.glyph--regular {
  color: #e9f2fb;
  --glyph-glow: rgba(233, 242, 251, 0.3);
}

.glyph--simplified {
  color: #7fe9ff;
  --glyph-glow: rgba(0, 240, 255, 0.4);
}
</style>
