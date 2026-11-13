export type ChatRole = 'assistant' | 'user'

/** 一条 RAG 引用来源（对应后端 sources 事件的 item，顺序即正文中的 [n] 编号）。 */
export interface ChatSource {
  id: string
  title: string
  page: string
}

export interface ChatMessage {
  id: string
  role: ChatRole
  content: string
  createdAt: number
  streaming?: boolean
  sources?: ChatSource[]
}

export interface AiContext {
  page: string
  char?: string
}
