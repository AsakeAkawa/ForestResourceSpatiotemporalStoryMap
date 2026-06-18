<template>
  <div class="gee-analysis-dashboard">
    <aside class="sidebar-control apple-blur-panel">
      <div class="brand-title">
        <h2 class="text-glow-title">区域遥感数据实时分析系统</h2>
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

      <div class="panel-footer mic-card">
        <div class="export-header">
          <h3>分析结果导出 (05-03)</h3>
        </div>
        <div class="export-actions">
          <button @click="executeExport('TIFF')">GeoTIFF</button>
          <button @click="executeExport('PNG')">PNG 专题图</button>
          <button @click="executeExport('PDF')">面积报告</button>
        </div>
      </div>
    </aside>

    <main class="main-display">
      <section class="map-viewport">
        <div v-if="isComputing" class="gis-loading-overlay apple-blur-panel">
          <div class="radar-scan"></div>
          <p class="loading-text">正在拉取 Landsat/Sentinel-2 影像计算数据...</p>
        </div>

        <div class="map-canvas-placeholder">
          <div class="crosshair-center"></div>
          <div class="status-badge apple-blur-panel text-glow-green">
            {{ activeSection === 'index' ? '📡 单期辐射反演状态' : '📡 时空两期差分状态' }}
          </div>
          <div class="spatial-info apple-blur-panel">
            <p class="coordinate-text">中心坐标: 108°17'E, 40°11'N | 投影系: WGS 84 / UTM zone 49N</p>
            <p class="target-text text-glow-green">
              当前观测：{{ activeSection === 'index' ? `${calcConfig.year}年 / 区域: ${calcConfig.region} / 指标: ${calcConfig.indicator}` : `时段: ${compareConfig.startYear}-${compareConfig.endYear} / 指标: ${compareConfig.indicator} 差分` }}
            </p>
          </div>
        </div>

        <div class="gis-legend apple-blur-panel">
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
        <div class="chart-container apple-blur-panel">
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
  NDWI: "归一化水体指数 (Normalized Water Index)",
  BSI: "裸土指数 (Bare Soil Index)",
  RSEI: "遥感生态指数 (Remote Ecological Index)"
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
      backgroundColor: 'transparent',
      title: { 
        text: `库布其沙漠 ${calcConfig.indicator} 宏观历史恢复演变趋势`, 
        textStyle: { color: '#ffffff', fontSize: 14, fontWeight: '700', textShadowColor: 'rgba(0,0,0,0.7)', textShadowBlur: 4 } 
      },
      tooltip: { trigger: 'axis', backgroundColor: 'rgba(6, 18, 12, 0.95)', borderColor: '#2ecc71', textStyle: { color: '#fff', fontSize: 13 } },
      grid: { left: '55', right: '25', top: '45', bottom: '35' },
      xAxis: { type: 'category', data: ['1985', '1995', '2005', '2015', '2024'], axisLine: { lineStyle: { color: 'rgba(255,255,255,0.2)' } }, axisLabel: { color: 'rgba(255,255,255,0.7)', fontSize: 11, fontWeight: 500 } },
      yAxis: { type: 'value', min: 0, max: 1, splitLine: { lineStyle: { color: 'rgba(255,255,255,0.04)' } }, axisLabel: { color: 'rgba(255,255,255,0.7)', fontSize: 11, fontWeight: 500 } },
      series: [{
        name: calcConfig.indicator,
        type: 'line',
        smooth: true,
        color: '#2ecc71',
        lineStyle: { width: 2.5 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(46, 204, 113, 0.25)' },
            { offset: 1, color: 'rgba(46, 204, 113, 0)' }
          ])
        },
        data: currentData
      }]
    }, true)
  } else {
    chartInstance.setOption({
      backgroundColor: 'transparent',
      title: { 
        text: `时段 (${compareConfig.startYear}-${compareConfig.endYear}) 像元级生态等级转移斑块占比`, 
        textStyle: { color: '#ffffff', fontSize: 14, fontWeight: '700', textShadowColor: 'rgba(0,0,0,0.7)', textShadowBlur: 4 } 
      },
      tooltip: { trigger: 'item', backgroundColor: 'rgba(6, 18, 12, 0.95)', borderColor: '#2ecc71', formatter: '{b} : {c}%', textStyle: { color: '#fff', fontSize: 13 } },
      grid: { left: '55', right: '25', top: '45', bottom: '35' },
      xAxis: { type: 'category', data: ['显著退化', '轻微退化', '基本不变', '轻微改善', '显著改善'], axisLine: { lineStyle: { color: 'rgba(255,255,255,0.2)' } }, axisLabel: { color: 'rgba(255,255,255,0.7)', fontSize: 11, fontWeight: 500 } },
      yAxis: { type: 'value', splitLine: { lineStyle: { color: 'rgba(255,255,255,0.04)' } }, axisLabel: { color: 'rgba(255,255,255,0.7)', fontSize: 11, fontWeight: 500 } },
      series: [{
        type: 'bar',
        barWidth: '35%',
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
.gee-analysis-dashboard {
  display: flex;
  width: 100vw;
  height: 100vh;
  background: transparent;
  color: #e2eaf0;
  font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif;
  overflow: hidden;
  pointer-events: none;
  box-sizing: border-box;
}

/* 🍏 统一高级毛玻璃重构：融入森林暗绿压光，防止卫星杂色图穿透 */
.apple-blur-panel {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.02) 0%, rgba(0, 0, 0, 0.25) 100%) !important;
  background-color: rgba(6, 18, 12, 0.55) !important; /* 暗绿压光板 */
  backdrop-filter: blur(25px) saturate(160%) !important;
  -webkit-backdrop-filter: blur(25px) saturate(160%) !important;
  border: 1px solid rgba(255, 255, 255, 0.09) !important;
  box-shadow: 0 12px 42px rgba(0, 0, 0, 0.6) !important;
}

/* 💡 文字物理阴影突围 */
.text-glow-title {
  font-size: 19px; 
  font-weight: 700; 
  color: #ffffff !important; 
  letter-spacing: 0.5px; 
  margin: 0;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.8);
}
.text-glow-green {
  color: #2ecc71 !important;
  font-weight: 700 !important;
  text-shadow: 0 0 10px rgba(46, 204, 113, 0.4);
}

/* ==================== 左侧控制侧边栏样式 ==================== */
.sidebar-control {
  width: 350px;
  height: 100%;
  padding: 24px;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  z-index: 10;
  pointer-events: auto;
  box-sizing: border-box;
}

.system-code { font-size: 10.5px; color: #2ecc71; font-family: monospace; background: rgba(46, 204, 113, 0.15); padding: 3px 8px; border-radius: 4px; display: inline-block; margin-top: 6px; font-weight: bold; border: 1px solid rgba(46, 204, 113, 0.2); }

/* 模块导航弹性盒 */
.module-nav { display: flex; gap: 8px; margin-top: 22px; background: rgba(0, 0, 0, 0.2); padding: 4px; border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.06); }
.module-nav button { flex: 1; padding: 10px 0; background: transparent; border: 1px solid transparent; color: rgba(255,255,255,0.55); font-size: 13.5px; cursor: pointer; border-radius: 6px; transition: all 0.2s; font-weight: 600; text-shadow: 0 1px 2px rgba(0,0,0,0.5); }
.module-nav button:hover { color: #ffffff; background: rgba(255,255,255,0.05); }
.module-nav button .nav-id { font-family: monospace; font-size: 11px; opacity: 0.6; margin-right: 2px; }
.module-nav button.active { background: rgba(46, 204, 113, 0.18); color: #2ecc71; font-weight: 700; border: 1px solid rgba(46, 204, 113, 0.3); text-shadow: none; }

.panel-body { flex: 1; overflow-y: auto; padding-right: 2px; margin-top: 15px; }
.panel-body::-webkit-scrollbar { width: 4px; }
.panel-body::-webkit-scrollbar-thumb { background: #1b4d2f; border-radius: 2px; }

/* 交互表单项优化 */
.setting-item { margin-bottom: 20px; }
.setting-label { display: block; font-size: 13px; color: rgba(255,255,255,0.85); margin-bottom: 8px; font-weight: 600; text-shadow: 0 1px 2px rgba(0,0,0,0.5); }
.gis-select { width: 100%; padding: 11px 14px; background: rgba(0, 0, 0, 0.35); color: #ffffff; border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 8px; outline: none; font-size: 14px; font-weight: 500; cursor: pointer; transition: all 0.2s; box-shadow: inset 0 1px 3px rgba(0,0,0,0.2); }
.gis-select:focus { border-color: #2ecc71; background: rgba(6, 18, 12, 0.7); }
.gis-select option { background-color: #0c1c13; color: #fff; }

/* 遥感指标卡片格栅 */
.indicator-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
.indicator-card { background: rgba(0, 0, 0, 0.2); border: 1px solid rgba(255, 255, 255, 0.08); padding: 12px; border-radius: 8px; cursor: pointer; transition: all 0.2s; }
.indicator-card:hover { border-color: rgba(46, 204, 113, 0.4); background: rgba(46, 204, 113, 0.05); }
.indicator-card.selected { border-color: #2ecc71; background: rgba(46, 204, 113, 0.12); box-shadow: 0 0 10px rgba(46,204,113,0.1); }
.card-header { display: flex; align-items: center; gap: 8px; }
.card-header .dot { width: 6px; height: 6px; border-radius: 50%; background: #34495e; }
.indicator-card.selected .card-header .dot { background: #2ecc71; box-shadow: 0 0 6px #2ecc71; }
.card-header .title { font-size: 13.5px; font-weight: 700; color: #ffffff; text-shadow: 0 1px 2px rgba(0,0,0,0.5); }
.indicator-card .desc { font-size: 11px; color: rgba(255,255,255,0.45); margin-top: 6px; line-height: 1.35; transform: scale(0.95); transform-origin: left top; font-weight: 500; }
.indicator-card.selected .desc { color: rgba(255,255,255,0.75); }

/* 计算动作按钮 */
.gis-btn { width: 100%; padding: 13px; border: none; border-radius: 6px; font-weight: 700; cursor: pointer; font-size: 13.5px; transition: all 0.2s; margin-top: 6px; text-shadow: 0 1px 2px rgba(0,0,0,0.2); }
.gis-btn:disabled { opacity: 0.35; cursor: not-allowed; }
.btn-primary { background: #2ecc71; color: #050f0a; box-shadow: 0 4px 12px rgba(46,204,113,0.2); }
.btn-warn { background: #e67e22; color: #ffffff; box-shadow: 0 4px 12px rgba(230,126,34,0.2); }
.gis-btn:hover:not(:disabled) { filter: brightness(1.1); transform: translateY(-1px); }

/* 内层微卡片隔离 */
.mic-card { background: rgba(0, 0, 0, 0.25) !important; border: 1px solid rgba(255, 255, 255, 0.07) !important; }
.panel-footer { margin-top: auto; padding: 14px; border-radius: 8px; }
.export-header h3 { font-size: 12.5px; color: rgba(255,255,255,0.8); margin-bottom: 10px; font-weight: 600; margin-top: 0; text-shadow: 0 1px 1px rgba(0,0,0,0.5); }
.export-actions { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; }
.export-actions button { padding: 9px 0; background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.1); color: rgba(255,255,255,0.85); font-size: 12px; font-weight: 600; border-radius: 6px; cursor: pointer; transition: all 0.2s; }
.export-actions button:hover { background: rgba(46, 204, 113, 0.15); border-color: rgba(46, 204, 113, 0.3); color: #2ecc71; }

/* ==================== 右侧主展示视窗样式 ==================== */
.main-display { flex: 1; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
.map-viewport { height: calc(100vh - 250px); padding: 20px; position: relative; pointer-events: none; box-sizing: border-box; }
.map-canvas-placeholder { width: 100%; height: 100%; border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.05); display: flex; align-items: center; justify-content: center; position: relative; pointer-events: none; }
.crosshair-center { width: 20px; height: 20px; position: relative; opacity: 0.25; }
.crosshair-center::before, .crosshair-center::after { content: ''; position: absolute; background: #2ecc71; }
.crosshair-center::before { top: 9px; left: 0; width: 20px; height: 1px; }
.crosshair-center::after { top: 0; left: 9px; width: 1px; height: 20px; }

/* 悬浮窗体强化 */
.status-badge { position: absolute; top: 16px; left: 16px; padding: 8px 14px; border-radius: 8px; font-size: 12.5px; pointer-events: auto; }
.spatial-info { position: absolute; bottom: 16px; left: 16px; font-family: monospace; line-height: 1.5; padding: 10px 14px; border-radius: 8px; }
.coordinate-text { font-size: 11.5px; color: rgba(255,255,255,0.55); margin: 0; text-shadow: 0 1px 2px rgba(0,0,0,0.6); }
.target-text { font-size: 13px; margin-top: 3px; margin-bottom: 0; }

.gis-loading-overlay { position: absolute; inset: 20px; display: flex; flex-direction: column; align-items: center; justify-content: center; z-index: 5; border-radius: 8px; pointer-events: auto; }
.loading-text { font-size: 14px; color: #fff; font-weight: 600; text-shadow: 0 2px 4px rgba(0,0,0,0.8); }
.radar-scan { width: 36px; height: 36px; border: 2px solid rgba(46, 204, 113, 0.15); border-top-color: #2ecc71; border-radius: 50%; animation: spin 0.8s linear infinite; margin-bottom: 12px; }

/* 科学图例弱化边界 */
.gis-legend { position: absolute; bottom: 26px; right: 36px; padding: 14px 18px; border-radius: 8px; min-width: 250px; pointer-events: auto; }
.legend-title { font-size: 12px; color: #ffffff; margin-bottom: 10px; font-weight: 700; text-shadow: 0 1px 2px rgba(0,0,0,0.6); }
.legend-scale { display: flex; height: 8px; border-radius: 4px; overflow: hidden; margin-bottom: 8px; }
.legend-scale span { flex: 1; }
.legend-labels { display: flex; justify-content: space-between; font-size: 11px; color: rgba(255,255,255,0.65); font-weight: 500; text-shadow: 0 1px 2px rgba(0,0,0,0.6); }

/* 底部数智报表 */
.analytics-panel { height: 250px; padding: 0 20px 20px 20px; flex-shrink: 0; pointer-events: auto; box-sizing: border-box; }
.chart-container { width: 100%; height: 100%; border-radius: 12px; padding: 16px; box-sizing: border-box; }
.chart-core { width: 100%; height: 100%; }

@keyframes spin { to { transform: rotate(360deg); } }
</style>