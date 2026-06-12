import { createRouter, createWebHistory } from 'vue-router'
import DetailViewer from '../components/DetailViewer.vue'

const routes = [
  { path: '/detail/:id', component: DetailViewer, props: true }
]

export default createRouter({
  history: createWebHistory(),
  routes
})