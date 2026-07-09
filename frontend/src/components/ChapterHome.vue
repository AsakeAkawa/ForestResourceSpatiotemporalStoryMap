<template>
  <div class="home-narrative-layer">
    <div class="left-gradient-mask"></div>

    <div class="art-content-container">
      <header class="hero-header">
        <div class="brand-badge">
          <span class="pulse-dot"></span> 时空叙事 · 1985 - 2024
        </div>
        <h1 class="main-project-title">山河复翠</h1>
        <div class="sub-title-wrapper">
          <span class="accent-line"></span>
          <h2 class="sub-project-title">中国生态修复工程四十载时空演变地图</h2>
        </div>
      </header>
      
      <main class="narrative-body">
        <section class="narrative-paragraph">
          <span class="section-tag">项目背景</span>
          <p>
            自20世纪1980年代以来，中国实施了一系列举世瞩目的重大生态修复工程，如三北防护林、退耕还林还草、京津风沙源治理等。本平台通过长时序遥感与GIS空间分析技术，客观见证四十载山河变绿的壮丽史诗。
          </p>
        </section>

        <section class="narrative-paragraph">
          <span class="section-tag">内容概述</span>
          <p>
            平台集成三大核心功能：<strong>全国生态时空演变</strong>、<strong>重大生态工程展示</strong>以及<strong>区域遥感实时分析</strong>，支持全方位数据可视化与交互探索。
          </p>
        </section>
      </main>

      <footer class="meta-footer">
        <div class="team-meta">制作团队：第二组</div>
        <div class="source-meta">数据来源：CATCD / GEE 遥感时序数据</div>
      </footer>
    </div>

    <div class="map-audit-info">
      底图来源：高德地图 | 森林覆盖数据：CATCD / 中科院空天院
    </div>
  </div>
</template>

<script setup>
// 保持逻辑纯净，地图联动由 App.vue 调度
</script>

<style scoped>
/* 撑满全屏的交互层 */
.home-narrative-layer {
  position: fixed;
  top: 0; left: 0;
  width: 100vw; height: 100vh;
  pointer-events: none;
  z-index: 9;
}

/* 🌓 核心视觉：从左到页面中间的黑底渐变（完美充当背景，文字更清晰） */
.left-gradient-mask {
  position: absolute;
  top: 0; left: 0;
  width: 100%; height: 100%;
  /* 从最左侧 85% 不透明度，平滑过渡到页面 50% 处完全透明，右侧 50% 毫无遮挡显示地图 */
  background: linear-gradient(to right, 
    rgba(10, 25, 16, 0.9) 0%, 
    rgba(10, 25, 16, 0.75) 25%, 
    rgba(10, 25, 16, 0.4) 40%, 
    rgba(10, 25, 16, 0) 55%
  );
  z-index: 1;
}

/* ✍️ 艺术化内容容器 */
.art-content-container {
  pointer-events: auto; /* 恢复鼠标交互 */
  position: absolute;
  top: 0; left: 0;
  width: 45%; /* 严格控制在左侧渐变范围内 */
  height: 100%;
  padding: 12% 0 5% 6%; /* 错落有致的四周留白 */
  box-sizing: border-box;
  z-index: 2;
  display: flex;
  flex-direction: column;
  justify-content: space-between; /* 顶部标题、中部内容、底部小字拉开空间 */
  animation: artFloatUp 1s cubic-bezier(0.16, 1, 0.3, 1);
}

/* 标签样式 */
.brand-badge {
  font-size: 13px;
  color: #2ecc71;
  font-weight: 700;
  letter-spacing: 3px;
  margin-bottom: 15px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.pulse-dot {
  width: 6px; height: 6px;
  background-color: #2ecc71;
  border-radius: 50%;
  box-shadow: 0 0 8px #2ecc71;
}

/* 🌟 大标题艺术化：字号放大，加入高阶渐变裁剪 */
.main-project-title {
  font-size: 64px; /* 巨幅主标题 */
  font-weight: 900;
  margin: 0;
  letter-spacing: 8px;
  line-height: 1.1;
  background: linear-gradient(to right, #ffffff, #a2f2c2, #2ecc71);
  -webkit-background-clip: text;
  -moz-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  color: transparent;
  text-shadow: 0 4px 20px rgba(0,0,0,0.4);
}

.sub-title-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 15px;
}
.accent-line {
  width: 24px; height: 2px;
  background: #2ecc71;
}
.sub-project-title {
  font-size: 18px; /* 副标题放大 */
  color: rgba(255, 255, 255, 0.7);
  margin: 0;
  font-weight: 400;
  letter-spacing: 2px;
}

/* 中部叙事正文区 */
.narrative-body {
  margin: 40px 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 35px; /* 段落间距拉开 */
}
.narrative-paragraph {
  max-width: 520px;
}
.section-tag {
  display: inline-block;
  font-size: 12px;
  font-weight: bold;
  color: #2ecc71;
  background: rgba(46, 204, 113, 0.15);
  padding: 2px 8px;
  border-radius: 4px;
  margin-bottom: 10px;
  letter-spacing: 1px;
}
.narrative-paragraph p {
  font-size: 16px; /* 正文放大 */
  line-height: 1.9;
  color: rgba(255, 255, 255, 0.88);
  text-align: justify;
  margin: 0;
  text-shadow: 0 2px 8px rgba(0,0,0,0.5);
}
.narrative-paragraph strong {
  color: #2ecc71;
  font-weight: 600;
}

/* 底部附属团队信息 */
.meta-footer {
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  padding-top: 20px;
  max-width: 520px;
}
.team-meta {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
  font-weight: bold;
  margin-bottom: 5px;
}
.source-meta {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
}

/* 右下角符合国家标准的审图号标注 */
.map-audit-info {
  position: absolute;
  bottom: 15px; right: 20px;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.45);
  background: rgba(10, 25, 16, 0.6);
  backdrop-filter: blur(4px);
  padding: 4px 12px;
  border-radius: 4px;
  pointer-events: auto;
  border: 1px solid rgba(255,255,255,0.05);
}

/* 优雅的入场动画 */
@keyframes artFloatUp {
  from { transform: translateY(30px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}
</style>