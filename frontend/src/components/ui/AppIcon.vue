<script setup lang="ts">
type IconName =
  | 'lens'
  | 'code'
  | 'timeline'
  | 'user'
  | 'spark'
  | 'close'
  | 'send'
  | 'arrow'
  | 'reset'
  | 'bulb'
  | 'book'
  | 'compare'
  | 'play'
  | 'pause'
  | 'heart'

withDefaults(defineProps<{ name: IconName; size?: number; filled?: boolean }>(), {
  size: 20,
  filled: false,
})
</script>

<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    :fill="filled ? 'currentColor' : 'none'"
    stroke="currentColor"
    stroke-width="1.7"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <template v-if="name === 'lens'">
      <circle cx="10.5" cy="10.5" r="6.5" />
      <path d="M15.4 15.4 21 21" />
      <path d="M7.8 10.5h5.4" opacity="0.7" />
    </template>
    <template v-else-if="name === 'code'">
      <path d="m8 6-5 6 5 6M16 6l5 6-5 6M14 4l-4 16" />
    </template>
    <template v-else-if="name === 'timeline'">
      <path d="M3 12h18" />
      <circle cx="6.5" cy="12" r="1.6" />
      <circle cx="12" cy="12" r="1.6" />
      <circle cx="17.5" cy="12" r="1.6" />
      <path d="M6.5 9V5.5M12 9V5.5M17.5 9V5.5" opacity="0.7" />
    </template>
    <template v-else-if="name === 'user'">
      <circle cx="12" cy="8" r="3.6" />
      <path d="M4.5 20.5c.7-3.6 3.6-5.5 7.5-5.5s6.8 1.9 7.5 5.5" />
    </template>
    <template v-else-if="name === 'spark'">
      <path d="M11 3.5 12.7 8.3 17.5 10l-4.8 1.7L11 16.5l-1.7-4.8L4.5 10l4.8-1.7L11 3.5Z" />
      <path d="M18 15.5l.8 2.2 2.2.8-2.2.8-.8 2.2-.8-2.2-2.2-.8 2.2-.8.8-2.2Z" opacity="0.8" />
    </template>
    <template v-else-if="name === 'close'">
      <path d="M6 6l12 12M18 6 6 18" />
    </template>
    <template v-else-if="name === 'send'">
      <path d="M4 11.5 20 4l-7.5 16-2-6.5L4 11.5Z" />
      <path d="M10.5 13.5 20 4" />
    </template>
    <template v-else-if="name === 'arrow'">
      <path d="M5 12h14M13 6l6 6-6 6" />
    </template>
    <template v-else-if="name === 'reset'">
      <path d="M4 10a8 8 0 1 1 2.2 8" />
      <path d="M4 4v6h6" />
    </template>
    <template v-else-if="name === 'bulb'">
      <path d="M9 18h6M10 21h4" />
      <path d="M12 3a6 6 0 0 0-3.6 10.8c.6.5 1 1.2 1.1 2h5c.1-.8.5-1.5 1.1-2A6 6 0 0 0 12 3Z" />
    </template>
    <template v-else-if="name === 'book'">
      <path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v15H6.5A2.5 2.5 0 0 0 4 20.5v-15Z" />
      <path d="M4 20.5A2.5 2.5 0 0 1 6.5 18H20" />
    </template>
    <template v-else-if="name === 'compare'">
      <rect x="3.5" y="5" width="7" height="14" rx="1.5" />
      <rect x="13.5" y="5" width="7" height="14" rx="1.5" />
      <path d="M7 9h0M7 12h0M7 15h0M17 9h0M17 12h0M17 15h0" stroke-width="2.2" />
    </template>
    <template v-else-if="name === 'play'">
      <path d="M7 5.5v13l11-6.5-11-6.5Z" />
    </template>
    <template v-else-if="name === 'pause'">
      <path d="M8.5 5.5v13M15.5 5.5v13" />
    </template>
    <template v-else-if="name === 'heart'">
      <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
    </template>
  </svg>
</template>
