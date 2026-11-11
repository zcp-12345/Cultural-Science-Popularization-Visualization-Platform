# 字形素材目录（待接入）

时间轴组件当前以大字示意占位渲染字形。接入真实字形时，请按以下约定放置 SVG：

```
public/glyphs/{汉字}/{时期}.svg
```

时期 id 与 `src/data/eras.ts` 一致：

| id | 时期 |
| --- | --- |
| `oracle` | 甲骨文 |
| `bronze` | 金文 |
| `seal` | 小篆 |
| `clerical` | 隶书 |
| `regular` | 楷书 |
| `simplified` | 简体字 |

示例：`public/glyphs/中/oracle.svg`。

## 授权要求

- 仅使用明确开放许可（如 SIL OFL、CC0、CC BY）的字体或数据集，并在 `CREDITS.md` 记录来源、许可证与署名要求。
- 拓片、字帖扫描图的版权状态需逐个确认，不要直接使用来源不明的图片。
- 建议统一为单色 `currentColor` 的 SVG path，viewBox 统一为 `0 0 100 100`，便于按时期着色。
