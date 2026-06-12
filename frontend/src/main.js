import { createApp } from 'vue'
import App from './App.vue'
import { createRouter, createWebHistory } from 'vue-router'
import DetailViewer from './components/DetailViewer.vue'

// 1. 定义路由规则
const routes = [
  { 
    path: '/detail/:id', 
    name: 'Detail',
    component: DetailViewer, 
    props: true 
  }
]

// 2. 创建路由实例
const router = createRouter({
  history: createWebHistory(),
  routes
})

const app = createApp(App)

// 3. 核心：让全家桶插件生效
app.use(router)
app.mount('#app')