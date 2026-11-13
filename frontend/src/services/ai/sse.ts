/**
 * SSE（text/event-stream）解析器，用于消费后端 `POST /ai/chat` 的流式响应。
 *
 * 后端约定：每个事件一帧 `data: {"type":"token","text":"..."}`，
 * 结束帧为 `data: {"type":"done"}`，帧与帧之间以空行分隔。
 */
export type AiStreamEvent = { type: 'token'; text: string } | { type: 'done' }

function parseEvent(payload: string): AiStreamEvent | null {
  try {
    const parsed = JSON.parse(payload) as { type?: unknown; text?: unknown }
    if (parsed.type === 'token' && typeof parsed.text === 'string') {
      return { type: 'token', text: parsed.text }
    }
    if (parsed.type === 'done') {
      return { type: 'done' }
    }
  } catch {
    // 非 JSON / 未知事件类型，跳过该帧
  }
  return null
}

/** 处理一行，命中事件边界时返回解析出的事件，否则返回 null。 */
function consumeLine(line: string, dataLines: string[]): AiStreamEvent | null {
  if (line === '') {
    if (dataLines.length === 0) return null
    const payload = dataLines.join('\n')
    dataLines.length = 0
    return parseEvent(payload)
  }

  if (line.startsWith('data:')) {
    // SSE 规范：冒号后若紧跟单个空格则去除；其余字段（event/id/retry/注释）忽略
    let value = line.slice(5)
    if (value.startsWith(' ')) value = value.slice(1)
    dataLines.push(value)
  }
  return null
}

/**
 * 从 ReadableStream 逐事件产出 token / done。
 * 用流式 TextDecoder 兜住跨 chunk 的断行，兼容 \r\n 与 \n。
 */
export async function* parseSse(
  stream: ReadableStream<Uint8Array>,
): AsyncGenerator<AiStreamEvent> {
  const reader = stream.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''
  const dataLines: string[] = []

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })

      let index: number
      while ((index = buffer.indexOf('\n')) !== -1) {
        const line = buffer.slice(0, index).replace(/\r$/, '')
        buffer = buffer.slice(index + 1)
        const event = consumeLine(line, dataLines)
        if (event) yield event
      }
    }

    // 流结束：清空残留（后端正常以空行结尾，此处兜底处理无结尾换行的情况）
    buffer += decoder.decode()
    if (buffer) {
      const event = consumeLine(buffer.replace(/\r$/, ''), dataLines)
      if (event) yield event
    }
    const lastEvent = consumeLine('', dataLines)
    if (lastEvent) yield lastEvent
  } finally {
    reader.releaseLock()
  }
}
