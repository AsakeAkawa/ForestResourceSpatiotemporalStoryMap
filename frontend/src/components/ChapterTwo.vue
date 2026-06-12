<template>
  <div class="fullscreen-interactive-layer">
    <div ref="tooltipElement" class="map-tooltip"></div>
    
    <div class="top-mission-banner" v-if="activePointId === null">
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
      <transition name="poster-smooth">
        <div v-if="activePoint" class="epic-text-layout" :key="activePoint.id">
          
          <div class="fullscreen-dark-blur"></div>

          <button class="minimal-close-btn" @click="closeArchive">✕</button>
          
          <div class="text-main-body">
            
            <h1 class="story-title">{{ activePoint.detailTitle }}</h1>
            
            <div class="story-sub-banner">
              <span class="line-left"></span>
              <span class="sub-text">建设节点 · {{ activePoint.year }}年</span>
              <span class="line-right"></span>
            </div>
            
            <div class="quote-container">
              <p class="story-paragraph">{{ activePoint.detailText }}</p>
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
import { ref, onMounted, onUnmounted, computed, watch, defineEmits } from 'vue'
import { useRouter } from 'vue-router'

import Feature from 'ol/Feature'
import Point from 'ol/geom/Point'
import VectorSource from 'ol/source/Vector'
import VectorLayer from 'ol/layer/Vector'
import { fromLonLat } from 'ol/proj'
import { Style, Circle, Fill, Stroke } from 'ol/style'
import Overlay from 'ol/Overlay'

const router = useRouter()
const emit = defineEmits(['toggle-immersive'])
const options = { maxOpacityOnActive: 0.5, maxDistance: 120000, activeOn: 30000 }

const pointsData = ref([
  {
    id: 'saihanba',
    name: '塞罕坝机械林场',
    detailTitle: '塞罕坝 · 筑起绿色长城的防线',
    year: '2002',
    detailText: '三代人，大半个世纪。他们在高原荒漠上顶风冒雪，硬是用青春和汗水将漫天黄沙改写成了广袤无垠的万顷林海。',
    img: 'https://images.unsplash.com/photo-1542273917363-3b1817f69a2d?auto=format&fit=crop&w=1600&q=80',
    geoCoord: [117.2, 42.4],
    currentOpacity: 0
  },
  {
    id: 'youyu',
    name: '右玉县防护林',
    detailTitle: '山西右玉 · 塞上不毛之地的蜕变',
    year: '2006',
    detailText: '在风沙肆虐的黄土高原死角，全县人民持之以恒数十载。迎风栽树，背风造林，终将贫瘠不毛之地拓荒成璀璨的生态绿洲。',
    img: 'https://images.unsplash.com/photo-1502082553048-f009c37129b9?auto=format&fit=crop&w=1600&q=80',
    geoCoord: [112.4, 40.0],
    currentOpacity: 0
  }
])

const activePointId = ref(null)
const tooltipElement = ref(null)
const activePoint = computed(() => pointsData.value.find(p => p.id === activePointId.value))

watch(activePointId, (newId) => {
  const status = newId !== null
  emit('toggle-immersive', status)
  window.dispatchEvent(new CustomEvent('global-immersive-toggle', { detail: status }))
})

const closeArchive = () => {
  activePointId.value = null
}

let mainMapInstance = null 
let tooltipOverlay = null
let vectorLayer = null

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
    
    feat.setStyle(new Style({
      image: new Circle({
        radius: 10,
        fill: new Fill({ color: '#2ecc71' }),
        stroke: new Stroke({ color: '#ffffff', width: 2 })
      })
    }))
    subSource.addFeature(feat)
  })

  vectorLayer = new VectorLayer({ source: subSource })
  vectorLayer.set('name', 'chapter-two-sub-layer')
  vectorLayer.setZIndex(999) 
  mainMapInstance.addLayer(vectorLayer)

  mainMapInstance.on('pointermove', handleMapPointerMove)
  mainMapInstance.on('click', handleMapClick)
}

function handleMapPointerMove(evt) {
  if (evt.dragging || !mainMapInstance) return
  const mouseCoord = evt.coordinate
  const pixel = evt.pixel
  if (!mouseCoord || !pixel) return

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
  emit('toggle-immersive', false)
  window.dispatchEvent(new CustomEvent('global-immersive-toggle', { detail: false }))
  if (mainMapInstance) {
    mainMapInstance.un('pointermove', handleMapPointerMove)
    mainMapInstance.un('click', handleMapClick)
    if (tooltipOverlay) mainMapInstance.removeOverlay(tooltipOverlay)
    if (vectorLayer) mainMapInstance.removeLayer(vectorLayer)
  }
})
</script>

<style scoped>
/* 🌐 直接引入公共网络字体源（思源宋体高级变体），确保任何人打开网页均能正常显示艺术字 */
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;700&display=swap');

.story-title, .story-paragraph, .sub-text {
  font-family: 'Noto Serif SC', serif;
}

.fullscreen-interactive-layer { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; pointer-events: none; z-index: 9; }
.map-tooltip { display: none; background: rgba(27, 77, 47, 0.9); color: white; padding: 6px 14px; border-radius: 4px; font-size: 13px; font-weight: bold; white-space: nowrap; box-shadow: 0 4px 12px rgba(0,0,0,0.3); pointer-events: none; z-index: 99; border: 1px solid rgba(255,255,255,0.2); }
.top-mission-banner { pointer-events: auto; position: absolute; top: 105px; left: 50%; transform: translateX(-50%); background: rgba(10, 25, 16, 0.8); backdrop-filter: blur(4px); border: 1px solid rgba(46, 204, 113, 0.2); color: white; padding: 8px 20px; border-radius: 20px; font-size: 12px; z-index: 10; }

.fullscreen-backgrounds { position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 1; }
.full-bg-element { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background-size: cover; background-position: center; transition: opacity 0.6s cubic-bezier(0.16, 1, 0.3, 1); }

.fullscreen-text-canvas { position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 3; }
.epic-text-layout { pointer-events: auto; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; position: relative; box-sizing: border-box; }

/* 🎛️ 覆盖全屏的暗色透明毛玻璃背景带（增强过渡羽化） */
.fullscreen-dark-blur {
  position: absolute;
  inset: 0;
  width: 100vw;
  height: 100vh;
  /* 整体微调，四角做大范围透明淡出渐变，保证底图信息不流失 */
  background: radial-gradient(
    circle at center, 
    rgba(6, 18, 12, 0.65) 0%, 
    rgba(6, 18, 12, 0.5) 60%, 
    rgba(6, 18, 12, 0) 100%
  );
  backdrop-filter: blur(8px);
  z-index: -1;
}

/* ✕ 右上角经典关闭按钮样式 */
.minimal-close-btn { 
  position: absolute; 
  top: 120px; 
  right: 5%; 
  background: none; 
  border: none; 
  color: rgba(255, 255, 255, 0.6); 
  font-size: 16px; 
  cursor: pointer; 
  transition: color 0.2s, transform 0.2s;
  z-index: 15;
}
.minimal-close-btn:hover { 
  color: #ffffff; 
  transform: scale(1.15);
}

/* 主体文字盒子 */
.text-main-body { 
  max-width: 900px; 
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
}

/* 大标题 */
.story-title { 
  color: #ffffff; 
  font-size: 50px; 
  font-weight: 500; 
  margin: 0 0 20px 0; 
  letter-spacing: 4px;
  text-shadow: 0 4px 15px rgba(0,0,0,0.5); 
}

/* 副标题 */
.story-sub-banner {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  gap: 25px;
  margin-bottom: 40px;
}
.story-sub-banner .line-left,
.story-sub-banner .line-right {
  width: 70px;
  height: 1px;
  background: rgba(255, 255, 255, 0.25);
}
.story-sub-banner .sub-text {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.8);
  letter-spacing: 6px; 
}

/* 正文段落 */
.quote-container {
  max-width: 700px;
  margin-bottom: 35px;
}
.story-paragraph { 
  color: rgba(255,255,255,0.9); 
  font-size: 17px; 
  line-height: 2.3; 
  margin: 0 0 25px 0; 
  text-align: center;
  letter-spacing: 1.5px;
  text-shadow: 0 2px 8px rgba(0,0,0,0.6); 
}
.photo-courtesy {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.35);
  letter-spacing: 1px;
  margin: 0;
}

/* 底部极简查看详情链接 */
.view-more-btn { 
  background: transparent;
  color: rgba(255, 255, 255, 0.65); 
  border-bottom: 1px dashed rgba(255, 255, 255, 0.3);
  border-top: none; border-left: none; border-right: none;
  padding: 6px 8px; 
  font-size: 12px;
  letter-spacing: 2px;
  cursor: pointer; 
  transition: all 0.3s ease; 
}
.view-more-btn:hover { 
  color: #2ecc71;
  border-bottom-color: #2ecc71;
  transform: translateY(-1px);
}

/* 入场过渡动效 */
.poster-smooth-enter-active,
.poster-smooth-leave-active { 
  transition: all 0.7s cubic-bezier(0.16, 1, 0.3, 1); 
}
.poster-smooth-enter-from, 
.poster-smooth-leave-to { 
  opacity: 0; 
  transform: scale(1.02);
}
</style>