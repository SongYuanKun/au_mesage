import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import tsconfigPaths from 'vite-tsconfig-paths'

export default defineConfig({
  plugins: [react(), tsconfigPaths()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    css: false,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json-summary', 'html'],
      reportsDirectory: './coverage',
      all: true,
      include: ['src/**/*.{ts,tsx}'],
      exclude: [
        'src/**/*.test.{ts,tsx}',
        'src/test/**',
        'src/main.tsx',
        'src/vite-env.d.ts',
      ],
      // 现状基线（2026-10-19）：pages、hooks 等尚缺测试，覆盖率只许升不许降。
      // 目标仍为行 80% / 分支 70%（见 docs/au_metal_price_platform_development_standards_cicd.md），补测试后逐步抬升
      thresholds: {
        lines: 32,
        statements: 32,
        functions: 35,
        branches: 28,
      },
    },
  },
})
