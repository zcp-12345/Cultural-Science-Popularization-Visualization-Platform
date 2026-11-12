import type { UserProfile } from './user'

export interface TokenPair {
  accessToken: string
  tokenType: string
}

export interface AuthResponse extends TokenPair {
  user: UserProfile
}
