<template>
  <div class="story-map-container">
    <div class="top-minimal-nav-bar">
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

    <div v-if="$route.path === '/'" class="chapter-component-container">
      <transition name="fade-layer" mode="out-in">
        <component :is="activeComponent" />
      </transition>
    </div>

    <div id="ol-map-container"></div>

    <router-view />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

import 'ol/ol.css'
import Map from 'ol/Map'
import View from 'ol/View'
import TileLayer from 'ol/layer/Tile'
import VectorLayer from 'ol/layer/Vector'
import OSM from 'ol/source/OSM'
import VectorSource from 'ol/source/Vector'
import { fromLonLat, transform } from 'ol/proj'
import Feature from 'ol/Feature'
import LineString from 'ol/geom/LineString'
import Point from 'ol/geom/Point'
import { Style, Stroke, Fill, Circle } from 'ol/style'
import ScaleLine from 'ol/control/ScaleLine' // 💡 动态比例尺控件

// 导入所有篇章（新增首页组件）
import ChapterHome from './components/ChapterHome.vue'
import ChapterOne from './components/ChapterOne.vue'
import ChapterTwo from './components/ChapterTwo.vue'
import ChapterThree from './components/ChapterThree.vue'

// 四个一级菜单项
const chapters = [
  { id: 0, navName: "首页", component: ChapterHome },
  { id: 1, navName: "全国生态时空演变", component: ChapterOne },
  { id: 2, navName: "重大生态工程", component: ChapterTwo },
  { id: 3, navName: "区域遥感数据实时分析", component: ChapterThree }
]

const currentIndex = ref(0)
const activeComponent = computed(() => chapters[currentIndex.value].component)

let map = null
let view = null

onMounted(() => {
  // 💡 1. 按照功能文档要求设定：地图中心点为东经104°，北纬35°，缩放级别为5级
  view = new View({
    center: fromLonLat([104.0, 35.0]),
    zoom: 5,
    maxZoom: 18,
    minZoom: 4
  })

  map = new Map({
    target: 'ol-map-container',
    layers: [
      new TileLayer({ source: new OSM() }) // 默认底图
    ],
    view: view,
    controls: [] // 清空默认控件，方便下面自定义
  })

  // 💡 2. 挂载动态比例尺控件（满足文档 1.1.4 节第 6 条要求）
  const scaleControl = new ScaleLine({
    units: 'metric',
    bar: false,
    className: 'custom-scale-line'
  })
  map.addControl(scaleControl)

  // 全局共享空间挂载
  window.olMap = map
  window.ol = {
    proj: { fromLonLat, transform },
    geom: { Point, LineString },
    Feature: Feature,
    source: { Vector: VectorSource },
    layer: { Vector: VectorLayer },
    style: { Style, Stroke, Fill, Circle }
  }
})

function switchPage(index) {
  if (index === currentIndex.value) return
  currentIndex.value = index

  // 💡 3. 视角联动：如果用户点击了“首页”，地图以 1 秒的丝滑动画自动飞回全国视角中心
  if (index === 0 && view) {
    view.animate({
      center: fromLonLat([104.0, 35.0]),
      zoom: 5,
      duration: 1000
    })
  }
}
</script>

<style scoped>
body, html { margin: 0; padding: 0; width: 100%; height: 100%; font-family: sans-serif; }
.story-map-container { width: 100vw; height: 100vh; overflow: hidden; position: relative; }

/* 悬浮胶囊导航栏（保留你之前最满意的样式，增加支持点击穿透） */
.top-minimal-nav-bar {
  position: absolute;
  top: 30px; left: 0; width: 100%;
  z-index: 10;
  display: flex;
  justify-content: center;
  pointer-events: none;
}
.nav-links-container {
  display: flex;
  gap: 30px; /* 菜单项变多，稍微收窄间距防止溢出 */
}
.nav-item {
  pointer-events: auto;
  font-size: 14px;
  font-weight: bold;
  color: rgba(255, 255, 255, 0.85);
  background-color: rgba(27, 77, 47, 0.75);
  backdrop-filter: blur(6px);
  padding: 10px 22px;
  border-radius: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  user-select: none;
  border: 1px solid rgba(255, 255, 255, 0.1);
}
.nav-item:hover, .nav-item.active {
  background-color: rgba(27, 77, 47, 0.95);
  color: #2ecc71;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(46, 204, 113, 0.3);
}
.nav-item.active {
  background-color: rgba(27, 77, 47, 1);
  border: 1px solid rgba(46, 204, 113, 0.4);
}

.chapter-component-container { position: absolute; top: 0; left: 0; width: 100vw; height: 100vh; pointer-events: none; z-index: 8; }
#ol-map-container { position: absolute; top: 0; left: 0; width: 100vw; height: 100vh; z-index: 1; }

/* 🌟 自定义左下角 OpenLayers 动态比例尺样式 */
:deep(.custom-scale-line) {
  position: absolute;
  bottom: 20px;
  left: 20px;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid #999;
  border-top: none;
  color: #333;
  font-size: 11px;
  text-align: center;
  padding: 1px 5px;
  z-index: 5;
}

/* 篇章切换渐变 */
.fade-layer-enter-active, .fade-layer-leave-active { transition: opacity 0.3s ease; }
.fade-layer-enter-from, .fade-layer-leave-to { opacity: 0; }
</style>