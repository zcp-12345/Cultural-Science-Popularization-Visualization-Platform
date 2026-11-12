import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { apiFetch, withToken } from '@/services/api'
import type { AuthResponse, TokenPair } from '@/types/auth'
import type { ActivityKind, FavoritesResponse, UserProfile, UserStats } from '@/types/user'

function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}

function emptyStats(): UserStats {
  return { scanned: 0, encoded: 0, streakDays: 0 }
}

export const useUserStore = defineStore('user', () => {
  // access token 只存内存，绝不写 localStorage（防持久型 XSS 窃取）；
  // refresh token 由后端下发 HttpOnly; Secure; SameSite=Lax Cookie。
  const token = ref<string | null>(null)
  const profile = ref<UserProfile | null>(null)
  // 学习统计与收藏（M4 已持久化到后端；未登录时仅为本地临时计数）
  const stats = ref<UserStats>(emptyStats())
  const favorites = ref<string[]>([])

  // 登录态以 token 为准，profile 永远不作权限依据。
  const isLoggedIn = computed(() => token.value !== null)

  function setSession(data: AuthResponse) {
    token.value = data.accessToken
    profile.value = data.user
    void loadProgress()
  }

  function clearSession() {
    token.value = null
    profile.value = null
    stats.value = emptyStats()
    favorites.value = []
  }

  async function loadProgress() {
    if (!token.value) return
    try {
      const [nextStats, nextFavorites] = await Promise.all([
        apiFetch<UserStats>('/users/me/stats', withToken(token.value)),
        apiFetch<FavoritesResponse>('/users/me/favorites', withToken(token.value)),
      ])
      stats.value = nextStats
      favorites.value = nextFavorites.items
    } catch {
      // 后端不可达 / 未登录：保留本地值
    }
  }

  async function login(email: string, password: string) {
    const normalized = email.trim().toLowerCase()
    if (!isValidEmail(normalized)) throw new Error('请输入有效的邮箱地址')
    if (password.length < 6) throw new Error('密码至少需要 6 位')

    const data = await apiFetch<AuthResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email: normalized, password }),
    })
    setSession(data)
  }

  async function register(name: string, email: string, password: string) {
    const trimmedName = name.trim()
    const normalized = email.trim().toLowerCase()
    if (trimmedName.length < 1) throw new Error('请输入昵称')
    if (!isValidEmail(normalized)) throw new Error('请输入有效的邮箱地址')
    if (password.length < 6) throw new Error('密码至少需要 6 位')

    const data = await apiFetch<AuthResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ name: trimmedName, email: normalized, password }),
    })
    setSession(data)
  }

  async function logout() {
    try {
      await apiFetch<void>('/auth/logout', { method: 'POST', ...withToken(token.value) })
    } catch {
      // 后端登出失败也清空本地会话（token 不落盘，无状态可泄）
    } finally {
      clearSession()
    }
  }

  async function fetchMe() {
    profile.value = await apiFetch<UserProfile>('/users/me', withToken(token.value))
  }

  // 启动时：内存无 token 但可能有 refresh cookie → 静默刷新换新 access 并拉取资料。
  async function bootstrap() {
    if (token.value) return
    try {
      const data = await apiFetch<TokenPair>('/auth/refresh', { method: 'POST' })
      token.value = data.accessToken
      await fetchMe()
      await loadProgress()
    } catch {
      // 无有效 refresh cookie，或后端未启动 → 保持未登录
      clearSession()
    }
  }

  // 记录一次学习行为：本地乐观自增，登录态下同步到后端（后端为权威值）。
  async function recordActivity(kind: ActivityKind) {
    if (kind === 'scan') stats.value.scanned += 1
    else stats.value.encoded += 1
    if (!token.value) return
    try {
      stats.value = await apiFetch<UserStats>('/users/me/stats/activity', {
        method: 'POST',
        ...withToken(token.value),
        body: JSON.stringify({ kind }),
      })
    } catch {
      // 后端不可达：保留本地乐观计数
    }
  }

  function recordScan() {
    void recordActivity('scan')
  }

  function recordEncoding() {
    void recordActivity('encode')
  }

  const isFavorite = (char: string) => favorites.value.includes(char)

  async function addFavorite(char: string) {
    if (!favorites.value.includes(char)) favorites.value.push(char)
    if (!token.value) return
    try {
      const res = await apiFetch<FavoritesResponse>('/users/me/favorites', {
        method: 'POST',
        ...withToken(token.value),
        body: JSON.stringify({ char }),
      })
      favorites.value = res.items
    } catch {
      // 后端不可达：保留本地乐观收藏
    }
  }

  async function removeFavorite(char: string) {
    favorites.value = favorites.value.filter((c) => c !== char)
    if (!token.value) return
    try {
      const res = await apiFetch<FavoritesResponse>(
        `/users/me/favorites/${encodeURIComponent(char)}`,
        { method: 'DELETE', ...withToken(token.value) },
      )
      favorites.value = res.items
    } catch {
      // 后端不可达：保留本地乐观移除
    }
  }

  async function toggleFavorite(char: string) {
    if (isFavorite(char)) await removeFavorite(char)
    else await addFavorite(char)
  }

  return {
    token,
    profile,
    stats,
    favorites,
    isLoggedIn,
    login,
    register,
    logout,
    fetchMe,
    bootstrap,
    recordScan,
    recordEncoding,
    isFavorite,
    addFavorite,
    removeFavorite,
    toggleFavorite,
  }
})
