<script setup lang="ts">
import { computed, ref } from 'vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import EvolutionTimeline from '@/components/timeline/EvolutionTimeline.vue'
import GlyphFigure from '@/components/timeline/GlyphFigure.vue'
import { DEFAULT_CHARACTER, ERAS, TIMELINE_CHARACTERS } from '@/data/eras'

const selectedChar = ref(DEFAULT_CHARACTER)
const selectedEraId = ref(ERAS[0].id)

const character = computed(
  () => TIMELINE_CHARACTERS.find((item) => item.char === selectedChar.value) ?? TIMELINE_CHARACTERS[0],
)
const era = computed(() => ERAS.find((item) => item.id === selectedEraId.value) ?? ERAS[0])
const note = computed(() => character.value.notes[era.value.id] ?? '')

function selectEra(id: string) {
  selectedEraId.value = id
}
</script>

<template>
  <div class="timeline-page page">
    <header class="page-head">
      <div>
        <span class="badge">D3 · 三千年字形长卷</span>
        <h1>汉字演变时间轴</h1>
        <p>
          从商代甲骨上的刀刻，到今天的规范字形，汉字走过了三千多年。选择一个字，看它在不同书体中的写法变化。
        </p>
      </div>
      <span class="page-head__mark" aria-hidden="true">
        <AppIcon name="timeline" :size="34" />
      </span>
    </header>

    <section class="char-picker panel">
      <span class="char-picker__label">选择汉字</span>
      <div class="char-picker__list">
        <button
          v-for="item in TIMELINE_CHARACTERS"
          :key="item.char"
          type="button"
          :class="['char-option', { 'char-option--active': item.char === selectedChar }]"
          @click="selectedChar = item.char"
        >
          <strong>{{ item.char }}</strong>
          <span>{{ item.pinyin }}</span>
        </button>
      </div>
      <p class="char-picker__meaning">{{ character.meaning }}</p>
    </section>

    <section class="timeline-panel panel">
      <header class="timeline-panel__head">
        <div>
          <h2>字体演变，一键考古</h2>
          <p>点击时间轴节点切换朝代；时间轴按朝代等距排列，非等比时间。</p>
        </div>
        <span class="badge">D3.js</span>
      </header>

      <EvolutionTimeline :eras="ERAS" :selected-id="selectedEraId" @select="selectEra" />
    </section>

    <section class="detail">
      <article class="glyph-card panel">
        <div class="glyph">
          <GlyphFigure :char="character.char" :era="era.id" :size="108" />
          <span class="glyph__badge">真实古文字形</span>
        </div>
        <div class="glyph-card__meta">
          <span class="badge">{{ era.dynasty }}</span>
          <h2>{{ era.name }}</h2>
          <p class="glyph-card__period">{{ era.period }}</p>
          <ul class="traits">
            <li v-for="trait in era.traits" :key="trait">{{ trait }}</li>
          </ul>
        </div>
      </article>

      <article class="note-card panel">
        <span class="badge badge--gold">「{{ character.char }}」在这一时期</span>
        <h3>{{ era.name }} · {{ character.pinyin }}</h3>
        <p class="note-card__note">{{ note }}</p>
        <p class="note-card__summary">{{ era.summary }}</p>
      </article>
    </section>

    <section class="strip panel">
      <header class="strip__head">
        <h2>「{{ character.char }}」的字形示意</h2>
        <span class="badge badge--muted">已接入授权真实字形 · CC0 / OFL</span>
      </header>
      <div class="strip__row">
        <button
          v-for="item in ERAS"
          :key="item.id"
          type="button"
          :class="['strip__item', { 'strip__item--active': item.id === selectedEraId }]"
          @click="selectEra(item.id)"
        >
          <span class="strip__era">{{ item.name }}</span>
          <GlyphFigure :char="character.char" :era="item.id" :size="44" />
          <span class="strip__period">{{ item.period }}</span>
        </button>
      </div>
    </section>

    <footer class="footnote">
      <p>
        字形为授权真实字形：甲骨、金文、小篆、隶书来自汉典与中研院小學堂（CC0）摹本，楷书来自霞鹜文楷、简体来自思源宋体（均 SIL
        OFL）。逐字来源见 <code>public/glyphs/CREDITS.md</code> 与 <code>manifest.json</code>，由
        <code>tools/glyphs/build_glyphs.py</code> 生成。
      </p>
    </footer>
  </div>
</template>

<style scoped>
.timeline-page {
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
  color: var(--c-gold);
  background: var(--c-gold-soft);
  border: 1px solid rgba(255, 204, 0, 0.28);
  box-shadow: var(--shadow-gold);
}

/* 汉字选择 */
.char-picker {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 14px;
  padding: 16px 20px;
}

.char-picker__label {
  font-size: 11px;
  letter-spacing: 0.14em;
  color: var(--c-text-faint);
}

.char-picker__list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.char-option {
  display: flex;
  align-items: baseline;
  gap: 7px;
  padding: 6px 14px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.09);
  background: rgba(255, 255, 255, 0.03);
  color: var(--c-text-dim);
  transition:
    color 0.2s ease,
    border-color 0.2s ease,
    background 0.2s ease,
    transform 0.2s var(--ease-out);
}

.char-option strong {
  font-family: var(--font-serif);
  font-size: 20px;
  font-weight: 700;
}

.char-option span {
  font-size: 10px;
  color: var(--c-text-faint);
}

.char-option:hover {
  transform: translateY(-1px);
  border-color: rgba(255, 204, 0, 0.4);
}

.char-option--active {
  color: #1a1300;
  background: linear-gradient(120deg, var(--c-gold), #ffe680);
  border-color: transparent;
  box-shadow: 0 0 20px rgba(255, 204, 0, 0.28);
}

.char-option--active span {
  color: rgba(26, 19, 0, 0.6);
}

.char-picker__meaning {
  margin: 0 0 0 auto;
  font-size: 12px;
  color: var(--c-text-faint);
}

/* 时间轴 */
.timeline-panel {
  padding: 20px 24px 10px;
}

.timeline-panel__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 4px;
}

.timeline-panel__head h2 {
  margin: 0 0 5px;
  font-size: 16px;
  letter-spacing: 0.06em;
}

.timeline-panel__head p {
  margin: 0;
  font-size: 11.5px;
  color: var(--c-text-faint);
}

/* 详情 */
.detail {
  display: grid;
  grid-template-columns: minmax(0, 0.9fr) minmax(0, 1.1fr);
  gap: 14px;
}

.glyph-card {
  display: flex;
  align-items: center;
  gap: 22px;
  padding: 22px;
}

.glyph {
  position: relative;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 168px;
  height: 168px;
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background:
    radial-gradient(circle at 50% 32%, rgba(255, 255, 255, 0.08), transparent 68%),
    rgba(255, 255, 255, 0.025);
  overflow: hidden;
}

.glyph::after {
  content: '';
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.035) 1px, transparent 1px);
  background-size: 18px 18px;
  mask-image: radial-gradient(circle, #000 20%, transparent 72%);
}

.glyph__badge {
  position: absolute;
  right: 10px;
  bottom: 8px;
  z-index: 1;
  padding: 1px 7px;
  border-radius: 999px;
  font-size: 9px;
  letter-spacing: 0.08em;
  color: rgba(233, 242, 251, 0.5);
  background: rgba(0, 0, 0, 0.35);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.glyph-card__meta {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
  min-width: 0;
}

.glyph-card__meta h2 {
  margin: 0;
  font-family: var(--font-serif);
  font-size: 28px;
  letter-spacing: 0.1em;
}

.glyph-card__period {
  margin: 0;
  font-size: 11.5px;
  color: var(--c-text-faint);
}

.traits {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin: 4px 0 0;
  padding: 0;
  list-style: none;
}

.traits li {
  padding: 2px 9px;
  border-radius: 999px;
  font-size: 10.5px;
  color: var(--c-cyan);
  background: var(--c-cyan-soft);
  border: 1px solid rgba(0, 240, 255, 0.18);
}

.note-card {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 10px;
  padding: 22px 24px;
}

.note-card h3 {
  margin: 0;
  font-size: 17px;
  letter-spacing: 0.05em;
}

.note-card__note {
  margin: 0;
  font-size: 14px;
  line-height: 2;
  color: rgba(233, 242, 251, 0.9);
}

.note-card__summary {
  margin: auto 0 0;
  padding-top: 14px;
  border-top: 1px dashed rgba(0, 240, 255, 0.14);
  font-size: 12px;
  line-height: 1.8;
  color: var(--c-text-faint);
}

/* 演变条 */
.strip {
  padding: 18px 20px;
}

.strip__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.strip__head h2 {
  margin: 0;
  font-size: 15px;
  letter-spacing: 0.06em;
}

.strip__row {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 8px;
}

.strip__item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 12px 8px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.07);
  background: rgba(255, 255, 255, 0.02);
  transition:
    border-color 0.2s ease,
    background 0.2s ease,
    transform 0.2s var(--ease-out);
}

.strip__item:hover {
  transform: translateY(-2px);
  border-color: rgba(0, 240, 255, 0.32);
}

.strip__item--active {
  border-color: rgba(255, 204, 0, 0.5);
  background: rgba(255, 204, 0, 0.06);
  box-shadow: 0 0 22px rgba(255, 204, 0, 0.1);
}

.strip__era {
  font-size: 10.5px;
  letter-spacing: 0.08em;
  color: var(--c-text-faint);
}

.strip__period {
  font-size: 8.5px;
  text-align: center;
  line-height: 1.35;
  color: var(--c-text-faint);
}

.footnote {
  padding: 2px;
}

.footnote p {
  margin: 0;
  font-size: 11.5px;
  line-height: 1.8;
  color: var(--c-text-faint);
}

.footnote code {
  font-family: var(--font-mono);
  font-size: 10.5px;
  color: var(--c-text-dim);
}

@media (max-width: 900px) {
  .detail {
    grid-template-columns: minmax(0, 1fr);
  }

  .strip__row {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .page-head__mark {
    display: none;
  }

  .char-picker__meaning {
    margin-left: 0;
    width: 100%;
  }

  .glyph-card {
    flex-direction: column;
    align-items: flex-start;
  }

  .glyph {
    width: 100%;
    height: 160px;
  }

  .timeline-panel {
    padding: 16px 14px 6px;
  }
}
</style>
