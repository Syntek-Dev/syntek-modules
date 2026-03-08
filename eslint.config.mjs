import js from "@eslint/js";
import tsPlugin from "@typescript-eslint/eslint-plugin";
import tsParser from "@typescript-eslint/parser";
import reactPlugin from "eslint-plugin-react";
import reactHooksPlugin from "eslint-plugin-react-hooks";
import importPlugin from "eslint-plugin-import";
import globals from "globals";
import { createRequire } from "module";

// Load the local Syntek ESLint rules. createRequire is used because this
// config is an ES module but the rule files use CommonJS exports.
const require = createRequire(import.meta.url);
const noHardcodedDesignValues = require("./eslint-rules/no-hardcoded-design-values.js");

/** @type {import("eslint").Linter.Config[]} */
export default [
  // Global ignores
  {
    ignores: [
      "node_modules/**",
      "dist/**",
      ".next/**",
      "out/**",
      "coverage/**",
      ".turbo/**",
      "target/**",
      ".venv/**",
      "playwright-report/**",
      "test-results/**",
      "**/src/generated/**",
    ],
  },

  // Base JS rules
  js.configs.recommended,

  // TypeScript + React files
  {
    files: ["**/*.ts", "**/*.tsx"],
    plugins: {
      "@typescript-eslint": tsPlugin,
      react: reactPlugin,
      "react-hooks": reactHooksPlugin,
      import: importPlugin,
    },
    languageOptions: {
      parser: tsParser,
      parserOptions: {
        ecmaVersion: "latest",
        sourceType: "module",
        ecmaFeatures: { jsx: true },
      },
      globals: {
        ...globals.browser,
        ...globals.node,
        ...globals.es2024,
      },
    },
    rules: {
      ...tsPlugin.configs.recommended.rules,
      ...reactPlugin.configs.recommended.rules,
      ...reactHooksPlugin.configs.recommended.rules,
      "react/react-in-jsx-scope": "off",
      "react/prop-types": "off",
      "@typescript-eslint/no-unused-vars": ["error", { argsIgnorePattern: "^_" }],
      "@typescript-eslint/explicit-function-return-type": "off",
      "@typescript-eslint/no-explicit-any": "warn",
      "no-undef": "off",
      "import/order": [
        "error",
        {
          groups: ["builtin", "external", "internal", "parent", "sibling", "index"],
          "newlines-between": "always",
          alphabetize: { order: "asc" },
        },
      ],
    },
    settings: {
      react: { version: "detect" },
    },
  },

  // Test files — relaxed rules
  {
    files: ["**/*.test.ts", "**/*.test.tsx", "**/*.spec.ts", "**/*.spec.tsx"],
    rules: {
      "@typescript-eslint/no-explicit-any": "off",
      "@typescript-eslint/no-non-null-assertion": "off",
    },
  },

  // Syntek design token enforcement — rejects hardcoded colour, spacing,
  // font-size, and font-family literals in web and mobile source files.
  // Excludes the token definitions themselves and all test files.
  {
    files: ["packages/web/**/*.ts", "packages/web/**/*.tsx", "mobile/**/*.ts", "mobile/**/*.tsx"],
    ignores: ["shared/tokens/**", "**/*.test.ts", "**/*.test.tsx", "**/*.spec.ts", "**/*.spec.tsx"],
    plugins: {
      syntek: {
        rules: {
          "no-hardcoded-design-values": noHardcodedDesignValues,
        },
      },
    },
    rules: {
      "syntek/no-hardcoded-design-values": "error",
    },
  },
];
