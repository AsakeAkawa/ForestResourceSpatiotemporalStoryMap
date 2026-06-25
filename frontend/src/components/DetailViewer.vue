<template>
  <div class="chapter-detail-container">
    
    <header class="detail-minimal-header">
      <div class="back-action-btn" @click="goBack">
        <span class="back-arrow">‹</span> 返回上一页
      </div>
    </header>

    <div class="left-full-sidebar">
      <div class="metrics-minimal-grid">
        <div class="metric-wrapper-item" v-for="stat in projectData?.indicators?.stats" :key="stat.label">
          <div class="metric-art-title">{{ stat.label }}</div>
          <div class="metric-actual-value">{{ stat.value }}</div>
        </div>
      </div>

      <div class="media-massive-block placeholder-style">
        <div class="placeholder-inside-view">
          <span class="placeholder-icon">🛰️</span>
          <span class="placeholder-main-text">LANDSAT / MODIS 历史遥感影像演变对比</span>
          <span class="wait-status-tag">内容待插入</span>
        </div>
      </div>

      <div class="horizontal-timeline-wrapper">
        <div class="horizontal-timeline-track">
          <div class="timeline-step-node" v-for="step in projectData?.multimedia?.timeSteps" :key="step.year">
            <span class="step-node-year">{{ step.year }}年</span>
            <span class="step-node-dot"></span>
            <span class="step-node-text">{{ step.title }}</span>
          </div>
        </div>
      </div>

      <div class="media-massive-block placeholder-style">
        <div class="placeholder-inside-view">
          <span class="placeholder-icon">📺</span>
          <span class="placeholder-main-text">现场一线生态无人机高清纪实视频</span>
          <span class="wait-status-tag">内容待插入</span>
        </div>
      </div>
    </div>

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

    <div class="map-top-right-vacuum-zone">
      <div class="vacuum-gis-tip">[ 实时联动：OpenLayers 动态矢量边界已加载 ]</div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ecoDatabase from '../assets/data/ecoprojects.json' 

const route = useRoute()
const router = useRouter()

const targetId = ref(route.params.id || 'saihanba')
const projectData = computed(() => ecoDatabase.projects.find(p => p.id === targetId.value))

let demoVectorLayer = null

const projectGeoMockData = {
  saihanba: { center: [117.25, 42.40], coords: [[116.9, 42.1], [117.6, 42.2], [117.7, 42.6], [117.1, 42.6], [116.9, 42.1]] },
  youyu: { center: [112.45, 40.00], coords: [[112.1, 39.7], [112.7, 39.8], [112.8, 40.3], [112.2, 40.2], [112.1, 39.7]] }
}

onMounted(() => {
  const appNavBar = document.querySelector('.top-minimal-nav-bar')
  if (appNavBar) appNavBar.style.display = 'none'

  const map = window.olMap
  const olData = window.ol
  if (map && olData) {
    const geoInfo = projectGeoMockData[targetId.value] || projectGeoMockData['saihanba']
    const compensatedCenter = [geoInfo.center[0] - 4.5, geoInfo.center[1] - 0.8]
    
    map.getView().animate({
      center: olData.proj.fromLonLat(compensatedCenter),
      zoom: 6,
      duration: 1200
    })

    const polygonCoords = geoInfo.coords.map(pt => olData.proj.fromLonLat(pt))
    const feature = new olData.Feature({
      geometry: new olData.geom.LineString(polygonCoords)
    })

    feature.setStyle(new olData.style.Style({
      stroke: new olData.style.Stroke({ color: '#618764', width: 3, lineDash: [6, 4] }),
      fill: new olData.style.Fill({ color: 'rgba(156, 176, 128, 0.05)' })
    }))

    const vectorSource = new olData.source.Vector({ features: [feature] })
    demoVectorLayer = new olData.layer.Vector({ source: vectorSource, zIndex: 10 })
    
    map.addLayer(demoVectorLayer)
  }
})

onUnmounted(() => {
  const appNavBar = document.querySelector('.top-minimal-nav-bar')
  if (appNavBar) appNavBar.style.display = 'flex'

  const map = window.olMap
  if (map && demoVectorLayer) {
    map.removeLayer(demoVectorLayer)
  }
})

function goBack() {
  router.push('/')
}
</script>

<style scoped>
/* ==================== 🌳 FULL-WIDTH BOTTOM GRADIENT SYSTEM (V11) ==================== */
.chapter-detail-container {
  position: fixed;
  top: 0; left: 0; width: 100vw; height: 100vh;
  z-index: 9;
  pointer-events: none; 
  user-select: none;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

/* 🌓 左侧固有过渡带（只负责左侧多媒体面板背景保护） */
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

/* 💥 核心变革：横向 100% 贯穿整个大屏底部的无边界深度渐变 */
/* 它和左侧过渡带在底部十字交叉，形成一个极度自然、柔和的 L 型暗色遮罩视界，无任何硬边缘线条 */
.chapter-detail-container::after {
  content: "";
  position: absolute;
  bottom: 0; left: 0; 
  width: 100vw; 
  height: 45vh; /* 遮罩高度占屏幕下半部分 45% */
  background: linear-gradient(to top, 
    rgba(10, 25, 16, 0.92) 0%,   /* 最底部加深到 92%，确保文字托得极稳 */
    rgba(10, 25, 16, 0.70) 30%, 
    rgba(10, 25, 16, 0.35) 65%, 
    rgba(10, 25, 16, 0) 100%     /* 向上平滑消隐，完全透明 */
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
  top: 75px; left: 45px; width: 32%; height: calc(100vh - 100px);
  box-sizing: border-box; display: flex; flex-direction: column; gap: 18px; 
  z-index: 3; /* 高于底层渐变板 */
}
.media-massive-block {
  flex: 1.5; position: relative; background: rgba(39, 51, 56, 0.85);
  border: 1px solid rgba(156, 176, 128, 0.15); border-radius: 6px; overflow: hidden;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
}
.placeholder-inside-view {
  width: 100%; height: 100%; display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: 8px; color: #9CB080;
  padding: 20px; box-sizing: border-box; text-align: center;
}
.placeholder-main-text { font-size: 14px; font-weight: 600; color: rgba(255,255,255,0.9); line-height: 1.4; }
.wait-status-tag {
  font-size: 11px; font-weight: bold; background: rgba(97, 135, 100, 0.3); 
  padding: 2px 8px; border-radius: 3px; color: #9CB080; border: 1px solid rgba(156, 176, 128, 0.2);
}
.metrics-minimal-grid {
  display: flex; gap: 20px; background: rgba(255, 255, 255, 0.01);
  padding: 10px 0; border-bottom: 1px solid rgba(156, 176, 128, 0.15);
}
.metric-wrapper-item { display: flex; flex-direction: column; gap: 4px; }
.metric-art-title { font-size: 13px; font-weight: 500; color: #9CB080; opacity: 0.7; }
.metric-actual-value { font-size: 26px; font-weight: 700; color: #ffffff; font-family: 'Impact', sans-serif; }

.horizontal-timeline-wrapper {
  background: rgba(39, 51, 56, 0.4); border: 1px solid rgba(156, 176, 128, 0.15); border-radius: 4px; padding: 12px 14px;
}
.horizontal-timeline-track { display: flex; justify-content: space-between; gap: 12px; }
.timeline-step-node { display: flex; flex-direction: column; align-items: center; gap: 4px; flex: 1; }
.step-node-year { font-size: 12px; font-weight: 700; color: #618764; font-family: monospace; }
.step-node-dot { width: 5px; height: 5px; background: rgba(255,255,255,0.35); border-radius: 50%; }
.step-node-text { font-size: 11px; color: rgba(255,255,255,0.65); text-align: center; white-space: nowrap; }

/* ==================== 3. 右下角：纯文字排版叙事区 ==================== */
.right-bottom-text-narrative-zone {
  position: absolute;
  bottom: 0; right: 0; 
  z-index: 3; /* 提至全局底层渐变之上，确保文本文字清晰可点 */
  pointer-events: auto;
  padding: 0 45px 50px 0; 
  box-sizing: border-box;
  display: flex; 
  flex-direction: column; 
  align-items: flex-end; 
  gap: 25px;
  width: 520px; 
  background: none !important; /* 彻底移除方块背景，改由全屏大底托住 */
}

/* 简介文本垂直叠放 */
.floating-brief-vertical-stack {
  display: flex; flex-direction: column; gap: 24px; width: 100%;
}
.minimal-brief-section {
  display: flex; flex-direction: column; gap: 8px; text-align: right; 
}
.brief-title-tag {
  font-size: 14px; font-weight: 800; margin: 0; letter-spacing: 2px; padding-right: 10px; 
  color: #2ecc71; /* 使用高德/OSM 导航同款高饱和翠绿标签 */
  border-right: 3px solid #2ecc71; line-height: 1; 
}

/* 💥 绝对整齐划一：三个简介正文在全局贯穿底部大渐变的映衬下，无论切到什么复杂的白底图都能完美护航 */
.brief-paragraph-text { 
  font-size: 14px; 
  font-weight: 500; 
  line-height: 1.7; 
  color: rgba(255, 255, 255, 0.95); 
  margin: 0; 
  text-align: justify;
}

/* 底部大标题行 */
.giant-headline-row-right {
  display: flex; align-items: baseline; justify-content: flex-end; 
  gap: 15px; white-space: nowrap; width: 100%; margin-top: 5px;
}
.active-project-code {
  font-size: 18px; font-weight: 800; color: #2ecc71; font-family: monospace; letter-spacing: 1px;
}
.narrative-giant-title {
  font-size: 50px; font-weight: 900; margin: 0; letter-spacing: -1.5px;
  
  /* ✨ 完美保全：大标题高级、微妙的由白到中度灰绿的文字渐变色 */
  background: linear-gradient(to bottom, #ffffff 30%, #9CB080 100%);
  -webkit-background-clip: text; 
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

/* ==================== 4. 右上角：OpenLayers 地图物理穿透盲区 ==================== */
.map-top-right-vacuum-zone {
  position: absolute;
  top: 0; right: 0; width: 64vw; height: calc(100vh - 300px); z-index: 2;
  box-sizing: border-box; padding: 100px 45px 0 0;
  display: flex; justify-content: flex-end; align-items: flex-start;
}
.vacuum-gis-tip {
  font-size: 11px; font-family: monospace; color: #618764;
  background: rgba(39, 51, 56, 0.85); padding: 5px 10px; border-radius: 3px;
  border: 1px solid rgba(156, 176, 128, 0.2); backdrop-filter: blur(4px);
}
</style>