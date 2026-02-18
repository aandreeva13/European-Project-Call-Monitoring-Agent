import path from 'path';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Dev server proxy so the frontend can call the FastAPI backend via relative /api URLs
// without CORS issues (frontend: :3000 -> backend: :8000).
export default defineConfig({
  server: {
    port: 3000,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, '.'),
    },
  },
});
