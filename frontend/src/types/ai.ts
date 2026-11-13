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

/** 多轮记忆：随请求带回的最近几轮对话（后端注入 LLM 消息序列）。 */
export interface ChatHistoryEntry {
  role: ChatRole
  content: string
}
