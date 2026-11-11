import { isGb2312Char } from './gb2312'
import type { LegacyEncodingId, LegacyResult } from '@/types/encoding'

/**
 * 浏览器原生只提供 UTF-8 编码器，但 TextDecoder 支持按 GBK / Big5 解码。
 * 这里用「反向索引」把双字节合法区段的解码结果映射回字节，得到字符 → 字节的编码能力。
 * 索引只在首次使用时构建（GBK 约 24k 项 / Big5 约 20k 项，实测 < 30ms）。
 *
 * Phase 2 将由后端 Python codecs 提供权威结果，此实现届时作为离线兜底。
 */
const indexCache = new Map<'gbk' | 'big5', Map<string, number[]>>()

function buildIndex(encoding: 'gbk' | 'big5'): Map<string, number[]> {
  const cached = indexCache.get(encoding)
  if (cached) return cached

  const decoder = new TextDecoder(encoding)
  const map = new Map<string, number[]>()

  for (let lead = 0x81; lead <= 0xfe; lead += 1) {
    for (let trail = 0x40; trail <= 0xfe; trail += 1) {
      if (trail === 0x7f) continue // GBK / Big5 均不使用 0x7F 作为尾字节
      const char = decoder.decode(new Uint8Array([lead, trail]))
      if (char.length === 1 && char !== '�' && !map.has(char)) {
        map.set(char, [lead, trail])
      }
    }
  }

  indexCache.set(encoding, map)
  return map
}

function asciiBytes(char: string): number[] | null {
  const codePoint = char.codePointAt(0)
  return codePoint !== undefined && codePoint < 0x80 ? [codePoint] : null
}

function encodeWith(encoding: 'gbk' | 'big5', char: string): number[] | null {
  const ascii = asciiBytes(char)
  if (ascii) return ascii
  return buildIndex(encoding).get(char) ?? null
}

export function encodeLegacy(char: string, encoding: LegacyEncodingId): LegacyResult {
  if (!char) return { bytes: null, available: false }

  if (encoding === 'gb2312') {
    const bytes = encodeWith('gbk', char)
    if (!bytes) {
      return { bytes: null, available: false, note: '不在 GBK 字符集内，因此也不在 GB2312 内' }
    }
    if (bytes.length === 1) {
      return { bytes, available: true, note: 'ASCII 单字节，GB2312 与 GBK 共用' }
    }
    return isGb2312Char(char)
      ? { bytes, available: true }
      : { bytes: null, available: false, note: '位于 GBK 扩展区，GB2312 未收录' }
  }

  if (encoding === 'gbk') {
    const bytes = encodeWith('gbk', char)
    return bytes
      ? { bytes, available: true }
      : { bytes: null, available: false, note: '不在 GBK 字符集内' }
  }

  const bytes = encodeWith('big5', char)
  return bytes
    ? { bytes, available: true }
    : { bytes: null, available: false, note: '不在 Big5 / HKSCS 字符集内（Big5 以繁体字为主）' }
}
