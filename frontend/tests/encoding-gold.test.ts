import { describe, expect, it } from 'vitest'
import { describeChar } from '@/services/encoding'
import { isGb2312Char, gb2312CharCount } from '@/services/encoding/gb2312'
import goldData from '@/data/encoding-gold.json'
import gb2312Set from '@/data/gb2312-characters.json'

/** number[] → "E4 B8 AD"；null 保持 null，便于与 Python 金标准直接比对 */
function hexOf(bytes: number[] | null): string | null {
  return bytes === null
    ? null
    : bytes.map((byte) => byte.toString(16).toUpperCase().padStart(2, '0')).join(' ')
}

/** Python `big5` 收录、但 WHATWG/浏览器 `big5` 不收录的 A1 行标点 */
const BIG5_WHATWG_MISSING = new Set(['¥', '•'])

describe('编码金标准（Python codecs 生成）', () => {
  it('GB2312 权威集合规模与抽样', () => {
    expect(gb2312Set.count).toBe(7445)
    expect(gb2312CharCount()).toBe(7445)
    expect(isGb2312Char('中')).toBe(true)
    expect(isGb2312Char('龍')).toBe(false)
    expect(isGb2312Char('镕')).toBe(false)
  })

  it.each(goldData.characters)('逐字对齐 Python codecs：$char ($codePoint)', (entry) => {
    const d = describeChar(entry.char)

    // UTF-8 / UTF-16 两端口径完全一致
    expect(hexOf(d.utf8.bytes)).toBe(entry.utf8)
    expect(hexOf(d.utf16.bytesLE)).toBe(entry.utf16le)
    expect(hexOf(d.utf16.bytesBE)).toBe(entry.utf16be)

    // GB2312 / GBK：前端反向索引结果应与 Python codecs 一致
    expect(hexOf(d.legacy.gb2312.bytes)).toBe(entry.gb2312)
    expect(hexOf(d.legacy.gbk.bytes)).toBe(entry.gbk)

    // Big5 存在两种口径：
    //   1) HKSCS —— Python 无、浏览器 Chrome 有（Node ICU 亦无）→ 本套 Node 测试与 Python 一致；
    //   2) A1 标点行 —— Python `big5` 收录 ¥=A2 44、•=A1 45 等标点，
    //      而 WHATWG/浏览器 `big5` 不收录，前端返回 null。
    // 对第 2 类按浏览器口径断言为 null，其余字按 Python 口径精确比对。
    if (BIG5_WHATWG_MISSING.has(entry.char)) {
      expect(d.legacy.big5.bytes).toBeNull()
    } else {
      expect(hexOf(d.legacy.big5.bytes)).toBe(entry.big5)
    }
  })
})
