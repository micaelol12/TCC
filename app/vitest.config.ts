import { defineConfig } from 'vitest/config'
export default defineConfig({ test: { include: ['web/src/**/*.test.ts', 'shared/src/**/*.test.ts', 'extension/src/**/*.test.ts', 'extension/*.test.ts'], environment: 'node' } })
