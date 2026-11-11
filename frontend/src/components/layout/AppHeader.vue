<script setup lang="ts">
import { RouterLink } from 'vue-router'
import AppIcon from '@/components/ui/AppIcon.vue'
import { useUiStore } from '@/stores/ui'

const ui = useUiStore()

const navItems = [
  { to: '/', label: '透视镜' },
  { to: '/comparator', label: '编码对比' },
  { to: '/timeline', label: '演变时间轴' },
  { to: '/profile', label: '用户中心' },
]
</script>

<template>
  <header class="app-header">
    <RouterLink to="/" class="brand" aria-label="数字考古透视镜首页">
      <span class="brand__lens">
        <AppIcon name="lens" :size="22" />
        <span class="brand__scanline" aria-hidden="true"></span>
      </span>
      <span class="brand__text">
        数字考古透视镜
        <em>DIGITAL ARCHAEOLOGY LENS</em>
      </span>
    </RouterLink>

    <nav class="nav" aria-label="主导航">
      <RouterLink v-for="item in navItems" :key="item.to" :to="item.to" class="nav__link">
        {{ item.label }}
      </RouterLink>
    </nav>

    <button
      class="ai-button"
      type="button"
      :aria-expanded="ui.aiOpen"
      aria-controls="ai-drawer"
      :aria-label="ui.aiOpen ? '关闭 AI 考古助手' : '打开 AI 考古助手'"
      @click="ui.toggleAi()"
    >
      <AppIcon name="spark" :size="18" />
      <span>AI 助手</span>
      <i class="ai-button__dot" aria-hidden="true"></i>
    </button>
  </header>
</template>

<style scoped>
.app-header {
  position: sticky;
  top: 0;
  z-index: var(--z-header);
  display: flex;
  align-items: center;
  gap: 28px;
  height: var(--header-h);
  padding: 0 28px;
  background: rgba(6, 9, 16, 0.78);
  border-bottom: 1px solid var(--c-line);
  backdrop-filter: blur(16px);
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.brand__lens {
  position: relative;
  display: grid;
  place-items: center;
  width: 38px;
  height: 38px;
  border-radius: 50%;
  border: 1.5px solid var(--c-cyan);
  color: var(--c-cyan);
  box-shadow:
    0 0 16px rgba(0, 240, 255, 0.32),
    inset 0 0 12px rgba(0, 240, 255, 0.14);
  overflow: hidden;
}

.brand__scanline {
  position: absolute;
  left: 18%;
  width: 64%;
  height: 1.5px;
  background: linear-gradient(90deg, transparent, var(--c-cyan), transparent);
  box-shadow: 0 0 8px var(--c-cyan);
  animation: brand-scan 2.8s ease-in-out infinite;
}

@keyframes brand-scan {
  0% {
    top: 22%;
    opacity: 0;
  }
  40%,
  60% {
    opacity: 1;
  }
  100% {
    top: 78%;
    opacity: 0;
  }
}

.brand__text {
  display: flex;
  flex-direction: column;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.06em;
  line-height: 1.2;
  white-space: nowrap;
}

.brand__text em {
  font-style: normal;
  font-size: 8.5px;
  font-weight: 500;
  letter-spacing: 0.24em;
  color: var(--c-text-faint);
}

.nav {
  display: flex;
  gap: 6px;
  margin-left: auto;
}

.nav__link {
  padding: 7px 14px;
  border-radius: 999px;
  font-size: 14px;
  color: var(--c-text-dim);
  transition:
    color 0.2s ease,
    background 0.2s ease;
}

.nav__link:hover {
  color: var(--c-text);
  background: rgba(255, 255, 255, 0.04);
}

.nav__link.router-link-exact-active {
  color: var(--c-cyan);
  background: var(--c-cyan-soft);
  box-shadow: inset 0 0 0 1px rgba(0, 240, 255, 0.22);
}

.ai-button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 999px;
  border: 1px solid rgba(0, 240, 255, 0.35);
  background: linear-gradient(120deg, rgba(0, 240, 255, 0.14), rgba(255, 79, 216, 0.12));
  color: var(--c-text);
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.04em;
  transition:
    box-shadow 0.2s ease,
    border-color 0.2s ease,
    transform 0.2s var(--ease-out);
}

.ai-button:hover {
  border-color: var(--c-cyan);
  box-shadow: var(--shadow-cyan);
  transform: translateY(-1px);
}

.ai-button__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--c-green);
  box-shadow: 0 0 8px var(--c-green);
  animation: pulse 2s ease-in-out infinite;
}

@media (max-width: 860px) {
  .brand__text em {
    display: none;
  }
}

@media (max-width: 720px) {
  .app-header {
    gap: 14px;
    padding: 0 16px;
  }

  .nav {
    display: none;
  }

  .ai-button {
    margin-left: auto;
  }

  .ai-button span {
    display: none;
  }

  .ai-button {
    padding: 12px;
    min-width: 44px;
    min-height: 44px;
  }
}
</style>
