<template>
  <div class="detail-full-page">
    <div class="nav-back">
      <button @click="$router.back()"> ➔ 返回时空地图 </button>
    </div>
    <div class="content">
      <h1>深度档案：{{ id }}</h1>
      <p>这里是由 {{ id }} 组员负责编写的深度遥感分析、历史对比图表等详细内容...</p>
    </div>
  </div>
</template>

<script setup>
defineProps(['id'])
</script>

<style scoped>
.detail-full-page { 
  position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; 
  background: white; z-index: 100; padding: 50px; box-sizing: border-box;
}
.nav-back button { background: #1b4d2f; color: white; border: none; padding: 10px 20px; cursor: pointer; border-radius: 5px; }
</style>