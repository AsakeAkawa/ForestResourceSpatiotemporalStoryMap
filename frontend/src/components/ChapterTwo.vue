<template>
  <div class="fullscreen-interactive-layer">
    <div ref="tooltipElement" class="map-tooltip"></div>

    <div class="top-mission-banner" v-if="!activePoint">
      <span class="pulse-icon">📍</span>
      <span><strong>重大生态工程：</strong>鼠标悬停工程区域高亮边界，点击区域查看详情档案。</span>
    </div>

    <div class="legend-panel" v-if="!activePoint">
      <div class="legend-item legend-all" @click="filterProject(null)">
        <span class="legend-check" :class="{ active: selectedProject === null }"></span>
        <span class="legend-label">全部显示</span>
      </div>
      <div class="legend-item" v-for="p in projects" :key="p.id" @click="filterProject(p.id)">
        <span class="legend-check" :class="{ active: selectedProject === p.id }" :style="{ borderColor: p.color }"></span>
        <span class="legend-label">{{ p.name }}</span>
      </div>
    </div>

    <!-- 背景图：悬停时半透明，选中时全屏展示 -->
    <div class="fullscreen-backgrounds" :class="{ 'is-dimmed': activePoint !== null }">
      <div
        v-for="p in projects"
        :key="p.id"
        class="full-bg-element"
        :style="{
          backgroundImage: `url(${p.img})`,
          opacity: activePoint?.id === p.id ? 1 : (hoveredProject === p.id ? 0.45 : 0)
        }"
      ></div>
    </div>

    <!-- 沉浸式档案卡片 -->
    <div class="fullscreen-text-canvas">
      <transition name="poster-smooth">
        <div v-if="activePoint" class="epic-text-layout" :key="activePoint.id">
          <div class="fullscreen-dark-blur"></div>
          <button class="minimal-close-btn" @click="closeArchive">✕</button>
          <div class="text-main-body">
            <h1 class="story-title">{{ activePoint.name }}</h1>
            <div class="story-sub-banner">
              <span class="line-left"></span>
              <span class="sub-text">{{ activePoint.tags[0] }} · {{ activePoint.startYear }}年</span>
              <span class="line-right"></span>
            </div>
            <div class="quote-container">
              <p class="story-paragraph">{{ activePoint.baseInfo.bgText }}</p>
              <p class="photo-courtesy">数据源：GEE & Landsat 联合观测</p>
            </div>
            <div class="poster-footer-action">
              <button class="view-more-btn" @click="goToDetail(activePoint.id)">
                查看详情 ➔
              </button>
            </div>
          </div>
        </div>
      </transition>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Style, Fill, Stroke } from 'ol/style'
import Overlay from 'ol/Overlay'
import ecoDatabase from '../assets/data/ecoprojects.json'

const router = useRouter()

const projectImages = {
  sanbei: '/images/ecoprojects/sanbei/04_status_2.jpg',
  tianranlin: '/images/ecoprojects/tianranlin/06_forest_protection.jpg',
  tuigenghuanlin: '/images/ecoprojects/tuigenghuanlin/07_2020_shaanxi.jpg',
  tumuhauncao: '/images/ecoprojects/tumuhauncao/06_result_2.jpg'
}

const projects = ecoDatabase.projects.map(p => ({
  id: p.id,
  name: p.name,
  color: p.wmsColor || '#2ecc71',
  img: projectImages[p.id] || ''
}))

const allProjects = ecoDatabase.projects

const selectedProject = ref(null)
const hoveredProject = ref(null)
const activePointId = ref(null)
const tooltipElement = ref(null)
const activePoint = computed(() => allProjects.find(p => p.id === activePointId.value))

function filterProject(id) {
  selectedProject.value = id
  Object.keys(defaultStyleCache).forEach(k => delete defaultStyleCache[k])
  lastHoveredId = null
  if (window.filterBoundaryProject) {
    window.filterBoundaryProject(id)
  }
}

function closeArchive() {
  activePointId.value = null
}

function goToDetail(id) {
  router.push({ name: 'Detail', params: { id } })
}

let mainMapInstance = null
let tooltipOverlay = null
let lastHoveredId = null
const defaultStyleCache = {}

function makeHoverStyle(color) {
  return new Style({
    stroke: new Stroke({ color, width: 5 }),
    fill: new Fill({ color: color + '66' })
  })
}

function handlePointerMove(evt) {
  if (evt.dragging || !mainMapInstance) return
  const boundaryLayers = window.boundaryLayers
  if (!boundaryLayers) return

  let found = null
  const pixel = evt.pixel

  for (const [id, layer] of Object.entries(boundaryLayers)) {
    if (!layer.getVisible()) continue
    const feature = mainMapInstance.forEachFeatureAtPixel(pixel, f => f, {
      layerFilter: l => l === layer
    })
    if (feature) { found = id; break }
  }

  const cfg = window.projectLayerConfigs?.find(c => c.id === found) || {}
  const color = cfg.color || '#2ecc71'

  if (lastHoveredId && lastHoveredId !== found) {
    const prevLayer = boundaryLayers[lastHoveredId]
    if (prevLayer && defaultStyleCache[lastHoveredId]) {
      prevLayer.setStyle(defaultStyleCache[lastHoveredId])
    }
  }

  if (found && found !== lastHoveredId) {
    const layer = boundaryLayers[found]
    if (!defaultStyleCache[found] && layer) {
      defaultStyleCache[found] = layer.getStyle()
    }
    if (layer) layer.setStyle(makeHoverStyle(color))
  }

  lastHoveredId = found
  hoveredProject.value = found

  if (found) {
    const proj = projects.find(p => p.id === found)
    if (proj) {
      tooltipElement.value.innerText = proj.name
      tooltipOverlay.setPosition(evt.coordinate)
      tooltipElement.value.style.display = 'block'
    }
  } else {
    if (tooltipElement.value) tooltipElement.value.style.display = 'none'
  }
}

function handleClick(evt) {
  if (!mainMapInstance) return
  const boundaryLayers = window.boundaryLayers
  if (!boundaryLayers) return

  for (const [id, layer] of Object.entries(boundaryLayers)) {
    if (!layer.getVisible()) continue
    const feature = mainMapInstance.forEachFeatureAtPixel(evt.pixel, f => f, {
      layerFilter: l => l === layer
    })
    if (feature) {
      activePointId.value = id
      window.dispatchEvent(new CustomEvent('global-immersive-toggle', { detail: true }))
      return
    }
  }
  // 点击空白关闭
  activePointId.value = null
  window.dispatchEvent(new CustomEvent('global-immersive-toggle', { detail: false }))
}

onMounted(() => {
  const searchMap = () => {
    if (window.olMap) {
      mainMapInstance = window.olMap
      tooltipOverlay = new Overlay({
        element: tooltipElement.value,
        positioning: 'bottom-center',
        offset: [0, -15],
        stopEvent: false
      })
      mainMapInstance.addOverlay(tooltipOverlay)
      mainMapInstance.on('pointermove', handlePointerMove)
      mainMapInstance.on('click', handleClick)
      if (window.filterBoundaryProject) window.filterBoundaryProject(null)
    } else {
      setTimeout(searchMap, 100)
    }
  }
  searchMap()
})

onUnmounted(() => {
  window.dispatchEvent(new CustomEvent('global-immersive-toggle', { detail: false }))
  if (mainMapInstance) {
    mainMapInstance.un('pointermove', handlePointerMove)
    mainMapInstance.un('click', handleClick)
    if (tooltipOverlay) mainMapInstance.removeOverlay(tooltipOverlay)
  }
  if (window.filterBoundaryProject) window.filterBoundaryProject(null)
  const boundaryLayers = window.boundaryLayers
  if (boundaryLayers && lastHoveredId) {
    const layer = boundaryLayers[lastHoveredId]
    if (layer && defaultStyleCache[lastHoveredId]) {
      layer.setStyle(defaultStyleCache[lastHoveredId])
    }
  }
  lastHoveredId = null
})
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;700&display=swap');

.story-title, .story-paragraph, .sub-text {
  font-family: 'Noto Serif SC', serif;
}

.fullscreen-interactive-layer { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; pointer-events: none; z-index: 9; }
.map-tooltip { display: none; background: rgba(27, 77, 47, 0.9); color: white; padding: 6px 14px; border-radius: 4px; font-size: 13px; font-weight: bold; white-space: nowrap; box-shadow: 0 4px 12px rgba(0,0,0,0.3); pointer-events: none; z-index: 99; border: 1px solid rgba(255,255,255,0.2); }
.top-mission-banner { pointer-events: auto; position: absolute; top: 105px; left: 50%; transform: translateX(-50%); background: rgba(10, 25, 16, 0.8); backdrop-filter: blur(4px); border: 1px solid rgba(46, 204, 113, 0.2); color: white; padding: 8px 20px; border-radius: 20px; font-size: 12px; z-index: 10; }

.legend-panel { pointer-events: auto; position: absolute; bottom: 30px; right: 30px; display: flex; flex-direction: column; gap: 8px; z-index: 10; background: rgba(10, 25, 16, 0.75); backdrop-filter: blur(6px); border: 1px solid rgba(255,255,255,0.1); border-radius: 10px; padding: 14px 18px; }
.legend-item { display: flex; align-items: center; gap: 10px; cursor: pointer; padding: 4px 6px; border-radius: 6px; transition: background 0.2s; }
.legend-item:hover { background: rgba(255,255,255,0.06); }
.legend-all { border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 10px; margin-bottom: 2px; }
.legend-check { width: 18px; height: 18px; border-radius: 4px; border: 2px solid rgba(255,255,255,0.3); flex-shrink: 0; transition: all 0.2s; position: relative; }
.legend-check.active { border-color: #2ecc71; background: rgba(46,204,113,0.3); }
.legend-check.active::after { content: '✓'; position: absolute; top: -2px; left: 3px; font-size: 14px; color: #2ecc71; font-weight: bold; }
.legend-label { font-size: 14px; color: rgba(255,255,255,0.9); font-weight: 600; letter-spacing: 1.5px; }

.fullscreen-backgrounds { position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 1; }
.full-bg-element { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background-size: cover; background-position: center; transition: opacity 0.6s cubic-bezier(0.16, 1, 0.3, 1); will-change: opacity; }

.fullscreen-text-canvas { position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 3; }
.epic-text-layout { pointer-events: auto; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; position: relative; box-sizing: border-box; }

.fullscreen-dark-blur {
  position: absolute; inset: 0; width: 100vw; height: 100vh;
  background: radial-gradient(circle at center, rgba(6, 18, 12, 0.65) 0%, rgba(6, 18, 12, 0.5) 60%, rgba(6, 18, 12, 0) 100%);
  z-index: -1;
}

.minimal-close-btn { position: absolute; top: 120px; right: 5%; background: none; border: none; color: rgba(255, 255, 255, 0.6); font-size: 16px; cursor: pointer; transition: color 0.2s, transform 0.2s; z-index: 15; }
.minimal-close-btn:hover { color: #ffffff; transform: scale(1.15); }

.text-main-body { max-width: 900px; text-align: center; display: flex; flex-direction: column; align-items: center; }

.story-title { color: #ffffff; font-size: 50px; font-weight: 500; margin: 0 0 20px 0; letter-spacing: 4px; text-shadow: 0 4px 15px rgba(0,0,0,0.5); }

.story-sub-banner { display: flex; align-items: center; justify-content: center; width: 100%; gap: 25px; margin-bottom: 40px; }
.story-sub-banner .line-left, .story-sub-banner .line-right { width: 70px; height: 1px; background: rgba(255, 255, 255, 0.25); }
.story-sub-banner .sub-text { font-size: 13px; color: rgba(255, 255, 255, 0.8); letter-spacing: 6px; }

.quote-container { max-width: 700px; margin-bottom: 35px; }
.story-paragraph { color: rgba(255,255,255,0.9); font-size: 17px; line-height: 2.3; margin: 0 0 25px 0; text-align: center; letter-spacing: 1.5px; text-shadow: 0 2px 8px rgba(0,0,0,0.6); }
.photo-courtesy { font-size: 11px; color: rgba(255, 255, 255, 0.35); letter-spacing: 1px; margin: 0; }

.view-more-btn { background: transparent; color: rgba(255, 255, 255, 0.65); border-bottom: 1px dashed rgba(255, 255, 255, 0.3); border-top: none; border-left: none; border-right: none; padding: 6px 8px; font-size: 12px; letter-spacing: 2px; cursor: pointer; transition: all 0.3s ease; }
.view-more-btn:hover { color: #2ecc71; border-bottom-color: #2ecc71; transform: translateY(-1px); }

.poster-smooth-enter-active, .poster-smooth-leave-active { transition: all 0.7s cubic-bezier(0.16, 1, 0.3, 1); }
.poster-smooth-enter-from, .poster-smooth-leave-to { opacity: 0; transform: scale(1.02); }
</style>
