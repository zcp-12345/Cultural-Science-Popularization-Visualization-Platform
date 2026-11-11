import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUiStore = defineStore('ui', () => {
  const aiOpen = ref(false)

  function openAi() {
    aiOpen.value = true
  }

  function closeAi() {
    aiOpen.value = false
  }

  function toggleAi() {
    aiOpen.value = !aiOpen.value
  }

  return { aiOpen, openAi, closeAi, toggleAi }
})
