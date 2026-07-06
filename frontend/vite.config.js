import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
    
  ],

  server: {
    host: true, // 允许局域网和公网穿透访问
    allowedHosts: [
      '.trycloudflare.com',  // 显式放行 Cloudflare 的所有二级域名
      'all'                  // 注入全放行关键字
    ],
    proxy: {
      '/geoserver': {
        target: 'http://8.152.203.155:8080',
        changeOrigin: true
      },
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },

  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
})
