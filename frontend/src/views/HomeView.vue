<script setup lang="ts">
import { onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import AppIcon from '@/components/ui/AppIcon.vue'
import ScanChar from '@/components/ui/ScanChar.vue'
import AiNotesPanel from '@/components/ai/AiNotesPanel.vue'
import MagnifierLens from '@/components/magnifier/MagnifierLens.vue'
import { useArchaeologyStore } from '@/stores/archaeology'
import { useUiStore } from '@/stores/ui'
import { useUserStore } from '@/stores/user'

const archaeology = useArchaeologyStore()
const ui = useUiStore()
const user = useUserStore()
const route = useRoute()

const articleRef = ref<HTMLElement | null>(null)
const lens = reactive({ visible: false, x: 0, y: 0, char: '' })

const CJK_RE = /[㐀-䶿一-鿿豈-﫿\u{20000}-\u{2FA1F}]/u

let noteTimer: number | undefined
let hideTimer: number | undefined
let pinTimer: number | undefined
let pinned = false
let lastChar = ''

function scheduleNote(char: string) {
  window.clearTimeout(noteTimer)
  noteTimer = window.setTimeout(() => {
    if (archaeology.noteCharacter(char)) user.recordScan()
  }, 420)
}

function showAt(char: string, x: number, y: number) {
  if (!CJK_RE.test(char)) return
  window.clearTimeout(hideTimer)
  lens.char = char
  lens.x = x
  lens.y = y
  lens.visible = true

  if (char !== lastChar) {
    lastChar = char
    scheduleNote(char)
  }
}

function hideLens() {
  if (pinned) return
  window.clearTimeout(hideTimer)
  lens.visible = false
  lastChar = ''
}

function scheduleHide() {
  window.clearTimeout(hideTimer)
  hideTimer = window.setTimeout(hideLens, 260)
}

function charAtPoint(x: number, y: number): string | null {
  const doc = document as Document & {
    caretRangeFromPoint?: (x: number, y: number) => Range | null
    caretPositionFromPoint?: (x: number, y: number) => { offsetNode: Node; offset: number } | null
  }

  if (typeof doc.caretRangeFromPoint === 'function') {
    const range = doc.caretRangeFromPoint(x, y)
    if (range && range.startContainer.nodeType === Node.TEXT_NODE) {
      const node = range.startContainer as Text
      if (!articleRef.value?.contains(node)) return null
      const codePoint = node.data.codePointAt(range.startOffset)
      return codePoint ? String.fromCodePoint(codePoint) : null
    }
  }

  if (typeof doc.caretPositionFromPoint === 'function') {
    const position = doc.caretPositionFromPoint(x, y)
    if (position && position.offsetNode.nodeType === Node.TEXT_NODE) {
      const node = position.offsetNode as Text
      if (!articleRef.value?.contains(node)) return null
      const codePoint = node.data.codePointAt(position.offset)
      return codePoint ? String.fromCodePoint(codePoint) : null
    }
  }

  return null
}

function onPointerMove(event: PointerEvent) {
  if (event.pointerType && event.pointerType !== 'mouse' && event.pointerType !== 'pen') return
  pinned = false
  window.clearTimeout(pinTimer)

  const char = charAtPoint(event.clientX, event.clientY)
  if (char) showAt(char, event.clientX, event.clientY)
  else scheduleHide()
}

function pinChar(char: string, x: number, y: number) {
  pinned = true
  window.clearTimeout(pinTimer)
  showAt(char, x, y)
  if (archaeology.noteCharacter(char)) user.recordScan()
  pinTimer = window.setTimeout(() => {
    pinned = false
    lens.visible = false
    lastChar = ''
  }, 6000)
}

function inspect(char: string, el: HTMLElement) {
  const rect = el.getBoundingClientRect()
  pinChar(char, rect.left + rect.width / 2, rect.top + rect.height / 2)
}

function onArticleClick(event: MouseEvent) {
  if ((event.target as HTMLElement).closest('.scan-char')) return
  const char = charAtPoint(event.clientX, event.clientY)
  if (!char || !CJK_RE.test(char)) return
  pinChar(char, event.clientX, event.clientY)
}

function onScroll() {
  if (pinned) return
  lens.visible = false
  lastChar = ''
}

function scrollToArticle() {
  articleRef.value?.scrollIntoView({ behavior: 'smooth', block: 'center' })
}

// ----- 自动演示：依次扫过 中→龙→码→字，便于评审 / 无障碍演示，也可用 ?demo=1 自动开启 -----
const DEMO_CHARS = ['中', '龙', '码', '字']
const demoActive = ref(false)
let demoIndex = 0
let demoTimer: number | undefined

function findDemoEl(char: string): HTMLElement | null {
  return articleRef.value?.querySelector<HTMLElement>(`.scan-char[data-char="${char}"]`) ?? null
}

function demoStep() {
  const char = DEMO_CHARS[demoIndex % DEMO_CHARS.length]
  demoIndex += 1
  const el = findDemoEl(char)
  if (!el) return
  const rect = el.getBoundingClientRect()
  pinChar(char, rect.left + rect.width / 2, rect.top + rect.height / 2)
}

function startDemo() {
  stopDemo()
  demoActive.value = true
  articleRef.value?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  window.setTimeout(() => {
    if (!demoActive.value) return
    demoStep()
    demoTimer = window.setInterval(demoStep, 2400)
  }, 550)
}

function stopDemo() {
  demoActive.value = false
  window.clearInterval(demoTimer)
  demoTimer = undefined
  demoIndex = 0
  window.clearTimeout(pinTimer)
  pinned = false
  lens.visible = false
  lastChar = ''
}

function toggleDemo() {
  if (demoActive.value) stopDemo()
  else startDemo()
}

onMounted(() => {
  window.addEventListener('scroll', onScroll, { passive: true })
  if (route.query.demo === '1') startDemo()
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', onScroll)
  window.clearInterval(demoTimer)
  window.clearTimeout(noteTimer)
  window.clearTimeout(hideTimer)
  window.clearTimeout(pinTimer)
})
</script>

<template>
  <div class="home page">
    <section class="hero">
      <p class="hero__kicker">
        <span class="hero__line" aria-hidden="true"></span>
        数字考古透视镜 · CULTURAL SCIENCE POPULARIZATION
      </p>
      <h1>
        汉字的
        <span class="gradient-text">二进制</span>
        密码
      </h1>
      <p class="hero__lede">
        从甲骨文的刻痕到楷书的方寸，是三千年的字形故事；从 Unicode 码位到 UTF-8 字节，是计算机的编码故事。移动光标（触屏请轻点）扫过正文里的金色汉字，看它如何完成「查户口、变数字、装箱子」三步变身。
      </p>
      <div class="hero__actions">
        <button class="btn btn--primary" type="button" @click="scrollToArticle">
          开始扫描汉字
          <AppIcon name="arrow" :size="16" />
        </button>
        <RouterLink to="/comparator" class="btn">打开编码对比器</RouterLink>
        <button class="btn btn--ghost" type="button" @click="ui.openAi()">问 AI 助手</button>
        <button class="btn btn--ghost" type="button" :aria-pressed="demoActive" @click="toggleDemo">
          <AppIcon :name="demoActive ? 'pause' : 'play'" :size="15" />
          {{ demoActive ? '停止演示' : '自动演示' }}
        </button>
      </div>
      <dl class="hero__stats">
        <div>
          <dt>3</dt>
          <dd>步变身</dd>
        </div>
        <div>
          <dt>5</dt>
          <dd>种编码对照</dd>
        </div>
        <div>
          <dt>3000+</dt>
          <dd>年字形演变</dd>
        </div>
      </dl>
    </section>

    <section class="scan-section">
      <article
        ref="articleRef"
        class="article panel"
        @pointermove="onPointerMove"
        @pointerleave="scheduleHide"
        @click="onArticleClick"
      >
        <header class="article__head">
          <span class="badge">扫描区</span>
          <p><i class="article__pulse" aria-hidden="true"></i>移动光标或轻点正文，透视镜会跟随你</p>
        </header>

        <h2>汉字的「二进制」密码</h2>

        <p>
          汉字是中华文明的瑰宝，每一个方块字都蕴含着深厚的历史与文化。从甲骨文的刻画，到金文的铸造，再到小篆、隶书、楷书的演变，汉字承载着民族的记忆。当这些古老的符号进入现代计算机，它们经历了一场奇妙的二进制变身。
        </p>
        <p>
          例如<ScanChar char="中" @inspect="inspect" />字，它不仅仅是一个简单的符号，更是中华民族精神的象征。在计算机的世界里，它被赋予了唯一的数字身份，通过精密的编码规则，在数字洪流中穿梭，实现了跨越时空的传播与永生。
        </p>
        <p>
          又如<ScanChar char="龙" @inspect="inspect" />字，作为中华民族的图腾，象征着力量与祥瑞；<ScanChar char="码" @inspect="inspect" />字代表着代码与数字；<ScanChar char="字" @inspect="inspect" />字则是汉字体系的统称。每一个汉字，都有一段属于自己的故事。
        </p>
        <p>
          这个「数字考古透视镜」将带你深入汉字的微观世界，揭示它在计算机内部的二进制密码。从活字印刷的「一个字一个印」，到计算机的「一个字一个码位、多种编码」，人类在信息记录的道路上不断换工具。
        </p>
        <p>
          在数字化的考古中，我们会发现：计算机并不存储笔画，它存储的是汉字在 Unicode 中的码位，再按 UTF-8 等规则写成字节。笔画属于字形，码位属于字符，这是两个层面。这种从「形」到「数」的跨越，不仅是技术的进步，更是文化的延续。通过 UTF-8 编码，汉字得以在全球互联网上自由穿梭。
        </p>
        <p>
          当我们再次审视这些方块字时，不妨想象它们在 CPU 内部跳动的样子。每一个 0 和 1 的组合，都是对文明的一次致敬。
        </p>

        <p class="article__hint">
          提示：也可以直接点击金色汉字，或用 Tab 键选中后按回车——透视镜会把结果写进右侧的考古笔记。
        </p>
      </article>

      <AiNotesPanel />
    </section>

    <section class="features">
      <header class="features__head">
        <h2>继续探索</h2>
        <p>四个入口覆盖编码对比、字形演变、AI 问答与用户中心，前端 Vue3 + 后端 FastAPI + AI 层三层架构。</p>
      </header>
      <div class="feature-grid">
        <RouterLink to="/comparator" class="feature panel">
          <span class="feature__icon"><AppIcon name="compare" :size="22" /></span>
          <div class="feature__body">
            <h3>编码对比器</h3>
            <p>同一个汉字，在 Unicode 中有一个码位；写成 UTF-8、UTF-16、GB2312、GBK、Big5 时各占几个字节？</p>
          </div>
          <span class="feature__tag">交互工具</span>
        </RouterLink>

        <RouterLink to="/timeline" class="feature panel">
          <span class="feature__icon"><AppIcon name="timeline" :size="22" /></span>
          <div class="feature__body">
            <h3>汉字演变时间轴</h3>
            <p>D3 驱动的三千年长卷：甲骨文 → 金文 → 小篆 → 隶书 → 楷书；简体字是 1956 年后的现代规范节点。</p>
          </div>
          <span class="feature__tag">D3</span>
        </RouterLink>

        <button class="feature panel" type="button" @click="ui.openAi()">
          <span class="feature__icon"><AppIcon name="spark" :size="22" /></span>
          <div class="feature__body">
            <h3>AI 考古助手</h3>
            <p>关于编码与演变的问答面板，由 DeepSeek + RAG 基于知识库检索流式生成，离线时回退本地回答。</p>
          </div>
          <span class="feature__tag">AI 在线</span>
        </button>

        <RouterLink to="/profile" class="feature panel">
          <span class="feature__icon"><AppIcon name="user" :size="22" /></span>
          <div class="feature__body">
            <h3>用户中心</h3>
            <p>学习档案、收藏与进度的真实用户系统，部分统计图表仍为示意。</p>
          </div>
          <span class="feature__tag">JWT 登录</span>
        </RouterLink>
      </div>
    </section>

    <MagnifierLens :visible="lens.visible" :x="lens.x" :y="lens.y" :char="lens.char" />
  </div>
</template>

<style scoped>
.home {
  display: flex;
  flex-direction: column;
  gap: 56px;
}

/* ----- Hero ----- */
.hero {
  padding-top: 28px;
  max-width: 860px;
}

.hero__kicker {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0 0 18px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.22em;
  color: var(--c-cyan);
  text-transform: uppercase;
}

.hero__line {
  width: 38px;
  height: 1px;
  background: linear-gradient(90deg, var(--c-cyan), transparent);
  box-shadow: 0 0 8px var(--c-cyan);
}

.hero h1 {
  margin: 0 0 20px;
  font-family: var(--font-serif);
  font-size: clamp(2.2rem, 6vw, 4rem);
  font-weight: 700;
  line-height: 1.16;
  letter-spacing: 0.06em;
}

.hero__lede {
  max-width: 640px;
  margin: 0 0 28px;
  font-size: 15.5px;
  line-height: 1.9;
  color: var(--c-text-dim);
}

.hero__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 40px;
}

.hero__stats {
  display: flex;
  flex-wrap: wrap;
  gap: 0;
  margin: 0;
  padding: 18px 0;
  border-top: 1px solid var(--c-line);
  border-bottom: 1px solid var(--c-line);
}

.hero__stats div {
  display: flex;
  align-items: baseline;
  gap: 8px;
  padding-right: 36px;
  margin-right: 36px;
  border-right: 1px solid rgba(255, 255, 255, 0.07);
}

.hero__stats div:last-child {
  border-right: none;
  margin-right: 0;
  padding-right: 0;
}

.hero__stats dt {
  font-size: 30px;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: var(--c-gold);
  text-shadow: 0 0 20px rgba(255, 204, 0, 0.28);
}

.hero__stats dd {
  margin: 0;
  font-size: 12px;
  letter-spacing: 0.08em;
  color: var(--c-text-faint);
}

/* ----- 扫描区 ----- */
.scan-section {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 340px;
  gap: 18px;
  align-items: start;
}

.article {
  padding: 26px 30px 30px;
}

.article__head {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 18px;
}

.article__head p {
  display: flex;
  align-items: center;
  gap: 7px;
  margin: 0;
  font-size: 11.5px;
  letter-spacing: 0.04em;
  color: var(--c-text-faint);
}

.article__pulse {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--c-green);
  box-shadow: 0 0 8px var(--c-green);
  animation: pulse 2s ease-in-out infinite;
}

.article h2 {
  margin: 0 0 20px;
  text-align: center;
  font-size: 22px;
  letter-spacing: 0.16em;
  color: var(--c-text);
}

.article p {
  margin: 0 0 1.05em;
  font-size: 14.5px;
  line-height: 2;
  text-indent: 2em;
  color: rgba(233, 242, 251, 0.88);
}

.article__hint {
  margin-top: 22px !important;
  padding-top: 16px;
  border-top: 1px dashed rgba(0, 240, 255, 0.14);
  text-indent: 0 !important;
  font-size: 12px !important;
  line-height: 1.7 !important;
  color: var(--c-text-faint) !important;
}

/* ----- 入口卡片 ----- */
.features__head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 18px;
}

.features__head h2 {
  margin: 0;
  font-size: 19px;
  letter-spacing: 0.1em;
}

.features__head p {
  margin: 0;
  font-size: 12px;
  color: var(--c-text-faint);
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.feature {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 20px;
  text-align: left;
  transition:
    transform 0.25s var(--ease-out),
    border-color 0.25s ease,
    box-shadow 0.25s ease;
}

.feature:hover {
  transform: translateY(-3px);
  border-color: rgba(0, 240, 255, 0.38);
  box-shadow:
    var(--shadow-panel),
    0 0 28px rgba(0, 240, 255, 0.12);
}

.feature__icon {
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 42px;
  height: 42px;
  border-radius: 12px;
  color: var(--c-cyan);
  background: var(--c-cyan-soft);
  border: 1px solid rgba(0, 240, 255, 0.24);
}

.feature__body h3 {
  margin: 2px 0 6px;
  font-size: 15px;
  letter-spacing: 0.04em;
}

.feature__body p {
  margin: 0;
  font-size: 12.5px;
  line-height: 1.75;
  color: var(--c-text-dim);
}

.feature__tag {
  position: absolute;
  top: 16px;
  right: 16px;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 10px;
  letter-spacing: 0.06em;
  color: var(--c-cyan);
  background: var(--c-cyan-soft);
  border: 1px solid rgba(0, 240, 255, 0.2);
}

.scan-section :deep(.notes) {
  position: sticky;
  top: calc(var(--header-h) + 20px);
  max-height: calc(100vh - var(--header-h) - 40px);
}

@media (max-width: 960px) {
  .scan-section {
    grid-template-columns: minmax(0, 1fr);
  }

  .scan-section :deep(.notes) {
    position: static;
    max-height: 420px;
  }
}

@media (max-width: 720px) {
  .home {
    gap: 40px;
  }

  .hero {
    padding-top: 8px;
  }

  .hero__stats div {
    padding-right: 22px;
    margin-right: 22px;
  }

  .hero__stats dt {
    font-size: 24px;
  }

  .article {
    padding: 20px 18px 24px;
  }

  .article p {
    font-size: 13.5px;
  }

  .feature-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .features__head {
    flex-direction: column;
    gap: 6px;
  }
}
</style>
