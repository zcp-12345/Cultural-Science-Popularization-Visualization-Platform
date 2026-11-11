import { describe, expect, it } from 'vitest'
import { describeChar, summarizeText } from '@/services/encoding'

describe('describeChar', () => {
  it('把「中」写成 UTF-8 / UTF-16 / GB2312 / GBK / Big5', () => {
    const d = describeChar('中')

    expect(d.codePoint).toBe(0x4e2d)
    expect(d.unicodeHex).toBe('4E2D')
    expect(d.utf8.bytes).toEqual([0xe4, 0xb8, 0xad])
    expect(d.utf8.parts.map((part) => part.marker)).toEqual(['1110', '10', '10'])
    expect(d.utf16.units).toHaveLength(1)
    expect(d.utf16.isSurrogatePair).toBe(false)
    expect(d.legacy.gb2312.bytes).toEqual([0xd6, 0xd0])
    expect(d.legacy.gbk.bytes).toEqual([0xd6, 0xd0])
    expect(d.legacy.big5.bytes).toEqual([0xa4, 0xa4])
    expect(d.block).toContain('CJK')
  })

  it('处理扩展 B 区的「𠮷」：4 字节 UTF-8 与 UTF-16 代理对', () => {
    const d = describeChar('𠮷')

    expect(d.codePoint).toBe(0x20bb7)
    expect(d.utf8.bytes).toEqual([0xf0, 0xa0, 0xae, 0xb7])
    expect(d.utf8.parts.map((part) => part.marker)).toEqual(['11110', '10', '10', '10'])
    expect(d.utf16.isSurrogatePair).toBe(true)
    expect(d.utf16.units[0].hex).toBe('D842')
    expect(d.utf16.units[1].hex).toBe('DFB7')
    expect(d.legacy.gbk.available).toBe(false)
    expect(d.block).toContain('扩展 B')
  })

  it('ASCII 在传统字符集中保持单字节', () => {
    const d = describeChar('A')

    expect(d.utf8.bytes).toEqual([0x41])
    expect(d.utf8.parts[0].marker).toBe('0')
    expect(d.legacy.gb2312.bytes).toEqual([0x41])
    expect(d.legacy.gbk.bytes).toEqual([0x41])
    expect(d.legacy.big5.bytes).toEqual([0x41])
  })

  it('区分 GBK 扩展区与 GB2312 子集', () => {
    const d = describeChar('镕')

    expect(d.legacy.gbk.available).toBe(true)
    expect(d.legacy.gb2312.available).toBe(false)
  })

  it('呈现简体 / 繁体在 Big5 中的覆盖差异', () => {
    // 注意：浏览器端 Big5 解码器含 HKSCS 增补（例如「龙」「华」可命中），
    // 而 Node 的 ICU 数据不含。测试选取两端口径一致的字，避免环境依赖。
    expect(describeChar('码').legacy.big5.available).toBe(false)
    expect(describeChar('龍').legacy.big5.available).toBe(true)
    expect(describeChar('龍').legacy.gb2312.available).toBe(false)
  })
})

describe('summarizeText', () => {
  it('汇总混合文本的字节数与覆盖情况', () => {
    const summary = summarizeText('中码A')

    expect(summary.utf8.bytes).toBe(3 + 3 + 1)
    expect(summary.utf16.bytes).toBe(2 + 2 + 2)
    expect(summary.gb2312.covered).toBe(3)
    expect(summary.gb2312.missing).toEqual([])
    expect(summary.big5.covered).toBe(2)
    expect(summary.big5.missing).toEqual(['码'])
  })

  it('空文本返回零值', () => {
    const summary = summarizeText('')

    expect(summary.utf8.total).toBe(0)
    expect(summary.utf8.bytes).toBe(0)
    expect(summary.gbk.covered).toBe(0)
  })
})
