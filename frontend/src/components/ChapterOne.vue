<template>
  <div class="chapter-one-container">
    
    <div class="side-panel left-panel apple-blur-panel">
      <div class="chart-wrapper split-half">
        <div class="chart-art-title">全国森林覆盖率长时序演变 (1985-2024)</div>
        <div ref="lineChartRef" class="echart-container"></div>
      </div>
      <div class="panel-inner-sep"></div>
      <div class="chart-wrapper split-half">
        <div class="chart-art-title">阶段性森林蓄积量与净增幅 (亿立方米)</div>
        <div ref="barChartRef" class="echart-container"></div>
      </div>
    </div>

    <div class="side-panel right-panel apple-blur-panel">
      <div class="chart-wrapper split-half">
        <div class="chart-art-title">七大地理分区森林面积占比估计</div>
        <div ref="pieChartRef" class="echart-container"></div>
      </div>
      <div class="panel-inner-sep"></div>
      <div class="chart-wrapper split-half">
        <div class="chart-art-title">当年林业工程造林结构特征 (万公顷)</div>
        <div ref="structureChartRef" class="echart-container"></div>
      </div>
    </div>

    <div class="map-layer-placeholder" :key="currentYear">
      <div class="placeholder-border-box">
        <div class="scan-line"></div>
        <div class="layer-meta-info">
          <span class="layer-title">GEOSERVER WMS 开放时空图层规范服务</span>
          <h3 class="layer-year">{{ currentYear }} 年 全国森林覆盖栅格数据</h3>
          <span class="layer-status" style="color: #2ecc71;">[ GeoServer 服务联动渲染中 ]</span>
        </div>
      </div>
    </div>

    <div class="bottom-composite-console">
      
      <div class="console-left-title-zone">
        <div class="active-year-title">{{ currentYear }}<span class="year-unit">年</span></div>
        <div class="title-text-group">
          <h2 class="narrative-title">中国国土绿化时空演变</h2>
          <span class="narrative-subtitle">Spatio-Temporal Evolution Big Data</span>
        </div>
      </div>

      <div class="console-divider"></div>

      <div class="timeline-control-left">
        <button class="art-play-btn" :class="{ 'is-playing': isPlaying }" @click.stop="togglePlay">
          {{ isPlaying ? '⏸ 暂停' : '▶ 轮播' }}
        </button>
      </div>

      <div class="horizontal-axis-container">
        <div class="horizontal-track-line"></div>

        <div class="nodes-row-wrapper">
          <div class="active-slider-cursor" :style="{ left: cursorLeft }"></div>
          <div
            v-for="(node, idx) in timelineNodes"
            :key="node.year"
            class="horizontal-node"
            :class="{ 'is-active': currentYear === node.year, 'is-milestone': node.isMilestone }"
            @click.stop="selectYear(node.year)"
          >
            <div class="h-node-dot">
              <span v-if="node.isMilestone" class="h-milestone-star">★</span>
            </div>
            <div class="h-node-label">
              <span class="h-node-year">{{ node.year }}</span>
              <span v-if="node.isMilestone" class="h-milestone-name">{{ node.milestoneName }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="timeline-click-hint">💡 点击节点精准定位年份</div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

const timelineNodes = [
  { year: 1985, isMilestone: false },
  { year: 1995, isMilestone: false },
  { year: 2000, isMilestone: true, milestoneName: '天保·退耕' },
  { year: 2010, isMilestone: false },
  { year: 2014, isMilestone: true, milestoneName: '生态文明' },
  { year: 2024, isMilestone: false }
]

const historicalData = {
  1985: {
    coverage: 12.54, volume: 90.3, volumeGrow: 1.22, structure: [110, 75, 45],
    pie: [
      { name: '东北', value: 16.37 }, { name: '华北', value: 12.17 }, { name: '华东', value: 14.79 },
      { name: '华中', value: 9.51 }, { name: '华南', value: 10.70 }, { name: '西南', value: 26.94 }, { name: '西北', value: 9.53 }
    ]
  },
  1995: {
    coverage: 13.82, volume: 112.7, volumeGrow: 2.24, structure: [170, 105, 60],
    pie: [
      { name: '东北', value: 16.71 }, { name: '华北', value: 11.10 }, { name: '华东', value: 15.36 },
      { name: '华中', value: 10.16 }, { name: '华南', value: 11.31 }, { name: '西南', value: 26.93 }, { name: '西北', value: 8.43 }
    ]
  },
  2000: {
    coverage: 16.41, volume: 124.9, volumeGrow: 2.44, structure: [270, 200, 105],
    pie: [
      { name: '东北', value: 15.02 }, { name: '华北', value: 9.89 }, { name: '华东', value: 15.90 },
      { name: '华中', value: 10.73 }, { name: '华南', value: 11.40 }, { name: '西南', value: 28.98 }, { name: '西北', value: 8.09 }
    ]
  },
  2010: {
    coverage: 18.40, volume: 151.9, volumeGrow: 2.64, structure: [360, 275, 160],
    pie: [
      { name: '东北', value: 14.74 }, { name: '华北', value: 10.33 }, { name: '华东', value: 15.36 },
      { name: '华中', value: 10.95 }, { name: '华南', value: 11.07 }, { name: '西南', value: 29.14 }, { name: '西北', value: 8.42 }
    ]
  },
  2014: {
    coverage: 20.36, volume: 162.8, volumeGrow: 2.88, structure: [385, 300, 195],
    pie: [
      { name: '东北', value: 14.26 }, { name: '华北', value: 10.51 }, { name: '华东', value: 14.98 },
      { name: '华中', value: 10.81 }, { name: '华南', value: 11.43 }, { name: '西南', value: 29.47 }, { name: '西北', value: 8.54 }
    ]
  },
  2024: {
    coverage: 23.92, volume: 195.2, volumeGrow: 3.24, structure: [465, 370, 265],
    pie: [
      { name: '东北', value: 13.39 }, { name: '华北', value: 10.96 }, { name: '华东', value: 14.24 },
      { name: '华中', value: 10.66 }, { name: '华南', value: 11.64 }, { name: '西南', value: 29.74 }, { name: '西北', value: 9.37 }
    ]
  }
}

const currentYear = ref(1985)
const isPlaying = ref(false)
let playTimer = null

const lineChartRef = ref(null)
const barChartRef = ref(null)
const pieChartRef = ref(null)
const structureChartRef = ref(null)

let lineChartInstance = null
let barChartInstance = null
let pieChartInstance = null
let structureChartInstance = null

const currentNarrative = computed(() => historicalData[currentYear.value])
const cursorLeft = computed(() => {
  const idx = timelineNodes.findIndex(n => n.year === currentYear.value)
  const n = timelineNodes.length
  return ((idx / (n - 1)) * 100) + '%'
})

// 🌟 核心监听：响应式年份被篡改或轮播改变时，立刻向外广播全局自定义事件
watch(currentYear, (newYear) => {
  updateDynamicCharts()
  
  // 发送自定义事件，交由宿主环境 App.vue 捕获处理
  window.dispatchEvent(new CustomEvent('change-forest-year', { detail: newYear }))
})

function initCharts() {
  if (lineChartRef.value) lineChartInstance = echarts.init(lineChartRef.value, 'dark')
  if (barChartRef.value) barChartInstance = echarts.init(barChartRef.value, 'dark')
  if (pieChartRef.value) pieChartInstance = echarts.init(pieChartRef.value, 'dark')
  if (structureChartRef.value) structureChartInstance = echarts.init(structureChartRef.value, 'dark')

  updateDynamicCharts()
}

function updateDynamicCharts() {
  const years = Object.keys(historicalData).map(Number)

  // 1. 折线图 (左上)
  if (lineChartInstance) {
    lineChartInstance.setOption({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis', backgroundColor: 'rgba(10,25,16,0.95)', borderColor: '#2ecc71' },
      grid: { left: '15%', right: '5%', top: '15%', bottom: '15%' },
      xAxis: { type: 'category', data: years, axisLine: { lineStyle: { color: 'rgba(255,255,255,0.2)' } } },
      yAxis: { type: 'value', min: 10, max: 26, axisLabel: { formatter: '{value}%' }, splitLine: { lineStyle: { color: 'rgba(255,255,255,0.03)' } } },
      series: [{
        data: years.map(y => historicalData[y].coverage),
        type: 'line', smooth: true, color: '#2ecc71', lineStyle: { width: 2.5 },
        areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(46,204,113,0.15)' }, { offset: 1, color: 'rgba(46,204,113,0)' }]) }
      }]
    })
    const idx = years.indexOf(currentYear.value)
    lineChartInstance.dispatchAction({ type: 'showTip', seriesIndex: 0, dataIndex: idx })
  }

  // 2. 柱状图 (左下)
  if (barChartInstance) {
    barChartInstance.setOption({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis', backgroundColor: 'rgba(10,25,16,0.95)' },
      grid: { left: '15%', right: '5%', top: '15%', bottom: '15%' },
      xAxis: { type: 'category', data: years, axisLine: { lineStyle: { color: 'rgba(255,255,255,0.2)' } } },
      yAxis: { type: 'value', splitLine: { lineStyle: { color: 'rgba(255,255,255,0.03)' } } },
      series: [
        { name: '总蓄积量', type: 'bar', data: years.map(y => historicalData[y].volume), itemStyle: { color: '#27ae60' }, barWidth: '35%' },
        { name: '年净增幅', type: 'line', data: years.map(y => historicalData[y].volumeGrow), itemStyle: { color: '#f1c40f' }, lineStyle: { width: 2 } }
      ]
    })
    const idx = years.indexOf(currentYear.value)
    barChartInstance.dispatchAction({ type: 'showTip', seriesIndex: 0, dataIndex: idx })
  }

  // 3. 饼图 (右上)
  if (pieChartInstance) {
    pieChartInstance.setOption({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'item', formatter: '{b}: {c}%' },
      series: [{
        type: 'pie', radius: ['35%', '60%'], avoidLabelOverlap: false,
        itemStyle: { borderRadius: 3 },
        label: { show: true, color: 'rgba(255,255,255,0.6)', fontSize: 10 },
        color: ['#2ecc71', '#3498db', '#f39c12', '#e74c3c', '#9b59b6', '#1abc9c', '#e67e22'],
        data: currentNarrative.value.pie
      }]
    })
  }

  // 4. 条形图 (右下)
  if (structureChartInstance) {
    structureChartInstance.setOption({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: '25%', right: '8%', top: '10%', bottom: '15%' },
      xAxis: { type: 'value', splitLine: { show: false }, axisLabel: { color: 'rgba(255,255,255,0.4)' } },
      yAxis: { type: 'category', data: ['人工防护林', '天然次生林', '经济兼修林'], axisLine: { lineStyle: { color: 'rgba(255,255,255,0.2)' } }, axisLabel: { color: 'rgba(255,255,255,0.7)', fontSize: 10 } },
      series: [{
        type: 'bar',
        data: currentNarrative.value.structure,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: 'rgba(26, 188, 156, 0.2)' },
            { offset: 1, color: '#1abc9c' }
          ]),
          borderRadius: [0, 4, 4, 0]
        },
        barWidth: '40%'
      }]
    })
  }
}

function selectYear(year) {
  currentYear.value = year
}

function togglePlay() {
  isPlaying.value = !isPlaying.value
  if (isPlaying.value) {
    const years = timelineNodes.map(n => n.year)
    playTimer = setInterval(() => {
      let currIdx = years.indexOf(currentYear.value)
      let nextIdx = (currIdx + 1) % years.length
      currentYear.value = years[nextIdx]
    }, 4500)
  } else {
    clearInterval(playTimer)
  }
}

onMounted(() => {
  nextTick(() => { initCharts() })
  
  // 🌟 初始化触发：组件一旦被挂载，默认立刻同步 1985 年图层到外部地图中
  window.dispatchEvent(new CustomEvent('change-forest-year', { detail: currentYear.value }))

  window.addEventListener('resize', () => {
    lineChartInstance?.resize()
    barChartInstance?.resize()
    pieChartInstance?.resize()
    structureChartInstance?.resize()
  })
})

onUnmounted(() => {
  clearInterval(playTimer)
  lineChartInstance?.dispose()
  barChartInstance?.dispose()
  pieChartInstance?.dispose()
  structureChartInstance?.dispose()
})
</script>

<style scoped>
.chapter-one-container {
  position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 9; user-select: none;
}

.chapter-one-container::before {
  content: "";
  position: absolute;
  top: 0; left: 0; width: 100%; height: 100%;
  background: linear-gradient(to right, rgba(5,13,8,0.7) 0%, rgba(5,13,8,0) 28%, rgba(5,13,8,0) 72%, rgba(5,13,8,0.7) 100%);
  z-index: 1;
}

.apple-blur-panel {
  background: rgba(255, 255, 255, 0.04) !important;
  backdrop-filter: blur(20px) saturate(150%) !important;
  -webkit-backdrop-filter: blur(20px) saturate(150%) !important;
  border: 1px solid rgba(255, 255, 255, 0.09) !important;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5);
}

.side-panel {
  pointer-events: auto;
  position: absolute;
  top: 80px;
  bottom: 135px;
  width: 24%;
  padding: 20px 16px;
  box-sizing: border-box;
  border-radius: 18px;
  z-index: 3;
  display: flex;
  flex-direction: column;
}
.left-panel { left: 40px; }
.right-panel { right: 40px; }

.split-half { flex: 1; min-height: 0; display: flex; flex-direction: column; }
.panel-inner-sep { height: 1px; background: rgba(255, 255, 255, 0.06); margin: 16px 0; }

.chart-wrapper { display: flex; flex-direction: column; }
.chart-art-title { font-size: 12px; font-weight: 600; color: rgba(255,255,255,0.7); border-left: 3px solid #2ecc71; padding-left: 8px; margin-bottom: 8px; }
.echart-container { flex: 1; width: 100%; min-height: 0; }

.map-layer-placeholder {
  position: absolute; top: 38%; left: 50%; transform: translate(-50%, -50%);
  width: 360px; height: 180px; background: rgba(46, 204, 113, 0.01);
  border: 1px dashed rgba(46, 204, 113, 0.12); border-radius: 6px; z-index: 2;
}
.placeholder-border-box { position: relative; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; overflow: hidden; }
.scan-line { position: absolute; top: 0; left: 0; width: 100%; height: 1px; background: linear-gradient(to right, transparent, rgba(46,204,113,0.4), transparent); animation: radarScan 4s linear infinite; }
.layer-meta-info { text-align: center; }
.layer-title { font-size: 10px; color: #2ecc71; letter-spacing: 0.5px; display: block; margin-bottom: 4px; opacity: 0.7; }
.layer-year { font-size: 14px; font-weight: 700; margin: 0 0 4px 0; color: #ffffff; }
.layer-status { font-size: 9.5px; color: rgba(255,255,255,0.2); font-family: monospace; }

.bottom-composite-console {
  pointer-events: auto; 
  position: absolute;
  bottom: 30px; 
  left: 40px;  
  width: calc(100% - 80px); 
  height: 80px; 
  background: rgba(8, 20, 13, 0.8); 
  backdrop-filter: blur(25px) saturate(140%);
  -webkit-backdrop-filter: blur(25px) saturate(140%);
  border: 1px solid rgba(255,255,255,0.08); 
  border-radius: 16px;
  padding: 0 30px; 
  box-sizing: border-box;
  display: flex; 
  align-items: center; 
  z-index: 10;
  box-shadow: 0 16px 45px rgba(0,0,0,0.6);
}

.console-left-title-zone {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
}
.active-year-title {
  font-size: 52px; 
  font-weight: 900; 
  color: #2ecc71; 
  line-height: 0.9;
  font-family: 'Impact', sans-serif;
  background: linear-gradient(to bottom, #ffffff 30%, #2ecc71 100%);
  -webkit-background-clip: text; 
  background-clip: text;
  -webkit-text-fill-color: transparent;
}
.year-unit { font-size: 18px; font-weight: bold; margin-left: 2px; color: #fff; -webkit-text-fill-color: #fff; }
.title-text-group { display: flex; flex-direction: column; gap: 1px; }
.narrative-title { font-size: 20px; color: #ffffff; font-weight: 800; margin: 0; letter-spacing: 1.5px; }
.narrative-subtitle { font-size: 10px; color: rgba(255,255,255,0.3); font-family: monospace; letter-spacing: 0.5px; text-transform: uppercase; }

.console-divider {
  width: 1px; height: 36px; background: rgba(255,255,255,0.08); margin: 0 25px; flex-shrink: 0;
}

.timeline-control-left { margin-right: 20px; flex-shrink: 0; }
.art-play-btn {
  background: rgba(46, 204, 113, 0.12); color: #2ecc71; border: 1px solid rgba(46, 204, 113, 0.3); padding: 6px 16px;
  border-radius: 10px; font-size: 12px; font-weight: bold; cursor: pointer; transition: all 0.2s;
}
.art-play-btn:hover, .art-play-btn.is-playing { background: #2ecc71; color: #fff; box-shadow: 0 0 12px rgba(46,204,113,0.4); }

.horizontal-axis-container { flex: 1; height: 100%; position: relative; display: flex; align-items: center; overflow: hidden; }
.horizontal-track-line { position: absolute; left: 50px; right: 50px; top: 50%; transform: translateY(-50%); height: 3px; background: rgba(255,255,255,0.08); z-index: 1; }
.active-slider-cursor {
  position: absolute; top: 50%; transform: translate(-50%, -50%); width: 10px; height: 10px; background: #ffffff; border-radius: 50%; z-index: 3; box-shadow: 0 0 16px 5px #2ecc71; transition: left 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

.nodes-row-wrapper { display: flex; justify-content: space-between; position: relative; z-index: 2; width: 100%; height: 100%; align-items: center; padding: 0 55px; box-sizing: border-box; }
.horizontal-node { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; cursor: pointer; position: relative; flex-shrink: 0; }

.h-node-dot { width: 10px; height: 10px; background: rgba(255,255,255,0.18); border-radius: 50%; transition: all 0.2s ease; display: flex; align-items: center; justify-content: center; margin-bottom: 4px; }
.horizontal-node:hover .h-node-dot, .horizontal-node.is-active .h-node-dot { background: #2ecc71; transform: scale(1.3); }
.horizontal-node.is-milestone .h-node-dot { width: 14px; height: 14px; background: #e67e22; box-shadow: 0 0 8px #e67e22; }
.h-milestone-star { font-size: 8px; color: white; line-height: 1; }

.h-node-label { display: flex; flex-direction: column; align-items: center; }
.h-node-year { font-size: 13px; color: rgba(255,255,255,0.35); font-weight: 700; font-family: monospace; }
.horizontal-node.is-active .h-node-year { color: #2ecc71; font-size: 15px; }

.h-milestone-name { 
  font-size: 10px; color: #e67e22; font-weight: bold; background: rgba(230,126,34,0.12); 
  padding: 1px 5px; border-radius: 4px; white-space: nowrap; 
  position: absolute; top: 6px; left: 50%; transform: translateX(-50%);
}

.timeline-click-hint { font-size: 11px; color: rgba(255,255,255,0.2); width: 130px; text-align: right; flex-shrink: 0; padding-left: 15px; border-left: 1px solid rgba(255,255,255,0.05); }

@keyframes radarScan { 0% { top: 0; } 50% { top: 100%; } 100% { top: 0; } }
</style>