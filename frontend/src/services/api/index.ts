/**
 * Phase 2 接口层占位。
 *
 * 约定：
 * - 所有请求走 VITE_API_BASE_URL（FastAPI，默认 /api/v1）
 * - 返回类型与 src/types 中的定义保持一致，后端 OpenAPI 生成类型后可替换此文件
 * - 鉴权预留 Authorization: Bearer <JWT>
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

  const response = await fetch(`${BASE_URL}${path}`, { ...init, headers })

  if (!response.ok) {
    throw new ApiError(response.status, `请求失败（${response.status}）`)
  }

  return (await response.json()) as T
}

export function withToken(token: string | null): RequestInit {
  // 拒绝占位 / mock 前缀的 token，防止把演示用的假凭证当真鉴权发给后端
  if (token && (token.startsWith('mock.') || token.startsWith('demo.') || token.startsWith('placeholder'))) {
    throw new ApiError(401, '无效的演示凭证，请重新登录')
  }
  return token ? { headers: { Authorization: `Bearer ${token}` } } : {}
}
