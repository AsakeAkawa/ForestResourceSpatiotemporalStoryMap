<template>
  <div class="chapter-one-container" @mousemove="handleGlobalMouseMove" @mouseup="handleGlobalMouseUp">
    <div class="left-narrative-panel">
      <header class="panel-header">
        <div class="active-year-title">{{ currentYear }}<span class="year-unit">年</span></div>
        <h2 class="narrative-title">中国国土绿化时空演变长卷</h2>
        <div class="art-decorator-line"></div>
      </header>
      
      <main class="narrative-content">
        <section class="narrative-section">
          <h3 class="section-art-title">时代治理背景</h3>
          <p class="section-paragraph">{{ currentNarrative.policy }}</p>
        </section>
        
        <section class="narrative-section">
          <h3 class="section-art-title">生态修复成效</h3>
          <p class="section-paragraph highlight-text">{{ currentNarrative.achievement }}</p>
        </section>
      </main>

      <div class="charts-zone">
        <div class="chart-wrapper">
          <div class="chart-art-title">全国森林覆盖率长时序演变 (1985-2020)</div>
          <div ref="lineChartRef" class="echart-container"></div>
        </div>
        <div class="chart-wrapper">
          <div class="chart-art-title">七大地理分区森林面积占比估计</div>
          <div ref="pieChartRef" class="echart-container"></div>
        </div>
      </div>
    </div>

    <div class="map-layer-placeholder" :key="currentYear">
      <div class="placeholder-border-box">
        <div class="scan-line"></div>
        <div class="layer-meta-info">
          <span class="layer-title">LANDSAT / MODIS 卫星遥感时序合成影像</span>
          <h3 class="layer-year">{{ currentYear }} 年 全国森林覆盖栅格数据</h3>
          <span class="layer-status">[ 遥感影像待挂载 ]</span>
        </div>
      </div>
    </div>

    <div class="right-vertical-timeline" @pointerdown="handleSliderDown">
      <div class="timeline-header-box">
        <button class="art-play-btn" :class="{ 'is-playing': isPlaying }" @click.stop="togglePlay">
          {{ isPlaying ? '⏸ 暂停演变' : '▶ 动态轮播' }}
        </button>
      </div>

      <div class="vertical-axis-wrapper" ref="axisWrapperRef">
        <div class="vertical-track-line"></div>
        
        <div class="active-slider-cursor" :style="{ top: cursorTop + 'px' }"></div>

        <div 
          v-for="(node, idx) in timelineNodes" 
          :key="node.year"
          class="vertical-node"
          :class="{ 
            'is-active': currentYear === node.year,
            'is-milestone': node.isMilestone 
          }"
          :style="{ height: nodeHeight + 'px' }"
          @click.stop="selectYear(node.year)"
        >
          <div class="v-node-dot">
            <span v-if="node.isMilestone" class="v-milestone-star">★</span>
          </div>
          <div class="v-node-label">
            <span class="v-node-year">{{ node.year }}</span>
            <span v-if="node.isMilestone" class="v-milestone-name">{{ node.milestoneName }}</span>
          </div>
        </div>
      </div>
      
      <div class="timeline-drag-hint">↕ 鼠标可在右侧轴区上下拖拽滑动切换年份</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

// --- 1. 模拟长时序生态演变大数据库 ---
const timelineNodes = [
  { year: 1985, isMilestone: false },
  { year: 1990, isMilestone: false },
  { year: 1995, isMilestone: false },
  { year: 1999, isMilestone: true, milestoneName: '退耕还林筹备' },
  { year: 2000, isMilestone: true, milestoneName: '天保工程启动' },
  { year: 2005, isMilestone: false },
  { year: 2010, isMilestone: false },
  { year: 2015, isMilestone: true, milestoneName: '生态文明顶层规划' },
  { year: 2020, isMilestone: false }
]

const historicalData = {
  1985: { coverage: 12.0, policy: "20世纪80年代，我国开始大规模国土绿化探索，三北防护林体系一期工程进入总结巩固阶段。", achievement: "全国森林覆盖率约12.0%，整体基数较低，北方风沙侵蚀与南方水土流失形势严峻。", pie: [{ name: '东北区', value: 35 }, { name: '华南区', value: 20 }, { name: '西南区', value: 18 }, { name: '其他', value: 27 }] },
  1990: { coverage: 12.9, policy: "启动林业重大生态工程大江大河流域综合治理，重视大江大河中上游水土保持。", achievement: "森林覆盖率微升至12.9%，人工林种植面积开始出现显著破局增长。", pie: [{ name: '东北区', value: 34 }, { name: '华南区', value: 21 }, { name: '西南区', value: 19 }, { name: '其他', value: 26 }] },
  1995: { coverage: 13.9, policy: "加速推进消灭荒山行动，南方多省掀起全民义务植树的高潮。", achievement: "全国森林总面积稳步扩张，区域生态屏障雏形初现，覆盖率逼近14%。", pie: [{ name: '东北区', value: 32 }, { name: '华南区', value: 23 }, { name: '西南区', value: 20 }, { name: '其他', value: 25 }] },
  1999: { coverage: 15.1, policy: "面对98特大洪灾，国家痛定思痛，开始在中上游地区筹备、试点“退耕还林还草”大战略。", achievement: "生态治理理念发生历史性根本转变，全面由破坏、索取转向有计划、大范围的休养生息。", pie: [{ name: '东北区', value: 31 }, { name: '华南区', value: 23 }, { name: '西南区', value: 21 }, { name: '其他', value: 25 }] },
  2000: { coverage: 16.6, policy: "天然林资源保护工程（天保工程）在全国范围内全面正式启动，全面停止长江上游、黄河上中游天然林商品性采伐。", achievement: "数万名伐木工人“放下斧头，拿起锄头”，亿亩天然林进入全面封育休养状态。", pie: [{ name: '东北区', value: 30 }, { name: '华南区', value: 24 }, { name: '西南区', value: 22 }, { name: '其他', value: 24 }] },
  2005: { coverage: 18.2, policy: "退耕还林工程进入全面爆发期，中西部荒山野岭大范围披绿，绿色版图向西北干旱区大幅西进。", achievement: "森林覆盖率实现历史性跨越突破18%，遥感NDVI卫星监测显示中国北方变绿速度位居全球前列。", pie: [{ name: '东北区', value: 28 }, { name: '华南区', value: 25 }, { name: '西南区', value: 23 }, { name: '其他', value: 24 }] },
  2010: { coverage: 20.4, policy: "三北防护林五期工程开工，生态安全屏障体系全面写入国家主体功能区规划。", achievement: "全国森林覆盖率突破20%大关，生态文明理念开始深入人心，生态采伐迹地基本全面修复。", pie: [{ name: '东北区', value: 27 }, { name: '华南区', value: 26 }, { name: '西南区', value: 24 }, { name: '其他', value: 23 }] },
  2015: { coverage: 21.6, policy: "党中央明确提出“绿水青山就是金山银山”，生态文明体改革红利爆发，山水林田湖草沙一体化保护迈入新阶段。", achievement: "林长制等制度开始试点，大规模国土绿化由“粗放式数量扩张”走向“高质量精细化提质增效”。", pie: [{ name: '东北区', value: 26 }, { name: '华南区', value: 26 }, { name: '西南区', value: 25 }, { name: '其他', value: 23 }] },
  2020: { coverage: 23.0, policy: "全面完成新时代首期生态治理蓝图。中国宣布双碳目标，森林作为核心碳汇资产，其战略地位提到前所未有的高度。", achievement: "森林覆盖率正式达到23.04%，中国贡献了全球同期近四分之一的新增绿化面积，成就世界生态治理史上的东方奇迹。", pie: [{ name: '东北区', value: 25 }, { name: '华南区', value: 26 }, { name: '西南区', value: 26 }, { name: '其他', value: 23 }] }
}

// --- 2. 状态声明 ---
const currentYear = ref(1985)
const isPlaying = ref(false)
const axisWrapperRef = ref(null)
let playTimer = null

// 拖拽滑动相关变量
const isDragging = ref(false)
const nodeHeight = 65 // 每个纵向节点的空间高度

const lineChartRef = ref(null)
const pieChartRef = ref(null)
let lineChartInstance = null
let pieChartInstance = null

const currentNarrative = computed(() => historicalData[currentYear.value])

// 计算当前高亮下游标应该处于的绝对 Y 轴高度
const cursorTop = computed(() => {
  const idx = timelineNodes.findIndex(n => n.year === currentYear.value)
  return idx * nodeHeight + 10 // 10px 为微调对齐偏差
})

// --- 3. 纵向滑动控制核心算法 ---
function handleSliderDown(e) {
  // 排除点击播放按钮
  if (e.target.tagName === 'BUTTON') return
  isDragging.value = true
  calculateYearByPos(e)
}

function handleGlobalMouseMove(e) {
  if (!isDragging.value || !axisWrapperRef.value) return
  calculateYearByPos(e)
}

function handleGlobalMouseUp() {
  isDragging.value = false
}

function calculateYearByPos(e) {
  const rect = axisWrapperRef.value.getBoundingClientRect()
  // 计算鼠标相对时间轴轨道顶部的相对 Y 坐标
  const relativeY = e.clientY - rect.top
  
  // 边界约束
  let targetIdx = Math.floor(relativeY / nodeHeight)
  if (targetIdx < 0) targetIdx = 0
  if (targetIdx >= timelineNodes.length) targetIdx = timelineNodes.length - 1
  
  const targetYear = timelineNodes[targetIdx].year
  if (currentYear.value !== targetYear) {
    currentYear.value = targetYear
  }
}

// --- 4. 图表与轮播控制 ---
function initCharts() {
  if (!lineChartRef.value || !pieChartRef.value) return

  lineChartInstance = echarts.init(lineChartRef.value, 'dark')
  const years = Object.keys(historicalData).map(Number)
  const coverages = years.map(y => historicalData[y].coverage)

  lineChartInstance.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', backgroundColor: 'rgba(10,25,16,0.95)', borderColor: '#2ecc71' },
    grid: { left: '12%', right: '8%', top: '10%', bottom: '15%' },
    xAxis: { type: 'category', data: years, axisLine: { lineStyle: { color: 'rgba(255,255,255,0.2)' } } },
    yAxis: { type: 'value', min: 10, max: 25, axisLabel: { formatter: '{value}%' }, splitLine: { lineStyle: { color: 'rgba(255,255,255,0.03)' } } },
    series: [{
      data: coverages,
      type: 'line',
      smooth: true,
      color: '#2ecc71',
      lineStyle: { width: 3 },
      areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(46,204,113,0.2)' }, { offset: 1, color: 'rgba(46,204,113,0)' }]) }
    }]
  })

  pieChartInstance = echarts.init(pieChartRef.value, 'dark')
  updatePieChart()
}

function updatePieChart() {
  if (!pieChartInstance) return
  pieChartInstance.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'item', formatter: '{b}: {c}%' },
    series: [{
      type: 'pie',
      radius: ['45%', '70%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 4 },
      label: { show: true, color: 'rgba(255,255,255,0.7)', fontSize: 11 },
      color: ['#2ecc71', '#27ae60', '#1abc9c', '#16a085', '#2c3e50'],
      data: currentNarrative.value.pie
    }]
  })
}

watch(currentYear, () => {
  updatePieChart()
  if (lineChartInstance) {
    const idx = Object.keys(historicalData).map(Number).indexOf(currentYear.value)
    lineChartInstance.dispatchAction({ type: 'showTip', seriesIndex: 0, dataIndex: idx })
  }
})

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
  window.addEventListener('resize', () => {
    lineChartInstance?.resize()
    pieChartInstance?.resize()
  })
})

onUnmounted(() => {
  clearInterval(playTimer)
  lineChartInstance?.dispose()
  pieChartInstance?.dispose()
})
</script>

<style scoped>
/* 撑满全屏的底层交互层 */
.chapter-one-container {
  position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; pointer-events: none; z-index: 9; user-select: none;
}

/* 🌓 核心视觉：完全对齐首页！从左到页面中间的黑底渐变（完美充当背景，文字更清晰） */
.chapter-one-container::before {
  content: "";
  position: absolute;
  top: 0; left: 0;
  width: 100%; height: 100%;
  /* 采用与首页一模一样的多阶段平滑渐变，无任何生硬截断，右侧 50% 毫无遮挡显示地图 */
  background: linear-gradient(to right, 
    rgba(10, 25, 16, 0.95) 0%, 
    rgba(10, 25, 16, 0.8) 25%, 
    rgba(10, 25, 16, 0.45) 42%, 
    rgba(10, 25, 16, 0) 58%
  );
  z-index: 1;
}

/* ✍️ 艺术化内容容器：不再设置死背景和宽度硬切，只负责排版 */
.left-narrative-panel {
  pointer-events: auto;
  position: absolute;
  top: 0; left: 0;
  width: 42%; /* 严格控制在渐变安全范围内 */
  height: 100%;
  padding: 110px 0 40px 6%; /* 左侧留出 6% 的气口，与首页对齐 */
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  z-index: 3;
}

/* 艺术化大字号标题 */
.active-year-title {
  font-size: 80px; /* 年份再次放大，视觉冲击力拉满 */
  font-weight: 900;
  color: #2ecc71;
  line-height: 1;
  font-family: 'Impact', sans-serif;
  letter-spacing: 2px;
  background: linear-gradient(to bottom, #ffffff, #2ecc71);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  text-shadow: 0 4px 20px rgba(0,0,0,0.4);
}
.year-unit { font-size: 24px; font-weight: bold; margin-left: 8px; color: #fff; -webkit-text-fill-color: #fff; }
.narrative-title { font-size: 24px; color: rgba(255,255,255,0.95); font-weight: 800; margin: 8px 0 0 0; letter-spacing: 1px; }
.art-decorator-line { width: 40px; height: 3px; background: #2ecc71; margin-top: 15px; }

/* 纯文字无框叙事区 */
.narrative-content { display: flex; flex-direction: column; gap: 25px; margin: 40px 0; }
.narrative-section { background: none; padding: 0; border: none; } 
.section-art-title {
  font-size: 13px; color: #2ecc71; font-weight: bold; letter-spacing: 2px;
  margin-bottom: 8px; text-transform: uppercase; border-left: 2px solid #2ecc71; padding-left: 8px;
}
.section-paragraph {
  font-size: 15px; line-height: 1.8; color: rgba(255, 255, 255, 0.88); margin: 0; text-align: justify;
  text-shadow: 0 2px 6px rgba(0,0,0,0.6);
}
.highlight-text { color: #ffffff; font-weight: 500; }

/* 图表区：完美融入通透的遮罩底色 */
.charts-zone { flex: 1; display: flex; flex-direction: column; gap: 20px; min-height: 0; }
.chart-wrapper { flex: 1; min-height: 0; display: flex; flex-direction: column; background: transparent; padding: 0; }
.chart-art-title { font-size: 12px; color: rgba(255,255,255,0.4); border-left: 2px solid rgba(255,255,255,0.2); padding-left: 8px; margin-bottom: 5px; }
.echart-container { flex: 1; width: 100%; min-height: 0; }

/* 📺 地图中央遥感图像高亮占位层 */
.map-layer-placeholder {
  position: absolute; top: 50%; left: 58%; transform: translate(-50%, -50%);
  width: 440px; height: 280px; background: rgba(46, 204, 113, 0.02);
  border: 1px dashed rgba(46, 204, 113, 0.2); border-radius: 4px; z-index: 2;
}
.placeholder-border-box { position: relative; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; overflow: hidden; }
.scan-line { position: absolute; top: 0; left: 0; width: 100%; height: 1px; background: linear-gradient(to right, transparent, rgba(46,204,113,0.7), transparent); animation: radarScan 4s linear infinite; }
.layer-meta-info { text-align: center; }
.layer-title { font-size: 11px; color: #2ecc71; letter-spacing: 1px; display: block; margin-bottom: 5px; }
.layer-year { font-size: 18px; font-weight: 800; margin: 0 0 5px 0; color: #ffffff; }
.layer-status { font-size: 11px; color: rgba(255,255,255,0.3); font-family: monospace; }

/* 🎚️ 3. 右侧悬浮：纵向悬浮时间滑轴（样式微调使其独立高感） */
.right-vertical-timeline {
  pointer-events: auto;
  position: absolute;
  top: 120px; right: 40px; bottom: 50px; width: 160px;
  background: rgba(10, 25, 16, 0.85); backdrop-filter: blur(8px);
  border: 1px solid rgba(46, 204, 113, 0.15); border-radius: 16px;
  padding: 20px 10px; box-sizing: border-box;
  display: flex; flex-direction: column; align-items: center; z-index: 10;
  box-shadow: -5px 5px 25px rgba(0,0,0,0.5);
  cursor: ns-resize;
}

.timeline-header-box { width: 100%; margin-bottom: 20px; display: flex; justify-content: center; }
.art-play-btn {
  background: transparent; color: #2ecc71; border: 1px solid #2ecc71; padding: 6px 14px;
  border-radius: 15px; font-size: 11px; font-weight: bold; cursor: pointer; transition: all 0.2s; width: 90%;
}
.art-play-btn:hover, .art-play-btn.is-playing { background: #2ecc71; color: #fff; box-shadow: 0 0 10px #2ecc71; }

.vertical-axis-wrapper {
  flex: 1; width: 100%; position: relative;
  display: flex; flex-direction: column; align-items: flex-start;
  padding-left: 20px; box-sizing: border-box;
}
.vertical-track-line {
  position: absolute; top: 15px; bottom: 15px; left: 25px; width: 2px;
  background: rgba(255,255,255,0.1); z-index: 1;
}

.active-slider-cursor {
  position: absolute; left: 22px; width: 8px; height: 8px;
  background: #ffffff; border-radius: 50%; z-index: 3;
  box-shadow: 0 0 12px 4px #2ecc71;
  transition: top 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.vertical-node {
  position: relative; z-index: 2; display: flex; align-items: center;
  gap: 15px; width: 100%; cursor: pointer;
}
.v-node-dot {
  width: 8px; height: 8px; background: rgba(255,255,255,0.2); border-radius: 50%;
  transition: all 0.2s ease; display: flex; align-items: center; justify-content: center;
}
.vertical-node:hover .v-node-dot, .vertical-node.is-active .v-node-dot {
  background: #2ecc71; transform: scale(1.2);
}

.vertical-node.is-milestone .v-node-dot {
  width: 14px; height: 14px; background: #e67e22; box-shadow: 0 0 6px #e67e22;
}
.v-milestone-star { font-size: 8px; color: white; }

.v-node-label { display: flex; flex-direction: column; justify-content: center; }
.v-node-year { font-size: 13px; color: rgba(255,255,255,0.5); font-weight: 700; font-family: monospace; }
.vertical-node.is-active .v-node-year { color: #2ecc71; font-size: 15px; }

.v-milestone-name {
  font-size: 9px; color: #e67e22; font-weight: bold; margin-top: 1px;
  background: rgba(230,126,34,0.1); padding: 0px 4px; border-radius: 2px;
  white-space: nowrap; position: absolute; left: 65px;
}

.timeline-drag-hint {
  font-size: 9px; color: rgba(255,255,255,0.25); text-align: center;
  margin-top: 15px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 8px;
}

@keyframes radarScan { 0% { top: 0; } 50% { top: 100%; } 100% { top: 0; } }
</style>