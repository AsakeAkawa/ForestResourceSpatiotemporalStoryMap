<template>
  <div class="gee-analysis-dashboard">
    <aside class="sidebar-control">
      <div class="brand-title">
        <h2>区域遥感数据实时分析系统</h2>
        <span class="system-code">MODULE // SHFC2601-05</span>
      </div>

      <nav class="module-nav">
        <button 
          :class="{ active: activeSection === 'index' }" 
          @click="changeSection('index')"
        >
          <span class="nav-id">05-01</span> 遥感指数计算
        </button>
        <button 
          :class="{ active: activeSection === 'compare' }" 
          @click="changeSection('compare')"
        >
          <span class="nav-id">05-02</span> 空间变化检测
        </button>
      </nav>

      <div class="panel-body">
        <section v-if="activeSection === 'index'" class="control-group">
          <div class="setting-item">
            <label class="setting-label">目标年份选择</label>
            <select v-model="calcConfig.year" class="gis-select" @change="syncVisualizations">
              <option v-for="year in yearRange" :key="year" :value="year">{{ year }} 年</option>
            </select>
          </div>

          <div class="setting-item">
            <label class="setting-label">分析区域范围</label>
            <select v-model="calcConfig.region" class="gis-select" @change="syncVisualizations">
              <option value="all">库布齐沙漠全区 (默认)</option>
              <option value="dugui">独贵特拉镇区域</option>
              <option value="jigesitai">吉格斯太镇区域</option>
              <option value="hangjin">杭锦旗北部沙区</option>
            </select>
          </div>

          <div class="setting-item">
            <label class="setting-label">生态核心指标</label>
            <div class="indicator-grid">
              <div 
                v-for="(label, key) in indicatorMap" 
                :key="key" 
                class="indicator-card"
                :class="{ selected: calcConfig.indicator === key }"
                @click="setIndicator(key)"
              >
                <div class="card-header">
                  <span class="dot"></span>
                  <span class="title">{{ key }}</span>
                </div>
                <p class="desc">{{ label }}</p>
              </div>
            </div>
          </div>

          <button class="gis-btn btn-primary" :disabled="isComputing" @click="triggerGEE">
            {{ isComputing ? 'GEE 像元级运算中...' : '调用 GEE 云端实时计算' }}
          </button>
        </section>

        <section v-if="activeSection === 'compare'" class="control-group">
          <div class="setting-item">
            <label class="setting-label">起始年份 (Time 1)</label>
            <select v-model="compareConfig.startYear" class="gis-select" @change="syncVisualizations">
              <option v-for="year in yearRange" :key="year" :value="year">{{ year }} 年</option>
            </select>
          </div>

          <div class="setting-item">
            <label class="setting-label">结束年份 (Time 2)</label>
            <select v-model="compareConfig.endYear" class="gis-select" @change="syncVisualizations">
              <option v-for="year in yearRange" :key="year" :value="year">{{ year }} 年</option>
            </select>
          </div>

          <div class="setting-item">
            <label class="setting-label">差分检测基准指标</label>
            <select v-model="compareConfig.indicator" class="gis-select" @change="syncVisualizations">
              <option v-for="(label, key) in indicatorMap" :key="key" :value="key">{{ key }} - {{ label }}</option>
            </select>
          </div>

          <button class="gis-btn btn-warn" :disabled="isComputing" @click="triggerCompare">
            {{ isComputing ? '空间多时相差分中...' : '执行两期逐像元差分' }}
          </button>
        </section>
      </div>

      <footer class="panel-footer">
        <div class="export-header">
          <h3>分析结果导出 (05-03)</h3>
        </div>
        <div class="export-actions">
          <button @click="executeExport('TIFF')">GeoTIFF 栅格</button>
          <button @click="executeExport('PNG')">PNG 专题图</button>
          <button @click="executeExport('PDF')">PDF 面积报告</button>
        </div>
      </footer>
    </aside>

    <main class="main-display">
      <section class="map-viewport">
        <div v-if="isComputing" class="gis-loading-overlay">
          <div class="radar-scan"></div>
          <p>正在拉取 Landsat/Sentinel-2 影像计算数据...</p>
        </div>

        <div class="map-canvas-placeholder">
          <div class="crosshair-center"></div>
          <div class="status-badge">
            {{ activeSection === 'index' ? '单期辐射反演状态' : '时空两期差分状态' }}
          </div>
          <div class="spatial-info">
            <p class="coordinate-text">中心坐标: 108°17'E, 40°11'N | 投影系: WGS 84 / UTM zone 49N</p>
            <p class="target-text">
              当前观测：{{ activeSection === 'index' ? `${calcConfig.year}年 / 区域: ${calcConfig.region} / 指标: ${calcConfig.indicator}` : `时段: ${compareConfig.startYear}-${compareConfig.endYear} / 指标: ${compareConfig.indicator} 差分` }}
            </p>
          </div>
        </div>

        <div class="gis-legend">
          <div class="legend-title">{{ activeLegend.title }}</div>
          <div class="legend-scale">
            <span v-for="(color, i) in activeLegend.colors" :key="i" :style="{ backgroundColor: color }"></span>
          </div>
          <div class="legend-labels">
            <span v-for="(label, i) in activeLegend.labels" :key="i">{{ label }}</span>
          </div>
        </div>
      </section>

      <section class="analytics-panel">
        <div class="chart-container">
          <div ref="chartDom" class="chart-core"></div>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick, computed } from "vue"
import * as echarts from "echarts"

const yearRange = Array.from({ length: 2024 - 1985 + 1 }, (_, i) => 1985 + i)
const indicatorMap = {
  FVC: "植被覆盖度 (Fractional Vegetation Cover)",
  NDWI: "归一化水体指数 (Normalized Difference Water Index)",
  BSI: "裸土指数 (Bare Soil Index)",
  RSEI: "遥感生态指数 (Remote Sensing Ecological Index)"
}

const activeSection = ref("index") 
const isComputing = ref(false)
const chartDom = ref(null)
let chartInstance = null

const calcConfig = reactive({
  year: 2024,
  region: "all",
  indicator: "FVC"
})

const compareConfig = reactive({
  startYear: 2000,
  endYear: 2024,
  indicator: "RSEI"
})

const activeLegend = computed(() => {
  if (activeSection.value === 'index') {
    return {
      title: `${calcConfig.indicator} 指数数值分级反演`,
      colors: ['#a6611a', '#dfc27d', '#f5f5f5', '#80cdc1', '#018571'],
      labels: ['0.0 (极低)', '0.2', '0.5', '0.8', '1.0 (极高)']
    }
  } else {
    return {
      title: `${compareConfig.indicator} 生态治理变化分级`,
      colors: ['#d73027', '#f46d43', '#fee08b', '#d9ef8b', '#66bd63', '#1a9850'],
      labels: ['显著退化', '轻微退化', '基本不变', '轻微改善', '显著改善']
    }
  }
})

const changeSection = (section) => {
  activeSection.value = section
  nextTick(() => {
    if (chartInstance) {
      chartInstance.resize()
    }
    syncVisualizations()
  })
}

const setIndicator = (ind) => {
  calcConfig.indicator = ind
  syncVisualizations()
}

const triggerGEE = () => {
  isComputing.value = true
  setTimeout(() => {
    isComputing.value = false
    syncVisualizations()
  }, 800)
}

const triggerCompare = () => {
  if (compareConfig.startYear >= compareConfig.endYear) {
    alert("分析提示：两期变化检测的结束年份必须大于起始年份。")
    return
  }
  isComputing.value = true
  setTimeout(() => {
    isComputing.value = false
    syncVisualizations()
  }, 800)
}

const executeExport = (format) => {
  alert(`[SHFC2601-05-03] 正在对当前视窗内数据进行几何裁剪与坐标系打包，导出目标格式：[${format}]。`)
}

const syncVisualizations = () => {
  if (!chartInstance) return

  if (activeSection.value === 'index') {
    const indexMockData = {
      FVC: [0.12, 0.18, 0.29, 0.43, 0.54],
      NDWI: [0.05, 0.07, 0.11, 0.14, 0.12],
      BSI: [0.72, 0.61, 0.48, 0.35, 0.24],
      RSEI: [0.22, 0.31, 0.45, 0.58, 0.69]
    }
    const currentData = indexMockData[calcConfig.indicator] || [0.1, 0.2, 0.3, 0.4, 0.5]

    chartInstance.setOption({
      title: { 
        text: `库布其沙漠 ${calcConfig.indicator} 宏观历史恢复演变趋势`, 
        textStyle: { color: '#2ecc71', fontSize: 15, fontWeight: '600' } 
      },
      tooltip: { trigger: 'axis', backgroundColor: '#0a1910', borderColor: 'rgba(46, 204, 113, 0.2)', textStyle: { color: '#fff', fontSize: 13 } },
      grid: { left: '50', right: '25', top: '45', bottom: '35' },
      xAxis: { type: 'category', data: ['1985', '1995', '2005', '2015', '2024'], axisLine: { lineStyle: { color: 'rgba(46, 204, 113, 0.15)' } }, axisLabel: { color: '#a5bccc', fontSize: 12 } },
      yAxis: { type: 'value', min: 0, max: 1, splitLine: { lineStyle: { color: 'rgba(46, 204, 113, 0.03)' } }, axisLabel: { color: '#a5bccc', fontSize: 12 } },
      series: [{
        name: calcConfig.indicator,
        type: 'line',
        smooth: true,
        color: '#2ecc71',
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(46, 204, 113, 0.2)' },
            { offset: 1, color: 'rgba(46, 204, 113, 0)' }
          ])
        },
        data: currentData
      }]
    }, true)
  } else {
    chartInstance.setOption({
      title: { 
        text: `时段 (${compareConfig.startYear}-${compareConfig.endYear}) 像元级生态等级转移斑块占比`, 
        textStyle: { color: '#2ecc71', fontSize: 15, fontWeight: '600' } 
      },
      tooltip: { trigger: 'item', backgroundColor: '#0a1910', borderColor: 'rgba(46, 204, 113, 0.2)', formatter: '{b} : {c}%', textStyle: { fontSize: 13 } },
      grid: { left: '50', right: '25', top: '45', bottom: '35' },
      xAxis: { type: 'category', data: ['显著退化', '轻微退化', '基本不变', '轻微改善', '显著改善'], axisLine: { lineStyle: { color: 'rgba(46, 204, 113, 0.15)' } }, axisLabel: { color: '#a5bccc', fontSize: 12 } },
      yAxis: { type: 'value', splitLine: { lineStyle: { color: 'rgba(46, 204, 113, 0.03)' } }, axisLabel: { color: '#a5bccc', fontSize: 12 } },
      series: [{
        type: 'bar',
        barWidth: '40%',
        data: [
          { value: 4.2, itemStyle: { color: '#e74c3c' } },
          { value: 9.8, itemStyle: { color: '#e67e22' } },
          { value: 32.1, itemStyle: { color: '#f1c40f' } },
          { value: 38.4, itemStyle: { color: '#2ecc71' } },
          { value: 15.5, itemStyle: { color: '#27ae60' } }
        ]
      }]
    }, true)
  }
}

onMounted(() => {
  nextTick(() => {
    if (chartDom.value) {
      chartInstance = echarts.init(chartDom.value)
      syncVisualizations()
    }
  })
  window.addEventListener('resize', () => chartInstance && chartInstance.resize())
})
</script>

<style scoped>
/* 保持全屏穿透视图层，不破坏页面比例 */
.gee-analysis-dashboard {
  display: flex;
  width: 100vw;
  height: 100vh;
  background: transparent;
  color: #dae3eb;
  font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif;
  overflow: hidden;
  pointer-events: none;
  box-sizing: border-box;
}

/* ==================== 左侧控制侧边栏样式（原汁原味位置） ==================== */
.sidebar-control {
  width: 350px;
  height: 100%;
  background: rgba(10, 25, 16, 0.75); /* 深绿半透明底框 */
  backdrop-filter: blur(8px);
  border-right: 1px solid rgba(255, 255, 255, 0.04); /* 极弱化边界线条 */
  padding: 24px; /* 彻底还原原本位置与间距 */
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  box-shadow: 10px 0 30px rgba(0, 0, 0, 0.5); /* 靠阴影平滑过渡边界 */
  z-index: 10;
  pointer-events: auto;
  box-sizing: border-box;
}

.brand-title h2 { font-size: 19px; font-weight: 600; color: #ffffff; letter-spacing: 0.5px; margin: 0; }
.system-code { font-size: 11px; color: #2ecc71; font-family: monospace; background: rgba(46, 204, 113, 0.12); padding: 3px 8px; border-radius: 3px; display: inline-block; margin-top: 6px; font-weight: bold; }

/* 模块导航 */
.module-nav { display: flex; gap: 8px; margin-top: 24px; background: rgba(5, 15, 10, 0.8); padding: 4px; border-radius: 6px; border: 1px solid rgba(255, 255, 255, 0.03); }
.module-nav button { flex: 1; padding: 10px 0; background: transparent; border: none; color: #a5bccc; font-size: 14px; cursor: pointer; border-radius: 4px; transition: all 0.2s; font-weight: 500; }
.module-nav button .nav-id { font-family: monospace; font-size: 12px; opacity: 0.7; margin-right: 2px; }
.module-nav button.active { background: #1b4d2f; color: #2ecc71; font-weight: 600; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }

.panel-body { flex: 1; overflow-y: auto; padding-right: 2px; margin-top: 15px; }
.panel-body::-webkit-scrollbar { width: 4px; }
.panel-body::-webkit-scrollbar-thumb { background: #1b4d2f; border-radius: 2px; }

/* 交互表单 */
.setting-item { margin-bottom: 22px; }
.setting-label { display: block; font-size: 14px; color: #ffffff; margin-bottom: 8px; font-weight: 500; }
.gis-select { width: 100%; padding: 12px; background: rgba(10, 25, 16, 0.85); color: #ffffff; border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 4px; outline: none; font-size: 14.5px; cursor: pointer; transition: border-color 0.2s; }
.gis-select:focus { border-color: #2ecc71; }

/* 遥感指标卡片 */
.indicator-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
.indicator-card { background: rgba(10, 25, 16, 0.6); border: 1px solid rgba(255, 255, 255, 0.04); padding: 12px; border-radius: 4px; cursor: pointer; transition: all 0.2s; }
.indicator-card:hover { border-color: rgba(46, 204, 113, 0.3); background: rgba(27, 77, 47, 0.15); }
.indicator-card.selected { border-color: #2ecc71; background: rgba(46, 204, 113, 0.08); }
.card-header { display: flex; align-items: center; gap: 8px; }
.card-header .dot { width: 6px; height: 6px; border-radius: 50%; background: #2c3e50; }
.indicator-card.selected .card-header .dot { background: #2ecc71; box-shadow: 0 0 6px #2ecc71; }
.card-header .title { font-size: 14px; font-weight: bold; color: #ffffff; }
.indicator-card .desc { font-size: 11px; color: #a5bccc; margin-top: 6px; line-height: 1.35; transform: scale(0.95); transform-origin: left top; }

.gis-btn { width: 100%; padding: 14px; border: none; border-radius: 4px; font-weight: bold; cursor: pointer; font-size: 14px; transition: all 0.2s; margin-top: 6px; }
.gis-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.btn-primary { background: #2ecc71; color: #0a1910; }
.btn-warn { background: #e67e22; color: #ffffff; }
.gis-btn:hover:not(:disabled) { filter: brightness(1.1); transform: translateY(-1px); }

.panel-footer { margin-top: auto; background: rgba(10, 25, 16, 0.8); padding: 16px; border-radius: 6px; border: 1px solid rgba(255, 255, 255, 0.04); }
.export-header h3 { font-size: 13px; color: #ffffff; margin-bottom: 12px; font-weight: 500; margin-top: 0; }
.export-actions { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
.export-actions button { padding: 10px 0; background: #1b4d2f; border: none; color: #ffffff; font-size: 12.5px; border-radius: 4px; cursor: pointer; }
.export-actions button:hover { background: #27ae60; }

/* ==================== 右侧主展示视窗样式 ==================== */
.main-display { flex: 1; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }

/* 地图画板视窗利用 calc 排除掉底部图表高度，精准卡住内容不溢出 */
.map-viewport { height: calc(100vh - 250px); padding: 20px; position: relative; pointer-events: none; box-sizing: border-box; }

.map-canvas-placeholder { width: 100%; height: 100%; border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.02); display: flex; align-items: center; justify-content: center; position: relative; pointer-events: none; }
.crosshair-center { width: 20px; height: 20px; position: relative; opacity: 0.3; }
.crosshair-center::before, .crosshair-center::after { content: ''; position: absolute; background: #2ecc71; }
.crosshair-center::before { top: 9px; left: 0; width: 20px; height: 1px; }
.crosshair-center::after { top: 0; left: 9px; width: 1px; height: 20px; }

/* 弱化边界线：去除硬色细线，改用透明边缘和柔和投影 */
.status-badge { position: absolute; top: 16px; left: 16px; background: rgba(10, 25, 16, 0.75); backdrop-filter: blur(5px); padding: 8px 14px; border-radius: 4px; font-size: 13px; border: 1px solid rgba(255, 255, 255, 0.04); color: #2ecc71; pointer-events: auto; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }
.spatial-info { position: absolute; bottom: 16px; left: 16px; font-family: monospace; line-height: 1.6; background: rgba(10, 25, 16, 0.75); backdrop-filter: blur(5px); padding: 10px 14px; border-radius: 4px; border: 1px solid rgba(255, 255, 255, 0.04); box-shadow: 0 4px 12px rgba(0,0,0,0.3); }
.coordinate-text { font-size: 12px; color: #a5bccc; margin: 0; }
.target-text { font-size: 13.5px; color: #2ecc71; font-weight: bold; margin-top: 3px; margin-bottom: 0; }

.gis-loading-overlay { position: absolute; inset: 20px; background: rgba(10, 25, 16, 0.85); display: flex; flex-direction: column; align-items: center; justify-content: center; z-index: 5; border-radius: 8px; backdrop-filter: blur(4px); pointer-events: auto; font-size: 14.5px; color: #ffffff; }
.radar-scan { width: 40px; height: 40px; border: 2px solid rgba(46, 204, 113, 0.2); border-top-color: #2ecc71; border-radius: 50%; animation: spin 0.8s linear infinite; margin-bottom: 14px; }

/* 科学图例弱化边界 */
.gis-legend { position: absolute; bottom: 26px; right: 36px; background: rgba(10, 25, 16, 0.75); backdrop-filter: blur(5px); padding: 14px 18px; border-radius: 4px; border: 1px solid rgba(255, 255, 255, 0.04); min-width: 250px; box-shadow: 0 6px 20px rgba(0,0,0,0.4); pointer-events: auto; }
.legend-title { font-size: 12.5px; color: #ffffff; margin-bottom: 10px; font-weight: bold; }
.legend-scale { display: flex; height: 8px; border-radius: 4px; overflow: hidden; margin-bottom: 8px; }
.legend-scale span { flex: 1; }
.legend-labels { display: flex; justify-content: space-between; font-size: 11.5px; color: #a5bccc; }

/* 底部数智报表：完美限制在视口底端 */
.analytics-panel { height: 250px; padding: 0 20px 20px 20px; flex-shrink: 0; pointer-events: auto; box-sizing: border-box; }
.chart-container { width: 100%; height: 100%; background: rgba(10, 25, 16, 0.75); backdrop-filter: blur(5px); border-radius: 8px; padding: 18px; border: 1px solid rgba(255, 255, 255, 0.04); box-shadow: 0 6px 20px rgba(0,0,0,0.4); box-sizing: border-box; }
.chart-core { width: 100%; height: 100%; }

@keyframes spin { to { transform: rotate(360deg); } }
</style>