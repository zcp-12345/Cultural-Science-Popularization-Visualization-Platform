import { defineStore } from 'pinia'
import { ref } from 'vue'
import { streamReply } from '@/services/ai/aiService'
import type { AiContext, ChatMessage } from '@/types/ai'

function welcomeMessage(): ChatMessage {
  return {
    id: 'welcome',
    role: 'assistant',
    content:
      '你好，我是数字考古助手。可以问我「UTF-8 为什么汉字要占 3 个字节」，或者让我讲讲「甲骨文到楷书」的演变。',
    createdAt: Date.now(),
  }
}

export const useChatStore = defineStore('chat', () => {
  const messages = ref<ChatMessage[]>([welcomeMessage()])
  const isStreaming = ref(false)

  let sequence = 1
  let controller: AbortController | null = null

  async function send(text: string, context: AiContext) {
    // 兜底截断，避免绕过 textarea maxlength 的超长输入（如直接调用 store）
    const question = text.trim().slice(0, 500)
    if (!question || isStreaming.value) return

    messages.value.push({
      id: `user-${sequence++}`,
      role: 'user',
      content: question,
      createdAt: Date.now(),
    })

    messages.value.push({
      id: `assistant-${sequence++}`,
      role: 'assistant',
      content: '',
      createdAt: Date.now(),
      streaming: true,
    })

    // 取回响应式代理，直接修改原始对象不会触发更新
    const reply = messages.value[messages.value.length - 1]

    isStreaming.value = true
    controller = new AbortController()

    try {
      for await (const chunk of streamReply(question, context, controller.signal)) {
        reply.content += chunk
      }
    } catch (error) {
      if (!(error instanceof DOMException && error.name === 'AbortError')) {
        reply.content += '\n\n（回答中断，请重试）'
      }
    } finally {
      reply.streaming = false
      isStreaming.value = false
      controller = null
    }
  }

  function stop() {
    controller?.abort()
  }

  function reset() {
    stop()
    messages.value = [welcomeMessage()]
    isStreaming.value = false
  }

  return { messages, isStreaming, send, stop, reset }
})
