/**
 * 字形 SVG 路径约定：public/glyphs/{汉字}/{时期}.svg
 * 由 tools/glyphs/build_glyphs.py 生成，见 public/glyphs/CREDITS.md。
 */

export function glyphSrc(char: string, era: string): string {
  return `/glyphs/${encodeURIComponent(char)}/${era}.svg`
}

/** 各时期字形来源署名（与 public/glyphs/manifest.json 一致）。 */
export const ERA_ATTRIBUTION: Record<string, string> = {
  oracle: '汉典甲骨文摹本 / 小學堂 · CC0',
  bronze: '汉典金文实例 / 小學堂 · CC0',
  seal: '汉典《说文》小篆 · CC0',
  clerical: '汉典隶书实例 / 小學堂 · CC0',
  regular: '霞鹜文楷 LXGW WenKai · OFL',
  simplified: '思源宋体 Noto Serif SC · OFL',
}
