/**
 * no-hardcoded-design-values.js
 *
 * Local ESLint v9 rule that rejects hardcoded design values in JSX style props
 * and React Native StyleSheet.create objects. Enforces use of token constants
 * from `@syntek/tokens` instead of raw colour, spacing, font-size, and
 * font-family literals.
 *
 * Patterns rejected:
 *   - Hex colours:               "#3B82F6", "#fff"
 *   - rgb/rgba literals:         "rgb(59,130,246)", "rgba(0,0,0,0.5)"
 *   - hsl/hsla literals:         "hsl(221,83%,53%)"
 *   - Hardcoded px spacing:      "16px", "4px"
 *   - Hardcoded rem font-size:   "1rem", "0.875rem"
 *   - Hardcoded font names:      "Inter", "Roboto", "Arial"
 *
 * Allowed values (not flagged):
 *   - Token constants:           COLOR_PRIMARY, SPACING_4, FONT_SANS
 *   - CSS var references:        "var(--color-primary)"
 *   - Semantic keywords:         "transparent", "inherit", "currentColor",
 *                                "none", "auto", "100%", "0"
 */

"use strict";

// ---------------------------------------------------------------------------
// Regex patterns for each category of hardcoded design value
// ---------------------------------------------------------------------------

/** Matches 3, 4, 6, or 8 digit hex colour literals. */
const HEX_COLOUR = /^#([0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$/;

/** Matches rgb() and rgba() functional colour notation. */
const RGB_COLOUR = /^rgba?\s*\(/i;

/** Matches hsl() and hsla() functional colour notation. */
const HSL_COLOUR = /^hsla?\s*\(/i;

/** Matches values ending in px (e.g. "16px", "4px", "0.5px"). */
const PX_VALUE = /^\d+(\.\d+)?px$/;

/** Matches values ending in rem (e.g. "1rem", "0.875rem"). */
const REM_VALUE = /^\d+(\.\d+)?rem$/;

/**
 * Common hardcoded font names to reject.
 *
 * Covers the most commonly misused fonts in Syntek UI packages. The list
 * deliberately avoids generic CSS keyword families (sans-serif, serif, monospace)
 * which are acceptable fallback stacks within token definitions.
 */
const HARDCODED_FONT_NAMES = new Set([
  "inter",
  "roboto",
  "arial",
  "helvetica",
  "verdana",
  "georgia",
  "times new roman",
  "times",
  "courier new",
  "courier",
  "trebuchet ms",
  "comic sans ms",
  "impact",
  "lato",
  "open sans",
  "montserrat",
  "poppins",
  "raleway",
  "nunito",
  "source sans pro",
  "ubuntu",
  "noto sans",
  "pt sans",
  "merriweather",
  "playfair display",
  "oswald",
]);

/**
 * Values that are explicitly allowed — generic CSS keywords that carry no
 * hardcoded design intention and cannot be replaced with a token constant.
 */
const ALLOWED_VALUES = new Set([
  "transparent",
  "inherit",
  "initial",
  "unset",
  "revert",
  "currentcolor",
  "currentColor",
  "none",
  "auto",
  "100%",
  "0",
  "0px",
  "0rem",
]);

// ---------------------------------------------------------------------------
// Helper functions
// ---------------------------------------------------------------------------

/**
 * Returns true when the string value is an allowed non-token literal that
 * does not represent a hardcoded design decision.
 *
 * @param {string} value - The string literal value to check.
 * @returns {boolean}
 */
function isAllowedValue(value) {
  return ALLOWED_VALUES.has(value) || ALLOWED_VALUES.has(value.toLowerCase());
}

/**
 * Returns true when the string value is a CSS custom property reference.
 * CSS var() references are generated from token constants and are permitted.
 *
 * @param {string} value - The string literal value to check.
 * @returns {boolean}
 */
function isCssVarReference(value) {
  return value.startsWith("var(--");
}

/**
 * Returns true when the string value is a hardcoded hex colour.
 *
 * @param {string} value - The string literal value to check.
 * @returns {boolean}
 */
function isHardcodedHex(value) {
  return HEX_COLOUR.test(value.trim());
}

/**
 * Returns true when the string value is a hardcoded rgb/rgba colour.
 *
 * @param {string} value - The string literal value to check.
 * @returns {boolean}
 */
function isHardcodedRgb(value) {
  return RGB_COLOUR.test(value.trim());
}

/**
 * Returns true when the string value is a hardcoded hsl/hsla colour.
 *
 * @param {string} value - The string literal value to check.
 * @returns {boolean}
 */
function isHardcodedHsl(value) {
  return HSL_COLOUR.test(value.trim());
}

/**
 * Returns true when the string value is a hardcoded px spacing or size value.
 *
 * @param {string} value - The string literal value to check.
 * @returns {boolean}
 */
function isHardcodedPx(value) {
  return PX_VALUE.test(value.trim());
}

/**
 * Returns true when the string value is a hardcoded rem font-size value.
 *
 * @param {string} value - The string literal value to check.
 * @returns {boolean}
 */
function isHardcodedRem(value) {
  return REM_VALUE.test(value.trim());
}

/**
 * Returns true when the string value is a hardcoded font family name.
 * Checks against the known set of commonly misused web fonts.
 *
 * @param {string} value - The string literal value to check.
 * @returns {boolean}
 */
function isHardcodedFontName(value) {
  return HARDCODED_FONT_NAMES.has(value.trim().toLowerCase());
}

/**
 * Classifies a string literal value and returns an error message if the value
 * is a hardcoded design value that should be replaced with a token constant.
 * Returns null when the value is permitted.
 *
 * @param {string} value - The string literal value to classify.
 * @returns {string | null} An error message, or null if the value is allowed.
 */
function getViolationMessage(value) {
  if (isAllowedValue(value) || isCssVarReference(value)) {
    return null;
  }

  if (isHardcodedHex(value)) {
    return `Hardcoded hex colour "${value}" found. Use a token constant from @syntek/tokens (e.g. COLOR_PRIMARY) instead.`;
  }

  if (isHardcodedRgb(value)) {
    return `Hardcoded rgb/rgba colour "${value}" found. Use a token constant from @syntek/tokens (e.g. COLOR_PRIMARY) instead.`;
  }

  if (isHardcodedHsl(value)) {
    return `Hardcoded hsl/hsla colour "${value}" found. Use a token constant from @syntek/tokens (e.g. COLOR_PRIMARY) instead.`;
  }

  if (isHardcodedPx(value)) {
    return `Hardcoded px value "${value}" found. Use a spacing token constant from @syntek/tokens (e.g. SPACING_4) instead.`;
  }

  if (isHardcodedRem(value)) {
    return `Hardcoded rem value "${value}" found. Use a font-size token constant from @syntek/tokens (e.g. FONT_SIZE_SM) instead.`;
  }

  if (isHardcodedFontName(value)) {
    return `Hardcoded font name "${value}" found. Use a font family token constant from @syntek/tokens (e.g. FONT_SANS) instead.`;
  }

  return null;
}

// ---------------------------------------------------------------------------
// AST visitor helpers
// ---------------------------------------------------------------------------

/**
 * Checks a single AST node that is a string Literal and reports a violation
 * if the value is a hardcoded design value.
 *
 * @param {import("eslint").Rule.RuleContext} context - The ESLint rule context.
 * @param {import("estree").Literal} node - The literal AST node to check.
 */
function checkLiteralNode(context, node) {
  if (typeof node.value !== "string") {
    return;
  }

  const message = getViolationMessage(node.value);
  if (message) {
    context.report({ node, message });
  }
}

/**
 * Recursively walks an ObjectExpression AST node and checks every string
 * Literal value found within it. Used for StyleSheet.create() call arguments
 * and JSX style={{ }} object expressions.
 *
 * @param {import("eslint").Rule.RuleContext} context - The ESLint rule context.
 * @param {import("estree").ObjectExpression} objectNode - The object AST node.
 */
function checkObjectExpression(context, objectNode) {
  for (const property of objectNode.properties) {
    if (property.type !== "Property") {
      continue;
    }

    const val = property.value;

    if (val.type === "Literal") {
      checkLiteralNode(context, val);
    } else if (val.type === "ObjectExpression") {
      // Handles nested objects (e.g. StyleSheet.create({ container: { ... } }))
      checkObjectExpression(context, val);
    } else if (val.type === "TemplateLiteral") {
      // Template literals with no expressions are effectively string literals.
      if (val.expressions.length === 0 && val.quasis.length === 1) {
        const raw = val.quasis[0].value.cooked ?? "";
        const message = getViolationMessage(raw);
        if (message) {
          context.report({ node: val, message });
        }
      }
    }
  }
}

/**
 * Returns true when the CallExpression node is a StyleSheet.create() call.
 *
 * @param {import("estree").CallExpression} node - The call expression node.
 * @returns {boolean}
 */
function isStyleSheetCreate(node) {
  return (
    node.callee.type === "MemberExpression" &&
    node.callee.object.type === "Identifier" &&
    node.callee.object.name === "StyleSheet" &&
    node.callee.property.type === "Identifier" &&
    node.callee.property.name === "create"
  );
}

// ---------------------------------------------------------------------------
// Rule definition
// ---------------------------------------------------------------------------

/** @type {import("eslint").Rule.RuleModule} */
const rule = {
  meta: {
    type: "problem",
    docs: {
      description:
        "Disallow hardcoded design values (colours, spacing, font-sizes, font names) in style props and StyleSheet.create objects. Use token constants from @syntek/tokens instead.",
      category: "Best Practices",
      recommended: true,
      url: "https://docs.syntek-studio.com/eslint-rules/no-hardcoded-design-values",
    },
    schema: [],
    messages: {},
  },

  create(context) {
    return {
      /**
       * Checks JSX `style` attribute values.
       *
       * Handles two forms:
       *   style={{ color: "#fff" }}      — JSXExpressionContainer wrapping ObjectExpression
       *   style={someVar}               — allowed (identifier reference, not a literal)
       */
      JSXAttribute(node) {
        // Only inspect the `style` attribute.
        if (node.name.type !== "JSXIdentifier" || node.name.name !== "style") {
          return;
        }

        const value = node.value;
        if (!value || value.type !== "JSXExpressionContainer") {
          return;
        }

        const expr = value.expression;
        if (expr.type === "ObjectExpression") {
          checkObjectExpression(context, expr);
        }
      },

      /**
       * Checks StyleSheet.create({ ... }) call arguments in React Native files.
       *
       * The outer object maps style name keys to nested style objects:
       *   StyleSheet.create({ container: { padding: "16px" } })
       */
      CallExpression(node) {
        if (!isStyleSheetCreate(node)) {
          return;
        }

        const args = node.arguments;
        if (args.length === 0 || args[0].type !== "ObjectExpression") {
          return;
        }

        checkObjectExpression(context, args[0]);
      },
    };
  },
};

module.exports = rule;
