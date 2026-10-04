import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./test-browser",
  outputDir: "./test-results/hooks",
  retries: 0,
  use: { baseURL: "http://127.0.0.1:5174", trace: "retain-on-failure" },
  webServer: {
    command: "node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5174 --strictPort",
    url: "http://127.0.0.1:5174",
    reuseExistingServer: false,
  },
});
