<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import AppIcon from '@/components/ui/AppIcon.vue'
import { useArchaeologyStore } from '@/stores/archaeology'
import { useChatStore } from '@/stores/chat'
import { useUiStore } from '@/stores/ui'
import type { AiContext } from '@/types/ai'

const ui = useUiStore()
const chat = useChatStore()
const archaeology = useArchaeologyStore()
const route = useRoute()

const draft = ref('')
const scroller = ref<HTMLElement | null>(null)
const drawer = ref<HTMLElement | null>(null)
const closeBtn = ref<HTMLButtonElement | null>(null)
const composer = ref<HTMLTextAreaElement | null>(null)
let lastFocused: HTMLElement | null = null

const pageName = computed(() => (route.meta.title as string | undefined) ?? '透视镜')
const context = computed<AiContext>(() => ({
  page: pageName.value,
  char: archaeology.currentChar || undefined,
}))

const suggestions = [
  'UTF-8 为什么汉字要占 3 个字节？',
  'GB2312 和 GBK 有什么区别？',
  '甲骨文和简体字之间发生了什么？',
  '「码」在 Big5 里为什么没有编码？',
]

function scrollToBottom(force = false) {
  const el = scroller.value
  if (!el) return
  if (force || el.scrollHeight - el.scrollTop - el.clientHeight < 80) {
    el.scrollTop = el.scrollHeight
  }
}

// 仅当用户停留在底部附近时才自动跟随滚动，避免向上翻看历史时被拽回
watch(
  () => chat.messages.map((message) => `${message.id}:${message.content.length}`).join('|'),
  () => nextTick(() => scrollToBottom()),
)

watch(
  () => ui.aiOpen,
  async (open) => {
    document.body.style.overflow = open ? 'hidden' : ''
    if (open) {
      lastFocused = document.activeElement as HTMLElement | null
      await nextTick()
      closeBtn.value?.focus()
      scrollToBottom(true)
    } else {
      chat.stop()
      lastFocused?.focus()
      lastFocused = null
    }
  },
)

// 支持 /ai 深链与 ?ai=1，便于演示直接打开面板
watch(
  () => route.query.ai,
  (value) => {
    if (value === '1') ui.openAi()
  },
  { immediate: true },
)

function submit(text?: string) {
  const value = text ?? draft.value
  if (!value.trim() || chat.isStreaming) return
  draft.value = ''
  void chat.send(value, context.value)
  nextTick(() => composer.value?.focus())
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
    event.preventDefault()
    submit()
  }
}

function handleEscape(event: KeyboardEvent) {
  if (event.key === 'Escape' && !event.isComposing && ui.aiOpen) ui.closeAi()
}

function trapFocus(event: KeyboardEvent) {
  if (event.key !== 'Tab') return
  const focusables = drawer.value?.querySelectorAll<HTMLElement>(
    'button:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
  )
  if (!focusables || focusables.length === 0) return
  const first = focusables[0]
  const last = focusables[focusables.length - 1]
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault()
    last.focus()
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault()
    first.focus()
  }
}

onMounted(() => window.addEventListener('keydown', handleEscape))

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleEscape)
  document.body.style.overflow = ''
})
</script>

<template>
  <Teleport to="body">
    <Transition name="drawer">
      <div v-if="ui.aiOpen" class="ai-layer" @click.self="ui.closeAi()">
        <aside
          id="ai-drawer"
          ref="drawer"
          class="ai-drawer"
          role="dialog"
          aria-modal="true"
          aria-label="AI 考古助手"
          @keydown="trapFocus"
        >
          <header class="ai-drawer__head">
            <div class="ai-drawer__title">
              <span class="ai-drawer__orb">
                <AppIcon name="spark" :size="18" />
              </span>
              <div>
                <h2>AI 考古助手</h2>
                <p><i class="status-dot"></i>在线 · DeepSeek + RAG</p>
              </div>
            </div>
            <div class="ai-drawer__actions">
              <button class="icon-btn" type="button" aria-label="清空对话" @click="chat.reset()">
                <AppIcon name="reset" :size="16" />
              </button>
              <button ref="closeBtn" class="icon-btn" type="button" aria-label="关闭 AI 考古助手" @click="ui.closeAi()">
                <AppIcon name="close" :size="18" />
              </button>
            </div>
          </header>

          <div class="ai-context">
            <span class="badge">页面 · {{ pageName }}</span>
            <span v-if="archaeology.currentChar" class="badge badge--gold">最近扫描 · {{ archaeology.currentChar }}</span>
            <span v-else class="badge badge--muted">未扫描</span>
          </div>

          <div
            ref="scroller"
            class="ai-messages"
            role="log"
            aria-live="polite"
            :aria-busy="chat.isStreaming"
            tabindex="0"
          >
            <div
              v-for="message in chat.messages"
              :key="message.id"
              :class="['msg', `msg--${message.role}`]"
            >
              <span v-if="message.role === 'assistant'" class="msg__avatar">
                <AppIcon name="lens" :size="14" />
              </span>
              <div class="msg__bubble">
                <span v-if="message.role === 'assistant'" class="msg__tag">AI 生成</span>
                <p class="msg__text">{{ message.content }}<span v-if="message.streaming && message.content" class="stream-caret"></span></p>
                <p v-if="message.streaming && !message.content" class="typing" aria-label="正在输入">
                  <i></i><i></i><i></i>
                </p>
              </div>
            </div>

            <div v-if="chat.messages.length === 1" class="ai-suggestions">
              <p>试试这些问题</p>
              <button
                v-for="item in suggestions"
                :key="item"
                type="button"
                class="suggestion"
                @click="submit(item)"
              >
                {{ item }}
              </button>
            </div>
          </div>

          <footer class="ai-composer">
            <div class="ai-composer__box">
              <textarea
                ref="composer"
                v-model="draft"
                rows="1"
                maxlength="500"
                aria-label="向 AI 助手提问"
                placeholder="问一个关于汉字编码或演变的问题…"
                @keydown="handleKeydown"
              ></textarea>
              <button
                v-if="chat.isStreaming"
                class="send-btn send-btn--stop"
                type="button"
                aria-label="停止生成"
                @click="chat.stop()"
              >
                <AppIcon name="close" :size="16" />
              </button>
              <button
                v-else
                class="send-btn"
                type="button"
                :disabled="!draft.trim()"
                aria-label="发送"
                @click="submit()"
              >
                <AppIcon name="send" :size="17" />
              </button>
            </div>
            <p class="ai-composer__hint">{{ draft.length }}/500 · Enter 发送 · Shift + Enter 换行</p>
            <p class="ai-composer__notice">内容由 AI 生成，仅供科普参考，不构成学术结论</p>
          </footer>
        </aside>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.ai-layer {
  position: fixed;
  inset: 0;
  z-index: var(--z-drawer);
  display: flex;
  justify-content: flex-end;
  background: rgba(2, 5, 10, 0.55);
  backdrop-filter: blur(3px);
}

.ai-drawer {
  display: flex;
  flex-direction: column;
  width: min(420px, 94vw);
  height: 100%;
  background: var(--c-panel-strong);
  border-left: 1px solid rgba(0, 240, 255, 0.2);
  box-shadow: -24px 0 60px rgba(0, 0, 0, 0.5);
  transition: transform 0.32s var(--ease-out);
}

.drawer-enter-active,
.drawer-leave-active {
  transition: opacity 0.25s ease;
}

.drawer-enter-from,
.drawer-leave-to {
  opacity: 0;
}

.drawer-enter-from .ai-drawer,
.drawer-leave-to .ai-drawer {
  transform: translateX(100%);
}

.ai-drawer__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 16px 18px;
  border-bottom: 1px solid var(--c-line);
}

.ai-drawer__title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.ai-drawer__orb {
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  color: var(--c-cyan);
  background: var(--c-cyan-soft);
  border: 1px solid rgba(0, 240, 255, 0.34);
  box-shadow: 0 0 18px rgba(0, 240, 255, 0.22);
}

.ai-drawer__title h2 {
  margin: 0;
  font-size: 15px;
  letter-spacing: 0.04em;
}

.ai-drawer__title p {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 3px 0 0;
  font-size: 11px;
  color: var(--c-text-faint);
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--c-gold);
  box-shadow: 0 0 8px var(--c-gold);
  animation: pulse 2s ease-in-out infinite;
}

.ai-drawer__actions {
  display: flex;
  gap: 4px;
}

.icon-btn {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--c-text-dim);
  transition:
    color 0.2s ease,
    background 0.2s ease,
    border-color 0.2s ease;
}

.icon-btn:hover {
  color: var(--c-text);
  background: rgba(255, 255, 255, 0.05);
  border-color: var(--c-line);
}

.ai-context {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 10px 18px;
  border-bottom: 1px solid rgba(0, 240, 255, 0.08);
}

.ai-messages {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 18px;
  overflow-y: auto;
  min-height: 0;
}

.msg {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  animation: slide-up 0.3s var(--ease-out);
}

.msg--user {
  flex-direction: row-reverse;
}

.msg__avatar {
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  color: var(--c-cyan);
  background: var(--c-cyan-soft);
  border: 1px solid rgba(0, 240, 255, 0.3);
}

.msg__bubble {
  max-width: 84%;
  padding: 10px 13px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.045);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-top-left-radius: 4px;
  font-size: 13px;
  line-height: 1.72;
}

.msg--user .msg__bubble {
  border-top-left-radius: 14px;
  border-top-right-radius: 4px;
  background: rgba(0, 240, 255, 0.1);
  border-color: rgba(0, 240, 255, 0.22);
  color: var(--c-text);
}

.msg__tag {
  display: inline-block;
  margin-bottom: 5px;
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 9px;
  letter-spacing: 0.08em;
  color: rgba(255, 204, 0, 0.78);
  background: rgba(255, 204, 0, 0.08);
  border: 1px solid rgba(255, 204, 0, 0.18);
}

.msg__text {
  margin: 0;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.stream-caret {
  display: inline-block;
  width: 6px;
  height: 14px;
  margin-left: 2px;
  vertical-align: -2px;
  background: var(--c-cyan);
  animation: blink 0.9s step-end infinite;
}

.typing {
  display: flex;
  gap: 4px;
  margin: 2px 0;
}

.typing i {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--c-cyan);
  opacity: 0.5;
  animation: typing-dot 1s ease-in-out infinite;
}

.typing i:nth-child(2) {
  animation-delay: 0.15s;
}

.typing i:nth-child(3) {
  animation-delay: 0.3s;
}

@keyframes typing-dot {
  0%,
  60%,
  100% {
    opacity: 0.3;
    transform: translateY(0);
  }
  30% {
    opacity: 1;
    transform: translateY(-3px);
  }
}

.ai-suggestions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 4px 4px 0 34px;
}

.ai-suggestions p {
  margin: 0 0 2px;
  font-size: 11px;
  letter-spacing: 0.08em;
  color: var(--c-text-faint);
}

.suggestion {
  padding: 9px 12px;
  text-align: left;
  font-size: 12.5px;
  line-height: 1.5;
  color: var(--c-text-dim);
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(0, 240, 255, 0.12);
  border-radius: 10px;
  transition:
    color 0.2s ease,
    border-color 0.2s ease,
    background 0.2s ease,
    transform 0.2s var(--ease-out);
}

.suggestion:hover {
  color: var(--c-text);
  border-color: rgba(0, 240, 255, 0.4);
  background: rgba(0, 240, 255, 0.06);
  transform: translateX(2px);
}

.ai-composer {
  padding: 12px 16px calc(14px + env(safe-area-inset-bottom, 0px));
  border-top: 1px solid var(--c-line);
  background: rgba(6, 9, 16, 0.55);
}

.ai-composer__box {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  padding: 8px 8px 8px 12px;
  border: 1px solid rgba(0, 240, 255, 0.22);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.03);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.ai-composer__box:focus-within {
  border-color: rgba(0, 240, 255, 0.55);
  box-shadow: 0 0 20px rgba(0, 240, 255, 0.12);
}

.ai-composer textarea {
  flex: 1;
  min-height: 22px;
  max-height: 110px;
  padding: 2px 0;
  border: none;
  background: transparent;
  resize: none;
  font-size: 13px;
  line-height: 1.5;
  outline: none;
}

.ai-composer textarea::placeholder {
  color: var(--c-text-faint);
}

.send-btn {
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 34px;
  height: 34px;
  border: none;
  border-radius: 10px;
  color: #04141a;
  background: linear-gradient(120deg, var(--c-cyan), var(--c-green));
  transition: opacity 0.2s ease, transform 0.2s var(--ease-out);
}

.send-btn:hover:not(:disabled) {
  transform: translateY(-1px);
}

.send-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.send-btn--stop {
  color: #fff;
  background: linear-gradient(120deg, var(--c-red), #ff8fa0);
}

.ai-composer__hint {
  margin: 8px 2px 0;
  font-size: 10.5px;
  color: var(--c-text-faint);
  text-align: center;
}

.ai-composer__notice {
  margin: 4px 2px 0;
  font-size: 10px;
  color: var(--c-text-faint);
  text-align: center;
}

@media (max-width: 720px) {
  .ai-drawer {
    width: 100%;
  }
}
</style>
