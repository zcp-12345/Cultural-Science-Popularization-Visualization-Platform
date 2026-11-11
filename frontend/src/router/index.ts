import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/HomeView.vue'),
      meta: { title: '透视镜' },
    },
    {
      path: '/comparator',
      name: 'comparator',
      component: () => import('@/views/ComparatorView.vue'),
      meta: { title: '编码对比器' },
    },
    {
      path: '/timeline',
      name: 'timeline',
      component: () => import('@/views/TimelineView.vue'),
      meta: { title: '汉字演变时间轴' },
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('@/views/ProfileView.vue'),
      meta: { title: '用户中心' },
    },
    {
      path: '/ai',
      redirect: { path: '/', query: { ai: '1' } },
      meta: { title: 'AI 考古助手' },
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('@/views/NotFoundView.vue'),
      meta: { title: '页面未找到' },
    },
  ],
  scrollBehavior(to, _from, savedPosition) {
    const reduce =
      typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (savedPosition) return savedPosition
    if (to.hash) return { el: to.hash, behavior: reduce ? 'auto' : 'smooth' }
    return { top: 0 }
  },
})

router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} · 数字考古透视镜` : '数字考古透视镜'
  // 进入路由成功即清理 chunk 重试标记，保证下次失败仍有重试机会
  sessionStorage.removeItem('dal.chunk-retry')
})

// 弱网 / 预览环境下的懒加载 chunk 失败：自动重试一次，再失败则渲染可访问的错误页
router.onError((error, to) => {
  const message = error instanceof Error ? error.message : String(error)
  const isChunkError = /Failed to fetch dynamically imported module|Importing a module script failed|Loading chunk/i.test(message)
  if (!isChunkError) return

  // 校验路径，防止协议相对跳转（//evil.com）
  if (!to.fullPath.startsWith('/') || to.fullPath.startsWith('//')) return

  const key = 'dal.chunk-retry'
  const count = Number(sessionStorage.getItem(key) ?? 0)
  if (count < 1) {
    sessionStorage.setItem(key, String(count + 1))
    window.location.assign(to.fullPath)
  } else {
    sessionStorage.removeItem(key)
    router.replace({ name: 'not-found', query: { reason: 'chunk' } })
  }
})

export default router
