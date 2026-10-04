import { defineConfig } from "@playwright/test";
import { randomBytes } from "node:crypto";
import path from "node:path";

process.env.TEST_BOOTSTRAP_PASSWORD ||= randomBytes(24).toString("base64url");
process.env.TEST_DATABASE_PATH ||= path.resolve(
  "../backend/.browser-tests/" + randomBytes(12).toString("hex") + ".db",
);
export default defineConfig({
  testDir: "./tests",
  workers: 1,
  timeout: 180000,
  expect: { timeout: 15000 },
  use: {
    baseURL: "http://127.0.0.1:3100",
    browserName: "chromium",
    ...(process.env.PLAYWRIGHT_CHANNEL
      ? { channel: process.env.PLAYWRIGHT_CHANNEL }
      : {}),
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  webServer: [
    {
      command:
        '"' +
        path.resolve(
          process.platform === "win32"
            ? "../.venv/Scripts/python.exe"
            : "../.venv/bin/python",
        ) +
        '" -m app.scripts.browser_test_server',
      cwd: "../backend",
      url: "http://127.0.0.1:8100/api/health",
      timeout: 60000,
      reuseExistingServer: false,
      env: {
        BROWSER_TEST_MODE: "1",
        TEST_BOOTSTRAP_PASSWORD: process.env.TEST_BOOTSTRAP_PASSWORD!,
        TEST_DATABASE_PATH: process.env.TEST_DATABASE_PATH!,
      },
    },
    {
      command: "npm run dev -- --port 3100",
      url: "http://127.0.0.1:3100/login",
      timeout: 120000,
      reuseExistingServer: false,
      env: {
        BACKEND_URL: "http://127.0.0.1:8100",
        NEXT_DIST_DIR: ".next-e2e",
        NEXT_TELEMETRY_DISABLED: "1",
      },
    },
  ],
});
