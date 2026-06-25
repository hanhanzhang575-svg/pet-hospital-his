import { defineConfig, loadEnv } from "vite";
import vue from "@vitejs/plugin-vue";
import { fileURLToPath, URL } from "node:url";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const backendUrl = env.VITE_BACKEND_URL || "http://127.0.0.1:8010";
  const base = env.VITE_BASE_PATH || (mode === "static" ? "./" : "/");

  return {
    base,
    plugins: [vue()],
    resolve: {
      alias: {
        "@": fileURLToPath(new URL("./src", import.meta.url))
      }
    },
    server: {
      port: 5173,
      proxy: {
        "/api": {
          target: backendUrl,
          changeOrigin: true
        }
      }
    },
    build: {
      chunkSizeWarningLimit: 1200,
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (!id.includes("node_modules")) return undefined;
            if (id.includes("element-plus") || id.includes("@element-plus")) return "element-plus";
            if (id.includes("echarts")) return "echarts";
            if (id.includes("@fullcalendar")) return "calendar";
            if (id.includes("xlsx")) return "xlsx";
            return "vendor";
          }
        }
      }
    }
  };
});

