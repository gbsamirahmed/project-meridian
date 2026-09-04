import { defineConfig } from "@playwright/test";

const visualPort = 4173;
const baseURL = `http://localhost:${visualPort}`;

export default defineConfig({
  testDir: "./scripts/visual",
  testMatch: "**/*.visual.spec.mjs",
  outputDir: "test-results/playwright",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 90_000,
  expect: {
    timeout: 10_000,
  },
  reporter: [["list"]],
  use: {
    baseURL,
    browserName: "chromium",
    headless: true,
    colorScheme: "dark",
    locale: "en-GB",
    timezoneId: "Europe/London",
    deviceScaleFactor: 1,
    trace: "retain-on-failure",
  },
  webServer: {
    command: "npm run dev -- --port 4173 --strictPort",
    url: baseURL,
    reuseExistingServer: false,
    timeout: 120_000,
    stdout: "pipe",
    stderr: "pipe",
  },
  projects: [
    { name: "desktop-1920x1080", use: { viewport: { width: 1920, height: 1080 } } },
    { name: "desktop-1440x900", use: { viewport: { width: 1440, height: 900 } } },
    { name: "desktop-1366x768", use: { viewport: { width: 1366, height: 768 } } },
  ],
});
