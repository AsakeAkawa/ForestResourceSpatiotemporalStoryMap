import { createApp, h } from 'vue'
import { createRouter, createWebHistory, RouterView } from 'vue-router'
import App from './App.vue'
import DetailViewer from './components/DetailViewer.vue'
import Login from './components/Login.vue'

// 1. 定义路由规则（App.vue 作为主布局，嵌套详情子路由；Login 为独立全屏路由）
const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/',
    component: App,
    children: [
      {
        path: 'detail/:id',
        name: 'Detail',
        component: DetailViewer,
        props: true
      }
    ]
  }
]

// 2. 创建路由实例
const router = createRouter({
  history: createWebHistory(),
  routes
})

// 3. 全局导航守卫：未登录用户重定向至登录页
router.beforeEach((to, _from, next) => {
  const isLoggedIn = localStorage.getItem('forest_isLoggedIn')

  // 已登录用户访问登录页 → 重定向到主页
  if (to.path === '/login' && isLoggedIn) {
    next('/')
    return
  }

  // 未登录用户访问受保护页面 → 重定向到登录页
  if (to.path !== '/login' && !isLoggedIn) {
    next('/login')
    return
  }

  next()
})

// 4. 创建应用实例并挂载
const app = createApp({ render: () => h(RouterView) })
app.use(router)
app.mount('#app')
