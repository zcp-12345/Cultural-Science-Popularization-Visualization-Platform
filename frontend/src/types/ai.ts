export type ChatRole = 'assistant' | 'user'

export interface ChatMessage {
  id: string
  role: ChatRole
  content: string
  createdAt: number
  streaming?: boolean
}

export interface AiContext {
  page: string
  char?: string
}
