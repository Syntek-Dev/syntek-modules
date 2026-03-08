/**
 * no-hardcoded-design-values.test.js
 *
 * Unit tests for the `syntek/no-hardcoded-design-values` ESLint rule using
 * the ESLint v9 RuleTester API.
 *
 * Valid cases confirm the rule does not flag permitted values (token constants,
 * CSS var references, semantic keywords, and zero/percentage values).
 *
 * Invalid cases confirm the rule flags hardcoded hex colours, rgb/rgba, hsl/hsla,
 * px spacing values, rem font-size values, and hardcoded font family names.
 */

"use strict";

const { RuleTester } = require("eslint");
const rule = require("../no-hardcoded-design-values.js");

const ruleTester = new RuleTester({
  languageOptions: {
    ecmaVersion: "latest",
    sourceType: "module",
    parserOptions: {
      ecmaFeatures: { jsx: true },
    },
  },
});

ruleTester.run("syntek/no-hardcoded-design-values", rule, {
  // -------------------------------------------------------------------------
  // Valid cases — must not trigger any errors
  // -------------------------------------------------------------------------
  valid: [
    // Token constant reference in JSX inline style
    {
      name: "JSX style with token constant identifier",
      code: `
        import { COLOR_PRIMARY, SPACING_4 } from '@syntek/tokens';
        const el = <div style={{ backgroundColor: COLOR_PRIMARY, padding: SPACING_4 }} />;
      `,
    },

    // CSS var reference string — produced by token constants at runtime
    {
      name: "JSX style with CSS var reference string",
      code: `
        const el = <div style={{ color: 'var(--color-primary)' }} />;
      `,
    },

    // Allowed semantic keywords
    {
      name: "JSX style with 'transparent'",
      code: `
        const el = <div style={{ backgroundColor: 'transparent' }} />;
      `,
    },
    {
      name: "JSX style with 'inherit'",
      code: `
        const el = <div style={{ color: 'inherit' }} />;
      `,
    },
    {
      name: "JSX style with 'currentColor'",
      code: `
        const el = <div style={{ color: 'currentColor' }} />;
      `,
    },
    {
      name: "JSX style with 'none'",
      code: `
        const el = <div style={{ outline: 'none' }} />;
      `,
    },
    {
      name: "JSX style with 'auto'",
      code: `
        const el = <div style={{ margin: 'auto' }} />;
      `,
    },
    {
      name: "JSX style with '100%'",
      code: `
        const el = <div style={{ width: '100%' }} />;
      `,
    },
    {
      name: "JSX style with '0'",
      code: `
        const el = <div style={{ margin: '0' }} />;
      `,
    },

    // StyleSheet.create with token constant references
    {
      name: "StyleSheet.create with token constants",
      code: `
        import { StyleSheet } from 'react-native';
        import { SPACING_4, COLOR_PRIMARY } from '@syntek/tokens';
        const styles = StyleSheet.create({
          container: { padding: SPACING_4, backgroundColor: COLOR_PRIMARY },
        });
      `,
    },

    // StyleSheet.create with CSS var reference
    {
      name: "StyleSheet.create with CSS var string",
      code: `
        import { StyleSheet } from 'react-native';
        const styles = StyleSheet.create({
          container: { color: 'var(--color-foreground)' },
        });
      `,
    },

    // Non-style JSX attribute — rule must not check non-style attributes
    {
      name: "Non-style JSX attribute with colour-like value is not flagged",
      code: `
        const el = <div data-color="#3B82F6" />;
      `,
    },

    // Numeric value in style — numbers are not string literals
    {
      name: "JSX style with numeric value",
      code: `
        const el = <div style={{ zIndex: 10, opacity: 0.5 }} />;
      `,
    },
  ],

  // -------------------------------------------------------------------------
  // Invalid cases — each must produce the expected error message
  // -------------------------------------------------------------------------
  invalid: [
    // Hex colour — 6 digit
    {
      name: "Hex colour 6-digit",
      code: `
        const el = <div style={{ color: '#3B82F6' }} />;
      `,
      errors: [
        {
          message:
            'Hardcoded hex colour "#3B82F6" found. Use a token constant from @syntek/tokens (e.g. COLOR_PRIMARY) instead.',
        },
      ],
    },

    // Hex colour — 3 digit shorthand
    {
      name: "Hex colour 3-digit shorthand",
      code: `
        const el = <div style={{ color: '#fff' }} />;
      `,
      errors: [
        {
          message:
            'Hardcoded hex colour "#fff" found. Use a token constant from @syntek/tokens (e.g. COLOR_PRIMARY) instead.',
        },
      ],
    },

    // rgb() colour
    {
      name: "rgb() colour",
      code: `
        const el = <div style={{ backgroundColor: 'rgb(59,130,246)' }} />;
      `,
      errors: [
        {
          message:
            'Hardcoded rgb/rgba colour "rgb(59,130,246)" found. Use a token constant from @syntek/tokens (e.g. COLOR_PRIMARY) instead.',
        },
      ],
    },

    // rgba() colour
    {
      name: "rgba() colour",
      code: `
        const el = <div style={{ borderColor: 'rgba(0,0,0,0.5)' }} />;
      `,
      errors: [
        {
          message:
            'Hardcoded rgb/rgba colour "rgba(0,0,0,0.5)" found. Use a token constant from @syntek/tokens (e.g. COLOR_PRIMARY) instead.',
        },
      ],
    },

    // hsl() colour
    {
      name: "hsl() colour",
      code: `
        const el = <div style={{ color: 'hsl(221,83%,53%)' }} />;
      `,
      errors: [
        {
          message:
            'Hardcoded hsl/hsla colour "hsl(221,83%,53%)" found. Use a token constant from @syntek/tokens (e.g. COLOR_PRIMARY) instead.',
        },
      ],
    },

    // Hardcoded px spacing
    {
      name: "Hardcoded px spacing value",
      code: `
        const el = <div style={{ padding: '16px' }} />;
      `,
      errors: [
        {
          message:
            'Hardcoded px value "16px" found. Use a spacing token constant from @syntek/tokens (e.g. SPACING_4) instead.',
        },
      ],
    },

    // Hardcoded small px spacing
    {
      name: "Hardcoded small px spacing value",
      code: `
        const el = <div style={{ margin: '4px' }} />;
      `,
      errors: [
        {
          message:
            'Hardcoded px value "4px" found. Use a spacing token constant from @syntek/tokens (e.g. SPACING_4) instead.',
        },
      ],
    },

    // Hardcoded rem font-size
    {
      name: "Hardcoded rem font-size",
      code: `
        const el = <div style={{ fontSize: '0.875rem' }} />;
      `,
      errors: [
        {
          message:
            'Hardcoded rem value "0.875rem" found. Use a font-size token constant from @syntek/tokens (e.g. FONT_SIZE_SM) instead.',
        },
      ],
    },

    // Hardcoded 1rem font-size
    {
      name: "Hardcoded 1rem font-size",
      code: `
        const el = <div style={{ fontSize: '1rem' }} />;
      `,
      errors: [
        {
          message:
            'Hardcoded rem value "1rem" found. Use a font-size token constant from @syntek/tokens (e.g. FONT_SIZE_SM) instead.',
        },
      ],
    },

    // Hardcoded font name — Inter
    {
      name: "Hardcoded font name Inter",
      code: `
        const el = <div style={{ fontFamily: 'Inter' }} />;
      `,
      errors: [
        {
          message:
            'Hardcoded font name "Inter" found. Use a font family token constant from @syntek/tokens (e.g. FONT_SANS) instead.',
        },
      ],
    },

    // Hardcoded font name — Roboto
    {
      name: "Hardcoded font name Roboto",
      code: `
        const el = <div style={{ fontFamily: 'Roboto' }} />;
      `,
      errors: [
        {
          message:
            'Hardcoded font name "Roboto" found. Use a font family token constant from @syntek/tokens (e.g. FONT_SANS) instead.',
        },
      ],
    },

    // StyleSheet.create with hardcoded hex colour
    {
      name: "StyleSheet.create with hardcoded hex colour",
      code: `
        import { StyleSheet } from 'react-native';
        const styles = StyleSheet.create({
          container: { backgroundColor: '#1D4ED8' },
        });
      `,
      errors: [
        {
          message:
            'Hardcoded hex colour "#1D4ED8" found. Use a token constant from @syntek/tokens (e.g. COLOR_PRIMARY) instead.',
        },
      ],
    },

    // StyleSheet.create with hardcoded px padding
    {
      name: "StyleSheet.create with hardcoded px padding",
      code: `
        import { StyleSheet } from 'react-native';
        const styles = StyleSheet.create({
          button: { padding: '8px' },
        });
      `,
      errors: [
        {
          message:
            'Hardcoded px value "8px" found. Use a spacing token constant from @syntek/tokens (e.g. SPACING_4) instead.',
        },
      ],
    },

    // Multiple violations in one style object
    {
      name: "Multiple violations in a single style object",
      code: `
        const el = <div style={{ color: '#fff', fontSize: '1rem' }} />;
      `,
      errors: [
        {
          message:
            'Hardcoded hex colour "#fff" found. Use a token constant from @syntek/tokens (e.g. COLOR_PRIMARY) instead.',
        },
        {
          message:
            'Hardcoded rem value "1rem" found. Use a font-size token constant from @syntek/tokens (e.g. FONT_SIZE_SM) instead.',
        },
      ],
    },
  ],
});

console.log("All no-hardcoded-design-values rule tests passed.");
