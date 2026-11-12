/**
 * Phase 2 接口层：与 FastAPI 后端通信。
 *
 * 约定：
 * - 所有请求走 VITE_API_BASE_URL（默认 /api/v1，开发期由 Vite proxy 转发到 :8000）
 * - 后端 Pydantic 用 camelCase 输出，返回类型与 src/types 1:1 对齐
 * - 鉴权：Authorization: Bearer <access_token>（token 仅存内存）
 * - credentials 'include'：让 refresh_token 的 HttpOnly Cookie 随请求发送
 */
const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  if (!headers.has('Content-Type') && init.body) {
    headers.set('Content-Type', 'application/json')
  }

  const response = await fetch(`${BASE_URL}${path}`, { ...init, headers, credentials: 'include' })

  if (!response.ok) {
    let message = `请求失败（${response.status}）`
    try {
      const body = await response.json()
      const detail = body?.detail
      if (typeof detail === 'string') message = detail
      else if (Array.isArray(detail) && detail.length > 0) message = '请求参数有误，请检查后重试'
    } catch {
      // 无 JSON 错误体，保留默认消息
    }
    throw new ApiError(response.status, message)
  }

  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}

export function withToken(token: string | null): RequestInit {
  // 拒绝占位 / mock 前缀的 token，防止把演示用的假凭证当真鉴权发给后端
  if (token && (token.startsWith('mock.') || token.startsWith('demo.') || token.startsWith('placeholder'))) {
    throw new ApiError(401, '无效的演示凭证，请重新登录')
  }
  return token ? { headers: { Authorization: `Bearer ${token}` } } : {}
}
