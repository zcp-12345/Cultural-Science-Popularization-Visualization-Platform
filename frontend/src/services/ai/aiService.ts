import { describeChar } from '@/services/encoding'
import { sleep } from '@/services/mock/delay'
import { parseSse } from '@/services/ai/sse'
import type { AiContext } from '@/types/ai'

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'

// ---------------------------------------------------------------------------
// 离线兜底（mock）回答：仅在 AI 服务不可达时启用，与 Phase 1 的人工答案保持一致。
// ---------------------------------------------------------------------------

interface CannedAnswer {
  match: RegExp
  answer: string
}

const DISCLAIMER =
  '\n\n> 当前为离线兜底回答（未连接 AI 服务）。服务连通后，将由 DeepSeek + RAG 基于知识库检索生成并标注来源。'

const CANNED: CannedAnswer[] = [
  {
    match: /utf-?8|三个字节|3个字节|三字节/i,
    answer:
      'UTF-8 是变长编码：ASCII 占 1 字节，常用汉字占 3 字节，扩展 B 区等生僻字占 4 字节。3 字节汉字的第一字节以「1110」开头，后两个字节都以「10」开头——这些前缀就是解码器识别边界的「暗号」。注意别把「字符集」与「字节数」混为一谈：单个常用汉字在 UTF-16 里只要 2 字节，比 UTF-8 的 3 字节更省；但英文文本在 UTF-8 里只占 1 字节，实际谁更省取决于文本构成。',
  },
  {
    match: /浏览器.*(gbk|big5|gb2312|编码)|(gbk|big5|gb2312).*浏览器|反向索引|textdecoder/i,
    answer:
      '浏览器原生没有 GBK/Big5 编码器，但 TextDecoder 能解码这些字符集。代码用双字节合法区段（首字节 0x81–0xFE、尾字节 0x40–0xFE）建「字符→字节」反向索引，首次约 20–30ms 后缓存；GB2312 用 Python codecs 生成的权威字符集判定，Phase 2 起全部改由后端 Python codecs 给权威结果。密钥只放后端，VITE_* 变量会打进前端包，不能放 DeepSeek key。',
  },
  {
    match: /gb2312|gbk|gb18030|国标/i,
    answer:
      '三者的关系是「逐层扩容」：GB2312（1980）收录 6763 个汉字，是简体中文的早期国家标准；GBK（1995）扩展到 21003 个汉字，并兼容 GB2312；GB18030 覆盖 Unicode 全部码位，其 2022 版已于 2023 年 8 月起强制实施。所以「GB2312 能编码」一定「GBK 能编码」，反过来不成立——比如「镕」只在 GBK 扩展区，GB2312 就查无此字。',
  },
  {
    match: /unicode|码位|码点|u\+/i,
    answer:
      'Unicode 是字符集（给每个字符分配唯一码位，如「中」= U+4E2D），UTF-8 / UTF-16 才是具体的编码方式（把码位变成字节）。这是最容易混淆的一点：Unicode 回答「你是几号」，UTF-8 回答「你被写成哪几个字节」。透视镜的第一步「查户口」查的是码位，第三步「装箱子」才是在做 UTF-8 编码。',
  },
  {
    match: /甲骨文|商代|占卜|刻辞/i,
    answer:
      '甲骨文是商代晚期刻在龟甲、兽骨上的文字，以占卜记录（卜辞）为主，也有记事刻辞、表谱刻辞和习刻，1899 年由王懿荣发现，是目前所见最早的成熟汉字体系。它已经具备象形、指事、会意、形声等造字方法，并不是「图画」的简单堆叠。把它放进时间轴，是理解「隶变」之前古文字形态的最佳起点。',
  },
  {
    match: /简体|简化字|汉字简化|简繁/i,
    answer:
      '简体字是 1956 年《汉字简化方案》、1964 年《简化字总表》之后的现代规范字形，属于文字政策与正字法节点，不是「进化终点」。多数简体字保留表意或读音线索，也有符号替代（「汉」「鸡」的「又」）、同音替代（「后」「面」）和草书楷化；繁体在台湾、香港仍是日常正体。产品把简体字放在时间轴末端，是叙事上的「现代节点」，不代表它比繁体更高级。',
  },
  {
    match: /big5|繁体|台湾|香港|龍|码.*big5/i,
    answer:
      'Big5 是 1984 年台湾制定的繁体中文传统字符集，传统收录约 1.3 万个字，以繁体为主。浏览器实现的 Big5 解码器通常包含 HKSCS（香港增补字符集）扩展，所以「龙」这类简体字在浏览器里可能查到编码；传统 Big5 表与 Python 的 big5 通常不含。「码」这类字仍不在其中。最直观的方式是在编码对比器里同时输入「龙」「龍」「码」对照。',
  },
  {
    match: /行书|草书|六段|6段|几个.*段|为什么.*段/i,
    answer:
      '时间轴选的是「正体/主流书写形态」的六个代表节点：甲骨文、金文、小篆、隶书、楷书、简体字，每一段对应一次明显的书体或制度变化。行书、草书是日常手写体，与正体并行发展、不是替代关系，放进同一条线会让「正体演变」叙事失焦；石鼓文、战国文字等也被并入相邻节点。这是教学抽象，不是全集。',
  },
  {
    match: /演变|隶变|小篆|金文|楷书|主线/i,
    answer:
      '教学上常把书体主线概括为：甲骨文 → 金文 → 小篆 → 隶书 → 楷书。这不是单线进化，各体长期并存：隶变发生在战国晚期至秦汉，把圆转的篆书线条拉直、解散，汉字从此由「古文字」进入「今文字」，是古今文字的分水岭；小篆是秦「书同文」的规范形态，楷书在魏晋成熟、唐代定型。1956 年《汉字简化方案》则是现代的用字规范事件。',
  },
  {
    match: /等比|比例|等距|真实时间|年代.*比例|比例.*年代/i,
    answer:
      '时间轴按朝代/节点等距排列，不是按真实年份比例：甲骨文到秦跨越约一千年，唐到现代也有一千多年，但节点间距相同，否则早期节点会挤在一起、现代节点被拉得很长。页面已标注「按朝代等距排列，非等比时间」，真实年代仍写在每个节点的 period 里，不会误导观众。',
  },
  {
    match: /emoji|表情|字素簇|grapheme|变体选择|zwj|😀/i,
    answer:
      '不一定「一个 emoji = 一个字符」。U+1F600 笑脸在 UTF-8 里占 4 字节、UTF-16 用代理对；而家庭组合 emoji 由多个码位加 ZWJ（零宽连接符）拼成，肤色、国旗还会叠加变体选择符或区域指示符。所以统计「字符数」时要区分码位、码元和字素簇，不能简单按字节或 length 算。',
  },
  {
    match: /代理对|surrogate|扩展\s*b|生僻字|𠮷|码元/i,
    answer:
      '「𠮷」这类超出基本多文种平面（BMP）的字符，UTF-16 必须用两个码元组成的「代理对」表示：高位 D800–DBFF、低位 DC00–DFFF，具体是 D842 DFB7；UTF-8 则需要 4 个字节，首字节以「11110」开头。这也是为什么「一个汉字 = 两个字节」只在常用字范围内成立——字符集边界之外，规则会变。',
  },
  {
    match: /length|charAt|charCodeAt|字符串长度|字符数|长度/i,
    answer:
      'JavaScript 字符串按 UTF-16 码元计数，不按 Unicode 码位。「中」是一个码元，length 为 1；「𠮷」是代理对，length 为 2，直接用 charAt 会拿到半个代理。正确做法是用 Array.from、for...of 或 codePointAt 按码位遍历，产品的输入框和逐字选择就是用 Array.from 处理的。',
  },
  {
    match: /乱码|mojibake|问号|显示不出|缺字|方框/i,
    answer:
      '乱码几乎都来自「编码/解码双方用了不同字符集」：比如浏览器按 UTF-8 解码一段 GBK 字节，就会得到一串�或古怪汉字；而显示方框、空白通常是「字体缺字」或「字符集不支持」，那是缺字，不是乱码。排查顺序：先看响应头 Content-Type 的 charset，再看文件是否真的按该编码保存，最后才看字体是否覆盖该字。',
  },
  {
    match: /三步|变身|透视镜|原理/i,
    answer:
      '三步变身对应三个概念：第一步「查户口」——在 Unicode 里找到码位（如 U+4E2D）；第二步「变数字」——把码位写成二进制；第三步「装箱子」——按 UTF-8 规则加上前缀标记，拆成 1–4 个字节，常用汉字通常是 3 个。紫色前缀是解码器识别边界的「暗号」，绿色部分才是真正的数据位。',
  },
  {
    match: /rag|架构|三层|fastapi|后端|技术栈|deepseek/i,
    answer:
      '产品是三层架构：Vue3 前端负责可视化与交互；FastAPI + PostgreSQL 后端负责汉字数据、编码转换与用户系统；AI 层用 RAG + DeepSeek。RAG 先把已审校的编码/演变知识切块做向量索引，提问时检索 top-k 片段再交给 DeepSeek 生成并要求标注来源，这样知识更新只改知识库、回答可追溯，检索不到时明确说「不知道」。',
  },
  {
    match: /胡编|幻觉|可信|准确|出错|保证|引用|来源/i,
    answer:
      '控制分三层：只摄入已审校文案、检索不到就拒答或转人工、回答带引用来源，UI 还显式标注「AI 生成」。Phase 1 的约 20 条回答是人工写的 mock，不是模型实时生成，评委即兴追问冷知识时可能落到泛化回答，这是已知缺口；Phase 3 会增加评测集和引用校验，但不能承诺 100% 不出错。',
  },
  {
    match: /ocr|识字|拍照|图片识别/i,
    answer:
      '现代印刷体或手写体 OCR 可以用 PaddleOCR 等成熟引擎，先转文字再交给大模型纠错和讲解，成本和准确率更可控。古文字 OCR（甲骨文、金文）属于研究级难题：字形变体多、拓片噪声大、标注数据少，现有准确率不足以支撑现场演示，建议列为 stretch。DeepSeek 常用的对话接口是文本模型，不能假设它能直接「看图识甲骨」。',
  },
  {
    match: /版权|授权|拓片|素材|字体|许可/i,
    answer:
      '编码数据来自 Unicode 字符数据库、Python codecs 和 GB 系列标准，Phase 2 由后端统一生成权威表；字形素材目前没有直接使用真实拓片，时间轴上是现代字体的大字示意并标注「现代字形示意」，避免冒充古文字。真实甲骨/金文/小篆 SVG 需要逐条记录来源与许可，拿不到授权就显示文字卡；字体本身也有版权，产品目前用系统字体栈规避。',
  },
  {
    match: /汉典|字典|书法|区别|竞品|为什么做这个|定位/i,
    answer:
      '汉典、书法字典、Unicode 查询站各解决一个点：查字义/字形、看书法、查码位，但很少把「编码」和「字形演变」放进同一条叙事。数字考古透视镜用透视镜三步讲「形→数」，用时间轴讲「形→变」，再用对比器和 AI 笔记把两条线串起来，定位是科普演示而不是字典工具——差异不在数据量，而在把抽象编码变成可看、可扫、可问的现场体验。',
  },
  {
    match: /网络|断网|手机|演示|比赛|现场|录屏|离线/i,
    answer:
      '演示兜底分三层：静态前端走 CDN 并预加载关键页面；`?ai=1` 深链可直接打开 AI 面板、减少现场点击，`?demo=1` 自动播放已列入计划；再准备断网录屏和本地构建包，避免依赖 Render 冷启动和实时 AI。手机端有底部 TabBar、点按固定透视镜、AI 抽屉全屏适配，但触屏没有 hover，演示脚本要改成「点按汉字」而不是「移动光标」。比赛规则允许联网再开 live，否则全程 mock/本地。',
  },
  {
    match: /你是谁|你好|在吗|hi|hello|嗨/i,
    answer:
      '我是这个产品的 AI 考古助手。可以问我汉字编码（Unicode / UTF-8 / GBK / Big5）、字形演变（甲骨文到楷书），或者产品接下来的架构安排。当前回答若服务未连通会回退到本地兜底，连通后由 DeepSeek + RAG 生成并标注来源。',
  },
]

const FALLBACK = [
  '我在。可以问我汉字编码（Unicode / UTF-8 / GBK / Big5）、字形演变（甲骨文到楷书），或者这个产品接下来的架构安排。',
  '这个问题更适合知识库来回答。当前先离线陪你聊聊编码与演变的基础知识——比如「UTF-8 为什么汉字要占 3 个字节？」',
]

function pickAnswer(question: string, context: AiContext): string {
  const hit = CANNED.find((item) => item.match.test(question))
  if (hit) return hit.answer

  const charLine = context.char
    ? `你刚刚扫描的「${context.char}」码位是 ${describeChar(context.char).unicodeHex}。`
    : ''
  return `${charLine}${FALLBACK[question.length % FALLBACK.length]}`
}

/** 离线兜底：保持 Phase 1 的人工答案，作为 AI 服务不可达时的降级路径。 */
export async function* mockReply(
  question: string,
  context: AiContext,
  signal: AbortSignal,
): AsyncGenerator<string> {
  await sleep(420 + Math.floor(Math.random() * 280), signal)

  const full = pickAnswer(question, context) + DISCLAIMER
  const chars = Array.from(full)

  for (let index = 0; index < chars.length; index += 2) {
    const chunk = chars.slice(index, index + 2).join('')
    yield chunk
    await sleep(14 + Math.floor(Math.random() * 26), signal)
  }
}

// ---------------------------------------------------------------------------
// 在线主路径：POST /api/v1/ai/chat（SSE），解析后端 token 帧后逐段产出。
// ---------------------------------------------------------------------------

function isAbortError(error: unknown): boolean {
  return error instanceof DOMException && error.name === 'AbortError'
}

async function* streamReplyRemote(
  question: string,
  context: AiContext,
  signal: AbortSignal,
): AsyncGenerator<string> {
  const response = await fetch(`${BASE_URL}/ai/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      question,
      page: context.page,
      char: context.char ?? null,
    }),
    credentials: 'include',
    signal,
  })

  if (!response.ok || !response.body) {
    let detail = ''
    try {
      const body = (await response.json()) as { detail?: unknown }
      if (typeof body.detail === 'string') detail = body.detail
    } catch {
      // 无 JSON 错误体，保留默认文案
    }
    throw new Error(detail || `AI 服务不可用（${response.status}）`)
  }

  for await (const event of parseSse(response.body)) {
    if (event.type === 'token' && event.text) {
      yield event.text
    }
  }
}

/**
 * Phase 3 主入口：在线走 SSE，服务不可达时回退离线 mock。
 * 接口签名与 Phase 1 保持一致，消费方（stores/chat.ts）无需改动。
 */
export async function* streamReply(
  question: string,
  context: AiContext,
  signal: AbortSignal,
): AsyncGenerator<string> {
  let yieldedRemote = false
  try {
    for await (const chunk of streamReplyRemote(question, context, signal)) {
      yieldedRemote = true
      yield chunk
    }
  } catch (error) {
    if (isAbortError(error)) throw error
    // 已产出部分在线 token 后失败：把错误抛给消费方，避免混入 mock 文本
    if (yieldedRemote) throw error
    // 尚未产出任何 token 即失败：回退离线 mock
  }

  if (!yieldedRemote) {
    yield* mockReply(question, context, signal)
  }
}
