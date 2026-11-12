# 数字考古透视镜 · 真实古文字字形落地方案（时间轴改造）

> 本文档回答「如何把时间轴上的现代字体示意占位，修正成有出处、有授权的真实古文字字形」。由四路并行研究（数据库 / 字体 / SVG 管线 / 授权）合并而成。

## 0. 核心结论

**以 `hanzi-glyphs-svg`（zhouyongh，GitHub）为唯一主力字形落地源，小學堂（中研院/臺大，CC0）作交叉核对，OFL 字体覆盖楷书/简体两栏；每字每期绑定 source + license + 出处证据，拿不到证据宁可显示文字卡，绝不冒充古文字。**

**关键认识（先纠正一个预期）**：甲骨文/金文没有 Unicode 码位，「真实拓片」对一个公开合规项目而言 = **古籍摹本/矢量化字形**（《甲骨文编》《金文编》《说文》刻本摹本），**不是**机构高清原拓照片——机构数字影像版权归己，禁止抓取。所以「修正成真实拓片」的正确实现是：把「现代字体大字占位」换成「**有出处、有许可的古文字矢量 SVG + 出处徽标**」，而不是去扒原拓图。

## 1. 按时期来源（一句话结论）

| 时期 | 推荐来源 | 授权 |
| --- | --- | --- |
| 楷书 regular | 霞鹜文楷 LXGW WenKai（备选思源宋体） | OFL 1.1，按 `ord(char)` 直接提轮廓 |
| 简体 simplified | 思源宋体/思源黑体 Noto Sans SC | OFL 1.1，零风险 |
| 小篆 seal | `hanzi-glyphs-svg` 篆书层（10,591 字） | CC0 |
| 隶书 clerical | `hanzi-glyphs-svg` 隶书层（11,947 字） | CC0 |
| 金文 bronze | `hanzi-glyphs-svg` 金文层（8,290 字），Wikimedia Commons ACC 补缺 | CC0 / PD |
| 甲骨文 oracle | `hanzi-glyphs-svg` 甲骨文层（11,416 字 CC0 + 1,203 字 CC BY 4.0），小學堂 CC0 交叉核对 | CC0 + CC BY（需署名） |

**回避名单（硬约束）**：崇羲篆體（CC BY-ND，禁改作）；漢典释义文本（CC BY-NC-ND）；教育部異體字字典（禁程序解析）；引得市（订阅制）；白川/漢儀陳體甲骨文、方正甲骨文字库（商用/轮廓提取存疑）；机构拓片扫描图（版权归机构）。

## 2. 文件约定

```
frontend/public/glyphs/{汉字}/{时期}.svg
时期 ∈ {oracle, bronze, seal, clerical, regular, simplified}
```

- 目录名用前端展示字：`public/glyphs/龙/oracle.svg` 的内容来自繁体「龍」的甲骨文字形；`中/日/水` 无繁简之分。
- **字→查询字映射（易漏的坑）**：`龙→龍`、`马→馬` 在 oracle/bronze/seal/clerical/regular 五栏都用繁体查询，仅 simplified 用简体本身。

归一化（`normalize.py` 强制）：
1. `viewBox="0 0 100 100"` + `preserveAspectRatio="xMidYMid meet"`，字形按包围盒等比居中，四周留 8 单位 padding；
2. 所有 `<path>` 统一 `fill="currentColor"`，删除源文件自带的 `fill/stroke/transform/width/height` 及 `<rect>` 背景（CSS 用时期色继承配色）；
3. 白底透明化，阴文拓片先反转；字体轮廓 Y 轴翻转（`TransformPen scale(1,-1)`）。

配套清单：`public/glyphs/manifest.json`（`available / src / queryChar / variants / license / glyph_status`）+ `public/glyphs/CREDITS.md`（逐字逐时期来源授权台账）。

源档归档（不入前端包，放仓库或独立资源仓，**勿放 OneDrive**）：`assets/glyphs-src/{fonts, oracle/, bronze/, index/*.csv}`。

## 3. 生产管线

- **Unicode 时期（楷/简）**：`ord(char)` 查 cmap → fontTools 提轮廓 → SVG。
- **非 Unicode 时期（甲骨/金/篆/隶）**：`(目标字, 时期)` → `index.csv` 查选定的异体 SVG → 直接归一化（hanzi-glyphs-svg 已是 SVG）；若拿到位图走 Potrace。

工具：`fontTools`（`TTFont`/`getBestCmap`/`getGlyphSet`/`SVGPathPen`/`BoundsPen`/`TransformPen`）；位图矢量化用 ImageMagick 预处理 + Potrace（`-s -t 2 --alphamax 0.6~1.0 -O 0.2`）。

统一脚本 `tools/glyphs/build_glyphs.py`（配置驱动 `config.yaml`）：逐 `(字, 时期)` 查 query 字 → 按 kind（font / svg-db）产出 → 归一化写 SVG → 收集 credits → 输出 `CREDITS.md` + `manifest.json`。缺字/授权未确认 → 不输出真实字形，降级文字卡。

## 4. 兜底显示（三态）

`glyph_status: real | placeholder | missing`

1. **real**：显示授权 SVG，右上角小标「出处 + 许可」（如「字形源：小學堂 · CC0」）。
2. **placeholder**：退回现代字体大字 + 明确标注「该时期字形未收录，此处为现代字形示意」，用低饱和灰调 + 虚线描边与真实字形区分。
3. **missing**：文字卡（字头 + 释文 +「古文字形暂缺 · 待补授权素材」），不做手绘/合成假古字。

前端最小改动：新增 `src/services/glyphs.ts` 的 `glyphSrc(char, eraId)`，`TimelineView.vue` 三处大字渲染换成按约定路径取 SVG，`@error` 回退文字卡。

## 5. 落地优先级（与后端 M1–M3 并行，不阻塞）

- **P0（先做，授权最干净、纯现成 SVG/字体）**：楷书 + 简体（OFL 字体提取）+ 小篆 + 隶书（hanzi-glyphs-svg CC0 层），先把 `build_glyphs.py` 整条管线跑通，输出 `CREDITS.md` + `manifest.json`。
- **P1（金文）**：hanzi-glyphs-svg 金文层（CC0），小學堂 CC0 交叉核对，Wikimedia Commons ACC 补缺。
- **P2（甲骨文，工序最多）**：hanzi-glyphs-svg 甲骨文层，需区分 CC0 与 CC BY 4.0 子集并对后者署名，逐字选「著录清晰、字形典型、授权明确」的异体；拿不到就降级文字卡。

## 6. 待用户拍板（2026-11-12 已拍板：三条均按推荐执行）

> ① 隶/篆用 hanzi-glyphs-svg 的 CC0 现成矢量；② 甲骨/金文接受「最接近拓片 = 古籍摹本矢量」定位；③ 字形 SVG 放前端 `public/glyphs/`，后端只出清单，Phase 3 再考虑动态代理。

1. 隶书/小篆是否接受用 hanzi-glyphs-svg（CC0 现成矢量），而非坚持找独立开源字体（现实：开源隶/篆字体稀缺，多为商业授权）。
2. 甲骨/金文是否接受「最接近拓片 = 古籍摹本矢量（hanzi-glyphs-svg + 小學堂双源）」这一定位。
3. 字形 SVG 长期放前端 `public/`（推荐，静态 CDN 友好），后端只出清单；Phase 3 再考虑 `/glyphs/{char}/{era}.svg` 动态代理。

## 7. 落地前待复核项（逐条打开原始页面确认，不凭检索摘要下结论）

1. hanzi-glyphs-svg 对 5 个示例字（尤其甲骨/金文层）在 `index.csv` 的逐字命中率；
2. 漢典「书法/字形」板块 CC0 为第三方解读，以 hanzi-glyphs-svg 的 provenance 溯源 + 小學堂独立核对为准，不单独依赖漢典原站抓图；
3. 方正甲骨文字库「免费商用」是否涵盖轮廓提取再分发，用前须向方正索取书面授权；
4. 青柳/临海隶书、峄山碑篆体授权仅有第三方收录站声明，非默认来源。

> 注：本次研究的联网抓取对部分站点（github.com / wikimedia / xiaoxue）被网络策略拦截，结论主要来自搜索摘要 + 官方文档片段，**授权条款在正式采用前必须逐条打开原始页面复核**。
