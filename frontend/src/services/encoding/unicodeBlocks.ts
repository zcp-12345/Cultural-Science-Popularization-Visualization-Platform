interface BlockRange {
  start: number
  end: number
  name: string
}

const BLOCKS: BlockRange[] = [
  { start: 0x0000, end: 0x007f, name: '基本拉丁字母（ASCII）' },
  { start: 0x0080, end: 0x00ff, name: '拉丁字母补充' },
  { start: 0x2000, end: 0x206f, name: '通用标点' },
  { start: 0x2190, end: 0x21ff, name: '箭头' },
  { start: 0x2e80, end: 0x2eff, name: 'CJK 部首补充' },
  { start: 0x2f00, end: 0x2fdf, name: '康熙部首' },
  { start: 0x3000, end: 0x303f, name: 'CJK 符号和标点' },
  { start: 0x3400, end: 0x4dbf, name: 'CJK 统一表意文字扩展 A' },
  { start: 0x4e00, end: 0x9fff, name: 'CJK 统一表意文字（基本区）' },
  { start: 0xf900, end: 0xfaff, name: 'CJK 兼容表意文字' },
  { start: 0xff00, end: 0xffef, name: '半角及全角形式' },
  { start: 0x20000, end: 0x2a6df, name: 'CJK 统一表意文字扩展 B' },
  { start: 0x2a700, end: 0x2b73f, name: 'CJK 统一表意文字扩展 C' },
  { start: 0x2b740, end: 0x2b81f, name: 'CJK 统一表意文字扩展 D' },
  { start: 0x2b820, end: 0x2ceaf, name: 'CJK 统一表意文字扩展 E' },
  { start: 0x2ceb0, end: 0x2ebef, name: 'CJK 统一表意文字扩展 F' },
  { start: 0x30000, end: 0x3134f, name: 'CJK 统一表意文字扩展 G' },
  { start: 0x31350, end: 0x323af, name: 'CJK 统一表意文字扩展 H' },
]

const PLANE_NAMES = [
  '基本多文种平面（BMP）',
  '第一辅助平面（SMP）',
  '第二表意文字平面（SIP）',
  '第三表意文字平面（TIP）',
]

export function unicodeBlockOf(codePoint: number): string {
  const hit = BLOCKS.find((block) => codePoint >= block.start && codePoint <= block.end)
  if (hit) return hit.name
  return `未收录区段 U+${codePoint.toString(16).toUpperCase()}`
}

export function planeOf(codePoint: number): number {
  return codePoint >> 16
}

export function planeNameOf(codePoint: number): string {
  return PLANE_NAMES[planeOf(codePoint)] ?? `第 ${planeOf(codePoint) + 1} 平面`
}
