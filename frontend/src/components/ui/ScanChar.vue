<script setup lang="ts">
const props = defineProps<{ char: string }>()
const emit = defineEmits<{ inspect: [char: string, el: HTMLElement] }>()

function inspect(event: Event) {
  emit('inspect', props.char, event.currentTarget as HTMLElement)
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault()
    inspect(event)
  }
}
</script>

<template>
  <span
    class="scan-char"
    role="button"
    tabindex="0"
    :data-char="char"
    :aria-label="`用透视镜查看汉字「${char}」`"
    @click="inspect"
    @keydown="onKeydown"
  >
    {{ char }}
  </span>
</template>

<style scoped>
.scan-char {
  color: var(--c-gold);
  font-weight: 600;
  padding: 0 2px;
  border-bottom: 1px dashed rgba(255, 204, 0, 0.55);
  border-radius: 3px;
  cursor: crosshair;
  transition:
    background 0.2s ease,
    box-shadow 0.2s ease,
    color 0.2s ease;
}

.scan-char:hover {
  color: #ffe066;
  background: rgba(255, 204, 0, 0.12);
  box-shadow: 0 0 14px rgba(255, 204, 0, 0.28);
}

.scan-char:focus-visible {
  color: #ffe066;
  background: rgba(255, 204, 0, 0.16);
  outline: 2px solid #ffe066;
  outline-offset: 2px;
}
</style>
