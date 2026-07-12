# 山河复翠：中国生态修复工程四十载时空演变地图平台

> 基于 WebGIS 的交互式在线叙事地图平台，以动态故事、地图探索与实时遥感分析三大篇章，直观呈现中国 1985–2024 年森林生态系统的时空演变历程。

**Landscape Revitalized: 40-Year Spatiotemporal Map Platform for China's Ecological Restoration Projects** — An interactive WebGIS-based story map platform that presents the spatiotemporal evolution of China's forest ecosystems (1985–2024) through dynamic narratives, map exploration, and real-time remote sensing analysis.

[![Vue 3](https://img.shields.io/badge/Vue-3.x-4FC08D?logo=vuedotjs)](https://vuejs.org/)
[![Vite](https://img.shields.io/badge/Vite-latest-646CFF?logo=vite)](https://vite.dev/)
[![OpenLayers](https://img.shields.io/badge/OpenLayers-7.x-1F6B75?logo=openlayers)](https://openlayers.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python)](https://www.python.org/)
[![GeoServer](https://img.shields.io/badge/GeoServer-WMS/WCS-8CB44A?logo=geoserver)](https://geoserver.org/)
[![ECharts](https://img.shields.io/badge/ECharts-5.x-AA344D)](https://echarts.apache.org/)
[![Landsat](https://img.shields.io/badge/Data-Landsat_5/8/9-808080)](https://landsat.gsfc.nasa.gov/)

---

## 技术栈 / Tech Stack

| 层级 Layer | 技术 Technology |
| ---------- | --------------- |
| 前端框架 Frontend | Vue 3 (Composition API) + Vite |
| 地图引擎 Map | OpenLayers 7 |
| 图表 Charts | ECharts 5 |
| 后端 Backend | FastAPI (Python) |
| 遥感处理 RS Processing | NumPy + Rasterio + PIL |
| 空间数据服务 Geo | GeoServer (WMS / WCS) |
| 数据源 Data | Landsat 5/8/9, CATCD 森林覆盖数据集 |

---

## 系统架构 / System Architecture

```mermaid
graph TB
    subgraph 表现展示层["🎨 表现展示层 Presentation"]
        VUE[Vue 3 + Vite<br/>OpenLayers + ECharts]
    end

    subgraph 应用服务层["⚙️ 应用服务层 Application"]
        API[RESTful API<br/>FastAPI]
        AUTH[用户认证<br/>登录/会话管理]
    end

    subgraph 算法服务层["🔬 算法服务层 Algorithm"]
        NDVI[NDVI 植被指数]
        FVC[FVC 覆盖度]
        NDWI[NDWI 水体指数]
        BSI[BSI 裸土指数]
        RSEI[RSEI 生态指数<br/>PCA 降维]
        CHANGE[变化检测<br/>逐像元差分]
    end

    subgraph 地图服务层["🗺️ 地图服务层 Map Service"]
        GS[GeoServer<br/>WMS / WCS]
    end

    subgraph 数据层["💾 数据层 Data"]
        CATCD[CATCD 森林覆盖<br/>1985-2024 全国]
        L5[Landsat 5<br/>1986-1995]
        L8[Landsat 8<br/>2015-2021]
        L9[Landsat 9<br/>2022-2024]
        ECO[生态工程<br/>GeoJSON 边界]
    end

    VUE -->|HTTP| API
    VUE -->|WMS GetMap| GS
    API -->|WCS GetCoverage| GS
    API --> NDVI --> FVC
    API --> BSI
    API --> NDWI
    API --> RSEI
    NDVI --> CHANGE
    GS --> CATCD
    GS --> L5
    GS --> L8
    GS --> L9
    VUE -->|GeoJSON| ECO
```

---

## 功能篇章 / Functional Chapters

### 登录页面 / Login Portal

> [!NOTE]
> **打字机过场动画**是本平台的标志性设计——登录后触发三段式叙事过渡：首段逐字打印中国森林生态成就数据，次段浮现生态文明金句，末段呈现"进入平台"入口。全程支持空格键跳过，暗色毛玻璃背景叠加森林底图，营造沉浸式故事感。

> The login portal features a signature **typewriter-style narrative transition**: after authentication, three sequential stages unfold — ecological achievement statistics typed line-by-line, a quote on ecological civilization, and finally the platform entrance. Spacebar to skip. Dark glassmorphism backdrop over forest imagery creates an immersive storytelling atmosphere.

### 篇章〇 · 首页 / Chapter 0 · Home

> [!NOTE]
> 平台门户页面，左侧 45% 区域呈现深绿渐变遮罩 + 毛玻璃质感，承载项目标题"山河复翠"（渐变金绿大字）、副标题、项目背景与内容概述。右侧透出全幅卫星底图。底部附团队信息与审图号标注。

> The landing page displays the project title "山河复翠" (Landscape Revitalized) in gradient gold-green typography, with project background and content overview on a dark gradient mask covering the left 45% of the viewport. The right side reveals the full satellite basemap.

### 篇章一 · 全国生态时空演变 (1985–2024) / Chapter 1 · National Forest Spatiotemporal Evolution

- 6 个标准年份（1985 / 1995 / 2000 / 2010 / 2014 / 2024）全国森林覆盖栅格 WMS 动态加载
- 前端 `postrender` 钩子实时 Gamma 拉伸 + 颜色渲染（灰度 → 绿米渐变）
- 四张 ECharts 动态图表：森林覆盖率折线图、蓄积量双轴柱状图、七区占比饼图、林种结构条形图
- 底部时间轴：节点切换 + 自动轮播，年份切换联动图表与地图图层

### 篇章二 · 重大生态工程 / Chapter 2 · Major Ecological Projects

- 四大工程边界矢量图层（三北防护林 / 天然林保护 / 退耕还林 / 退牧还草），填充图案与图例一致（斜线 / 十字网 / 横线 / 点阵）
- 地图交互点位：鼠标靠近触发工程名称提示 + 半透明背景渐显；点击展开简介卡片 → 跳转详情页
- 详情页：成效指标卡、里程碑时间轴、B 站纪实视频嵌入、实景照片自动轮播、立项背景 / 治理举措 / 空间跨度文字叙事

### 篇章三 · 区域遥感数据实时分析（库布齐沙漠） / Chapter 3 · Real-Time Remote Sensing Analysis (Kubuqi Desert)

- **遥感指数计算**：NDVI / FVC / NDWI / BSI / RSEI 五种生态指标，按选定年份一键计算
- **空间变化检测**：双时相 NDVI 逐像元差分，红-白-绿发散色带渲染
- **后端计算流水线**：GeoServer WCS 按需获取多波段影像 → NumPy 像元级运算 → 色带渲染 → PNG 返回前端叠加
- **分阶段进度动画**：图像调用 → 指数计算 → 专题图渲染，进度条均匀滚动
- **结果导出**：GeoTIFF（LZW 压缩）/ PNG 专题图（含色标图例）/ PDF 面积统计报告
- **内存缓存**：预览计算后缓存原始数据，重复导出零等待

---

## 项目结构 / Project Structure

```
ForestResourceSpatiotemporalStoryMap/
├── frontend/                       # Vue 3 前端
│   ├── src/
│   │   ├── App.vue                 # OpenLayers 地图、WMS 图层、颜色渲染
│   │   ├── components/
│   │   │   ├── Login.vue           # 登录页（打字机过场动画）
│   │   │   ├── ChapterHome.vue     # 篇章〇 · 首页
│   │   │   ├── ChapterOne.vue      # 篇章一 · 全国森林时空演变
│   │   │   ├── ChapterTwo.vue      # 篇章二 · 重大生态工程
│   │   │   ├── ChapterThree.vue    # 篇章三 · 遥感实时分析
│   │   │   └── DetailViewer.vue    # 工程详情页
│   │   ├── router/index.js
│   │   └── assets/data/            # 工程 JSON 数据
│   ├── public/
│   │   ├── images/ecoprojects/     # 工程实景图片
│   │   └── data/*.geojson          # 四大工程空间边界
│   └── vite.config.js
│
├── backend/                        # FastAPI 遥感分析后端
│   ├── main.py                     # API 入口 (20 个路由)
│   ├── config.py                   # 波段映射、WET 系数、GeoServer 配置
│   ├── cache.py                    # 内存缓存
│   ├── ndvi.py                     # NDVI 归一化植被指数
│   ├── fvc.py                      # FVC 植被覆盖度（百分位法）
│   ├── ndwi.py                     # NDWI 归一化水体指数
│   ├── bsi.py                      # BSI 裸土指数
│   ├── rsei.py                     # RSEI 遥感生态指数（PCA 降维）
│   ├── change_detection.py         # 双时相 NDVI 差分变化检测
│   ├── export_module.py            # GeoTIFF / PNG / PDF 导出
│   └── requirements.txt
│
└── README.md
```

---

## 代码速查 / Code Reference

### 前端核心函数 (App.vue)

| 函数 | 行号 | 说明 |
|------|------|------|
| `onMounted()` | L136–373 | 地图初始化、所有图层创建、事件监听 |
| `switchPage(index)` | L391–420 | 篇章切换：层可见性 + 视图动画 |
| `updateForestWmsYear(year)` | L130–134 | 切换 WMS 图层年份参数 |
| `changeMapSource(id)` | L382–389 | 底图类型切换（影像/地形/街道） |
| `filterBoundaryProject(id)` | L302–330 | 工程边界单选/全选样式切换 |
| postrender 钩子 | L203–236 | SLD 10 级逐级色带 + Alpha 透明度 |

### 前端组件功能速查

| 组件 | 文件 | 核心功能 |
|------|------|------|
| 登录页 | Login.vue | 三段式打字机过场动画、空格跳过、毛玻璃底图 |
| 首页 | ChapterHome.vue | 品牌大标题、渐变遮罩、底图来源文字 |
| 篇章一 | ChapterOne.vue | ECharts 四图联动、时间轴面板、年份广播 |
| 篇章二 | ChapterTwo.vue | 边界 hover/click 交互、图例过滤、档案卡片 |
| 篇章三 | ChapterThree.vue | 遥感计算 UI、进度条动画、结果叠加、导出 |
| 详情页 | DetailViewer.vue | 指标卡片、时间轴、视频、照片轮播、文字叙事 |

### 后端 API 路由总览 (main.py)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| GET | `/api/bounds` | 库布齐研究区范围与可用年份 |
| GET/POST | `/api/{ndvi\|fvc\|ndwi\|bsi\|rsei}/{year}` | 遥感指数 PNG + 地理边界头 |
| GET | `/api/change/{y1}/{y2}` | 双时相 NDVI 逐像元差分 |
| GET | `/api/export?format={TIFF\|PNG\|PDF}` | 分析结果导出 |
| GET | `/api/info/{year}` | 年份卫星/波段信息 |

### 遥感计算模块公式

| 模块 | 核心函数 | 公式/方法 |
|------|------|------|
| ndvi.py | `calc_ndvi()` | $\text{NDVI} = (\text{NIR} - \text{Red}) / (\text{NIR} + \text{Red})$ |
| fvc.py | `calc_fvc()` | $\text{FVC} = (\text{NDVI} - \text{NDVI}_5)/(\text{NDVI}_{95} - \text{NDVI}_5)$，百分位法 |
| ndwi.py | `calc_ndwi()` | $\text{NDWI} = (\text{Green} - \text{NIR}) / (\text{Green} + \text{NIR})$ |
| bsi.py | `calc_bsi()` | $\text{BSI} = ((\text{SWIR1}+\text{Red}) - (\text{NIR}+\text{Blue})) / ((\text{SWIR1}+\text{Red}) + (\text{NIR}+\text{Blue}))$ |
| rsei.py | `pca_first_component()` | NDVI + WET + NDBSI → PCA 降维 → $\text{RSEI} = 1 - \text{PC1}_\text{norm}$ |
| change_detection.py | `calc_change()` | $\Delta\text{NDVI} = \text{NDVI}_{\text{year2}} - \text{NDVI}_{\text{year1}}$ |
| export_module.py | `export_geotiff()` | Float32 单波段 GeoTIFF，LZW 压缩，EPSG:4326 |

### 图层 Z-Index 层级

| zIndex | 图层 | 可见篇章 |
|--------|------|------|
| 1 | 底图瓦片（高德卫星/矢量、Esri 地形） | 全篇 |
| 998 | 库布齐沙漠边界 | 篇章三 |
| 999 | 全国森林覆盖 WMS | 篇章一 |
| 1000 | 遥感计算结果图层 | 篇章三 |
| 2000 | 重大工程边界 | 篇章二 |

### 资源文件

| 路径 | 规模 | 用途 |
|------|------|------|
| `public/data/sanbei.geojson` | ~13MB | 三北防护林边界 |
| `public/data/tianranlin.geojson` | ~13MB | 天然林保护边界 |
| `public/data/tuigenghuanlin.geojson` | ~13MB | 退耕还林边界 |
| `public/data/tumuhauncao.geojson` | ~13MB | 退牧还草边界 |
| `public/data/kubuqi_boundary.geojson` | ~448KB | 库布齐沙漠边界 |
| `src/assets/data/ecoprojects.json` | ~25KB | 工程全文数据（描述/指标/媒体/时间轴） |
| `public/images/ecoprojects/` | ~26 张 | 工程实景照片 |

---

## 开发环境要求 / Prerequisites

| 工具 Tool | 版本 Version |
| --------- | ------------ |
| Node.js | ≥ 18 |
| Python | ≥ 3.10 |
| GDAL | 系统库（rasterio 依赖） |

---

## 本地运行 / Local Development

### 前端 / Frontend

```bash
cd frontend
npm install
npm run dev
```

### 后端 / Backend

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

> [!TIP]
> 开发环境下 Vite 代理将 `/api` 转发至 `localhost:8000`，`/geoserver` 转发至阿里云 GeoServer，从而绕过浏览器跨域限制。
>
> In development, Vite proxies `/api` → `localhost:8000` and `/geoserver` → Alibaba Cloud GeoServer, bypassing browser CORS restrictions.

---

## 数据来源 / Data Sources

- 森林覆盖：CATCD 数据集，中国科学院空天信息创新研究院
- 库布齐多光谱：Landsat 5 TM (1986–1995) / Landsat 8 OLI (2015–2021) / Landsat 9 OLI-2 (2022–2024)
- 工程信息：《全国重要生态系统保护和修复重大工程总体规划 (2021–2035)》《中国森林资源报告》
