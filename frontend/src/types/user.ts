export interface UserProfile {
  id: string
  name: string
  email: string
  joinedAt: string
}

export interface UserStats {
  scanned: number
  encoded: number
  streakDays: number
}

export type ActivityKind = 'scan' | 'encode'

export interface FavoritesResponse {
  items: string[]
}
