<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterLink } from 'vue-router'
import AppIcon from '@/components/ui/AppIcon.vue'
import { useArchaeologyStore } from '@/stores/archaeology'
import { useUserStore } from '@/stores/user'

const user = useUserStore()
const archaeology = useArchaeologyStore()

const mode = ref<'login' | 'register'>('login')
const name = ref('')
const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)
const animationEnabled = ref(true)
const aiHints = ref(true)

const modules = [
  { name: '透视镜三步动画', progress: 100 },
  { name: '编码对比器', progress: 72 },
  { name: '汉字演变时间轴', progress: 45 },
  { name: 'AI 考古助手', progress: 20 },
]

const initial = computed(() => user.profile?.name.slice(0, 1).toUpperCase() ?? '?')
const joinedLabel = computed(() =>
  user.profile ? new Date(user.profile.joinedAt).toLocaleDateString('zh-CN') : '',
)

const statItems = computed(() => [
  { label: '扫描汉字', value: user.stats.scanned, hint: '累计透视次数' },
  { label: '编码查询', value: user.stats.encoded, hint: '对比器查询次数' },
  { label: '连续学习', value: `${user.stats.streakDays} 天`, hint: '保持考古手感' },
])

const recent = computed(() => {
  if (archaeology.notes.length) {
    return archaeology.notes.slice(0, 4).map((note) => ({
      title: `透视「${note.char}」`,
      detail: `U+${note.unicodeHex} · UTF-8 ${note.utf8Count} 字节`,
    }))
  }

  return [
    { title: '透视「龙」', detail: 'U+9F99 · UTF-8 3 字节' },
    { title: '对比 GBK / Big5', detail: '「码」不在 Big5 字符集内' },
    { title: '浏览演变时间轴', detail: '小篆 ·「中」' },
    { title: '询问 AI 助手', detail: 'UTF-8 为什么占 3 字节' },
  ]
})

async function submit() {
  if (loading.value) return
  error.value = ''
  loading.value = true

  try {
    if (mode.value === 'login') {
      await user.login(email.value, password.value)
    } else {
      await user.register(name.value, email.value, password.value)
    }
    password.value = ''
  } catch (err) {
    error.value = err instanceof Error ? err.message : '操作失败，请重试'
  } finally {
    loading.value = false
  }
}

function switchMode(next: 'login' | 'register') {
  mode.value = next
  error.value = ''
}
</script>

<template>
  <div class="profile page">
    <header class="page-head">
      <div>
        <span class="badge badge--gold">Phase 2 · JWT 用户系统已接入</span>
        <h1>用户中心</h1>
        <p>把每一次透视、每一次编码查询留下来。账号由 FastAPI + JWT 提供，学习统计与收藏已持久化到后端。</p>
      </div>
      <span class="page-head__mark" aria-hidden="true">
        <AppIcon name="user" :size="34" />
      </span>
    </header>

    <!-- 未登录 -->
    <section v-if="!user.isLoggedIn" class="auth">
      <article class="auth__intro panel">
        <h2>把每一次考古留下来</h2>
        <p>
          登录后可以保存扫描记录、收藏汉字、查看学习进度。账号由后端 FastAPI 持久化（密码仅存哈希），
          刷新凭证存 HttpOnly Cookie，access token 仅存内存。
        </p>
        <ul>
          <li><AppIcon name="book" :size="16" /><span>扫描历史与编码查询记录</span></li>
          <li><AppIcon name="spark" :size="16" /><span>个性化 AI 考古助手上下文</span></li>
          <li><AppIcon name="timeline" :size="16" /><span>字形学习进度与收藏夹</span></li>
        </ul>
        <div class="auth__notice">
          <AppIcon name="bulb" :size="16" />
          <span>真实账号：注册后由后端持久化，密码仅存哈希，任何密钥都不会进前端。</span>
        </div>
      </article>

      <form class="auth__form panel" @submit.prevent="submit">
        <div class="auth__tabs" role="tablist" aria-label="登录或注册">
          <button
            type="button"
            role="tab"
            :aria-selected="mode === 'login'"
            :class="{ 'is-active': mode === 'login' }"
            @click="switchMode('login')"
          >
            登录
          </button>
          <button
            type="button"
            role="tab"
            :aria-selected="mode === 'register'"
            :class="{ 'is-active': mode === 'register' }"
            @click="switchMode('register')"
          >
            注册
          </button>
        </div>

        <label v-if="mode === 'register'" class="field">
          <span>昵称</span>
          <input v-model="name" type="text" autocomplete="nickname" placeholder="怎么称呼你" />
        </label>

        <label class="field">
          <span>邮箱</span>
          <input v-model="email" type="email" autocomplete="email" placeholder="you@example.com" />
        </label>

        <label class="field">
          <span>密码</span>
          <input
            v-model="password"
            type="password"
            :autocomplete="mode === 'login' ? 'current-password' : 'new-password'"
            placeholder="至少 6 位"
          />
        </label>

        <p v-if="error" class="auth__error" role="alert">{{ error }}</p>

        <button class="btn btn--primary auth__submit" type="submit" :disabled="loading">
          <AppIcon name="arrow" :size="16" />
          {{ loading ? '处理中…' : mode === 'login' ? '登录' : '创建账号' }}
        </button>

        <p class="auth__switch">
          {{ mode === 'login' ? '还没有账号？' : '已经有账号？' }}
          <button type="button" @click="switchMode(mode === 'login' ? 'register' : 'login')">
            {{ mode === 'login' ? '注册一个' : '去登录' }}
          </button>
        </p>
      </form>
    </section>

    <!-- 已登录 -->
    <template v-else>
      <section class="profile-head panel">
        <div class="avatar" aria-hidden="true">{{ initial }}</div>
        <div class="profile-head__meta">
          <span class="badge">已登录</span>
          <h2>{{ user.profile?.name }}</h2>
          <p>{{ user.profile?.email }} · 加入于 {{ joinedLabel }}</p>
        </div>
        <button class="btn btn--ghost btn--sm" type="button" @click="user.logout()">退出登录</button>
      </section>

      <section class="stats">
        <article v-for="stat in statItems" :key="stat.label" class="stat panel">
          <span class="stat__label">{{ stat.label }}</span>
          <strong class="stat__value">{{ stat.value }}</strong>
          <span class="stat__hint">{{ stat.hint }}</span>
        </article>
      </section>

      <div class="dashboard">
        <section class="progress panel">
          <header class="card-head">
            <h2>学习进度</h2>
            <span class="badge badge--muted">MOCK</span>
          </header>
          <ul>
            <li v-for="item in modules" :key="item.name">
              <div class="progress__row">
                <span>{{ item.name }}</span>
                <b class="mono">{{ item.progress }}%</b>
              </div>
              <div class="progress__track" role="progressbar" :aria-valuenow="item.progress" aria-valuemin="0" aria-valuemax="100">
                <span :style="{ width: `${item.progress}%` }"></span>
              </div>
            </li>
          </ul>
        </section>

        <section class="recent panel">
          <header class="card-head">
            <h2>最近活动</h2>
            <span class="badge badge--muted">{{ archaeology.notes.length ? '实时' : 'MOCK' }}</span>
          </header>
          <ul>
            <li v-for="item in recent" :key="item.title">
              <strong>{{ item.title }}</strong>
              <span>{{ item.detail }}</span>
            </li>
          </ul>
        </section>

        <section class="favorites panel">
          <header class="card-head">
            <h2>收藏的汉字</h2>
            <span class="badge badge--gold">已同步</span>
          </header>
          <div v-if="user.favorites.length" class="favorites__row">
            <div v-for="char in user.favorites" :key="char" class="favorite">
              <RouterLink
                :to="{ path: '/comparator', query: { q: char } }"
                class="favorite__link"
                :aria-label="`在编码对比器中打开 ${char}`"
              >
                {{ char }}
              </RouterLink>
              <button
                class="favorite__remove"
                type="button"
                :aria-label="`取消收藏 ${char}`"
                @click="user.removeFavorite(char)"
              >
                <AppIcon name="close" :size="11" />
              </button>
            </div>
          </div>
          <p v-else class="favorites__empty">还没有收藏的汉字——去编码对比器，点字卡右上角的心形把它收进来。</p>
          <p v-if="user.favorites.length">点击汉字直接跳到编码对比器，点右上角 × 取消收藏。</p>
        </section>

        <section class="settings panel">
          <header class="card-head">
            <h2>偏好设置</h2>
          </header>
          <label class="toggle">
            <span>动画效果</span>
            <input v-model="animationEnabled" type="checkbox" />
            <i aria-hidden="true"></i>
          </label>
          <label class="toggle">
            <span>AI 主动提示</span>
            <input v-model="aiHints" type="checkbox" />
            <i aria-hidden="true"></i>
          </label>
          <p class="settings__note">Phase 2 将持久化到用户配置表。</p>
        </section>
      </div>

      <div class="phase-banner panel">
        <AppIcon name="bulb" :size="20" />
        <p>
          <strong>Phase 2 · M4 已完成：</strong>学习统计与收藏已由后端 FastAPI 持久化（SQLite，按用户隔离）。
          前端请求封装在 <code>src/services/api</code>，类型定义在 <code>src/types/user.ts</code>。
        </p>
      </div>
    </template>
  </div>
</template>

<style scoped>
.profile {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.page-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  padding: 8px 0 4px;
}

.page-head h1 {
  margin: 14px 0 10px;
  font-family: var(--font-serif);
  font-size: clamp(1.9rem, 4vw, 2.6rem);
  letter-spacing: 0.08em;
}

.page-head p {
  max-width: 680px;
  margin: 0;
  font-size: 14px;
  line-height: 1.85;
  color: var(--c-text-dim);
}

.page-head__mark {
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 64px;
  height: 64px;
  border-radius: 18px;
  color: var(--c-cyan);
  background: var(--c-cyan-soft);
  border: 1px solid rgba(0, 240, 255, 0.28);
  box-shadow: var(--shadow-cyan);
}

/* 登录 / 注册 */
.auth {
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(0, 0.95fr);
  gap: 16px;
  align-items: stretch;
}

.auth__intro {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 28px;
  background:
    radial-gradient(80% 120% at 0% 0%, rgba(0, 240, 255, 0.1), transparent 60%),
    var(--c-panel);
}

.auth__intro h2 {
  margin: 0;
  font-family: var(--font-serif);
  font-size: 26px;
  letter-spacing: 0.08em;
}

.auth__intro > p {
  margin: 0;
  font-size: 13px;
  line-height: 1.9;
  color: var(--c-text-dim);
}

.auth__intro ul {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin: 6px 0;
  padding: 0;
  list-style: none;
}

.auth__intro li {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12.5px;
  color: var(--c-text-dim);
}

.auth__intro li :deep(svg) {
  color: var(--c-gold);
}

.auth__notice {
  display: flex;
  gap: 9px;
  margin-top: auto;
  padding: 12px;
  border-radius: 10px;
  border: 1px dashed rgba(255, 204, 0, 0.28);
  background: rgba(255, 204, 0, 0.05);
  font-size: 11.5px;
  line-height: 1.65;
  color: var(--c-text-dim);
}

.auth__notice :deep(svg) {
  flex-shrink: 0;
  color: var(--c-gold);
}

.auth__form {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 26px;
}

.auth__tabs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4px;
  padding: 4px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.auth__tabs button {
  padding: 8px;
  border: none;
  border-radius: 999px;
  background: transparent;
  font-size: 13px;
  color: var(--c-text-dim);
  transition:
    color 0.2s ease,
    background 0.2s ease;
}

.auth__tabs button.is-active {
  color: #04141a;
  background: linear-gradient(120deg, var(--c-cyan), var(--c-green));
  font-weight: 700;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.field span {
  font-size: 11.5px;
  letter-spacing: 0.08em;
  color: var(--c-text-faint);
}

.field input {
  padding: 11px 13px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.03);
  font-size: 13.5px;
  outline: none;
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

.field input:focus {
  border-color: rgba(0, 240, 255, 0.5);
  box-shadow: 0 0 0 3px rgba(0, 240, 255, 0.08);
}

.field input::placeholder {
  color: var(--c-text-faint);
}

.auth__error {
  margin: 0;
  padding: 9px 12px;
  border-radius: 8px;
  background: rgba(255, 93, 115, 0.08);
  border: 1px solid rgba(255, 93, 115, 0.3);
  font-size: 12px;
  color: #ffb3bf;
}

.auth__submit {
  margin-top: 4px;
  width: 100%;
}

.auth__submit:disabled {
  opacity: 0.6;
  cursor: wait;
}

.auth__switch {
  margin: 0;
  text-align: center;
  font-size: 11.5px;
  color: var(--c-text-faint);
}

.auth__switch button {
  border: none;
  background: none;
  padding: 0;
  font-size: inherit;
  color: var(--c-cyan);
}

/* 已登录 */
.profile-head {
  display: flex;
  align-items: center;
  gap: 18px;
  padding: 22px 24px;
}

.avatar {
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 66px;
  height: 66px;
  border-radius: 50%;
  font-family: var(--font-serif);
  font-size: 28px;
  font-weight: 700;
  color: #04141a;
  background: linear-gradient(120deg, var(--c-cyan), var(--c-green));
  box-shadow: 0 0 26px rgba(0, 240, 255, 0.35);
}

.profile-head__meta {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
}

.profile-head__meta h2 {
  margin: 0;
  font-size: 20px;
  letter-spacing: 0.04em;
}

.profile-head__meta p {
  margin: 0;
  font-size: 11.5px;
  color: var(--c-text-faint);
}

.profile-head > .btn {
  margin-left: auto;
}

.stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.stat {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 18px 20px;
}

.stat__label {
  font-size: 11px;
  letter-spacing: 0.1em;
  color: var(--c-text-faint);
}

.stat__value {
  font-size: 30px;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: var(--c-gold);
  text-shadow: 0 0 20px rgba(255, 204, 0, 0.2);
}

.stat__hint {
  font-size: 10.5px;
  color: var(--c-text-faint);
}

.dashboard {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.dashboard section {
  padding: 20px;
}

.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.card-head h2 {
  margin: 0;
  font-size: 14.5px;
  letter-spacing: 0.06em;
}

.progress ul {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.progress__row {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 6px;
  font-size: 12px;
  color: var(--c-text-dim);
}

.progress__row b {
  color: var(--c-cyan);
  font-weight: 600;
}

.progress__track {
  height: 5px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.06);
  overflow: hidden;
}

.progress__track span {
  display: block;
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--c-cyan), var(--c-green));
  box-shadow: 0 0 10px rgba(0, 240, 255, 0.4);
}

.recent ul {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.recent li {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 8px 10px;
  border-left: 2px solid rgba(0, 240, 255, 0.3);
  background: rgba(255, 255, 255, 0.025);
  border-radius: 0 8px 8px 0;
}

.recent strong {
  font-size: 12.5px;
  font-weight: 600;
  color: var(--c-text);
}

.recent span {
  font-size: 11px;
  color: var(--c-text-faint);
}

.favorites__row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.favorite {
  position: relative;
}

.favorite__link {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  border-radius: 10px;
  border: 1px solid rgba(255, 204, 0, 0.22);
  background: rgba(255, 204, 0, 0.06);
  font-family: var(--font-serif);
  font-size: 21px;
  color: var(--c-gold);
  text-decoration: none;
  transition:
    transform 0.2s var(--ease-out),
    box-shadow 0.2s ease,
    border-color 0.2s ease;
}

.favorite__link:hover {
  transform: translateY(-2px);
  border-color: rgba(255, 204, 0, 0.55);
  box-shadow: 0 0 18px rgba(255, 204, 0, 0.18);
}

.favorite__remove {
  position: absolute;
  top: -6px;
  right: -6px;
  display: grid;
  place-items: center;
  width: 18px;
  height: 18px;
  padding: 0;
  border: none;
  border-radius: 50%;
  background: var(--c-panel);
  color: var(--c-text-faint);
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.14);
  cursor: pointer;
  transition: color 0.2s ease;
}

.favorite__remove:hover {
  color: #ffb3bf;
}

.favorites__empty {
  margin: 0;
  font-size: 12px;
  line-height: 1.7;
  color: var(--c-text-faint);
}

.favorites > p {
  margin: 12px 0 0;
  font-size: 11px;
  color: var(--c-text-faint);
}

.toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 9px 0;
  cursor: pointer;
  font-size: 12.5px;
  color: var(--c-text-dim);
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}

.toggle:last-of-type {
  border-bottom: none;
}

.toggle input {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle i {
  position: relative;
  flex-shrink: 0;
  width: 38px;
  height: 21px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.1);
  transition: background 0.2s ease;
}

.toggle i::after {
  content: '';
  position: absolute;
  top: 3px;
  left: 3px;
  width: 15px;
  height: 15px;
  border-radius: 50%;
  background: #c9d4e2;
  transition: transform 0.22s var(--ease-out);
}

.toggle input:checked + i {
  background: linear-gradient(120deg, var(--c-cyan), var(--c-green));
}

.toggle input:checked + i::after {
  transform: translateX(17px);
  background: #04141a;
}

.toggle input:focus-visible + i {
  outline: 2px solid var(--c-cyan);
  outline-offset: 2px;
}

.settings__note {
  margin: 10px 0 0;
  font-size: 10.5px;
  color: var(--c-text-faint);
}

.phase-banner {
  display: flex;
  gap: 12px;
  padding: 16px 20px;
  border-color: rgba(255, 204, 0, 0.22);
  background:
    radial-gradient(90% 160% at 0% 0%, rgba(255, 204, 0, 0.07), transparent 62%),
    var(--c-panel);
}

.phase-banner :deep(svg) {
  flex-shrink: 0;
  color: var(--c-gold);
}

.phase-banner p {
  margin: 0;
  font-size: 12px;
  line-height: 1.75;
  color: var(--c-text-dim);
}

.phase-banner code {
  font-family: var(--font-mono);
  font-size: 10.5px;
  color: var(--c-cyan);
}

@media (max-width: 900px) {
  .auth {
    grid-template-columns: minmax(0, 1fr);
  }

  .dashboard {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (max-width: 720px) {
  .page-head__mark {
    display: none;
  }

  .stats {
    grid-template-columns: minmax(0, 1fr);
  }

  .profile-head {
    flex-wrap: wrap;
  }

  .profile-head > .btn {
    margin-left: 0;
  }
}
</style>
