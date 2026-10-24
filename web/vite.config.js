import { fileURLToPath, URL } from 'node:url';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// `@contracts` points at the repository's contracts/ folder so the app and its tests use the
// same schema and fixtures as the Python engine.
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@contracts': fileURLToPath(new URL('../contracts', import.meta.url)),
    },
  },
  build: {
    // Both lazy payloads stay below the task's 1 MB ceiling. ECharts imports only
    // the chart types used by this application; the fixture is a single contract.
    chunkSizeWarningLimit: 1000,
  },
  server: {
    fs: { allow: ['..'] },
  },
  test: {
    environment: 'node',
    include: ['src/**/*.test.js'],
  },
});
