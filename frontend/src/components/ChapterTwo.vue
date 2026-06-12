<template>
  <div class="fullscreen-interactive-layer">
    <div ref="tooltipElement" class="map-tooltip"></div>
    
    <div class="top-mission-banner">
      <span class="pulse-icon">📍</span>
      <span><strong>重大生态工程：</strong>鼠标靠近站点触发感应，点击站点解锁档案并可查看详情。</span>
    </div>

    <div class="fullscreen-backgrounds" :class="{ 'is-dimmed': activePointId !== null }">
      <div 
        v-for="point in pointsData" 
        :key="point.id"
        class="full-bg-element"
        :style="{ 
          backgroundImage: `url(${point.img})`,
          opacity: activePointId === point.id ? 1 : point.currentOpacity 
        }"
      ></div>
    </div>

    <div class="fullscreen-text-canvas">
      <transition name="ppt-slide-down">
        <div v-if="activePoint" class="epic-text-layout" :key="activePoint.id">
          <button class="minimal-close-btn" @click="activePointId = null">✕ 退出档案</button>
          
          <div class="text-main-body">
            <div class="year-badge">✨ 建设节点 · {{ activePoint.year }}</div>
            <h1 class="story-title">{{ activePoint.detailTitle }}</h1>
            <div class="story-line"></div>
            <p class="story-paragraph">{{ activePoint.detailText }}</p>
            
            <button class="view-more-btn" @click="goToDetail(activePoint.id)">
              查看详情内容 ➔
            </button>
          </div>
        </div>
      </transition>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'

// 🌟 直接局部导入 OpenLayers 核心模块，彻底断绝全局变量挂载不上的隐患
import Feature from 'ol/Feature'
import Point from 'ol/geom/Point'
import VectorSource from 'ol/source/Vector'
import VectorLayer from 'ol/layer/Vector'
import { fromLonLat } from 'ol/proj'
import { Style, Circle, Fill, Stroke } from 'ol/style'
import Overlay from 'ol/Overlay'

const router = useRouter()
const options = { maxOpacityOnActive: 0.4, maxDistance: 120000, activeOn: 30000 }

const pointsData = ref([
  {
    id: 'saihanba',
    name: '塞罕坝机械林场',
    detailTitle: '塞罕坝：三代人铸就的绿色防线',
    year: '2002年',
    detailText: '位于河北北部，三代塞罕坝人顶风冒雪，创造了荒原变林海的生态奇迹。',
    img: 'https://images.unsplash.com/photo-1542273917363-3b1817f69a2d?auto=format&fit=crop&w=1600&q=80',
    geoCoord: [117.2, 42.4],
    currentOpacity: 0
  },
  {
    id: 'youyu',
    name: '右玉县防护林',
    detailTitle: '山西右玉：不毛之地变塞上绿洲',
    year: '2006年',
    detailText: '山西右玉县地处毛乌素沙漠边缘，全县人民坚持不懈植树造林。',
    img: 'https://images.unsplash.com/photo-1502082553048-f009c37129b9?auto=format&fit=crop&w=1600&q=80',
    geoCoord: [112.4, 40.0],
    currentOpacity: 0
  }
])

const activePointId = ref(null)
const tooltipElement = ref(null)
const activePoint = computed(() => pointsData.value.find(p => p.id === activePointId.value))

let mainMapInstance = null 
let tooltipOverlay = null
let vectorLayer = null

onMounted(() => {
  const searchMap = () => {
    // 只需要确保全局地图实例加载成功
    if (window.olMap) {
      mainMapInstance = window.olMap
      
      // 初始化提示浮层
      tooltipOverlay = new Overlay({
        element: tooltipElement.value,
        positioning: 'bottom-center',
        offset: [0, -15],
        stopEvent: false
      })
      mainMapInstance.addOverlay(tooltipOverlay)
      
      setupLayerAndListeners()
    } else { 
      setTimeout(searchMap, 100) 
    }
  }
  searchMap()
})

function setupLayerAndListeners() {
  const subSource = new VectorSource()

  pointsData.value.forEach(pt => {
    pt.projectedCoord = fromLonLat(pt.geoCoord)
    const feat = new Feature({
      geometry: new Point(pt.projectedCoord),
      isSubPoint: true,
      subPointId: pt.id,
      name: pt.name
    })
    
    // 使用直接导入的 Style 模块
    feat.setStyle(new Style({
      image: new Circle({
        radius: 10,  // 稍微调大半径，确保视觉上更明显
        fill: new Fill({ color: '#2ecc71' }),
        stroke: new Stroke({ color: '#ffffff', width: 2 })
      })
    }))
    subSource.addFeature(feat)
  })

  vectorLayer = new VectorLayer({ source: subSource })
  vectorLayer.set('name', 'chapter-two-sub-layer')
  
  // 🌟 核心点：提升子图层的层级，确保它不会被底图或者其他默认层压在底下
  vectorLayer.setZIndex(999) 
  
  mainMapInstance.addLayer(vectorLayer)

  // 绑定事件
  mainMapInstance.on('pointermove', handleMapPointerMove)
  mainMapInstance.on('click', handleMapClick)
}

function handleMapPointerMove(evt) {
  if (evt.dragging || !mainMapInstance) return
  const mouseCoord = evt.coordinate
  const pixel = evt.pixel
  if (!mouseCoord || !pixel) return

  // 1. 空间距离感应
  pointsData.value.forEach(pt => {
    if (!pt.projectedCoord) return
    const dx = mouseCoord[0] - pt.projectedCoord[0]
    const dy = mouseCoord[1] - pt.projectedCoord[1]
    const dist = Math.sqrt(dx * dx + dy * dy)
    
    if (dist <= options.activeOn) pt.currentOpacity = options.maxOpacityOnActive
    else if (dist <= options.maxDistance) {
      pt.currentOpacity = ((options.maxDistance - dist) / (options.maxDistance - options.activeOn)) * options.maxOpacityOnActive
    } else pt.currentOpacity = 0
  })

  // 2. 悬浮名称提示
  const feature = mainMapInstance.forEachFeatureAtPixel(pixel, (f) => f)
  if (feature && feature.get('isSubPoint')) {
    tooltipElement.value.innerText = feature.get('name')
    tooltipOverlay.setPosition(evt.coordinate)
    tooltipElement.value.style.display = 'block'
  } else {
    if (tooltipElement.value) tooltipElement.value.style.display = 'none'
  }
}

function handleMapClick(evt) {
  if (!mainMapInstance) return
  const feature = mainMapInstance.forEachFeatureAtPixel(evt.pixel, (f) => f)
  if (feature && feature.get('isSubPoint')) {
    const id = feature.get('subPointId')
    activePointId.value = activePointId.value === id ? null : id
  } else { 
    activePointId.value = null 
  }
}

function goToDetail(id) {
  router.push({ name: 'Detail', params: { id } })
}

onUnmounted(() => {
  if (mainMapInstance) {
    mainMapInstance.un('pointermove', handleMapPointerMove)
    mainMapInstance.un('click', handleMapClick)
    if (tooltipOverlay) mainMapInstance.removeOverlay(tooltipOverlay)
    if (vectorLayer) mainMapInstance.removeLayer(vectorLayer)
  }
})
</script>

<style scoped>
/* 保持原样式不变 */
.fullscreen-interactive-layer { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; pointer-events: none; z-index: 9; }
.map-tooltip { display: none; background: rgba(27, 77, 47, 0.9); color: white; padding: 6px 14px; border-radius: 4px; font-size: 13px; font-weight: bold; white-space: nowrap; box-shadow: 0 4px 12px rgba(0,0,0,0.3); pointer-events: none; z-index: 99; border: 1px solid rgba(255,255,255,0.2); }
.top-mission-banner { pointer-events: auto; position: absolute; top: 105px; left: 50%; transform: translateX(-50%); background: rgba(0, 0, 0, 0.6); color: white; padding: 6px 18px; border-radius: 20px; font-size: 12px; z-index: 10; }
.fullscreen-backgrounds { position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 1; transition: background-color 0.5s ease; }
.fullscreen-backgrounds.is-dimmed { background-color: rgba(0, 0, 0, 0.85); }
.full-bg-element { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background-size: cover; background-position: center; mix-blend-mode: multiply; transition: opacity 0.25s linear; }
.fullscreen-text-canvas { position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 2; }
.epic-text-layout { pointer-events: auto; width: 100%; height: 100%; padding: 10% 12%; display: flex; flex-direction: column; justify-content: center; }
.ppt-slide-down-enter-active { transition: all 0.7s cubic-bezier(0.16, 1, 0.3, 1); }
.ppt-slide-down-enter-from { transform: translateY(-80px); opacity: 0; }
.minimal-close-btn { position: absolute; top: 120px; right: 5%; background: none; border: none; color: rgba(255,255,255,0.7); font-size: 14px; cursor: pointer; transition: color 0.2s; }
.minimal-close-btn:hover { color: white; }
.text-main-body { max-width: 700px; }
.year-badge { font-size: 14px; font-weight: bold; color: #2ecc71; margin-bottom: 10px; letter-spacing: 1px; }
.story-title { color: white; font-size: 42px; margin: 0 0 20px 0; font-weight: 800; text-shadow: 0 2px 10px rgba(0,0,0,0.5); }
.story-line { width: 50px; height: 4px; background: #2ecc71; margin-bottom: 30px; box-shadow: 0 0 8px #2ecc71; }
.story-paragraph { color: rgba(255,255,255,0.9); font-size: 18px; line-height: 1.9; margin-bottom: 40px; text-shadow: 0 1px 5px rgba(0,0,0,0.5); }
.view-more-btn { background: #2ecc71; color: white; border: none; padding: 12px 32px; border-radius: 30px; font-weight: bold; cursor: pointer; transition: all 0.25s ease; box-shadow: 0 4px 15px rgba(46, 204, 113, 0.3); }
.view-more-btn:hover { background: #27ae60; transform: translateY(-2px); box-shadow: 0 6px 20px rgba(46, 204, 113, 0.5); }
</style>