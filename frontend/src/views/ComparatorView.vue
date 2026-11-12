<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import AppIcon from '@/components/ui/AppIcon.vue'
import EncodingChart from '@/components/comparator/EncodingChart.vue'
import { describeChar, describeCharRemote, ENCODING_LABELS, formatHexBytes, summarizeText, summarizeTextRemote } from '@/services/encoding'
import { useUserStore } from '@/stores/user'
import type { CharDescription, LegacyEncodingId, TextSummary } from '@/types/encoding'

const route = useRoute()
const user = useUserStore()

const initialText = typeof route.query.q === 'string' && route.query.q ? route.query.q : '中华龙码'
const text = ref(initialText)
const selectedIndex = ref(0)
const copiedKey = ref('')

const samples = ['中', '龙', '龍', '镕', '𠮷', 'A']

const chars = computed(() => Array.from(text.value))
const descriptions = ref<CharDescription[]>([])
const summary = ref<TextSummary | null>(null)
const usingRemote = ref(false)
const selected = computed<CharDescription | null>(() => descriptions.value[selectedIndex.value] ?? null)

// 远程优先、本地兜底：本地先即时渲染，后端 Python codecs 结果到达后覆盖。
let refreshSeq = 0

async function refresh() {
  const seq = ++refreshSeq
  const currentChars = chars.value
  const currentText = text.value

  descriptions.value = currentChars.map(describeChar)
  summary.value = summarizeText(currentText)
  usingRemote.value = false

  try {
    const [remoteDescriptions, remoteSummary] = await Promise.all([
      Promise.all(currentChars.map(describeCharRemote)),
      summarizeTextRemote(currentText),
    ])
    if (seq !== refreshSeq) return // 丢弃过期结果
    descriptions.value = remoteDescriptions
    summary.value = remoteSummary
    usingRemote.value = true
  } catch {
    // 后端不可达：保留本地兜底结果
  }
}

const summaryRows = computed(() => {
  const current = summary.value
  if (!current) return []
  return [current.utf8, current.utf16, current.gb2312, current.gbk, current.big5]
})

const legacyCards = computed(() => {
  const current = selected.value
  if (!current) return []
  return (['gb2312', 'gbk', 'big5'] as LegacyEncodingId[]).map((id) => ({
    id,
    label: ENCODING_LABELS[id],
    result: current.legacy[id],
    description:
      id === 'gb2312'
        ? '1980 年国家标准，收录 6763 个汉字，是简体中文的早期基础字符集。'
        : id === 'gbk'
          ? '1995 年扩展标准，收录 21003 个汉字，向下兼容 GB2312。'
          : '繁体中文常用字符集，传统收录约 1.3 万字；浏览器实现含 Big5-HKSCS 增补字符。',
  }))
})

const unicodeBinaryRows = computed(() => {
  const bits = selected.value?.binary ?? ''
  const rows: string[] = []
  for (let index = 0; index < bits.length; index += 8) {
    rows.push(bits.slice(index, index + 8))
  }
  return rows
})

const utf8Note = computed(() => {
  const d = selected.value
  if (!d) return ''
  const count = d.utf8.bytes.length
  const marker = d.utf8.parts[0]?.marker ?? ''
  if (count === 1) {
    return '单字节编码：首字节以 0 开头，7 位数据位直接装下 ASCII 字符。'
  }
  const label = count === 2 ? '双字节' : count === 3 ? '三字节' : '四字节'
  return `变长编码：首字节的 ${marker} 是「${label}」标记，后续 ${count - 1} 个字节以 10 开头。紫色为标记位，绿色为数据位。`
})

const utf16Note = computed(() => {
  const d = selected.value
  if (!d) return ''
  return d.utf16.isSurrogatePair
    ? `该字位于${d.block}（${d.planeName}），超出基本多文种平面（BMP），UTF-16 需要用两个码元（代理对）才能表示。`
    : '常用汉字位于基本多文种平面（BMP），UTF-16 用一个码元（2 字节）即可表示。'
})

let copyTimer: number | undefined
let recordTimer: number | undefined

watch(
  text,
  () => {
    selectedIndex.value = 0
    window.clearTimeout(recordTimer)
    recordTimer = window.setTimeout(() => user.recordEncoding(), 900)
    void refresh()
  },
  { immediate: true },
)

async function copy(value: string, key: string) {
  try {
    await navigator.clipboard.writeText(value)
    copiedKey.value = key
  } catch {
    copiedKey.value = ''
  }
  window.clearTimeout(copyTimer)
  copyTimer = window.setTimeout(() => {
    copiedKey.value = ''
  }, 1400)
}

function byteHex(byte: number): string {
  return byte.toString(16).toUpperCase().padStart(2, '0')
}

function displayChar(char: string): string {
  return char === ' ' ? '␠' : char
}

onBeforeUnmount(() => {
  window.clearTimeout(copyTimer)
  window.clearTimeout(recordTimer)
})
</script>

<template>
  <div class="comparator page">
    <header class="page-head">
      <div>
        <span class="badge">Phase 2 · Python codecs 权威编码</span>
        <h1>编码对比器</h1>
        <p>
          同一个汉字，在 Unicode 中只有一个码位；写成 UTF-8、UTF-16、GB2312、GBK、Big5 时，会得到完全不同的字节。输入任意汉字，逐位查看它从「码位」到「字节」的转换。
        </p>
      </div>
      <span class="page-head__mark" aria-hidden="true">
        <AppIcon name="compare" :size="34" />
      </span>
    </header>

    <section class="editor panel">
      <label for="encoding-input">输入汉字或短句</label>
      <div class="editor__row">
        <input
          id="encoding-input"
          v-model="text"
          maxlength="80"
          autocomplete="off"
          spellcheck="false"
          placeholder="例如：中华龙码"
        />
        <span class="editor__count mono">{{ chars.length }}/80</span>
      </div>

      <div class="editor__samples">
        <span>试试：</span>
        <button v-for="sample in samples" :key="sample" type="button" class="sample" @click="text = sample">
          {{ sample }}
        </button>
      </div>

      <div v-if="chars.length" class="editor__chips" aria-label="逐字选择">
        <button
          v-for="(char, index) in chars"
          :key="`${char}-${index}`"
          type="button"
          :class="['char-chip', { 'char-chip--active': index === selectedIndex }]"
          @click="selectedIndex = index"
        >
          {{ displayChar(char) }}
        </button>
      </div>
    </section>

    <div v-if="!selected" class="empty panel">
      <AppIcon name="code" :size="28" />
      <p>输入至少一个汉字，开始逐字节考古。</p>
    </div>

    <template v-else>
      <section class="detail-grid">
        <article class="char-card panel">
          <div class="char-card__glyph">{{ selected.char }}</div>
          <button
            class="char-card__fav"
            :class="{ 'char-card__fav--active': user.isFavorite(selected.char) }"
            type="button"
            :aria-pressed="user.isFavorite(selected.char)"
            :aria-label="user.isFavorite(selected.char) ? `取消收藏 ${selected.char}` : `收藏 ${selected.char}`"
            @click="user.toggleFavorite(selected.char)"
          >
            <AppIcon name="heart" :size="18" :filled="user.isFavorite(selected.char)" />
          </button>
          <div class="char-card__meta">
            <span class="badge">Unicode 码位</span>
            <strong class="mono char-card__code">U+{{ selected.unicodeHex }}</strong>
            <dl>
              <div>
                <dt>所处平面</dt>
                <dd>{{ selected.planeName }}</dd>
              </div>
              <div>
                <dt>所属区段</dt>
                <dd>{{ selected.block }}</dd>
              </div>
              <div>
                <dt>码位二进制</dt>
                <dd class="mono char-card__binary">{{ unicodeBinaryRows.join(' ') }}</dd>
              </div>
            </dl>
          </div>
        </article>

        <div class="chart-card panel">
          <EncodingChart :description="selected" />
        </div>
      </section>

      <section class="encoding-cards">
        <article class="card panel">
          <header class="card__head">
            <div class="card__title">
              <span class="card__label mono">UTF-8</span>
              <span class="badge badge--gold">{{ selected.utf8.bytes.length }} 字节</span>
            </div>
            <button class="copy" type="button" @click="copy(selected.utf8.text, 'utf8')">
              {{ copiedKey === 'utf8' ? '已复制' : '复制' }}
            </button>
          </header>

          <div class="byte-row">
            <div v-for="(part, index) in selected.utf8.parts" :key="index" class="byte">
              <span class="byte__marker">{{ part.marker }}</span><span class="byte__data">{{ part.data }}</span>
              <span class="byte__hex mono">0x{{ byteHex(part.byte) }}</span>
            </div>
          </div>

          <p class="card__note">
            {{ utf8Note }}
          </p>
        </article>

        <article class="card panel">
          <header class="card__head">
            <div class="card__title">
              <span class="card__label mono">UTF-16</span>
              <span class="badge badge--gold">{{ selected.utf16.units.length * 2 }} 字节</span>
              <span v-if="selected.utf16.isSurrogatePair" class="badge">代理对</span>
            </div>
            <button class="copy" type="button" @click="copy(formatHexBytes(selected.utf16.bytesLE), 'utf16')">
              {{ copiedKey === 'utf16' ? '已复制' : '复制' }}
            </button>
          </header>

          <div class="unit-row">
            <div v-for="(unit, index) in selected.utf16.units" :key="index" class="unit">
              <span class="unit__hex mono">0x{{ unit.hex }}</span>
              <span class="unit__bits mono">{{ unit.binary }}</span>
            </div>
          </div>

          <div class="byte-line">
            <span>小端（LE）</span>
            <b class="mono">{{ formatHexBytes(selected.utf16.bytesLE) }}</b>
          </div>
          <div class="byte-line">
            <span>大端（BE）</span>
            <b class="mono">{{ formatHexBytes(selected.utf16.bytesBE) }}</b>
          </div>

          <p class="card__note">{{ utf16Note }}</p>
        </article>

        <article v-for="card in legacyCards" :key="card.id" class="card panel" :class="{ 'card--off': !card.result.available }">
          <header class="card__head">
            <div class="card__title">
              <span class="card__label mono">{{ card.label }}</span>
              <span v-if="card.result.available" class="badge badge--gold">{{ card.result.bytes?.length }} 字节</span>
              <span v-else class="badge badge--muted">不支持</span>
            </div>
            <button
              v-if="card.result.available && card.result.bytes"
              class="copy"
              type="button"
              @click="copy(formatHexBytes(card.result.bytes), card.id)"
            >
              {{ copiedKey === card.id ? '已复制' : '复制' }}
            </button>
          </header>

          <template v-if="card.result.available">
            <div class="byte-row byte-row--plain">
              <div v-for="(byte, index) in card.result.bytes ?? []" :key="index" class="byte byte--plain">
                <span class="byte__hex mono">{{ byteHex(byte) }}</span>
                <span class="byte__dec mono">{{ byte }}</span>
              </div>
            </div>
          </template>
          <div v-else class="unavailable">
            <AppIcon name="close" :size="15" />
            <span>{{ card.result.note || '该字符不在此字符集内' }}</span>
          </div>

          <p class="card__note">{{ card.description }}</p>
        </article>
      </section>

      <section class="summary panel">
        <header class="summary__head">
          <div>
            <h2>整段文本的编码开销</h2>
            <p>共 {{ chars.length }} 个字符 · UTF-16 按小端字节统计</p>
          </div>
          <span class="badge badge--muted">{{ usingRemote ? '后端 Python codecs' : '本地兜底 · 离线' }}</span>
        </header>

        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th scope="col">编码</th>
                <th scope="col">总字节</th>
                <th scope="col">可编码字符</th>
                <th scope="col">缺失字符</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in summaryRows" :key="row.label">
                <td class="mono summary__name">{{ row.label }}</td>
                <td class="mono">{{ row.bytes }} B</td>
                <td class="mono">{{ row.covered }}/{{ row.total }}</td>
                <td>
                  <span v-if="row.missing.length" class="missing">{{ row.missing.join(' ') }}</span>
                  <span v-else class="ok">全部覆盖</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <p class="summary__note">
          Unicode 是字符集，负责分配码位；UTF-8 / UTF-16 是 Unicode 的两种编码方式；GB2312 / GBK / Big5 则是各自独立的字符集，同时规定了字符到字节的映射，它们之间靠映射表转换，因此 Unicode 本身不参与字节数比较。
        </p>
      </section>
    </template>

    <footer class="footnote">
      <p>
        数据说明：编码结果优先由后端 FastAPI + Python codecs 提供（权威口径），后端不可达时自动回退本地计算（离线兜底）。GB2312 / GBK / Big5
        均为传统双字节字符集，覆盖范围不同，出现「不支持」本身就是编码史的现场证据。Python 的 Big5 为传统 Big5（不含 HKSCS 增补），因此「龙」等简体字通常无编码；浏览器
        Big5 解码器含 HKSCS，覆盖范围更大。
      </p>
    </footer>
  </div>
</template>

<style scoped>
.comparator {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.page-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  padding: 8px 0 4px;
}

.page-head h1 {
  margin: 14px 0 10px;
  font-family: var(--font-serif);
  font-size: clamp(1.9rem, 4vw, 2.6rem);
  letter-spacing: 0.08em;
}

.page-head p {
  max-width: 680px;
  margin: 0;
  font-size: 14px;
  line-height: 1.85;
  color: var(--c-text-dim);
}

.page-head__mark {
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 64px;
  height: 64px;
  border-radius: 18px;
  color: var(--c-cyan);
  background: var(--c-cyan-soft);
  border: 1px solid rgba(0, 240, 255, 0.28);
  box-shadow: var(--shadow-cyan);
}

/* 输入区 */
.editor {
  padding: 20px 22px;
}

.editor label {
  display: block;
  margin-bottom: 10px;
  font-size: 12px;
  letter-spacing: 0.1em;
  color: var(--c-text-faint);
}

.editor__row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 4px 0 10px;
  border-bottom: 1px solid rgba(0, 240, 255, 0.22);
}

.editor__row:focus-within {
  border-color: rgba(0, 240, 255, 0.6);
  box-shadow: 0 10px 24px -18px rgba(0, 240, 255, 0.5);
}

.editor input {
  flex: 1;
  min-width: 0;
  padding: 6px 0;
  border: none;
  background: transparent;
  font-family: var(--font-serif);
  font-size: 22px;
  letter-spacing: 0.08em;
  outline: none;
}

.editor input::placeholder {
  color: var(--c-text-faint);
  font-family: var(--font-sans);
  font-size: 15px;
  letter-spacing: 0.02em;
}

.editor__count {
  flex-shrink: 0;
  font-size: 11px;
  color: var(--c-text-faint);
}

.editor__samples {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
  font-size: 12px;
  color: var(--c-text-faint);
}

.sample {
  min-width: 32px;
  padding: 3px 10px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.03);
  font-family: var(--font-serif);
  font-size: 14px;
  color: var(--c-text-dim);
  transition:
    color 0.2s ease,
    border-color 0.2s ease,
    background 0.2s ease;
}

.sample:hover {
  color: var(--c-gold);
  border-color: rgba(255, 204, 0, 0.4);
  background: rgba(255, 204, 0, 0.08);
}

.editor__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px dashed rgba(0, 240, 255, 0.12);
}

.char-chip {
  display: grid;
  place-items: center;
  min-width: 36px;
  height: 36px;
  padding: 0 8px;
  border-radius: 9px;
  border: 1px solid rgba(255, 255, 255, 0.09);
  background: rgba(255, 255, 255, 0.03);
  font-family: var(--font-serif);
  font-size: 17px;
  color: var(--c-text-dim);
  transition:
    color 0.2s ease,
    border-color 0.2s ease,
    background 0.2s ease,
    transform 0.2s var(--ease-out);
}

.char-chip:hover {
  transform: translateY(-1px);
  border-color: rgba(0, 240, 255, 0.35);
}

.char-chip--active {
  color: #04141a;
  background: linear-gradient(120deg, var(--c-cyan), var(--c-green));
  border-color: transparent;
  box-shadow: 0 0 18px rgba(0, 240, 255, 0.3);
}

/* 详情 */
.detail-grid {
  display: grid;
  grid-template-columns: minmax(0, 0.92fr) minmax(0, 1.08fr);
  gap: 14px;
}

.char-card {
  position: relative;
  display: flex;
  align-items: center;
  gap: 22px;
  padding: 22px;
}

.char-card__fav {
  position: absolute;
  top: 14px;
  right: 14px;
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.03);
  color: var(--c-text-faint);
  cursor: pointer;
  transition:
    color 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

.char-card__fav:hover {
  color: var(--c-gold);
  border-color: rgba(255, 204, 0, 0.4);
}

.char-card__fav--active {
  color: var(--c-gold);
  border-color: rgba(255, 204, 0, 0.42);
  box-shadow: 0 0 14px rgba(255, 204, 0, 0.18);
}

.char-card__glyph {
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 132px;
  height: 132px;
  border-radius: 18px;
  border: 1px solid rgba(255, 204, 0, 0.28);
  background:
    radial-gradient(circle at 50% 34%, rgba(255, 204, 0, 0.14), transparent 66%),
    rgba(255, 255, 255, 0.025);
  font-family: var(--font-serif);
  font-size: 76px;
  line-height: 1;
  color: var(--c-gold);
  text-shadow: 0 0 28px rgba(255, 204, 0, 0.4);
}

.char-card__meta {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
  min-width: 0;
}

.char-card__code {
  font-size: 24px;
  letter-spacing: 0.06em;
  color: var(--c-cyan);
  text-shadow: 0 0 18px rgba(0, 240, 255, 0.35);
}

.char-card dl {
  display: grid;
  gap: 5px;
  margin: 6px 0 0;
  width: 100%;
}

.char-card dl div {
  display: flex;
  gap: 10px;
  font-size: 12px;
  line-height: 1.55;
}

.char-card dt {
  flex-shrink: 0;
  width: 66px;
  color: var(--c-text-faint);
}

.char-card dd {
  margin: 0;
  color: var(--c-text-dim);
  overflow-wrap: anywhere;
}

.char-card__binary {
  color: var(--c-green) !important;
  font-size: 11px;
  letter-spacing: 0.04em;
}

.chart-card {
  padding: 18px 20px;
}

/* 编码卡片 */
.encoding-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 14px;
}

.card {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 18px;
}

.card--off {
  border-style: dashed;
}

.card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.card__title {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.card__label {
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: var(--c-cyan);
}

.copy {
  padding: 3px 10px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: transparent;
  font-size: 11px;
  color: var(--c-text-faint);
  transition:
    color 0.2s ease,
    border-color 0.2s ease;
}

.copy:hover {
  color: var(--c-cyan);
  border-color: rgba(0, 240, 255, 0.4);
}

.byte-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.byte {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 6px 8px;
  border: 1px solid rgba(0, 240, 255, 0.36);
  border-radius: 7px;
  background: rgba(255, 255, 255, 0.03);
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 0.04em;
}

.byte__marker {
  color: var(--c-magenta);
  font-weight: 700;
}

.byte__data {
  color: var(--c-green);
}

.byte__hex {
  margin-top: 4px;
  font-size: 9.5px;
  color: var(--c-text-faint);
}

.byte--plain .byte__hex {
  margin-top: 0;
  font-size: 13px;
  color: var(--c-green);
}

.byte--plain {
  padding: 7px 11px;
}

.byte__dec {
  margin-top: 2px;
  font-size: 9px;
  color: var(--c-text-faint);
}

.unit-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.unit {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 6px 9px;
  border-radius: 7px;
  border: 1px solid rgba(0, 240, 255, 0.24);
  background: rgba(255, 255, 255, 0.03);
  font-size: 10px;
}

.unit__hex {
  color: var(--c-cyan);
  font-size: 12px;
}

.unit__bits {
  color: var(--c-green);
  font-size: 9.5px;
  letter-spacing: 0.06em;
}

.byte-line {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
  font-size: 11px;
  color: var(--c-text-faint);
}

.byte-line b {
  color: var(--c-text-dim);
  font-weight: 500;
  letter-spacing: 0.06em;
}

.unavailable {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px dashed rgba(255, 93, 115, 0.35);
  background: rgba(255, 93, 115, 0.06);
  font-size: 12px;
  line-height: 1.5;
  color: #ffb3bf;
}

.card__note {
  margin: 2px 0 0;
  font-size: 11.5px;
  line-height: 1.7;
  color: var(--c-text-faint);
}

.card__note b {
  color: var(--c-magenta);
  font-family: var(--font-mono);
  font-weight: 600;
}

/* 汇总表 */
.summary {
  padding: 20px 22px;
}

.summary__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 14px;
}

.summary__head h2 {
  margin: 0 0 4px;
  font-size: 16px;
  letter-spacing: 0.06em;
}

.summary__head p {
  margin: 0;
  font-size: 11.5px;
  color: var(--c-text-faint);
}

.table-wrap {
  overflow-x: auto;
}

.summary table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12.5px;
}

.summary th {
  padding: 8px 10px;
  text-align: left;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.08em;
  color: var(--c-text-faint);
  border-bottom: 1px solid rgba(0, 240, 255, 0.14);
  white-space: nowrap;
}

.summary td {
  padding: 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.045);
  color: var(--c-text-dim);
  white-space: nowrap;
}

.summary tbody tr:hover td {
  background: rgba(0, 240, 255, 0.03);
}

.summary__name {
  color: var(--c-cyan) !important;
  font-weight: 600;
}

.missing {
  color: var(--c-gold);
  font-family: var(--font-serif);
  letter-spacing: 0.1em;
}

.ok {
  color: var(--c-green);
}

.summary__note {
  margin: 12px 0 0;
  font-size: 11.5px;
  line-height: 1.7;
  color: var(--c-text-faint);
}

.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 54px 20px;
  color: var(--c-text-faint);
  border-style: dashed;
}

.empty p {
  margin: 0;
  font-size: 13px;
}

.footnote {
  padding: 4px 2px 0;
}

.footnote p {
  margin: 0;
  font-size: 11.5px;
  line-height: 1.8;
  color: var(--c-text-faint);
}

@media (max-width: 860px) {
  .detail-grid {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (max-width: 720px) {
  .page-head__mark {
    display: none;
  }

  .char-card {
    gap: 16px;
  }

  .char-card__glyph {
    width: 104px;
    height: 104px;
    font-size: 58px;
  }

  .char-card__code {
    font-size: 20px;
  }

  .summary td,
  .summary th {
    padding: 8px 6px;
  }
}
</style>
