<template>
  <div class="chapter-detail-container">

    <header class="detail-minimal-header">
      <div class="back-action-btn" @click="goBack">
        <span class="back-arrow">‹</span> 返回上一页
      </div>
    </header>

    <div class="left-full-sidebar">
      <!-- ① 成效指标卡片 -->
      <div class="metrics-minimal-grid">
        <div class="metric-wrapper-item" v-for="stat in projectData?.indicators?.stats" :key="stat.label">
          <div class="metric-art-title">{{ stat.label }}</div>
          <div class="metric-actual-value">{{ stat.value }}</div>
        </div>
      </div>

      <!-- ② 里程碑时间轴（移至此处，指标下方） -->
      <div class="horizontal-timeline-wrapper">
        <div class="horizontal-timeline-track">
          <div class="timeline-step-node" v-for="step in projectData?.multimedia?.timeSteps" :key="step.year">
            <span class="step-node-year">{{ step.year }}年</span>
            <span class="step-node-dot"></span>
            <span class="step-node-text">{{ step.title }}</span>
          </div>
        </div>
      </div>

      <!-- ③ 视频播放区块 -->
      <div class="media-massive-block video-block">
        <div class="block-head-bar">
          <span class="block-head-icon">🎬</span>
          <span class="block-head-label">工程纪实视频</span>
        </div>
        <div class="video-embed-wrapper">
          <iframe
            :src="projectData?.multimedia?.videoUrl"
            class="video-iframe"
            frameborder="0"
            allowfullscreen
            allow="autoplay; encrypted-media"
            @error="onVideoError"
          ></iframe>
        </div>
      </div>

      <!-- ④ 图片轮播 -->
      <div class="media-massive-block carousel-block" v-if="projectData?.multimedia?.gallery?.length">
        <div class="block-head-bar">
          <span class="block-head-icon">📷</span>
          <span class="block-head-label">工程一线实景纪实</span>
          <span class="carousel-counter">{{ carouselIndex + 1 }} / {{ projectData.multimedia.gallery.length }}</span>
        </div>
        <div class="carousel-stage" @mouseenter="stopCarousel" @mouseleave="startCarousel">
          <transition name="fade-cross" mode="out-in">
            <div class="carousel-slide" :key="carouselIndex">
              <img
                :src="projectData.multimedia.gallery[carouselIndex].src"
                :alt="projectData.multimedia.gallery[carouselIndex].caption"
                class="carousel-img"
                @error="onImgError"
              />
              <div class="carousel-caption-bar">
                {{ projectData.multimedia.gallery[carouselIndex].caption }}
              </div>
            </div>
          </transition>
        </div>
        <div class="carousel-dots">
          <span
            v-for="(_img, idx) in projectData.multimedia.gallery"
            :key="idx"
            class="carousel-dot"
            :class="{ 'is-active': idx === carouselIndex }"
            @click="carouselIndex = idx"
          ></span>
        </div>
      </div>
    </div>

    <!-- 右下角：文字叙事区（移除工程发展历程） -->
    <div class="right-bottom-text-narrative-zone">

      <div class="floating-brief-vertical-stack">
        <section class="minimal-brief-section">
          <h4 class="brief-title-tag">工程立项背景</h4>
          <p class="brief-paragraph-text">{{ projectData?.baseInfo?.bgText }}</p>
        </section>

        <section class="minimal-brief-section">
          <h4 class="brief-title-tag">核心治理举措</h4>
          <p class="brief-paragraph-text">{{ projectData?.indicators?.measures }}</p>
        </section>

        <section class="minimal-brief-section">
          <h4 class="brief-title-tag">地理与空间跨度</h4>
          <p class="brief-paragraph-text">{{ projectData?.baseInfo?.areaDesc }}</p>
        </section>
      </div>

      <div class="giant-headline-row-right">
        <h2 class="narrative-giant-title">{{ projectData?.baseInfo?.fullName }}</h2>
      </div>
    </div>

    <!-- 右上角 -->
    <div class="map-top-right-vacuum-zone">
      <div class="vacuum-gis-tip">[ 实时联动：OpenLayers WMS 工程边界已加载 ]</div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ecoDatabase from '../assets/data/ecoprojects.json'

const route = useRoute()
const router = useRouter()

const targetId = ref(route.params.id || 'sanbei')
const projectData = computed(() => ecoDatabase.projects.find(p => p.id === targetId.value))

// 🎠 图片轮播
const carouselIndex = ref(0)
let carouselTimer = null
const intervalMs = 3500

function startCarousel() {
  stopCarousel()
  const gallery = projectData.value?.multimedia?.gallery
  if (!gallery || gallery.length <= 1) return
  carouselTimer = setInterval(() => {
    carouselIndex.value = (carouselIndex.value + 1) % gallery.length
  }, intervalMs)
}
function stopCarousel() {
  clearInterval(carouselTimer)
}

// 切换工程时重置轮播
watch(() => targetId.value, () => {
  carouselIndex.value = 0
  startCarousel()
})

onMounted(() => {
  const appNavBar = document.querySelector('.top-minimal-nav-bar')
  if (appNavBar) appNavBar.style.display = 'none'

  // 仅显示当前工程的边界（高亮实色填充，由 filterBoundaryProject 统一处理）
  if (window.filterBoundaryProject) {
    window.filterBoundaryProject(targetId.value)
  }
  // 🗺️ 保持全国视角居中偏右，左侧面板不遮挡中国大陆
  const map = window.olMap
  if (map && window.ol) {
    map.getView().animate({
      center: window.ol.proj.fromLonLat([96.0, 37.0]),
      zoom: 4.5,
      duration: 1200
    })
  }
  startCarousel()
})

onUnmounted(() => {
  stopCarousel()
  const appNavBar = document.querySelector('.top-minimal-nav-bar')
  if (appNavBar) appNavBar.style.display = 'flex'
  // 🗺️ 返回时缩放到全国范围
  const map = window.olMap
  if (map && window.ol) {
    map.getView().animate({
      center: window.ol.proj.fromLonLat([104.0, 35.0]),
      zoom: 5,
      duration: 1200
    })
  }
})

function onImgError(e) {
  e.target.style.display = 'none'
}
function onVideoError(e) {
  // iframe 加载失败，静默处理
}
function goBack() {
  stopCarousel()
  // 先清状态，再导航
  if (window.filterBoundaryProject) window.filterBoundaryProject(null)
  router.push('/')
}
</script>

<style scoped>
/* ==================== FULL-WIDTH BOTTOM GRADIENT SYSTEM ==================== */
.chapter-detail-container {
  position: fixed;
  top: 0; left: 0; width: 100vw; height: 100vh;
  z-index: 9;
  pointer-events: none;
  user-select: none;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

.chapter-detail-container::before {
  content: "";
  position: absolute;
  top: 0; left: 0; width: 100%; height: 100%;
  background: linear-gradient(to right,
    rgba(39, 51, 56, 0.98) 0%,
    rgba(39, 51, 56, 0.92) 25%,
    rgba(43, 87, 72, 0.25) 45%,
    rgba(43, 87, 72, 0) 65%
  );
  z-index: 1;
}

.chapter-detail-container::after {
  content: "";
  position: absolute;
  bottom: 0; left: 0;
  width: 100vw;
  height: 45vh;
  background: linear-gradient(to top,
    rgba(10, 25, 16, 0.92) 0%,
    rgba(10, 25, 16, 0.70) 30%,
    rgba(10, 25, 16, 0.35) 65%,
    rgba(10, 25, 16, 0) 100%
  );
  z-index: 1;
}

/* ==================== 1. 顶部导航区 ==================== */
.detail-minimal-header {
  position: absolute;
  top: 0; left: 0; width: 100%; height: 70px;
  display: flex; align-items: center;
  padding: 0 45px; box-sizing: border-box;
  z-index: 10;
  pointer-events: auto;
}
.back-action-btn {
  display: flex; align-items: center; gap: 6px; cursor: pointer;
  font-size: 15px; font-weight: 600; color: #9CB080; transition: color 0.2s;
}
.back-action-btn:hover { color: #ffffff; }
.back-arrow { font-size: 26px; line-height: 0; position: relative; top: -1px; }

/* ==================== 2. 左侧大面板 ==================== */
.left-full-sidebar {
  pointer-events: auto;
  position: absolute;
  top: 75px; left: 45px; width: 34%; height: calc(100vh - 100px);
  box-sizing: border-box; display: flex; flex-direction: column; gap: 10px;
  z-index: 3;
}

/* ① 指标卡片行 */
.metrics-minimal-grid {
  display: flex; gap: 12px; background: rgba(255, 255, 255, 0.01);
  padding: 8px 0; border-bottom: 1px solid rgba(156, 176, 128, 0.15);
  flex-shrink: 0;
}
.metric-wrapper-item { display: flex; flex-direction: column; gap: 2px; flex: 1; }
.metric-art-title { font-size: 11px; font-weight: 500; color: #9CB080; opacity: 0.7; }
.metric-actual-value { font-size: 22px; font-weight: 700; color: #ffffff; font-family: 'Impact', sans-serif; }

/* ② 时间轴 */
.horizontal-timeline-wrapper {
  background: rgba(39, 51, 56, 0.4); border: 1px solid rgba(156, 176, 128, 0.15);
  border-radius: 4px; padding: 10px 12px; flex-shrink: 0;
}
.horizontal-timeline-track { display: flex; justify-content: space-between; gap: 8px; }
.timeline-step-node { display: flex; flex-direction: column; align-items: center; gap: 3px; flex: 1; }
.step-node-year { font-size: 11px; font-weight: 700; color: #618764; font-family: monospace; }
.step-node-dot { width: 4px; height: 4px; background: rgba(255,255,255,0.35); border-radius: 50%; }
.step-node-text { font-size: 10px; color: rgba(255,255,255,0.6); text-align: center; white-space: nowrap; }

/* 通用媒体块 */
.media-massive-block {
  position: relative; background: rgba(39, 51, 56, 0.85);
  border: 1px solid rgba(156, 176, 128, 0.15); border-radius: 6px; overflow: hidden;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
  flex-shrink: 0;
  display: flex; flex-direction: column;
}
.block-head-bar {
  display: flex; align-items: center; gap: 8px; padding: 8px 12px;
  border-bottom: 1px solid rgba(156, 176, 128, 0.12);
  flex-shrink: 0;
}
.block-head-icon { font-size: 14px; }
.block-head-label { font-size: 12px; font-weight: 600; color: rgba(255,255,255,0.85); flex: 1; }

/* ③ 视频区块 */
.video-block { flex: 1.5; min-height: 0; }
.video-embed-wrapper { flex: 1; position: relative; background: #000; min-height: 0; }
.video-iframe { position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: none; }

/* ④ 轮播区块 */
.carousel-block { flex: 1.2; min-height: 0; }
.carousel-counter { font-size: 10px; color: rgba(255,255,255,0.4); font-family: monospace; }
.carousel-stage { flex: 1; position: relative; overflow: hidden; min-height: 0; }
.carousel-slide { position: absolute; top: 0; left: 0; width: 100%; height: 100%; }
.carousel-img { width: 100%; height: 100%; object-fit: cover; display: block; }
.carousel-caption-bar {
  position: absolute; bottom: 0; left: 0; right: 0;
  background: linear-gradient(to top, rgba(0,0,0,0.8), transparent);
  color: rgba(255,255,255,0.9); font-size: 11px; font-weight: 500;
  padding: 20px 10px 6px; text-align: center;
}

.carousel-dots {
  display: flex; justify-content: center; gap: 6px;
  padding: 8px 0; flex-shrink: 0;
}
.carousel-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: rgba(255,255,255,0.25); cursor: pointer; transition: all 0.25s;
}
.carousel-dot.is-active { background: #2ecc71; transform: scale(1.4); }

/* 轮播过渡 */
.fade-cross-enter-active, .fade-cross-leave-active { transition: opacity 0.4s ease; }
.fade-cross-enter-from, .fade-cross-leave-to { opacity: 0; }

/* ==================== 3. 右下角：纯文字叙事区 ==================== */
.right-bottom-text-narrative-zone {
  position: absolute;
  bottom: 0; right: 0;
  z-index: 3;
  pointer-events: auto;
  padding: 0 45px 50px 0;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 20px;
  width: 560px;
  background: none !important;
}

.floating-brief-vertical-stack {
  display: flex; flex-direction: column; gap: 22px; width: 100%;
}
.minimal-brief-section {
  display: flex; flex-direction: column; gap: 6px; text-align: right;
}
.brief-title-tag {
  font-size: 15px; font-weight: 800; margin: 0; letter-spacing: 2px; padding-right: 10px;
  color: #2ecc71;
  border-right: 3px solid #2ecc71; line-height: 1;
}
.brief-paragraph-text {
  font-size: 14px;
  font-weight: 500;
  line-height: 1.8;
  color: rgba(255, 255, 255, 0.95);
  margin: 0;
  text-align: justify;
}

/* 底部大标题行 */
.giant-headline-row-right {
  display: flex; align-items: baseline; justify-content: flex-end;
  gap: 14px; white-space: nowrap; width: 100%; margin-top: 4px;
}
.narrative-giant-title {
  font-size: 46px; font-weight: 900; margin: 0; letter-spacing: -1.5px;
  background: linear-gradient(to bottom, #ffffff 30%, #9CB080 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

/* ==================== 4. 右上角 ==================== */
.map-top-right-vacuum-zone {
  position: absolute;
  top: 0; right: 0; width: 64vw; height: calc(100vh - 320px); z-index: 2;
  box-sizing: border-box; padding: 100px 45px 0 0;
  display: flex; justify-content: flex-end; align-items: flex-start;
}
.vacuum-gis-tip {
  font-size: 11px; font-family: monospace; color: #618764;
  background: rgba(39, 51, 56, 0.85); padding: 5px 10px; border-radius: 3px;
  border: 1px solid rgba(156, 176, 128, 0.2); backdrop-filter: blur(4px);
}
</style>
