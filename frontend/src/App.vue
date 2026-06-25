<template>
  <div class="story-map-container">
    
    <div class="top-minimal-nav-bar" :class="{ 'ui-hidden': isImmersiveMode }">
      <div class="nav-links-container apple-blur-box">
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

    <div class="top-right-group apple-blur-box" :class="{ 'ui-hidden': isImmersiveMode }">
      <div class="map-source-selector">
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
      <span class="top-right-sep"></span>
      <div class="user-session-bar">
        <span class="user-avatar">{{ userInitial }}</span>
        <span class="logout-action" @click="doLogout">退出</span>
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
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

import 'ol/ol.css'
import Map from 'ol/Map'
import View from 'ol/View'
import TileLayer from 'ol/layer/Tile'
import VectorLayer from 'ol/layer/Vector'
import OSM from 'ol/source/OSM'
import XYZ from 'ol/source/XYZ'
// 🌟 引入 ImageWMS 与 ImageLayer 替换原先不匹配的 Tile 切片架构
import ImageLayer from 'ol/layer/Image'
import ImageWMS from 'ol/source/ImageWMS'
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

const router = useRouter()

const chapters = [
  { id: 0, navName: "首页", component: ChapterHome },
  { id: 1, navName: "全国生态时空演变", component: ChapterOne },
  { id: 2, navName: "重大生态工程", component: ChapterTwo },
  { id: 3, navName: "区域遥感数据实时分析", component: ChapterThree }
]

const currentIndex = ref(0)
const activeComponent = computed(() => chapters[currentIndex.value].component)

const isImmersiveMode = ref(false)
function handleImmersiveToggle(status) {
  isImmersiveMode.value = status
}

const loggedInUser = ref(localStorage.getItem('forest_username') || '')
const userInitial = computed(() => loggedInUser.value ? loggedInUser.value.charAt(0).toUpperCase() : 'U')
function doLogout() {
  localStorage.removeItem('forest_isLoggedIn')
  localStorage.removeItem('forest_username')
  router.push('/login')
}

let map = null
let view = null
const layersPool = {}
let forestWmsLayer = null // 🌟 全局森林 WMS 图层变量，现在是一个 ImageLayer 实例

const currentSourceId = ref('gaode-sat')
const mapSources = [
  { id: 'gaode-sat', name: '卫星遥感' },
  { id: 'arcgis-dem', name: 'DEM' },
  { id: 'gaode-vec', name: '高德矢量' },
  { id: 'osm', name: 'OSM底图' }
]

// 🌟 动态更新 GeoServer WMS 图层参数的方法 (保持机制不变，ImageWMS 同样完美支持此方法)
function updateForestWmsYear(year) {
  if (!forestWmsLayer) return
  
  // 拼接动态图层名，如 eco_story_map:catcd_1985_forest_cover
  const layerName = `eco_story_map:catcd_${year}_forest_cover`
  
  // 利用 OpenLayers 提供的 updateParams 机制，无缝刷新单一动态渲染栅格
  forestWmsLayer.getSource().updateParams({
    'LAYERS': layerName
  })
}

onMounted(() => {
  view = new View({
    center: fromLonLat([104.0, 35.0]),
    zoom: 5,
    maxZoom: 18,
    minZoom: 4
  })

  layersPool['gaode-sat'] = new TileLayer({
    visible: true,
    source: new XYZ({ url: 'https://webst0{1-4}.is.autonavi.com/appmaptile?style=6&x={x}&y={y}&z={z}' })
  })

  layersPool['gaode-vec'] = new TileLayer({
    visible: false,
    source: new XYZ({ url: 'https://webrd0{1-4}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}' })
  })

  layersPool['osm'] = new TileLayer({
    visible: false,
    source: new OSM({ url: 'https://{a-c}.tile.openstreetmap.org/{z}/{x}/{y}.png' })
  })

  layersPool['arcgis-dem'] = new TileLayer({
    visible: false,
    className: 'dark-dem-layer', 
    source: new XYZ({
      url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Shaded_Relief/MapServer/tile/{z}/{y}/{x}',
      crossOrigin: 'anonymous'
    })
  })

  forestWmsLayer = new ImageLayer({
    visible: false, // 初始篇章为首页，默认隐藏
    zIndex: 999,    // 将层级拉高，防止被底图压盖
    source: new ImageWMS({
      url: 'http://172.26.63.161:8080/geoserver/eco_story_map/wms',
      // 🌟 核心：写在这里！强制 OpenLayers 在前端做重投影转换
      projection: 'EPSG:4326', 
      params: {
        'SERVICE': 'WMS',
        'VERSION': '1.1.0', 
        'REQUEST': 'GetMap',
        'LAYERS': 'eco_story_map:catcd_1985_forest_cover', 
        'FORMAT': 'image/png',
        'TRANSPARENT': 'true'
      },
      ratio: 1, 
      serverType: 'geoserver'
    })
  })

  map = new Map({
    target: 'ol-map-container',
    layers: [
      layersPool['gaode-sat'],
      layersPool['gaode-vec'],
      layersPool['osm'],
      layersPool['arcgis-dem'],
      forestWmsLayer // 🌟 将全新的森林单张动态 WMS 图层载入地图
    ],
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

  window.addEventListener('global-immersive-toggle', (e) => {
    isImmersiveMode.value = e.detail
  })

  // 🌟 注册全局监听：接收年份改变并向下传递给图层参数
  window.addEventListener('change-forest-year', (e) => {
    const targetYear = e.detail
    updateForestWmsYear(targetYear)
  })
})

function changeMapSource(sourceId) {
  if (currentSourceId.value === sourceId) return
  currentSourceId.value = sourceId
  
  Object.keys(layersPool).forEach(key => {
    layersPool[key].setVisible(key === sourceId)
  })
}

function switchPage(index) {
  if (index === currentIndex.value) return
  currentIndex.value = index
  isImmersiveMode.value = false
  
  // 🌟 核心控制：只有在“全国生态时空演变”（篇章索引为 1）时，才激活 WMS 栅格覆盖层
  if (forestWmsLayer) {
    forestWmsLayer.setVisible(index === 1)
  }

  if (!view) return
  
  if (index === 0 || index === 2) {
    view.animate({ center: fromLonLat([104.0, 35.0]), zoom: 5, duration: 1200 })
  } else if (index === 1) {
    view.animate({ center: fromLonLat([104.0, 36.0]), zoom: 4.2, duration: 1200 })
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

/* 🍏 核心复刻：升级为深色高级毛玻璃基类（完美对抗白色底图） */
.apple-blur-box {
  background: rgba(15, 25, 20, 0.75) !important; /* 🌟 引入深色半透明基底 */
  backdrop-filter: blur(20px) saturate(160%) !important;
  -webkit-backdrop-filter: blur(20px) saturate(160%) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important; /* 极其微弱的边缘高光 */
  box-shadow: 0 12px 32px 0 rgba(0, 0, 0, 0.4) !important; /* 加深阴影，使UI在白底上浮现出来 */
}

/* 🎬 顶部胶囊导航外盒 */
.top-minimal-nav-bar {
  position: absolute;
  top: 30px; left: 0; width: 100%;
  z-index: 10;
  display: flex;
  justify-content: center;
  pointer-events: none;
  transition: transform 0.6s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.5s ease;
}

.nav-links-container { 
  display: flex; 
  gap: 8px; 
  padding: 5px;
  border-radius: 24px;
  pointer-events: auto;
}

.nav-item {
  font-size: 13.5px; 
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8); 
  padding: 10px 24px;
  border-radius: 19px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.25, 1, 0.5, 1); 
  user-select: none;
}
.nav-item:hover { 
  color: #ffffff;
  background-color: rgba(255, 255, 255, 0.12); 
}
.nav-item.active { 
  background-color: rgba(46, 204, 113, 0.25); 
  color: #2ecc71;
  border: 1px solid rgba(46, 204, 113, 0.35);
  box-shadow: 0 4px 12px rgba(46, 204, 113, 0.25);
}

.top-right-group {
  position: absolute;
  top: 30px;
  right: 40px;
  z-index: 10;
  display: flex;
  align-items: center;
  border-radius: 16px;
  padding: 4px;
  transition: transform 0.6s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.5s ease;
}

.map-source-selector { display: flex; }
.top-right-sep { width: 1px; height: 16px; background: rgba(255, 255, 255, 0.25); margin: 0 4px; }
.user-session-bar { display: flex; align-items: center; gap: 8px; padding: 0 6px 0 0; }
.user-avatar {
  width: 26px; height: 26px;
  display: flex; align-items: center; justify-content: center;
  background-color: rgba(46, 204, 113, 0.25); color: #2ecc71;
  font-size: 11px; font-weight: 900; border-radius: 50%; flex-shrink: 0;
  border: 1px solid rgba(46, 204, 113, 0.35);
}
.logout-action {
  font-size: 12px; font-weight: 500; color: rgba(255, 255, 255, 0.6); 
  cursor: pointer; transition: color 0.2s ease, background 0.2s; padding: 4px 8px; border-radius: 8px;
}
.logout-action:hover { color: #ff6b6b; background: rgba(255, 107, 107, 0.15); }

.selector-item {
  font-size: 12.5px; font-weight: 600; color: rgba(255, 255, 255, 0.75); 
  padding: 6px 14px; border-radius: 12px; cursor: pointer; transition: all 0.2s ease;
}
.selector-item:hover { color: #fff; background-color: rgba(255, 255, 255, 0.1); }
.selector-item.active {
  background-color: rgba(46, 204, 113, 0.25); color: #2ecc71; 
  border: 1px solid rgba(46, 204, 113, 0.2);
}

.ui-hidden {
  opacity: 0 !important;
  transform: translateY(-50px) !important;
  pointer-events: none !important;
}

.chapter-component-container { 
  position: absolute; 
  top: 0; 
  left: 0; 
  width: 100%; 
  height: 100%; 
  pointer-events: none; 
  z-index: 8; 
}

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