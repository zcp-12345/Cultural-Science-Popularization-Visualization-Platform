<script setup lang="ts">
import { RouterLink } from 'vue-router'
import AppIcon from '@/components/ui/AppIcon.vue'
</script>

<template>
  <div class="not-found page">
    <span class="not-found__icon"><AppIcon name="lens" :size="36" /></span>
    <p class="not-found__code mono">404 · LOST IN TIME</p>
    <h1>这页字，没在甲骨上找到</h1>
    <p class="not-found__text">你访问的页面可能已经被历史掩埋，或者链接写错了。</p>
    <RouterLink to="/" class="btn btn--primary">
      回到透视镜
      <AppIcon name="arrow" :size="16" />
    </RouterLink>
  </div>
</template>

<style scoped>
.not-found {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 58vh;
  text-align: center;
  gap: 12px;
}

.not-found__icon {
  display: grid;
  place-items: center;
  width: 84px;
  height: 84px;
  border-radius: 50%;
  color: var(--c-cyan);
  border: 2px solid rgba(0, 240, 255, 0.5);
  box-shadow: 0 0 32px rgba(0, 240, 255, 0.28);
  margin-bottom: 8px;
}

.not-found__code {
  margin: 0;
  font-size: 11px;
  letter-spacing: 0.24em;
  color: var(--c-cyan);
}

.not-found h1 {
  margin: 0;
  font-family: var(--font-serif);
  font-size: clamp(1.6rem, 4vw, 2.2rem);
  letter-spacing: 0.08em;
}

.not-found__text {
  margin: 0 0 14px;
  font-size: 13.5px;
  color: var(--c-text-dim);
}
</style>
