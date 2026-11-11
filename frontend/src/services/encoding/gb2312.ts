import gb2312Data from '@/data/gb2312-characters.json'

/**
 * GB2312 权威字符集合，由 scripts/generate_encoding_gold.py 用 Python codecs 生成。
 * 用于精确判定某字符是否被 GB2312 收录（替代原先「字节落在 A1–F7 / A1–FE 区间」的近似）。
 *
 * Phase 2 后端将直接以 Python codecs 为准，此集合作为离线兜底。
 */
let membership: Set<string> | null = null

function buildMembership(): Set<string> {
  if (membership) return membership
  const set = new Set<string>()
  for (const char of gb2312Data.chars) set.add(char)
  membership = set
  return set
}

/** 字符是否被 GB2312 收录（不含 ASCII，ASCII 由调用方单字节分支处理） */
export function isGb2312Char(char: string): boolean {
  return buildMembership().has(char)
}

/** 集合大小（用于调试 / 展示） */
export function gb2312CharCount(): number {
  return buildMembership().size
}
