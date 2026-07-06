<template>
  <div class="gee-analysis-dashboard">
    <aside class="sidebar-control apple-blur-panel">
      <div class="brand-title">
        <h2 class="text-glow-title">区域遥感数据实时分析系统</h2>
      </div>

      <nav class="module-nav">
        <button
          :class="{ active: activeSection === 'index' }"
          @click="changeSection('index')"
        >
          遥感指数计算
        </button>
        <button
          :class="{ active: activeSection === 'compare' }"
          @click="changeSection('compare')"
        >
          空间变化检测
        </button>
      </nav>

      <div class="panel-body">
        <section v-if="activeSection === 'index'" class="control-group">
          <div class="setting-item">
            <label class="setting-label">目标年份选择</label>
            <select v-model="calcConfig.year" class="gis-select">
              <option v-for="year in yearRange" :key="year" :value="year">{{ year }} 年</option>
            </select>
          </div>

          <div class="setting-item">
            <label class="setting-label">分析区域范围</label>
            <select v-model="calcConfig.region" class="gis-select">
              <option value="all">库布齐沙漠全区</option>
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
            {{ isComputing ? '卫星影像传输计算中 (约20-30秒)...' : '开始计算' }}
          </button>
          <button class="gis-btn btn-clear" @click="removeLayer" :disabled="!hasResult">
            清除结果
          </button>
        </section>

        <section v-if="activeSection === 'compare'" class="control-group">
          <div class="setting-item">
            <label class="setting-label">起始年份 (Time 1)</label>
            <select v-model="compareConfig.startYear" class="gis-select">
              <option v-for="year in yearRange" :key="year" :value="year">{{ year }} 年</option>
            </select>
          </div>

          <div class="setting-item">
            <label class="setting-label">结束年份 (Time 2)</label>
            <select v-model="compareConfig.endYear" class="gis-select">
              <option v-for="year in yearRange" :key="year" :value="year">{{ year }} 年</option>
            </select>
          </div>

          <div class="setting-item">
            <label class="setting-label">差分检测基准指标</label>
            <div class="indicator-grid">
              <div
                v-for="(label, key) in indicatorMap"
                :key="key"
                class="indicator-card"
                :class="{ selected: compareConfig.indicator === key }"
                @click="compareConfig.indicator = key"
              >
                <div class="card-header">
                  <span class="dot"></span>
                  <span class="title">{{ key }}</span>
                </div>
                <p class="desc">{{ label }}</p>
              </div>
            </div>
          </div>

          <button class="gis-btn btn-warn" :disabled="isComputing" @click="triggerCompare">
            {{ isComputing ? '正在进行逐像元差分计算...' : '执行两期逐像元差分' }}
          </button>
        </section>
      </div>

      <div class="panel-footer mic-card">
        <div class="export-header">
          <h3>分析结果导出</h3>
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
        <div v-if="isComputing" class="gis-loading-overlay">
          <div class="load-box apple-blur-panel">
            <div class="radar-scan"></div>
            <p class="loading-text">{{ computingStage }}</p>
            <div class="progress-track">
              <div class="progress-fill" :style="{ width: progressPct + '%' }"></div>
            </div>
          </div>
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

    </main>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from "vue"
import ImageLayer from 'ol/layer/Image'
import Static from 'ol/source/ImageStatic'

// Only years with data: 1986-1995 (L5), 2015-2024 (L8/L9)
const availableYears = [...Array.from({length:10},(_,i)=>1986+i), ...Array.from({length:10},(_,i)=>2015+i)]
const yearRange = availableYears

const indicatorMap = {
  NDVI: "归一化植被指数 (Normalized Difference Vegetation Index)",
  FVC: "植被覆盖度 (Fractional Vegetation Cover)",
  NDWI: "归一化水体指数 (Normalized Water Index)",
  BSI: "裸土指数 (Bare Soil Index)",
  RSEI: "遥感生态指数 (Remote Ecological Index)"
}

const activeSection = ref("index")
const isComputing = ref(false)
const computingStage = ref("")
const progressPct = ref(0)

const calcConfig = reactive({
  year: 2024,
  region: "all",
  indicator: "NDVI"
})

const compareConfig = reactive({
  startYear: 2000,
  endYear: 2024,
  indicator: "RSEI"
})

const activeLegend = computed(() => {
  const legends = {
    NDVI:  { title: 'NDVI 植被指数分级', colors: ['#6e4000','#b58a2e','#e6c850','#b4d264','#78b43c','#328c1e','#0f4610'], labels: ['<0','0.0','0.2','0.4','0.6','0.8','1.0'] },
    FVC:   { title: 'FVC 植被覆盖度分级', colors: ['#b4965a','#c3b964','#91be46','#50aa32','#1e8c28','#0a641e','#003c14'], labels: ['0.0 (裸土)','0.2','0.4','0.6','0.8','1.0 (全覆盖)'] },
    NDWI:  { title: 'NDWI 水体指数分级', colors: ['#82501e','#c8aa78','#e6e1c8','#c8dceb','#64b4e6','#0a46d2','#051e64'], labels: ['<0 (旱地)','0.0','0.15','0.4','0.7','1.0 (深水)'] },
    BSI:   { title: 'BSI 裸土指数分级', colors: ['#006400','#50a028','#dcd278','#c8aa5a','#b98c3c','#a0461e','#5a2805'], labels: ['<0 (茂密)','0.0','0.2','0.5','0.7','1.0 (荒漠)'] },
    RSEI:  { title: 'RSEI 生态指数分级', colors: ['#b41e0f','#e6821e','#f5d23c','#d2dc50','#78c837','#28a028','#054614'], labels: ['0.0 (退化)','0.3','0.5','0.6','0.75','0.9','1.0 (优良)'] },
  }
  const changeLegend = { title: '植被变化检测', colors: ['#b40a0a','#eb5050','#faae8c','#fceee6','#f5f5f5','#e1f2dc','#a0e182','#32b432','#006400'], labels: ['< -0.2','-0.10','-0.03','0.0','0.0','0.03','0.10','0.2','> 0.2'] }
  const key = activeSection.value === 'index' ? calcConfig.indicator : 'CHANGE'
  return legends[key] || changeLegend
})

const changeSection = (section) => { activeSection.value = section }
const setIndicator = (ind) => { calcConfig.indicator = ind }

// 图层管理
let currentLayer = null
const hasResult = ref(false)

function apiPath(indicator, year) {
  return `/api/${indicator.toLowerCase()}/${year}`
}

function setStage(stage, pct) { computingStage.value = stage; progressPct.value = pct }

async function triggerGEE() {
  isComputing.value = true; progressPct.value = 0
  const y = calcConfig.year, ind = calcConfig.indicator
  try {
    // 4 pre-completion stages, ~6s each = 24s animation to match ~25s real work
    const stages = [
      { text: `正在连接遥感数据服务...`,                       pct:  5 },
      { text: `正在从 GeoServer 调用 ${y} 年卫星影像...`,      pct: 25 },
      { text: `影像接收完成，正在计算 ${ind} 指数...`,          pct: 55 },
      { text: `正在渲染专题图色带...`,                          pct: 80 },
    ]
    startProgressAnimation(stages, 6000)
    const resp = await fetch(apiPath(ind, y))
    if (!resp.ok) {
      let detail = `服务器错误: ${resp.status}`
      try { const e = await resp.json(); detail = e.detail || detail } catch (_) {}
      throw new Error(detail)
    }
    await renderLayer(resp)
    setStage(`计算完成 ✓`, 100)
    await delay(600)
  } catch (e) {
    alert(`${calcConfig.indicator} 计算失败: ${e.message}`)
    console.error(e)
  } finally {
    isComputing.value = false
  }
}

function delay(ms) { return new Promise(r => setTimeout(r, ms)) }

async function renderLayer(resp) {
  const west  = parseFloat(resp.headers.get('X-Bounds-West'))
  const south = parseFloat(resp.headers.get('X-Bounds-South'))
  const east  = parseFloat(resp.headers.get('X-Bounds-East'))
  const north = parseFloat(resp.headers.get('X-Bounds-North'))
  const blob = await resp.blob()
  const url = URL.createObjectURL(blob)
  removeLayer()
  const source = new Static({ url, projection: 'EPSG:4326', imageExtent: [west, south, east, north] })
  currentLayer = new ImageLayer({ source, zIndex: 1000, opacity: 0.85 })
  window.olMap.addLayer(currentLayer)
  window.__ndviLayer = currentLayer
  hasResult.value = true
}

function removeLayer() {
  if (currentLayer && window.olMap) {
    window.olMap.removeLayer(currentLayer)
    currentLayer = null
    window.__ndviLayer = null
  }
  hasResult.value = false
}

function makeChangeStages(y1, y2) {
  return [
    { text: `正在调用 ${y1} 年 (T1) 影像数据...`,          pct:  5 },
    { text: `T1 接收完成，正在调用 ${y2} 年 (T2) 影像...`,  pct: 25 },
    { text: `正在逐像元计算 NDVI 差分...`,                 pct: 55 },
    { text: `正在渲染植被变化检测专题图...`,               pct: 80 },
  ]
}

function startProgressAnimation(stages, stepMs) {
  let i = 0
  const tick = () => {
    if (i >= stages.length) return
    setStage(stages[i].text, stages[i].pct)
    i++
    if (i < stages.length) setTimeout(tick, stepMs)
  }
  tick()
}

const triggerCompare = async () => {
  if (compareConfig.startYear >= compareConfig.endYear) {
    alert("结束年份必须大于起始年份。")
    return
  }
  isComputing.value = true; progressPct.value = 0
  const y1 = compareConfig.startYear, y2 = compareConfig.endYear
  // change detection fetches two images → ~50s; 4 stages × 12s = 48s animation
  try {
    const stages = makeChangeStages(y1, y2)
    startProgressAnimation(stages, 12000)
    const resp = await fetch(`/api/change/${y1}/${y2}`)
    if (!resp.ok) {
      let detail = `服务器错误: ${resp.status}`
      try { const e = await resp.json(); detail = e.detail || detail } catch (_) {}
      throw new Error(detail)
    }
    await renderLayer(resp)
    setStage(`变化检测完成 ✓`, 100)
    await delay(600)
  } catch (e) {
    alert(`变化检测失败: ${e.message}`)
  } finally {
    isComputing.value = false
  }
}

const executeExport = async (format) => {
  // Determine indicator + year(s) based on active section
  let indicator, year, year2
  if (activeSection.value === 'index') {
    indicator = calcConfig.indicator
    year = calcConfig.year
    year2 = undefined
  } else {
    indicator = 'CHANGE'
    year = compareConfig.startYear
    year2 = compareConfig.endYear
  }
  if (!hasResult.value) {
    alert("请先执行计算，结果存在后才可导出。")
    return
  }
  const params = new URLSearchParams({ format, indicator, year: String(year) })
  if (year2) params.set('year2', String(year2))
  try {
    const resp = await fetch(`/api/export?${params}`)
    if (!resp.ok) throw new Error(`服务器错误: ${resp.status}`)
    const blob = await resp.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    const fn = resp.headers.get('Content-Disposition')?.match(/filename="(.+)"/)?.[1]
             || `${indicator}_${year}.${format.toLowerCase()}`
    a.download = fn
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  } catch (e) {
    alert(`导出失败: ${e.message}`)
  }
}

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


/* 模块导航弹性盒 */
.module-nav { display: flex; gap: 8px; margin-top: 22px; background: rgba(0, 0, 0, 0.2); padding: 4px; border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.06); }
.module-nav button { flex: 1; padding: 10px 0; background: transparent; border: 1px solid transparent; color: rgba(255,255,255,0.55); font-size: 13.5px; cursor: pointer; border-radius: 6px; transition: all 0.2s; font-weight: 600; text-shadow: 0 1px 2px rgba(0,0,0,0.5); }
.module-nav button:hover { color: #ffffff; background: rgba(255,255,255,0.05); }
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
.btn-clear { background: transparent; border: 1px solid rgba(255,255,255,0.2) !important; color: rgba(255,255,255,0.6); box-shadow: none; }
.btn-clear:hover:not(:disabled) { background: rgba(255,107,107,0.15); border-color: #ff6b6b !important; color: #ff6b6b; }
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
.map-viewport { flex: 1; padding: 20px; position: relative; pointer-events: none; box-sizing: border-box; }
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

.gis-loading-overlay { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); z-index: 20; pointer-events: none; }
.load-box { display: flex; flex-direction: column; align-items: center; gap: 10px; padding: 18px 36px; border-radius: 12px; min-width: 340px; }
.loading-text { font-size: 13px; color: #fff; font-weight: 600; text-shadow: 0 1px 3px rgba(0,0,0,0.8); margin: 0; white-space: nowrap; }
.radar-scan { width: 28px; height: 28px; border: 2px solid rgba(46, 204, 113, 0.15); border-top-color: #2ecc71; border-radius: 50%; animation: spin 0.8s linear infinite; }
.progress-track { width: 100%; height: 4px; background: rgba(255,255,255,0.12); border-radius: 2px; overflow: hidden; }
.progress-fill { height: 100%; background: #2ecc71; border-radius: 2px; transition: width 0.4s ease; }

/* 科学图例弱化边界 */
.gis-legend { position: absolute; bottom: 26px; right: 36px; padding: 14px 18px; border-radius: 8px; min-width: 250px; pointer-events: auto; }
.legend-title { font-size: 12px; color: #ffffff; margin-bottom: 10px; font-weight: 700; text-shadow: 0 1px 2px rgba(0,0,0,0.6); }
.legend-scale { display: flex; height: 8px; border-radius: 4px; overflow: hidden; margin-bottom: 8px; }
.legend-scale span { flex: 1; }
.legend-labels { display: flex; justify-content: space-between; font-size: 11px; color: rgba(255,255,255,0.65); font-weight: 500; text-shadow: 0 1px 2px rgba(0,0,0,0.6); }

@keyframes spin { to { transform: rotate(360deg); } }
</style>