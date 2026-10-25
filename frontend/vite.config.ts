import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 前端只与既有 FastAPI 后端通信，不做代理：跨域由后端 OM_CORS_ORIGINS 配置。
export default defineConfig({
  plugins: [vue()],
  server: {
    host: '127.0.0.1',
    port: 5173,
    strictPort: true,
  },
  preview: {
    host: '127.0.0.1',
    port: 5173,
    strictPort: true,
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
})
