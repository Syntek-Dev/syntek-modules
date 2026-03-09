/**
 * colour-utils.ts — CSS colour validation utility (US075)
 *
 * Provides runtime validation that a string is a recognised CSS colour value
 * in any format supported by the syntek-platform branding form:
 *   hex (#rrggbb, #rgb, #rrggbbaa, #rgba)
 *   rgb() / rgba()
 *   hsl() / hsla()
 *   hwb()
 *   lab() / lch()
 *   oklab() / oklch()
 *   CSS named colours (white, transparent, cornflowerblue, …)
 *
 * Used by the platform before saving an override to syntek-settings to ensure
 * only valid CSS colour strings are persisted.
 *
 * No DOM API is used — validation is purely regex and lookup-based so that
 * this module runs equally in Node.js, Deno, and browser environments.
 */

// ---------------------------------------------------------------------------
// Hex pattern — 3, 4, 6, or 8 hex digits (CSS Color Level 4)
// ---------------------------------------------------------------------------

const HEX_RE = /^#([0-9a-f]{3}|[0-9a-f]{4}|[0-9a-f]{6}|[0-9a-f]{8})$/i;

// ---------------------------------------------------------------------------
// Numeric component patterns
// ---------------------------------------------------------------------------

/** Integer 0–255 (no leading zeros for values > 0). */
const RGB_CH = "(?:25[0-5]|2[0-4]\\d|1\\d{2}|[1-9]\\d|\\d)";

/** Alpha value 0–1, including decimal fractions. */
const ALPHA = "(?:1(?:\\.0+)?|0(?:\\.\\d+)?)";

/** Hue — unbounded signed angle (CSS Color Level 4 wraps values outside 0–360). */
const HUE = "-?\\d+(?:\\.\\d+)?";

/** Percentage 0–100%. */
const PCT = "(?:100(?:\\.0+)?|\\d{1,2}(?:\\.\\d+)?)%";

/** Signed decimal number (used in lab/lch/oklab/oklch a/b/C components). */
const NUM = "-?\\d+(?:\\.\\d+)?";

/** Optional comma or space separator. */
const SEP = "(?:,\\s*|\\s+)";

/** Optional / alpha suffix for modern CSS Color Level 4 functions. */
const ALPHA_SLASH = `(?:\\s*/\\s*(?:${ALPHA}|${PCT}))?`;

/** L component for lab/lch: 0–100 (inclusive, with optional decimal). */
const LAB_L = "(?:100(?:\\.0+)?|\\d{1,2}(?:\\.\\d+)?)";

/** L component for oklab/oklch: 0–1 (inclusive, with optional decimal). */
const OK_L = "(?:1(?:\\.0+)?|0(?:\\.\\d+)?)";

// ---------------------------------------------------------------------------
// Colour function patterns
// ---------------------------------------------------------------------------

const RGB_RE = new RegExp(
  `^rgba?\\(\\s*${RGB_CH}${SEP}${RGB_CH}${SEP}${RGB_CH}(?:${SEP}${ALPHA})?\\s*\\)$`,
  "i",
);

// NOTE: hsla? matches both hsl() and hsla(). The optional alpha group means
// hsl(h, s%, l%, a) is accepted — this is intentional and spec-correct per
// CSS Color Level 4 which unifies hsl() and hsla() into a single function.
const HSL_RE = new RegExp(
  `^hsla?\\(\\s*${HUE}(?:deg)?${SEP}${PCT}${SEP}${PCT}(?:${SEP}${ALPHA})?\\s*\\)$`,
  "i",
);

const HWB_RE = new RegExp(`^hwb\\(\\s*${HUE}\\s+${PCT}\\s+${PCT}${ALPHA_SLASH}\\s*\\)$`, "i");

const LAB_RE = new RegExp(`^lab\\(\\s*${LAB_L}\\s+${NUM}\\s+${NUM}${ALPHA_SLASH}\\s*\\)$`, "i");

const LCH_RE = new RegExp(`^lch\\(\\s*${LAB_L}\\s+${NUM}\\s+${NUM}${ALPHA_SLASH}\\s*\\)$`, "i");

const OKLAB_RE = new RegExp(`^oklab\\(\\s*${OK_L}\\s+${NUM}\\s+${NUM}${ALPHA_SLASH}\\s*\\)$`, "i");

const OKLCH_RE = new RegExp(`^oklch\\(\\s*${OK_L}\\s+${NUM}\\s+${NUM}${ALPHA_SLASH}\\s*\\)$`, "i");

// ---------------------------------------------------------------------------
// CSS named colours — complete W3C list plus keywords
// Source: https://www.w3.org/TR/css-color-4/#named-colors
// ---------------------------------------------------------------------------

const CSS_NAMED_COLOURS = new Set<string>([
  // CSS colour keywords
  "transparent",
  // NOTE: currentColor is a valid <color> value per CSS Color Level 4 section 4.1.
  // However, using it in :root custom properties (e.g. --color-foreground: currentColor)
  // can create circular dependency issues if color: var(--color-foreground) is also set
  // on the same element. The platform should warn users about this in the branding form.
  "currentcolor",
  // W3C named colours
  "aliceblue",
  "antiquewhite",
  "aqua",
  "aquamarine",
  "azure",
  "beige",
  "bisque",
  "black",
  "blanchedalmond",
  "blue",
  "blueviolet",
  "brown",
  "burlywood",
  "cadetblue",
  "chartreuse",
  "chocolate",
  "coral",
  "cornflowerblue",
  "cornsilk",
  "crimson",
  "cyan",
  "darkblue",
  "darkcyan",
  "darkgoldenrod",
  "darkgray",
  "darkgreen",
  "darkgrey",
  "darkkhaki",
  "darkmagenta",
  "darkolivegreen",
  "darkorange",
  "darkorchid",
  "darkred",
  "darksalmon",
  "darkseagreen",
  "darkslateblue",
  "darkslategray",
  "darkslategrey",
  "darkturquoise",
  "darkviolet",
  "deeppink",
  "deepskyblue",
  "dimgray",
  "dimgrey",
  "dodgerblue",
  "firebrick",
  "floralwhite",
  "forestgreen",
  "fuchsia",
  "gainsboro",
  "ghostwhite",
  "gold",
  "goldenrod",
  "gray",
  "green",
  "greenyellow",
  "grey",
  "honeydew",
  "hotpink",
  "indianred",
  "indigo",
  "ivory",
  "khaki",
  "lavender",
  "lavenderblush",
  "lawngreen",
  "lemonchiffon",
  "lightblue",
  "lightcoral",
  "lightcyan",
  "lightgoldenrodyellow",
  "lightgray",
  "lightgreen",
  "lightgrey",
  "lightpink",
  "lightsalmon",
  "lightseagreen",
  "lightskyblue",
  "lightslategray",
  "lightslategrey",
  "lightsteelblue",
  "lightyellow",
  "lime",
  "limegreen",
  "linen",
  "magenta",
  "maroon",
  "mediumaquamarine",
  "mediumblue",
  "mediumorchid",
  "mediumpurple",
  "mediumseagreen",
  "mediumslateblue",
  "mediumspringgreen",
  "mediumturquoise",
  "mediumvioletred",
  "midnightblue",
  "mintcream",
  "mistyrose",
  "moccasin",
  "navajowhite",
  "navy",
  "oldlace",
  "olive",
  "olivedrab",
  "orange",
  "orangered",
  "orchid",
  "palegoldenrod",
  "palegreen",
  "paleturquoise",
  "palevioletred",
  "papayawhip",
  "peachpuff",
  "peru",
  "pink",
  "plum",
  "powderblue",
  "purple",
  "rebeccapurple",
  "red",
  "rosybrown",
  "royalblue",
  "saddlebrown",
  "salmon",
  "sandybrown",
  "seagreen",
  "seashell",
  "sienna",
  "silver",
  "skyblue",
  "slateblue",
  "slategray",
  "slategrey",
  "snow",
  "springgreen",
  "steelblue",
  "tan",
  "teal",
  "thistle",
  "tomato",
  "turquoise",
  "violet",
  "wheat",
  "white",
  "whitesmoke",
  "yellow",
  "yellowgreen",
]);

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Returns `true` if `value` is a recognised CSS colour string in any of the
 * supported formats. Tailwind palette names (e.g. "blue-600") are NOT valid
 * CSS colours and must be resolved to hex before this function is called.
 *
 * Supported formats: hex (#rgb, #rgba, #rrggbb, #rrggbbaa), rgb(), rgba(),
 * hsl(), hsla(), hwb(), lab(), lch(), oklab(), oklch(), and all standard CSS
 * named colours including `transparent` and `currentColor`.
 *
 * CSS-wide keywords (`inherit`, `initial`, `unset`) are NOT accepted — they
 * are not `<color>` values per CSS Color Level 4 section 4.1.
 *
 * No DOM API is used — validation is purely regex and Set-based.
 *
 * @param value - The string to validate as a CSS colour.
 * @returns `true` if the value is a valid CSS colour, `false` otherwise.
 */
export function isValidCssColour(value: string): boolean {
  const trimmed = value.trim();

  if (trimmed.length === 0) {
    return false;
  }

  // Hex colours
  if (trimmed.startsWith("#")) {
    return HEX_RE.test(trimmed);
  }

  // CSS function notations — check by prefix for performance
  const lower = trimmed.toLowerCase();

  if (lower.startsWith("rgba(") || lower.startsWith("rgb(")) {
    return RGB_RE.test(trimmed);
  }

  if (lower.startsWith("hsla(") || lower.startsWith("hsl(")) {
    return HSL_RE.test(trimmed);
  }

  if (lower.startsWith("hwb(")) {
    return HWB_RE.test(trimmed);
  }

  if (lower.startsWith("oklab(")) {
    return OKLAB_RE.test(trimmed);
  }

  if (lower.startsWith("oklch(")) {
    return OKLCH_RE.test(trimmed);
  }

  if (lower.startsWith("lab(")) {
    return LAB_RE.test(trimmed);
  }

  if (lower.startsWith("lch(")) {
    return LCH_RE.test(trimmed);
  }

  // CSS named colours (case-insensitive lookup)
  return CSS_NAMED_COLOURS.has(lower);
}
