import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    fs: {
      allow: [path.resolve(__dirname, '..')],
    },
    proxy: {
      '/proxy/wms': {
        target: 'https://wms.mapama.gob.es',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/proxy\/wms/, ''),
      },
      '/proxy/ign': {
        target: 'https://www.ign.es',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/proxy\/ign/, ''),
      },
    },
  },
  preview: {
    host: '0.0.0.0',
    port: 4173,
  },
});