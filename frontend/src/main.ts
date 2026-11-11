import { createPinia } from 'pinia'
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './styles/tokens.css'
import './styles/base.css'

const app = createApp(App)

// 组件渲染错误之外的兜底（事件处理器、异步任务等）：记录日志，避免静默失败
app.config.errorHandler = (error, _instance, info) => {
  console.error('[数字考古透视镜] 未捕获错误', info, error)
}

app.use(createPinia()).use(router).mount('#app')

// 未处理的 Promise 拒绝（如 Phase 3 的 AI 流式请求失败）也统一记录
window.addEventListener('unhandledrejection', (event) => {
  console.error('[数字考古透视镜] 未处理的 Promise 拒绝', event.reason)
})
