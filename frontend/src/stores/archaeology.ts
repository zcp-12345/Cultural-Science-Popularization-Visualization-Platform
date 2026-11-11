import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { describeChar } from '@/services/encoding'

export interface NoteItem {
  id: number
  char: string
  unicodeHex: string
  binaryPreview: string
  utf8Bytes: string
  utf8Count: number
  gb2312: boolean
  gbk: boolean
  big5: boolean
}

export const useArchaeologyStore = defineStore('archaeology', () => {
  const currentChar = ref('')
  const notes = ref<NoteItem[]>([])
  const scanCount = ref(0)
  let sequence = 1

  function noteCharacter(char: string): boolean {
    if (!char || char === currentChar.value) return false

    const info = describeChar(char)
    currentChar.value = char
    scanCount.value += 1

    const binary = info.binary
    notes.value.unshift({
      id: sequence++,
      char,
      unicodeHex: info.unicodeHex,
      binaryPreview:
        binary.length > 16
          ? `${binary.slice(0, 8)} ${binary.slice(8, 16)}…`
          : `${binary.slice(0, 8)} ${binary.slice(8, 16)}`,
      utf8Bytes: info.utf8.text,
      utf8Count: info.utf8.bytes.length,
      gb2312: info.legacy.gb2312.available,
      gbk: info.legacy.gbk.available,
      big5: info.legacy.big5.available,
    })

    if (notes.value.length > 6) notes.value.pop()
    return true
  }

  function clear() {
    notes.value = []
    currentChar.value = ''
  }

  const hasNotes = computed(() => notes.value.length > 0)

  return { currentChar, notes, scanCount, hasNotes, noteCharacter, clear }
})
