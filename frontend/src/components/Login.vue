<template>
  <div class="login-fullscreen">
    <div class="login-bg"></div>
    <div class="login-overlay"></div>

    <div class="top-credit">
      FOREST RESOURCE SPATIOTEMPORAL STORY MAP · 1980–2026
    </div>

    <div class="login-center-stage">
      <transition name="stage-swap" mode="out-in">
        <div v-if="!showTransitionStage" :key="showForm ? 'form' : 'title'">
          <div v-if="!showForm" class="hero-title-block">
            <div class="clean-container">
              <div class="title-accent-line"></div>
              <h1 class="brand-headline">山河复翠</h1>
              <p class="brand-subtitle">中国生态修复工程四十载时空演变地图</p>
              <p class="group-signature">——第二组呈现——</p>
              <div class="cta-button" @click="revealForm">
                <span>进入平台</span>
                <span class="cta-arrow">→</span>
              </div>
            </div>
          </div>

          <div v-else class="login-card-wrapper">
            <div class="login-card clean-container">
              <h2 class="card-heading">身份认证</h2>
              <div class="input-field">
                <label>用户名</label>
                <input
                  v-model="username"
                  type="text"
                  placeholder="请输入用户名"
                  ref="usernameInput"
                  autocomplete="username"
                />
              </div>
              <div class="input-field">
                <label>密码</label>
                <input
                  v-model="password"
                  type="password"
                  placeholder="请输入密码"
                  @keyup.enter="handleLoginClick"
                  autocomplete="current-password"
                />
              </div>
              <button class="submit-btn-cta" @click="handleLoginClick" :disabled="isLoggingIn">
                <span>{{ isLoggingIn ? '正在验证身份...' : '登录并开启复翠之旅' }}</span>
                <span class="cta-arrow" v-if="!isLoggingIn">→</span>
              </button>
              <p v-if="errorMsg" class="error-tip">{{ errorMsg }}</p>
              <p class="back-link" @click="backToTitle">← 返回门户说明</p>
            </div>
          </div>
        </div>
      </transition>
    </div>

    <transition name="fade">
      <div v-if="showTransitionStage" class="narrative-transition-stage">
        <div class="narrative-container">
          
          <template v-if="currentStage === 1">
            <div 
              v-for="(line, index) in pageOneLines" 
              :key="'p1-' + index" 
              class="narrative-line"
              :class="{ 'visible': true, 'typing-active': currentLineIndex === index }"
            >
              {{ displayedLines[index] }}
            </div>
          </template>

          <template v-if="currentStage === 2">
            <div class="quote-block">
              <p class="quote-text typing-active">{{ displayedQuoteText }}</p>
              <p v-if="showAuthor" class="quote-author">——习近平</p>
            </div>
          </template>

          <transition name="fade-slow">
            <div v-if="showFinalTrigger" class="final-trigger-zone" @click="enterPlatformMain">
              <div class="final-text-btn">
                <span>进入平台</span>
                <span class="text-arrow">→</span>
              </div>
            </div>
          </transition>

          <p v-if="!showFinalTrigger" class="skip-hint">按 空格 跳过</p>

        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const showForm = ref(false)
const username = ref('')
const password = ref('')
const errorMsg = ref('')
const isLoggingIn = ref(false)
const usernameInput = ref(null)

// --- 打字机多段控制状态机 ---
const showTransitionStage = ref(false)
const currentStage = ref(1) 
const currentLineIndex = ref(0)
const showAuthor = ref(false)
const showFinalTrigger = ref(false)

// 💡 第一页文案：已调整为四行，人工林大国成就单独成行
const pageOneLines = [
  "森林是陆地生态系统的主体，对碳汇、水源涵养、生物多样性保护具有重要意义。",
  "自20世纪80年代以来，中国实施了三北防护林、天然林保护、退耕还林等一系列重大生态工程，森林覆盖率从12%提升到超过24%。",
  "至2024年，森林面积达到2.2亿公顷，森林蓄积量超过194亿立方米。",
  "中国人工林面积保持世界首位，对全球增绿贡献率超过四分之一。"
]
const displayedLines = ref(['', '', '', ''])

// 第二页文案（金句）
const quoteTextSource = "「为山川大地增添锦绣，让中国式现代化底色更加亮丽。」"
const displayedQuoteText = ref('')

const skipRequested = ref(false)
let activeTypeInterval = null
let activeDelayTimeout = null
let resolveDelay = null

function revealForm() {
  showForm.value = true
  nextTick(() => {
    usernameInput.value?.focus()
  })
}

function backToTitle() {
  showForm.value = false
  errorMsg.value = ''
  username.value = ''
  password.value = ''
}

function handleLoginClick() {
  errorMsg.value = ''

  if (!username.value.trim()) {
    errorMsg.value = '请输入用户名'
    return
  }
  if (!password.value.trim()) {
    errorMsg.value = '请输入密码'
    return
  }

  isLoggingIn.value = true

  setTimeout(() => {
    localStorage.setItem('forest_isLoggedIn', 'true')
    localStorage.setItem('forest_username', username.value.trim())
    isLoggingIn.value = false
    
    showTransitionStage.value = true
    startNarrativeTimeline()
  }, 600)
}

// 控制全局大纪事时间轴
async function startNarrativeTimeline() {
  skipRequested.value = false

  // === 【第一页】 逐字打印四行字 ===
  currentStage.value = 1
  for (let i = 0; i < pageOneLines.length; i++) {
    if (skipRequested.value) break
    currentLineIndex.value = i
    await typeLine(i, pageOneLines[i])
    if (!skipRequested.value) await delay(700)
  }

  if (skipRequested.value) {
    await skipToEnd()
    return
  }

  await delay(1200)
  if (skipRequested.value) { await skipToEnd(); return }

  // === 【过渡】 切到第二页 ===
  currentStage.value = 0
  await delay(800)
  currentStage.value = 2

  // === 【第二页】 打印金句 ===
  await typeQuote(quoteTextSource)
  if (!skipRequested.value) {
    await delay(400)
    showAuthor.value = true
    await delay(2500)
  } else {
    await skipToEnd()
    return
  }

  // === 【第三页】 展现纯文字进入平台按钮 ===
  showFinalTrigger.value = true
}

async function skipToEnd() {
  // 清除所有正在进行的打字/延时定时器
  if (activeTypeInterval) { clearInterval(activeTypeInterval); activeTypeInterval = null }
  if (activeDelayTimeout) { clearTimeout(activeDelayTimeout); activeDelayTimeout = null }

  // 立即显示所有第一页文案全文
  if (currentStage.value === 1) {
    for (let i = 0; i < pageOneLines.length; i++) {
      displayedLines.value[i] = pageOneLines[i]
    }
  }

  // 立即显示第二页金句全文
  displayedQuoteText.value = quoteTextSource
  showAuthor.value = true

  // 直接进入第三页
  currentStage.value = 2
  await delay(600)
  showFinalTrigger.value = true
}

function typeLine(lineIdx, fullText) {
  return new Promise((resolve) => {
    let charIdx = 0
    activeTypeInterval = setInterval(() => {
      charIdx++
      displayedLines.value[lineIdx] = fullText.substring(0, charIdx)
      if (charIdx >= fullText.length || skipRequested.value) {
        clearInterval(activeTypeInterval)
        activeTypeInterval = null
        // 跳过时直接显示全文
        if (skipRequested.value) displayedLines.value[lineIdx] = fullText
        resolve()
      }
    }, 85)
  })
}

function typeQuote(fullText) {
  return new Promise((resolve) => {
    let charIdx = 0
    activeTypeInterval = setInterval(() => {
      charIdx++
      displayedQuoteText.value = fullText.substring(0, charIdx)
      if (charIdx >= fullText.length || skipRequested.value) {
        clearInterval(activeTypeInterval)
        activeTypeInterval = null
        if (skipRequested.value) displayedQuoteText.value = fullText
        resolve()
      }
    }, 95)
  })
}

function enterPlatformMain() {
  router.push('/')
}

function handleKeyDown(e) {
  if (e.code === 'Space' && showTransitionStage.value && !showFinalTrigger.value) {
    e.preventDefault()
    skipRequested.value = true
    // 立即中断当前正在等待的 delay
    if (resolveDelay) {
      resolveDelay()
      resolveDelay = null
    }
    if (activeDelayTimeout) {
      clearTimeout(activeDelayTimeout)
      activeDelayTimeout = null
    }
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
})

function delay(ms) {
  return new Promise(resolve => {
    resolveDelay = resolve
    activeDelayTimeout = setTimeout(() => {
      activeDelayTimeout = null
      resolveDelay = null
      resolve()
    }, ms)
  })
}
</script>

<style scoped>
.login-fullscreen {
  position: fixed;
  inset: 0;
  width: 100vw;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", "PingFang SC", sans-serif;
  user-select: none;
  background-color: #040a06;
}

/* ==================== 基础背景 ==================== */
.login-bg {
  position: absolute;
  inset: 0;
  z-index: 0;
  background: url('/forest-bg.jpg') center/cover no-repeat;
}

.login-overlay {
  position: absolute;
  inset: 0;
  z-index: 1;
  background:
    radial-gradient(ellipse at 50% 40%, transparent 10%, rgba(5, 13, 8, 0.55) 100%),
    linear-gradient(to bottom, rgba(5, 13, 8, 0.3) 0%, rgba(5, 13, 8, 0.1) 40%, rgba(5, 13, 8, 0.65) 100%);
  backdrop-filter: blur(6px) saturate(115%);
  -webkit-backdrop-filter: blur(6px) saturate(115%);
  pointer-events: none;
}

/* ==================== 顶部品牌 ==================== */
.top-credit {
  position: absolute;
  top: 36px;
  left: 0;
  width: 100%;
  text-align: center;
  z-index: 3;
  font-size: 11px;
  font-weight: 400;
  letter-spacing: 5px;
  color: rgba(180, 210, 190, 0.35);
  pointer-events: none;
}

/* ==================== 中心舞台 ==================== */
.login-center-stage {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 450px;
}

/* ==================== 纯净无边界容器 ==================== */
.clean-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  box-sizing: border-box;
  background: transparent !important;
  backdrop-filter: none !important;
  -webkit-backdrop-filter: none !important;
  border: none !important;
  box-shadow: none !important;
}

.hero-title-block .clean-container {
  padding: 20px;
}

.title-accent-line {
  width: 80px;
  height: 2px;
  background: linear-gradient(90deg, transparent, #2ecc71, transparent);
  margin-bottom: 32px;
  opacity: 0.8;
}

.brand-headline {
  font-size: 84px;
  font-weight: 900;
  letter-spacing: 20px;
  margin: 0;
  line-height: 1.15;
  text-indent: 20px;
  background: linear-gradient(to bottom, #ffffff 40%, #c4dec3 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  filter: drop-shadow(0 4px 15px rgba(0,0,0,0.6));
}

.brand-subtitle {
  font-size: 19px;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.9);
  margin: 24px 0 0 0;
  letter-spacing: 4px;
  text-shadow: 0 2px 8px rgba(0,0,0,0.5);
}

.group-signature {
  font-size: 13px;
  font-weight: 400;
  color: rgba(180, 200, 185, 0.55);
  margin: 28px 0 0 0;
  letter-spacing: 3px;
  font-style: italic;
}

/* ==================== 统一后的高级 CTA 风格按钮 ==================== */
.cta-button, .submit-btn-cta {
  margin-top: 56px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 12px 28px;
  border-radius: 24px;
  color: #2ecc71;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 4px;
  cursor: pointer;
  transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1);
  border: 1px solid rgba(46, 204, 113, 0.25);
  background: rgba(46, 204, 113, 0.02);
  outline: none;
}

.submit-btn-cta {
  width: 100%; 
  margin-top: 36px;
  font-family: inherit;
}

.cta-button:hover, .submit-btn-cta:hover:not(:disabled) {
  color: #fff;
  background: rgba(46, 204, 113, 0.2);
  border-color: rgba(46, 204, 113, 0.6);
  box-shadow: 0 0 20px rgba(46, 204, 113, 0.25);
}

.submit-btn-cta:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.cta-arrow {
  font-size: 16px;
  transition: transform 0.3s ease;
}

.cta-button:hover .cta-arrow, .submit-btn-cta:hover .cta-arrow {
  transform: translateX(6px);
}

/* ==================== 状态切换动画 ==================== */
.stage-swap-enter-active,
.stage-swap-leave-active {
  transition: all 0.5s cubic-bezier(0.16, 1, 0.3, 1);
}

.stage-swap-enter-from {
  opacity: 0;
  transform: scale(0.98) translateY(8px);
}

.stage-swap-leave-to {
  opacity: 0;
  transform: scale(1.01) translateY(-8px);
}

/* ==================== 身份认证输入项 ==================== */
.login-card-wrapper .login-card {
  width: 380px;
  padding: 20px 10px;
}

.card-heading {
  font-size: 24px;
  font-weight: 600;
  color: #ffffff;
  margin: 0 0 40px 0;
  letter-spacing: 6px;
  text-indent: 6px;
  text-shadow: 0 2px 8px rgba(0,0,0,0.5);
}

.input-field {
  margin-bottom: 32px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
}

.input-field label {
  font-size: 12px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.55);
  letter-spacing: 2px;
}

.input-field input {
  width: 100%;
  padding: 8px 0;
  background: transparent !important;
  border: none;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 0;
  color: #ffffff;
  font-size: 15px;
  outline: none;
  transition: all 0.3s ease;
  box-sizing: border-box;
}

.input-field input:focus {
  border-bottom-color: #2ecc71;
}

.error-tip {
  color: #ff6b6b;
  font-size: 13px;
  text-align: center;
  margin: 16px 0 0 0;
}

.back-link {
  color: rgba(255, 255, 255, 0.45);
  font-size: 13px;
  text-align: center;
  margin: 32px 0 0 0;
  cursor: pointer;
  transition: color 0.25s ease;
  letter-spacing: 2px;
}

.back-link:hover {
  color: #2ecc71;
}

/* ==================== 透光防焦虑过渡场景 ==================== */
.narrative-transition-stage {
  position: fixed;
  inset: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(4, 12, 7, 0.45); 
  z-index: 999;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 0 12%;
  box-sizing: border-box;
}

.narrative-container {
  width: 100%;
  max-width: 950px; /* 四行时略微加宽容器，保证在大屏上排版舒展 */
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.narrative-line {
  font-size: 20px; 
  line-height: 1.9;
  color: #ffffff;
  letter-spacing: 3px; 
  white-space: pre-wrap;
  text-align: left;
  text-shadow: 0 3px 12px rgba(0, 0, 0, 0.8); 
}

/* 第二页：习近平总书记金句专属美化排版 */
.quote-block {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 0;
}

.quote-text {
  font-size: 26px; 
  font-weight: 500;
  line-height: 1.8;
  color: #e3f5e2; 
  letter-spacing: 4px;
  text-align: center;
  text-shadow: 0 4px 15px rgba(0, 0, 0, 0.9);
}

.quote-author {
  margin-top: 32px;
  font-size: 16px;
  color: rgba(255, 255, 255, 0.6);
  letter-spacing: 3px;
  align-self: flex-end;
  margin-right: 10%;
  animation: fadeIn 1s forwards;
}

/* 当前正在打印的那一行的尾部闪烁光标 */
.narrative-line.typing-active::after, .quote-text.typing-active::after {
  content: '┃';
  color: #2ecc71;
  font-weight: bold;
  display: inline-block;
  margin-left: 4px;
  animation: blink 0.7s infinite;
}

/* 💡 第三页：全新去边框极简“进入平台”纯文字按钮 */
.final-trigger-zone {
  width: 100%;
  display: flex;
  justify-content: center;
  margin-top: 40px;
}

.final-text-btn {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  padding: 12px 32px;
  color: #2ecc71;
  font-size: 18px; /* 文字略微放大以显质感 */
  font-weight: 600;
  letter-spacing: 4px;
  cursor: pointer;
  background: transparent;
  border: none;
  transition: all 0.35s ease;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.5);
}

.final-text-btn:hover {
  color: #ffffff;
  text-shadow: 0 0 15px rgba(46, 204, 113, 0.8);
  transform: translateY(-2px);
}

.text-arrow {
  font-size: 20px;
  transition: transform 0.35s cubic-bezier(0.16, 1, 0.3, 1);
}

.final-text-btn:hover .text-arrow {
  transform: translateX(8px);
}

@keyframes blink { 50% { opacity: 0; } }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

/* 过渡动画 */
.fade-enter-active, .fade-leave-active { transition: opacity 0.6s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.fade-slow-enter-active { transition: opacity 1.5s ease-in; }
.fade-slow-enter-from { opacity: 0; }

/* ==================== 跳过提示 ==================== */
.skip-hint {
  position: absolute;
  bottom: 60px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 13px;
  letter-spacing: 2px;
  color: rgba(255, 255, 255, 0.25);
  margin: 0;
  pointer-events: none;
  animation: hintPulse 3s ease-in-out infinite;
}

@keyframes hintPulse {
  0%, 100% { opacity: 0.25; }
  50% { opacity: 0.55; }
}
</style>