import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    typecheck: {
      enabled: true,
      tsconfig: "./tsconfig.json",
    },
    coverage: {
      provider: "v8",
      include: ["src/**/*.ts", "src/**/*.tsx"],
      exclude: ["src/**/*.test.ts", "src/**/*.test.tsx", "src/generated/**"],
    },
  },
});
