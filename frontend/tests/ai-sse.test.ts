import { afterEach, describe, expect, it, vi } from 'vitest'
import { parseSse, type AiStreamEvent } from '@/services/ai/sse'
import { streamReply } from '@/services/ai/aiService'

// 离线 mock 的逐块 sleep 只是演示用，测试里让它立即返回，避免随机延时拖慢/抖动用例。
vi.mock('@/services/mock/delay', () => ({ sleep: async () => {} }))

function sseResponse(chunks: string[]): Response {
  const encoder = new TextEncoder()
  const body = new ReadableStream<Uint8Array>({
    start(controller) {
      for (const chunk of chunks) controller.enqueue(encoder.encode(chunk))
      controller.close()
    },
  })
  return new Response(body, { status: 200, headers: { 'Content-Type': 'text/event-stream' } })
}

async function collect(generator: AsyncGenerator<string>): Promise<string> {
  let out = ''
  for await (const chunk of generator) out += chunk
  return out
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('parseSse', () => {
  it('解析 token / done 事件', async () => {
    const stream = sseResponse([
      'data: {"type":"token","text":"你好"}\n\n',
      'data: {"type":"token","text":"世界"}\n\n',
      'data: {"type":"done"}\n\n',
    ]).body!

    const events: AiStreamEvent[] = []
    for await (const event of parseSse(stream)) events.push(event)

    expect(events).toEqual([
      { type: 'token', text: '你好' },
      { type: 'token', text: '世界' },
      { type: 'done' },
    ])
  })

  it('跨 chunk 边界与 CRLF 都能正确拆帧', async () => {
    const stream = sseResponse([
      'data: {"type":"to',
      'ken","text":"中',
      '文"}\r\n',
      '\r\ndata: {"type":"done"}\r\n\r\n',
    ]).body!

    const events: AiStreamEvent[] = []
    for await (const event of parseSse(stream)) events.push(event)

    expect(events).toEqual([
      { type: 'token', text: '中文' },
      { type: 'done' },
    ])
  })

  it('忽略未知事件与注释/冒号行', async () => {
    const stream = sseResponse([
      ': keep-alive\n\n',
      'data: {"type":"unknown","text":"跳过"}\n\n',
      'data: {"type":"token","text":"仅此"}\n\n',
      'data: {"type":"done"}\n\n',
    ]).body!

    const events: AiStreamEvent[] = []
    for await (const event of parseSse(stream)) events.push(event)

    expect(events).toEqual([{ type: 'token', text: '仅此' }, { type: 'done' }])
  })
})

describe('streamReply', () => {
  it('在线返回后端 token 流，并按契约传参', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      sseResponse([
        'data: {"type":"token","text":"UTF-8 "}\n\n',
        'data: {"type":"token","text":"汉字 3 字节"}\n\n',
        'data: {"type":"done"}\n\n',
      ]),
    )
    vi.stubGlobal('fetch', fetchMock)

    const out = await collect(
      streamReply('UTF-8 为什么汉字占 3 字节', { page: '透视镜' }, new AbortController().signal),
    )

    expect(out).toBe('UTF-8 汉字 3 字节')
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/ai/chat',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ question: 'UTF-8 为什么汉字占 3 字节', page: '透视镜', char: null }),
      }),
    )
  })

  it('后端不可用（503）时回退离线 mock', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: 'AI 服务未启用' }), {
          status: 503,
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
    )

    const out = await collect(
      streamReply('UTF-8 为什么汉字占 3 个字节', { page: '透视镜' }, new AbortController().signal),
    )

    expect(out).toContain('UTF-8 是变长编码')
    expect(out).toContain('离线兜底')
  })

  it('网络异常时回退离线 mock', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('network error')))

    const out = await collect(
      streamReply('GB2312 和 GBK 有什么区别', { page: '对比器' }, new AbortController().signal),
    )

    expect(out).toContain('GB2312（1980）')
  })

  it('用户中断抛出的 AbortError 不回退 mock，直接向上抛', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new DOMException('Aborted', 'AbortError')))

    const generator = streamReply('你好', { page: '透视镜' }, new AbortController().signal)
    await expect(generator.next()).rejects.toMatchObject({ name: 'AbortError' })
  })

  it('已产出 token 后流中断：抛出错误而不拼接 mock', async () => {
    const encoder = new TextEncoder()
    let pulls = 0
    const body = new ReadableStream<Uint8Array>({
      // 第一次 pull 产出一个 token 帧，第二次 pull 才报错，模拟「中途断流」
      pull(controller) {
        pulls += 1
        if (pulls === 1) {
          controller.enqueue(encoder.encode('data: {"type":"token","text":"部分"}\n\n'))
        } else {
          controller.error(new Error('connection reset'))
        }
      },
    })
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(body, { status: 200 })))

    await expect(
      collect(streamReply('你好', { page: '透视镜' }, new AbortController().signal)),
    ).rejects.toThrow('connection reset')
  })
})
