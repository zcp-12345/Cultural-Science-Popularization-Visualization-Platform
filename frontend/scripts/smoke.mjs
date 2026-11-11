// 冒烟测试：无头 Chromium 加载各路由，收集 console/page 错误并校验关键内容渲染。
// 依赖：playwright（`npm install --no-save playwright`）+ 已安装的 chromium。
import { chromium } from 'playwright'

const BASE = process.env.SMOKE_BASE ?? 'http://localhost:5173'
const routes = [
  { path: '/', title: '透视镜', checks: ['.hero h1', '.scan-char', '.notes'] },
  { path: '/comparator', title: '编码对比器', checks: ['.comparator.page', '.char-card__glyph', 'canvas, svg'] },
  { path: '/timeline', title: '汉字演变时间轴', checks: ['.timeline-page.page', 'svg'] },
  { path: '/profile', title: '用户中心', checks: ['.profile.page', '.panel'] },
  { path: '/nope-404', title: '页面未找到', checks: ['.not-found.page'] },
]

const browser = await chromium.launch()
let failures = 0

for (const r of routes) {
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })
  const errors = []
  page.on('console', (m) => {
    if (m.type() === 'error') errors.push(`console: ${m.text()}`)
  })
  page.on('pageerror', (e) => errors.push(`pageerror: ${e.message}`))

  await page.goto(BASE + r.path, { waitUntil: 'load' })
  await page.waitForTimeout(500)

  const found = []
  for (const sel of r.checks) {
    const n = await page.locator(sel).count()
    found.push(`${sel}:${n}`)
  }

  const ok = errors.length === 0
  if (!ok) failures++
  console.log(`[${ok ? 'OK' : 'FAIL'}] ${r.path}`)
  console.log(`       title="${await page.title()}"  ${found.join('  ')}`)
  for (const e of errors) console.log(`       ${e}`)

  await page.close()
}

await browser.close()
console.log(failures ? `\nSMOKE FAILED: ${failures} route(s) had console/page errors` : '\nSMOKE PASS: all routes rendered with no console/page errors')
process.exit(failures ? 1 : 0)
