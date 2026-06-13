import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './tests/e2e-playwright',
  testMatch: ['admin-control-room.spec.ts'],
  timeout: 60000,
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 1,
  workers: process.env.CI ? 1 : 2,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:4174',
    actionTimeout: 15000,
    navigationTimeout: 30000,
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: 'npm run preview:admin',
    url: 'http://localhost:4174',
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
  },
})
