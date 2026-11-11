export type LegacyEncodingId = 'gb2312' | 'gbk' | 'big5'

export interface Utf8BytePart {
  byte: number
  binary: string
  marker: string
  data: string
  isContinuation: boolean
}

export interface Utf16Unit {
  value: number
  hex: string
  binary: string
}

export interface LegacyResult {
  bytes: number[] | null
  available: boolean
  note?: string
}

export interface CharDescription {
  char: string
  codePoint: number
  unicodeHex: string
  binary: string
  plane: number
  planeName: string
  block: string
  utf8: {
    bytes: number[]
    text: string
    parts: Utf8BytePart[]
  }
  utf16: {
    units: Utf16Unit[]
    bytesLE: number[]
    bytesBE: number[]
    isSurrogatePair: boolean
  }
  legacy: Record<LegacyEncodingId, LegacyResult>
}

export interface EncodingAggregate {
  label: string
  bytes: number
  covered: number
  total: number
  missing: string[]
}

export interface TextSummary {
  utf8: EncodingAggregate
  utf16: EncodingAggregate
  gb2312: EncodingAggregate
  gbk: EncodingAggregate
  big5: EncodingAggregate
}
