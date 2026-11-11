<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { describeChar } from '@/services/encoding'

const props = defineProps<{
  visible: boolean
  x: number
  y: number
  char: string
}>()

const STEP_MS = [1000, 1500, 1500, 3000]
const step = ref(0)
const viewport = ref({ width: 1280, height: 800 })
const reduceMotion = ref(false)

const info = computed(() => (props.char ? describeChar(props.char) : null))
const binaryRows = computed(() => {
  const bits = info.value?.binary ?? ''
  const rows: string[] = []
  for (let index = 0; index < bits.length; index += 8) {
    rows.push(bits.slice(index, index + 8))
  }
  return rows
})

let timer: number | undefined

function stop() {
  if (timer !== undefined) {
    window.clearTimeout(timer)
    timer = undefined
  }
}

function schedule(index: number) {
  stop()
  timer = window.setTimeout(() => {
    step.value = (index + 1) % STEP_MS.length
    schedule(step.value)
  }, STEP_MS[index])
}

function start() {
  stop()
  if (reduceMotion.value) {
    step.value = 3
    return
  }
  step.value = 0
  schedule(0)
}

watch(
  () => props.visible,
  (visible) => {
    if (visible) {
      start()
    } else {
      stop()
      step.value = 0
    }
  },
)

function updateViewport() {
  viewport.value = { width: window.innerWidth, height: window.innerHeight }
}

let motionQuery: MediaQueryList | null = null
function onMotionChange(event: MediaQueryListEvent) {
  reduceMotion.value = event.matches
  if (props.visible) start()
}

onMounted(() => {
  updateViewport()
  window.addEventListener('resize', updateViewport)
  motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
  reduceMotion.value = motionQuery.matches
  motionQuery.addEventListener('change', onMotionChange)
  if (props.visible) start()
})

onBeforeUnmount(() => {
  stop()
  window.removeEventListener('resize', updateViewport)
  motionQuery?.removeEventListener('change', onMotionChange)
})

const size = computed(() => (viewport.value.width <= 720 ? 156 : 198))

const lensStyle = computed(() => {
  const margin = size.value / 2 + 12
  const x = Math.min(Math.max(props.x, margin), Math.max(margin, viewport.value.width - margin))
  const y = Math.min(Math.max(props.y, margin), Math.max(margin, viewport.value.height - margin))
  return {
    left: `${x}px`,
    top: `${y}px`,
    width: `${size.value}px`,
    height: `${size.value}px`,
  }
})
</script>

<template>
  <div class="lens" :class="{ 'lens--visible': visible }" :style="lensStyle" aria-hidden="true">
    <div class="lens__scanline"></div>
    <div class="lens__content">
      <Transition name="step" mode="out-in">
        <div v-if="step === 0 && info" key="step-0" class="step step--char">
          <span class="step__label">考古对象</span>
          <span class="step__char">{{ info.char }}</span>
          <span class="step__hint">{{ info.block }}</span>
        </div>

        <div v-else-if="step === 1 && info" key="step-1" class="step">
          <span class="step__label">① 查户口 · Unicode</span>
          <span class="step__unicode mono">U+{{ info.unicodeHex }}</span>
          <span class="step__hint">{{ info.planeName }}</span>
          <span class="step__hint step__hint--dim">{{ info.block }}</span>
        </div>

        <div v-else-if="step === 2 && info" key="step-2" class="step">
          <span class="step__label">② 变数字 · Binary</span>
          <div class="bit-grid">
            <div v-for="(row, rowIndex) in binaryRows" :key="rowIndex" class="bit-row">
              <span v-for="(bit, bitIndex) in row.split('')" :key="bitIndex" class="bit">{{ bit }}</span>
            </div>
          </div>
          <span class="step__hint mono">{{ info.binary.length }} 位码位二进制</span>
        </div>

        <div v-else-if="step === 3 && info" key="step-3" class="step">
          <span class="step__label">③ 装箱子 · UTF-8</span>
          <div class="byte-boxes">
            <div
              v-for="(part, index) in info.utf8.parts"
              :key="index"
              class="byte-box"
              :title="`0x${part.byte.toString(16).toUpperCase()}`"
            >
              <span class="byte-box__marker">{{ part.marker }}</span><span class="byte-box__data">{{ part.data }}</span>
            </div>
          </div>
          <span class="step__hint">{{ info.utf8.bytes.length }} 字节</span>
          <span class="step__hint step__hint--dim mono">{{ info.utf8.text }}</span>
        </div>
      </Transition>
    </div>
  </div>
</template>

<style scoped>
.lens {
  position: fixed;
  z-index: var(--z-lens);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  border: 3px solid var(--c-cyan);
  background: radial-gradient(circle at center, rgba(0, 22, 38, 0.97) 0%, rgba(0, 6, 12, 0.99) 100%);
  box-shadow:
    0 0 44px rgba(0, 240, 255, 0.4),
    inset 0 0 34px rgba(0, 240, 255, 0.12);
  pointer-events: none;
  opacity: 0;
  transform: translate(-50%, -50%) scale(0.88);
  transition:
    opacity 0.25s ease,
    transform 0.32s var(--ease-out);
  overflow: hidden;
  will-change: left, top;
}

.lens--visible {
  opacity: 1;
  transform: translate(-50%, -50%) scale(1);
}

.lens::before {
  content: '';
  position: absolute;
  inset: 9px;
  border-radius: 50%;
  border: 1px solid rgba(0, 240, 255, 0.18);
}

.lens::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background-image:
    linear-gradient(rgba(0, 240, 255, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 240, 255, 0.05) 1px, transparent 1px);
  background-size: 18px 18px;
  mask-image: radial-gradient(circle, #000 30%, transparent 74%);
}

.lens__scanline {
  position: absolute;
  left: 12%;
  width: 76%;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--c-cyan), transparent);
  box-shadow: 0 0 12px var(--c-cyan);
  animation: lens-scan 2.5s ease-in-out infinite;
  z-index: 2;
}

@keyframes lens-scan {
  0% {
    top: 12%;
    opacity: 0;
  }
  45%,
  55% {
    opacity: 0.9;
  }
  100% {
    top: 88%;
    opacity: 0;
  }
}

.lens__content {
  position: relative;
  z-index: 1;
  width: 100%;
  height: 100%;
}

.step {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 5px;
  padding: 22px;
  text-align: center;
}

.step__label {
  font-size: 9.5px;
  font-weight: 600;
  letter-spacing: 0.18em;
  color: rgba(0, 240, 255, 0.72);
  text-transform: uppercase;
}

.step__char {
  font-family: var(--font-serif);
  font-size: 58px;
  font-weight: 700;
  line-height: 1;
  color: var(--c-gold);
  text-shadow: 0 0 26px rgba(255, 204, 0, 0.55);
}

.step__unicode {
  font-size: 22px;
  font-weight: 700;
  color: var(--c-cyan);
  letter-spacing: 0.05em;
  text-shadow: 0 0 18px rgba(0, 240, 255, 0.5);
}

.step__hint {
  max-width: 100%;
  font-size: 9.5px;
  line-height: 1.5;
  color: rgba(233, 242, 251, 0.7);
  overflow-wrap: anywhere;
}

.step__hint--dim {
  color: rgba(233, 242, 251, 0.42);
  letter-spacing: 0.04em;
}

.bit-grid {
  display: grid;
  gap: 3px;
}

.bit-row {
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: 2px;
}

.bit {
  display: grid;
  place-items: center;
  width: 14px;
  height: 16px;
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--c-cyan);
  background: rgba(0, 240, 255, 0.08);
  border: 1px solid rgba(0, 240, 255, 0.24);
  border-radius: 2px;
}

.byte-boxes {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 4px;
}

.byte-box {
  padding: 4px 5px;
  border: 1px solid rgba(0, 240, 255, 0.5);
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.04);
  font-family: var(--font-mono);
  font-size: 10px;
  line-height: 1.2;
  letter-spacing: 0.04em;
}

.byte-box__marker {
  color: var(--c-magenta);
  font-weight: 700;
}

.byte-box__data {
  color: var(--c-green);
}

.step-enter-active,
.step-leave-active {
  transition:
    opacity 0.35s ease,
    transform 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

.step-enter-from {
  opacity: 0;
  transform: scale(0.8) translateY(10px);
}

.step-leave-to {
  opacity: 0;
  transform: scale(0.8) translateY(-10px);
}

@media (max-width: 720px) {
  .step {
    padding: 18px;
  }

  .step__char {
    font-size: 44px;
  }

  .step__unicode {
    font-size: 18px;
  }

  .bit {
    width: 11px;
    height: 13px;
    font-size: 8px;
  }

  .byte-box {
    font-size: 8.5px;
    padding: 3px 4px;
  }
}
</style>
