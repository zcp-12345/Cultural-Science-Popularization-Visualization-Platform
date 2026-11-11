<script setup lang="ts">
import { onErrorCaptured, ref } from 'vue'
import { RouterView } from 'vue-router'
import AiChatDrawer from '@/components/ai/AiChatDrawer.vue'
import AppHeader from '@/components/layout/AppHeader.vue'
import MobileTabBar from '@/components/layout/MobileTabBar.vue'
import { useUiStore } from '@/stores/ui'

const ui = useUiStore()

// 全局错误边界：捕获后代组件的渲染 / 生命周期错误，给出可恢复的降级页
const fatalError = ref<string | null>(null)

onErrorCaptured((error) => {
  fatalError.value = error instanceof Error ? error.message : String(error)
  console.error('[数字考古透视镜] 渲染错误', error)
  return false
})

function reload() {
  window.location.reload()
}
</script>

<template>
  <div class="app-shell">
    <a class="skip-link" href="#main">跳到主要内容</a>

    <div v-if="fatalError" class="error-boundary" role="alert">
      <div class="error-boundary__card">
        <h2>页面出现了问题</h2>
        <p class="error-boundary__detail">{{ fatalError }}</p>
        <button class="error-boundary__reload" type="button" @click="reload">重新加载</button>
      </div>
    </div>

    <div v-else class="app-shell__content" :inert="ui.aiOpen">
      <AppHeader />
      <main id="main" tabindex="-1">
        <RouterView v-slot="{ Component }">
          <Transition name="page" mode="out-in">
            <component :is="Component" />
          </Transition>
        </RouterView>
      </main>
      <MobileTabBar />
    </div>

    <AiChatDrawer />
  </div>
</template>

<style scoped>
.skip-link {
  position: fixed;
  top: -100%;
  left: 12px;
  z-index: 10000;
  padding: 10px 16px;
  border-radius: 0 0 10px 10px;
  background: var(--c-panel-strong);
  color: var(--c-cyan);
  border: 1px solid var(--c-line-strong);
  text-decoration: none;
}

.skip-link:focus {
  top: 12px;
}

.error-boundary {
  display: grid;
  place-items: center;
  min-height: 70vh;
  padding: 24px;
}

.error-boundary__card {
  max-width: 460px;
  padding: 32px;
  text-align: center;
  background: var(--c-panel-strong);
  border: 1px solid var(--c-line);
  border-radius: var(--radius-lg);
}

.error-boundary__card h2 {
  margin: 0 0 12px;
  font-size: 18px;
  letter-spacing: 0.06em;
  color: var(--c-gold);
}

.error-boundary__detail {
  margin: 0 0 20px;
  font-family: var(--font-mono);
  font-size: 12px;
  line-height: 1.6;
  color: var(--c-text-faint);
  overflow-wrap: anywhere;
}

.error-boundary__reload {
  padding: 9px 20px;
  border: none;
  border-radius: 10px;
  font-size: 13px;
  letter-spacing: 0.04em;
  color: #04141a;
  background: linear-gradient(120deg, var(--c-cyan), var(--c-green));
  cursor: pointer;
}
</style>
