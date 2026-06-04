import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

// https://vite.dev/config/
export default defineConfig({
  server: {
    proxy: {
      "/api": "http://localhost:5000",
    },
  },
  plugins: [vue()],
});
