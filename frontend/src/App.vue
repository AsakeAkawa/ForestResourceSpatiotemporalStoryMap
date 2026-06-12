<template>
  <div class="story-map-container">
    
    <div class="top-minimal-nav-bar" :class="{ 'ui-hidden': isImmersiveMode }">
      <div class="nav-links-container">
        <span 
          v-for="(chapter, index) in chapters" 
          :key="index"
          :class="{ active: currentIndex === index }"
          @click="switchPage(index)"
          class="nav-item"
        >
          {{ chapter.navName }}
        </span>
      </div>
    </div>

    <div class="map-source-selector" :class="{ 'ui-hidden': isImmersiveMode }">
      <div 
        v-for="source in mapSources" 
        :key="source.id"
        class="selector-item"
        :class="{ active: currentSourceId === source.id }"
        @click="changeMapSource(source.id)"
      >
        {{ source.name }}
      </div>
    </div>

    <div v-if="$route.path === '/'" class="chapter-component-container">
      <transition name="fade-layer" mode="out-in">
        <component 
          :is="activeComponent" 
          @toggle-immersive="handleImmersiveToggle"
        />
      </transition>
    </div>

    <div id="ol-map-container"></div>

    <router-view />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

import 'ol/ol.css'
import Map from 'ol/Map'
import View from 'ol/View'
import TileLayer from 'ol/layer/Tile'
import VectorLayer from 'ol/layer/Vector'
import OSM from 'ol/source/OSM'
import XYZ from 'ol/source/XYZ'
import VectorSource from 'ol/source/Vector'
import { fromLonLat, transform } from 'ol/proj'
import Feature from 'ol/Feature'
import LineString from 'ol/geom/LineString'
import Point from 'ol/geom/Point'
import { Style, Stroke, Fill, Circle } from 'ol/style'
import ScaleLine from 'ol/control/ScaleLine'

import ChapterHome from './components/ChapterHome.vue'
import ChapterOne from './components/ChapterOne.vue'
import ChapterTwo from './components/ChapterTwo.vue'
import ChapterThree from './components/ChapterThree.vue'

const chapters = [
  { id: 0, navName: "首页", component: ChapterHome },
  { id: 1, navName: "全国生态时空演变", component: ChapterOne },
  { id: 2, navName: "重大生态工程", component: ChapterTwo },
  { id: 3, navName: "区域遥感数据实时分析", component: ChapterThree }
]

const currentIndex = ref(0)
const activeComponent = computed(() => chapters[currentIndex.value].component)

// 🎬 新增：全屏沉浸模式状态
const isImmersiveMode = ref(false)
function handleImmersiveToggle(status) {
  isImmersiveMode.value = status
}

let map = null
let view = null
let baseTileLayer = null

const currentSourceId = ref('gaode-sat')
const mapSources = [
  { id: 'gaode-sat', name: '卫星遥感' },
  { id: 'gaode-vec', name: '高德矢量' },
  { id: 'osm', name: 'OSM底图' }
]

onMounted(() => {
  view = new View({
    center: fromLonLat([104.0, 35.0]),
    zoom: 5,
    maxZoom: 18,
    minZoom: 4
  })

  baseTileLayer = new TileLayer({
    source: new XYZ({
      url: 'https://webst0{1-4}.is.autonavi.com/appmaptile?style=6&x={x}&y={y}&z={z}'
    })
  })

  map = new Map({
    target: 'ol-map-container',
    layers: [baseTileLayer],
    view: view,
    controls: [] 
  })

  const scaleControl = new ScaleLine({
    units: 'metric',
    bar: false,
    className: 'custom-scale-line'
  })
  map.addControl(scaleControl)

  window.olMap = map
  window.ol = {
    proj: { fromLonLat, transform },
    geom: { Point, LineString },
    Feature: Feature,
    source: { Vector: VectorSource },
    layer: { Vector: VectorLayer },
    style: { Style, Stroke, Fill, Circle }
  }

  // 兜底：全局监听跨组件原生事件
  window.addEventListener('global-immersive-toggle', (e) => {
    isImmersiveMode.value = e.detail
  })
})

function changeMapSource(sourceId) {
  if (!baseTileLayer || currentSourceId.value === sourceId) return
  currentSourceId.value = sourceId
  
  let newSource = null
  if (sourceId === 'osm') {
    newSource = new OSM({ url: 'https://{a-c}.tile.openstreetmap.org/{z}/{x}/{y}.png' })
  } else if (sourceId === 'gaode-vec') {
    newSource = new XYZ({ url: 'https://webrd0{1-4}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}' })
  } else if (sourceId === 'gaode-sat') {
    newSource = new XYZ({ url: 'https://webst0{1-4}.is.autonavi.com/appmaptile?style=6&x={x}&y={y}&z={z}' })
  }
  
  if (newSource) {
    baseTileLayer.setSource(newSource)
  }
}

function switchPage(index) {
  if (index === currentIndex.value) return
  currentIndex.value = index
  
  // 切换页面时，自动恢复UI显示
  isImmersiveMode.value = false
  
  if (!view) return
  
  if (index === 0 || index === 1 || index === 2) {
    view.animate({ center: fromLonLat([104.0, 35.0]), zoom: 5, duration: 1200 })
  } else if (index === 3) {
    view.animate({ center: fromLonLat([108.28, 40.38]), zoom: 8, duration: 1200 })
  }
}
</script>

<style scoped>
body, html { margin: 0; padding: 0; width: 100%; height: 100%; background-color: #050d08; }

.story-map-container { 
  width: 100vw; 
  height: 100vh; 
  position: relative; 
  overflow: hidden; 
}

/* 🎬 悬浮胶囊导航栏：添加过渡动画 */
.top-minimal-nav-bar {
  position: absolute;
  top: 30px; left: 0; width: 100%;
  z-index: 10;
  display: flex;
  justify-content: center;
  pointer-events: none;
  transition: transform 0.6s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.5s ease;
}
/* 🎬 右上角多图源适配切换面板：添加过渡动画 */
.map-source-selector {
  position: absolute;
  top: 30px;
  right: 40px;
  z-index: 10;
  display: flex;
  background-color: rgba(10, 25, 16, 0.8);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(46, 204, 113, 0.2);
  border-radius: 15px;
  padding: 4px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.4);
  transition: transform 0.6s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.5s ease;
}

/* 🎬 激活沉浸模式时的隐藏样式：向上离屏滑出并淡出 */
.ui-hidden {
  opacity: 0 !important;
  transform: translateY(-50px) !important;
  pointer-events: none !important;
}

.nav-links-container { display: flex; gap: 30px; }
.nav-item {
  pointer-events: auto;
  font-size: 14px; font-weight: bold;
  color: rgba(255, 255, 255, 0.85); background-color: rgba(27, 77, 47, 0.75);
  backdrop-filter: blur(6px); padding: 10px 22px; border-radius: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2); cursor: pointer;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1); user-select: none;
  border: 1px solid rgba(255, 255, 255, 0.1);
}
.nav-item:hover, .nav-item.active {
  background-color: rgba(27, 77, 47, 0.95); color: #2ecc71;
  transform: translateY(-2px); box-shadow: 0 6px 20px rgba(46, 204, 113, 0.3);
}
.nav-item.active { background-color: rgba(27, 77, 47, 1); border: 1px solid rgba(46, 204, 113, 0.4); }

.selector-item {
  font-size: 12px;
  font-weight: bold;
  color: rgba(255,255,255,0.6);
  padding: 6px 14px;
  border-radius: 11px;
  cursor: pointer;
  transition: all 0.2s ease;
}
.selector-item:hover { color: #fff; }
.selector-item.active {
  background-color: #1b4d2f;
  color: #2ecc71;
  box-shadow: 0 2px 8px rgba(46,204,113,0.2);
}

.chapter-component-container { position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 8; }
#ol-map-container { position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 1; }

:deep(.custom-scale-line) {
  position: absolute; bottom: 20px; left: 20px;
  background: rgba(10, 25, 16, 0.75); border: 1px solid rgba(46, 204, 113, 0.3);
  border-top: none; color: #2ecc71; font-size: 11px;
  text-align: center; padding: 2px 6px; z-index: 5;
}

.fade-layer-enter-active, .fade-layer-leave-active { transition: opacity 0.3s ease; }
.fade-layer-enter-from, .fade-layer-leave-to { opacity: 0; }
</style>