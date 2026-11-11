<script setup lang="ts">
import { RouterLink } from 'vue-router'
import AppIcon from '@/components/ui/AppIcon.vue'

const tabs = [
  { to: '/', label: '透视镜', icon: 'lens' },
  { to: '/comparator', label: '编码对比', icon: 'compare' },
  { to: '/timeline', label: '时间轴', icon: 'timeline' },
  { to: '/profile', label: '我的', icon: 'user' },
] as const
</script>

<template>
  <nav class="tabbar" aria-label="移动端导航">
    <RouterLink v-for="tab in tabs" :key="tab.to" :to="tab.to" class="tabbar__item">
      <AppIcon :name="tab.icon" :size="20" />
      <span>{{ tab.label }}</span>
    </RouterLink>
  </nav>
</template>

<style scoped>
.tabbar {
  display: none;
}

@media (max-width: 720px) {
  .tabbar {
    position: fixed;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: var(--z-tabbar);
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    height: calc(var(--tabbar-h) + env(safe-area-inset-bottom, 0px));
    padding-bottom: env(safe-area-inset-bottom, 0px);
    background: rgba(8, 12, 22, 0.92);
    border-top: 1px solid var(--c-line);
    backdrop-filter: blur(18px);
  }

  .tabbar__item {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 3px;
    font-size: 11px;
    color: var(--c-text-faint);
    transition: color 0.2s ease;
  }

  .tabbar__item.router-link-exact-active {
    color: var(--c-cyan);
    text-shadow: 0 0 12px rgba(0, 240, 255, 0.5);
  }
}
</style>
