// vite.config.js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    // Proxy PHP API calls to your PHP server during development
    proxy: {
      '/get_types.php':          'http://localhost:8000',
      '/get_configs.php':        'http://localhost:8000',
      '/get_config_details.php': 'http://localhost:8000',
    }
  }
})
