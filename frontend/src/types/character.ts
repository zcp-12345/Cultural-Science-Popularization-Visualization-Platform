export interface Era {
  id: string
  name: string
  dynasty: string
  period: string
  summary: string
  traits: string[]
}

export interface TimelineCharacter {
  char: string
  pinyin: string
  meaning: string
  /** key 为 Era.id，值为该字在这一时期的简要说明 */
  notes: Record<string, string>
}
