# @syntek/tokens — Integration Guide

**Package**: `@syntek/tokens`\
**Last Updated**: `2026-03-08`\
**Applies to**: Next.js 16 + Tailwind CSS 4.2 / React Native 0.84 + NativeWind 4

---

## Overview

`@syntek/tokens` is a TypeScript + CSS package. All token values are defined as CSS custom
properties in `tokens.css`. The TypeScript constants in `tokens.ts` hold `var(--<name>)` references,
not resolved values (breakpoints are the exception — they are numeric pixels for use in JS).

This separation means:

- The same token reference works in inline styles, Tailwind arbitrary values, and NativeWind.
- Consuming projects override any token at `:root` in their own CSS without modifying this package
  or any component.
- No Tailwind CSS or PostCSS configuration is required inside `shared/tokens` itself.

---

## Does `shared/tokens` need Tailwind or PostCSS?

No. `shared/tokens` ships plain CSS and TypeScript. It has no dependency on Tailwind CSS, PostCSS,
or any build tool beyond `tsc`. Tailwind CSS 4 and PostCSS belong in each consuming application, not
in this shared package.

---

## Web — Next.js 16 + Tailwind CSS 4.2

### How Tailwind CSS 4 works

Tailwind CSS 4 no longer requires a `tailwind.config.js` for its core utility classes. Configuration
moves to CSS via the `@import "tailwindcss"` directive and an optional `@theme { }` block. The
`tokens.css` file from this package is pure CSS custom properties — it does not need to be a
Tailwind theme source.

### PostCSS setup

PostCSS configuration lives in each consuming Next.js application, not in this monorepo root. The
monorepo root has no Next.js app to serve. A consuming app sets up PostCSS as follows:

```js
// postcss.config.mjs — in the consuming Next.js app root
export default {
  plugins: {
    "@tailwindcss/postcss": {},
  },
};
```

Install the PostCSS plugin in the consuming app:

```bash
pnpm add -D @tailwindcss/postcss
```

### Importing tokens in a Next.js project

In the consuming app's global stylesheet (typically `app/globals.css` or `styles/globals.css`),
import the tokens file before the Tailwind directive so custom properties are available to all
Tailwind utilities:

```css
/* app/globals.css */
@import "@syntek/tokens/tokens.css";
@import "tailwindcss";
```

The `"@syntek/tokens/tokens.css"` path is resolved via the `exports` field in
`@syntek/tokens/package.json`:

```json
{
  "exports": {
    "./tokens.css": "./tokens.css"
  }
}
```

### Using token constants in React components

Import TypeScript constants for inline styles or Tailwind arbitrary values:

```tsx
import { COLOR_PRIMARY, SPACING_4, FONT_SIZE_BASE } from "@syntek/tokens";

// Inline style — value resolves at runtime via the CSS cascade.
<button style={{ backgroundColor: COLOR_PRIMARY, padding: SPACING_4 }}>
  Submit
</button>

// Tailwind arbitrary value — value resolves at build/runtime.
<button className={`bg-[${COLOR_PRIMARY}] p-[${SPACING_4}]`}>
  Submit
</button>
```

### Extending Tailwind theme with token values

To make token values available as first-class Tailwind utilities (e.g. `bg-primary`), add an
`@theme` block in the consuming app's global stylesheet after the imports:

```css
/* app/globals.css */
@import "@syntek/tokens/tokens.css";
@import "tailwindcss";

@theme {
  --color-primary: var(--color-primary);
  --color-secondary: var(--color-secondary);
  --color-destructive: var(--color-destructive);
  --color-muted: var(--color-muted);
  --color-surface: var(--color-surface);
  --color-background: var(--color-background);
  --color-foreground: var(--color-foreground);
  --color-border: var(--color-border);
}
```

With this in place, `className="bg-primary text-foreground"` works directly in components.

### Font families with next/font

`--font-sans`, `--font-serif`, and `--font-mono` default to system stacks in `tokens.css`. To apply
a custom font from `next/font`, inject the CSS variable at `:root` in the app's layout:

```tsx
// app/layout.tsx
import { Geist } from "next/font/google";

const geist = Geist({ subsets: ["latin"], variable: "--font-geist-sans" });

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={geist.variable}>
      <body>{children}</body>
    </html>
  );
}
```

Then override the token in the global stylesheet:

```css
/* app/globals.css */
@import "@syntek/tokens/tokens.css";
@import "tailwindcss";

:root {
  --font-sans: var(--font-geist-sans), ui-sans-serif, system-ui, sans-serif;
}
```

No component file ever references a font name directly.

---

## Mobile — React Native 0.84 + NativeWind 4

### NativeWind 4 and CSS variables

NativeWind 4 supports CSS variables natively. Token values from `tokens.css` can be applied in
NativeWind class names after configuring the preset in the consuming Expo project.

### Setup in a consuming Expo project

Install dependencies:

```bash
pnpm add @syntek/tokens nativewind
pnpm add -D tailwindcss
```

Create `tailwind.config.js` in the consuming Expo app, referencing token values from the package:

```js
// tailwind.config.js — in the consuming Expo app
const {
  BREAKPOINT_SM,
  BREAKPOINT_MD,
  BREAKPOINT_LG,
  BREAKPOINT_XL,
  BREAKPOINT_2XL,
} = require("@syntek/tokens");

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  presets: [require("nativewind/preset")],
  theme: {
    extend: {
      screens: {
        sm: `${BREAKPOINT_SM}px`,
        md: `${BREAKPOINT_MD}px`,
        lg: `${BREAKPOINT_LG}px`,
        xl: `${BREAKPOINT_XL}px`,
        "2xl": `${BREAKPOINT_2XL}px`,
      },
      colors: {
        primary: "var(--color-primary)",
        secondary: "var(--color-secondary)",
        destructive: "var(--color-destructive)",
        muted: "var(--color-muted)",
        surface: "var(--color-surface)",
        background: "var(--color-background)",
        foreground: "var(--color-foreground)",
        border: "var(--color-border)",
      },
    },
  },
};
```

The numeric breakpoint constants are used here because NativeWind expects pixel numbers, not CSS
variables, for responsive breakpoints.

### NativeWind TypeScript declaration

Add the NativeWind environment declaration to the consuming Expo app:

```ts
// nativewind-env.d.ts — in the consuming Expo app root
/// <reference types="nativewind/types" />
```

### Using token constants in React Native components

For StyleSheet (non-NativeWind), use the TypeScript constants directly:

```tsx
import { StyleSheet } from "react-native";
import { SPACING_4, SPACING_8, BREAKPOINT_MD } from "@syntek/tokens";

const styles = StyleSheet.create({
  container: {
    padding: parseInt(SPACING_4), // SPACING_4 = "var(--spacing-4)" — parse if needed
    margin: parseInt(SPACING_8),
  },
});
```

For NativeWind class-based styling, the CSS var references resolve through the NativeWind runtime:

```tsx
<View className="bg-primary p-4">
  <Text className="text-foreground">Hello</Text>
</View>
```

### CSS variable import for NativeWind

Import `tokens.css` in the Expo app entry point so NativeWind can resolve the custom properties:

```ts
// app/_layout.tsx
import "@syntek/tokens/tokens.css";
```

---

## Token override pattern

Any token can be overridden in a consuming project without modifying `@syntek/tokens`. Override at
`:root` after the tokens import:

```css
/* Consuming project globals.css */
@import "@syntek/tokens/tokens.css";

:root {
  /* Brand override — changes every component that uses COLOR_PRIMARY. */
  --color-primary: #7c3aed;

  /* Font override — applied via next/font or a local font file. */
  --font-sans: var(--font-inter), ui-sans-serif, system-ui, sans-serif;
}
```

No component, hook, or utility file changes are needed. The CSS cascade ensures the override takes
effect everywhere.

---

## What belongs where

| Concern                                  | Location                                   |
| ---------------------------------------- | ------------------------------------------ |
| Token values (CSS custom props)          | `shared/tokens/tokens.css`                 |
| Token references (TS constants)          | `shared/tokens/src/tokens.ts`              |
| Tailwind CSS 4 import directive          | Consuming app `globals.css`                |
| PostCSS config                           | Consuming app `postcss.config.mjs`         |
| `@theme {}` Tailwind extension           | Consuming app `globals.css`                |
| NativeWind preset + `tailwind.config.js` | Consuming Expo app                         |
| `next/font` variable injection           | Consuming Next.js `app/layout.tsx`         |
| Token brand overrides                    | Consuming app `globals.css` (after import) |

---

## Notes on AC3 — ESLint lint enforcement

The ESLint rule `syntek/no-hardcoded-design-values` is configured in `eslint.config.mjs` at the
monorepo root. The rule targets all `packages/web/**/*.{ts,tsx}` and `mobile/**/*.{ts,tsx}` source
files. It rejects hardcoded hex colours, `rgb()`/`rgba()` literals, `hsl()`/`hsla()` literals, `px`
spacing values, `rem` font-size values, and known font family names. Use token constants from
`@syntek/tokens` instead. See `eslint-rules/no-hardcoded-design-values.js` for the full rule
implementation and `eslint-rules/__tests__/no-hardcoded-design-values.test.js` for the unit tests.

---

## NativeWind 4 preset

`@syntek/tokens` ships a NativeWind 4 compatible Tailwind CSS config preset so consuming Expo
applications can use Syntek token utility classes (`bg-primary`, `p-4`, `font-sans`) without
manually mapping every CSS variable to a Tailwind key.

### Installation

Install the required packages in the consuming Expo project:

```bash
pnpm add @syntek/tokens nativewind
pnpm add -D tailwindcss
```

### `tailwind.config.js`

Import the preset and spread it into the `presets` array:

```js
// tailwind.config.js — in the consuming Expo app
const { nativewindPreset } = require("@syntek/tokens/nativewind");

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  presets: [nativewindPreset],
};
```

The preset maps all Syntek colour, spacing, font-size, font-family, border-radius, screen
breakpoint, and box-shadow tokens to Tailwind utility keys. Any key can be overridden in the
consuming project via the standard `theme.extend` block.

### `nativewind-env.d.ts`

Add the NativeWind type declaration file to the consuming Expo app root so TypeScript recognises the
`className` prop on React Native core components:

```ts
// nativewind-env.d.ts — in the consuming Expo app root
/// <reference types="nativewind/types" />
```

### `metro.config.js`

Configure the Metro bundler to process NativeWind CSS class names:

```js
// metro.config.js — in the consuming Expo app root
const { getDefaultConfig } = require("expo/metro-config");
const { withNativeWind } = require("nativewind/metro");

const config = getDefaultConfig(__dirname);

module.exports = withNativeWind(config, {
  input: "./global.css",
});
```

### `global.css` — importing token CSS variables

Create a global CSS entry point in the consuming Expo app. NativeWind loads this file at runtime so
the CSS custom properties defined in `tokens.css` are available to all utility classes:

```css
/* global.css — in the consuming Expo app root */
@import "@syntek/tokens/tokens.css";
@import "tailwindcss";
```

### `app/_layout.tsx` — importing global styles

Import the global CSS file in the root layout so NativeWind registers the token custom properties
before any component renders:

```tsx
// app/_layout.tsx — in the consuming Expo app
import "../global.css";

import { Stack } from "expo-router";

export default function RootLayout() {
  return <Stack />;
}
```

### Using NativeWind class names in components

With the preset active, use standard Tailwind utility class names backed by token values:

```tsx
import { View, Text } from "react-native";

export function Card() {
  return (
    <View className="bg-surface rounded-md p-4 shadow-md">
      <Text className="text-foreground font-sans text-base">Card content</Text>
    </View>
  );
}
```

### Using token constants in React Native `StyleSheet`

For `StyleSheet.create` patterns (non-NativeWind), use the TypeScript constants directly. Spacing
and breakpoint constants are numeric values; font-size and colour constants are CSS var strings
resolved by NativeWind at runtime:

```tsx
import { StyleSheet, View } from "react-native";

import { BREAKPOINT_SM, COLOR_SURFACE, FONT_SIZE_BASE, SPACING_4, SPACING_8 } from "@syntek/tokens";

const styles = StyleSheet.create({
  container: {
    // SPACING_4 is "var(--spacing-4)" — NativeWind resolves the var reference.
    padding: SPACING_4,
    margin: SPACING_8,
    backgroundColor: COLOR_SURFACE,
  },
  label: {
    fontSize: FONT_SIZE_BASE,
  },
});

// BREAKPOINT_SM is the numeric value 640 — use directly in JS media-query logic.
const isWide = windowWidth >= BREAKPOINT_SM;
```

### Runtime rendering note — AC5

Acceptance criterion 5 (verifying the preset renders correctly on iOS and Android) requires a
running Expo application with the preset wired in. This cannot be validated by automated tests in
`shared/tokens` alone, as it depends on the NativeWind CSS variable resolution layer running inside
the React Native bridge.

Verification steps are documented in `docs/TESTS/US003-MANUAL-TESTING.md` under the NativeWind
section. Run those steps against a consuming Expo app to confirm the token values resolve correctly
on both platforms before marking AC5 complete.
