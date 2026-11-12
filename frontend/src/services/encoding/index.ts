import { encodeLegacy } from './legacy'
import { planeNameOf, planeOf, unicodeBlockOf } from './unicodeBlocks'
import { apiFetch } from '@/services/api'
import type {
  CharDescription,
  EncodingAggregate,
  LegacyEncodingId,
  LegacyResult,
  TextSummary,
  Utf16Unit,
  Utf8BytePart,
} from '@/types/encoding'

const LEGACY_IDS: LegacyEncodingId[] = ['gb2312', 'gbk', 'big5']

export const ENCODING_LABELS: Record<string, string> = {
  unicode: 'Unicode',
  utf8: 'UTF-8',
  utf16: 'UTF-16',
  gb2312: 'GB2312',
  gbk: 'GBK',
  big5: 'Big5',
}

export function formatHexBytes(bytes: number[]): string {
  return bytes.map((byte) => byte.toString(16).toUpperCase().padStart(2, '0')).join(' ')
}

export function formatBinaryByte(byte: number): string {
  return byte.toString(2).padStart(8, '0')
}

export function describeChar(char: string): CharDescription {
  const codePoint = char.codePointAt(0) ?? 0

  const utf8Bytes = Array.from(new TextEncoder().encode(char))
  const utf8Parts: Utf8BytePart[] = utf8Bytes.map((byte, index) => {
    const binary = formatBinaryByte(byte)
    // 首字节标记位：1 字节 "0" / 2 字节 "110" / 3 字节 "1110" / 4 字节 "11110"
    // 续字节标记位固定为 "10"
    const markerLength = index === 0 ? (utf8Bytes.length === 1 ? 1 : utf8Bytes.length + 1) : 2
    return {
      byte,
      binary,
      marker: binary.slice(0, markerLength),
      data: binary.slice(markerLength),
      isContinuation: index > 0,
    }
  })

  const units: Utf16Unit[] = []
  for (let i = 0; i < char.length; i += 1) {
    const value = char.charCodeAt(i)
    units.push({
      value,
      hex: value.toString(16).toUpperCase().padStart(4, '0'),
      binary: value.toString(2).padStart(16, '0'),
    })
  }

  const bytesLE = units.flatMap((unit) => [unit.value & 0xff, (unit.value >> 8) & 0xff])
  const bytesBE = units.flatMap((unit) => [unit.value >> 8, unit.value & 0xff])

  const legacy = Object.fromEntries(
    LEGACY_IDS.map((id) => [id, encodeLegacy(char, id)]),
  ) as Record<LegacyEncodingId, LegacyResult>

  return {
    char,
    codePoint,
    unicodeHex: codePoint.toString(16).toUpperCase().padStart(4, '0'),
    binary: codePoint.toString(2).padStart(codePoint <= 0xffff ? 16 : 21, '0'),
    plane: planeOf(codePoint),
    planeName: planeNameOf(codePoint),
    block: unicodeBlockOf(codePoint),
    utf8: {
      bytes: utf8Bytes,
      text: formatHexBytes(utf8Bytes),
      parts: utf8Parts,
    },
    utf16: {
      units,
      bytesLE,
      bytesBE,
      isSurrogatePair: units.length === 2,
    },
    legacy,
  }
}

function aggregate(
  label: string,
  descriptions: CharDescription[],
  getBytes: (description: CharDescription) => number[] | null,
): EncodingAggregate {
  let bytes = 0
  let covered = 0
  const missing = new Set<string>()

  for (const description of descriptions) {
    const value = getBytes(description)
    if (value) {
      bytes += value.length
      covered += 1
    } else {
      missing.add(description.char.trim() === '' ? '空格' : description.char)
    }
  }

  return {
    label,
    bytes,
    covered,
    total: descriptions.length,
    missing: Array.from(missing),
  }
}

/** 整段文本的编码汇总，用于对比器底部的对照表 */
export function summarizeText(text: string): TextSummary {
  const descriptions = Array.from(text).map(describeChar)

  return {
    utf8: aggregate('UTF-8', descriptions, (d) => d.utf8.bytes),
    utf16: aggregate('UTF-16', descriptions, (d) => d.utf16.bytesLE),
    gb2312: aggregate('GB2312', descriptions, (d) => d.legacy.gb2312.bytes),
    gbk: aggregate('GBK', descriptions, (d) => d.legacy.gbk.bytes),
    big5: aggregate('Big5', descriptions, (d) => d.legacy.big5.bytes),
  }
}

/**
 * 在线调用后端 Python codecs（权威口径）。失败抛错，由调用方回退本地 describeChar。
 * 对应 backend/app/api/routes/encoding.py 的 POST /encoding/describe。
 */
export async function describeCharRemote(char: string): Promise<CharDescription> {
  return apiFetch<CharDescription>('/encoding/describe', {
    method: 'POST',
    body: JSON.stringify({ char }),
  })
}

/** 在线调用后端整段文本编码汇总（权威口径），失败由调用方回退本地 summarizeText。 */
export async function summarizeTextRemote(text: string): Promise<TextSummary> {
  return apiFetch<TextSummary>('/encoding/summarize', {
    method: 'POST',
    body: JSON.stringify({ text }),
  })
}

export { unicodeBlockOf, planeOf, planeNameOf }
