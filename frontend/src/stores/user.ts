import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { sleep } from '@/services/mock/delay'
import type { UserProfile, UserStats } from '@/types/user'

const STORAGE_KEY = 'dal.user.v1'

interface StoredProfile {
  profile: UserProfile
}

function readProfile(): StoredProfile | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? (JSON.parse(raw) as StoredProfile) : null
  } catch {
    return null
  }
}

function uid(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) return crypto.randomUUID()
  return Math.random().toString(36).slice(2, 12)
}

function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}

export const useUserStore = defineStore('user', () => {
  const session = typeof window === 'undefined' ? null : readProfile()
  const profile = ref<UserProfile | null>(session?.profile ?? null)
  // 安全约定：token 只保存在内存，绝不写入 localStorage（防持久型 XSS 窃取）。
  // Phase 1 为 `mock.` 前缀假令牌；Phase 2 换真实 JWT 后，access token 仍仅存内存，
  // refresh token 由后端下发 HttpOnly; Secure; SameSite=Lax Cookie。
  const token = ref<string | null>(null)
  const stats = ref<UserStats>({ scanned: 128, encoded: 46, streakDays: 5 })

  // Phase 1 mock 无真实鉴权，暂以 profile 是否存在判断登录态；
  // Phase 2 必须改为校验 token，profile 永远不能作为权限依据。
  const isLoggedIn = computed(() => profile.value !== null)

  function persist() {
    if (typeof window === 'undefined') return
    if (profile.value) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ profile: profile.value }))
    } else {
      localStorage.removeItem(STORAGE_KEY)
    }
  }

  async function login(email: string, password: string) {
    const normalized = email.trim().toLowerCase()
    if (!isValidEmail(normalized)) throw new Error('请输入有效的邮箱地址')
    if (password.length < 6) throw new Error('密码至少需要 6 位')

    await sleep(620)

    profile.value = {
      id: uid(),
      name: normalized.split('@')[0],
      email: normalized,
      joinedAt: new Date().toISOString(),
    }
    token.value = `mock.${uid()}`
    persist()
  }

  async function register(name: string, email: string, password: string) {
    const trimmedName = name.trim()
    const normalized = email.trim().toLowerCase()
    if (trimmedName.length < 1) throw new Error('请输入昵称')
    if (!isValidEmail(normalized)) throw new Error('请输入有效的邮箱地址')
    if (password.length < 6) throw new Error('密码至少需要 6 位')

    await sleep(720)

    profile.value = {
      id: uid(),
      name: trimmedName,
      email: normalized,
      joinedAt: new Date().toISOString(),
    }
    token.value = `mock.${uid()}`
    persist()
  }

  function logout() {
    profile.value = null
    token.value = null
    persist()
  }

  function recordScan() {
    stats.value.scanned += 1
  }

  function recordEncoding() {
    stats.value.encoded += 1
  }

  return {
    profile,
    token,
    stats,
    isLoggedIn,
    login,
    register,
    logout,
    recordScan,
    recordEncoding,
  }
})
