<script setup lang="ts">
import { computed } from 'vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import { useArchaeologyStore } from '@/stores/archaeology'

const archaeology = useArchaeologyStore()

const latest = computed(() => archaeology.notes[0] ?? null)
const announcement = computed(() =>
  latest.value ? `已透视「${latest.value.char}」：码位 U+${latest.value.unicodeHex}，UTF-8 共 ${latest.value.utf8Count} 字节` : '',
)
</script>

<template>
  <aside class="notes panel" aria-label="实时考古笔记">
    <p class="sr-only" role="status">{{ announcement }}</p>
    <header class="notes__head">
      <span class="notes__dot" aria-hidden="true"></span>
      <h2>实时考古笔记</h2>
      <span class="badge badge--muted">MOCK</span>
    </header>

    <div v-if="!archaeology.hasNotes" class="notes__ready">
      <AppIcon name="bulb" :size="30" />
      <strong>系统就绪</strong>
      <p>移动光标扫过左侧正文里的金色汉字，或用键盘 Tab 选中后按回车，见证「三步变身」。</p>
    </div>

    <TransitionGroup v-else name="note" tag="ul" class="notes__list">
      <li v-for="note in archaeology.notes" :key="note.id" class="note">
        <div class="note__head">
          <span class="note__char">{{ note.char }}</span>
          <span class="note__title">汉字「{{ note.char }}」的数字化考古</span>
          <span class="note__code mono">U+{{ note.unicodeHex }}</span>
        </div>

        <dl class="note__steps">
          <div>
            <dt>1 · 查户口</dt>
            <dd>
              Unicode 码位 <b class="mono">U+{{ note.unicodeHex }}</b>
            </dd>
          </div>
          <div>
            <dt>2 · 变数字</dt>
            <dd>
              二进制 <b class="mono">{{ note.binaryPreview }}</b>
            </dd>
          </div>
          <div>
            <dt>3 · 装箱子</dt>
            <dd>
              UTF-8 <b class="mono">{{ note.utf8Count }} 字节</b>
              <span class="mono note__hex">{{ note.utf8Bytes }}</span>
            </dd>
          </div>
        </dl>

        <div class="note__coverage">
          <span :class="['chip', note.gb2312 ? 'chip--on' : 'chip--off']">GB2312 {{ note.gb2312 ? '✓' : '✗' }}</span>
          <span :class="['chip', note.gbk ? 'chip--on' : 'chip--off']">GBK {{ note.gbk ? '✓' : '✗' }}</span>
          <span
            :class="['chip', note.big5 ? 'chip--on' : 'chip--off']"
            title="浏览器 Big5 解码器含 HKSCS 增补字符"
          >Big5 {{ note.big5 ? '✓' : '✗' }}</span>
        </div>
      </li>
    </TransitionGroup>
  </aside>
</template>

<style scoped>
.notes {
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: 16px;
  overflow: hidden;
}

.notes__head {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-bottom: 12px;
  margin-bottom: 12px;
  border-bottom: 1px solid rgba(0, 240, 255, 0.1);
  flex-shrink: 0;
}

.notes__head h2 {
  margin: 0;
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: var(--c-cyan);
}

.notes__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--c-cyan);
  box-shadow: 0 0 10px var(--c-cyan);
  animation: pulse 2s ease-in-out infinite;
}

.notes__head .badge {
  margin-left: auto;
  font-size: 10px;
  padding: 2px 8px;
}

.notes__ready {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  flex: 1;
  padding: 28px 18px;
  text-align: center;
  color: var(--c-text-dim);
  border: 1px dashed rgba(0, 240, 255, 0.16);
  border-radius: var(--radius-sm);
}

.notes__ready strong {
  color: var(--c-gold);
  letter-spacing: 0.08em;
}

.notes__ready p {
  margin: 0;
  font-size: 12.5px;
  line-height: 1.75;
}

.notes__list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin: 0;
  padding: 0 4px 4px 0;
  list-style: none;
  overflow-y: auto;
  min-height: 0;
}

.note {
  padding: 12px;
  border-left: 3px solid var(--c-cyan);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  background: rgba(255, 255, 255, 0.045);
  font-size: 12.5px;
  line-height: 1.65;
}

.note__head {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 8px;
}

.note__char {
  font-family: var(--font-serif);
  font-size: 22px;
  font-weight: 700;
  line-height: 1;
  color: var(--c-gold);
  text-shadow: 0 0 14px rgba(255, 204, 0, 0.45);
}

.note__title {
  font-weight: 700;
  color: var(--c-text);
}

.note__code {
  margin-left: auto;
  font-size: 10.5px;
  color: var(--c-cyan);
}

.note__steps {
  display: grid;
  gap: 4px;
  margin: 0 0 8px;
}

.note__steps div {
  display: flex;
  gap: 8px;
}

.note__steps dt {
  flex-shrink: 0;
  width: 66px;
  color: var(--c-text-faint);
  font-size: 11px;
  letter-spacing: 0.04em;
}

.note__steps dd {
  margin: 0;
  color: var(--c-text-dim);
  min-width: 0;
  overflow-wrap: anywhere;
}

.note__steps b {
  color: var(--c-green);
  font-weight: 600;
}

.note__hex {
  display: block;
  font-size: 10.5px;
  color: var(--c-text-faint);
  letter-spacing: 0.06em;
}

.note__coverage {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.chip {
  padding: 1px 8px;
  border-radius: 999px;
  font-size: 10.5px;
  font-family: var(--font-mono);
  border: 1px solid transparent;
}

.chip--on {
  color: var(--c-green);
  background: rgba(0, 255, 136, 0.08);
  border-color: rgba(0, 255, 136, 0.22);
}

.chip--off {
  color: var(--c-text-faint);
  background: rgba(255, 255, 255, 0.03);
  border-color: rgba(255, 255, 255, 0.07);
  text-decoration: line-through;
  text-decoration-color: rgba(255, 93, 115, 0.5);
}

.note-enter-active {
  transition:
    opacity 0.35s ease,
    transform 0.35s var(--ease-out);
}

.note-enter-from {
  opacity: 0;
  transform: translateX(18px);
}

.note-move {
  transition: transform 0.35s var(--ease-out);
}
</style>
