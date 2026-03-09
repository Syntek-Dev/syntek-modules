# Feature: Design Token Manifest
# US075 — As a platform administrator, I want a branding section in syntek-platform where I can edit
# colours, fonts, typography, spacing, and breakpoints through a form with a colour picker, so that
# my site's visual identity updates live without touching any code.

Feature: Design Token Manifest

  Background:
    Given the @syntek/tokens package is installed

  # ---------------------------------------------------------------------------
  # Manifest shape — every descriptor must have required fields
  # ---------------------------------------------------------------------------

  Scenario: TOKEN_MANIFEST exports a non-empty array of descriptors
    Given I import TOKEN_MANIFEST from "@syntek/tokens"
    When I inspect the manifest
    Then TOKEN_MANIFEST is an array with at least one entry

  Scenario: Every token descriptor has all required fields
    Given I import TOKEN_MANIFEST from "@syntek/tokens"
    When I inspect each entry in the manifest
    Then every token has a key field that is a non-empty string
    And every token has a cssVar field that starts with "--"
    And every token has a category field from the allowed TokenCategory union
    And every token has a type field from the allowed TokenWidgetType union
    And every token has a default field that is a string or number
    And every token has a label field that is a non-empty string

  # ---------------------------------------------------------------------------
  # Widget type correctness — drives platform branding form UI
  # ---------------------------------------------------------------------------

  Scenario: Colour tokens drive a colour picker widget
    Given TOKEN_MANIFEST is consumed by the platform branding form
    When a user edits a colour token
    Then the platform renders a colour picker widget driven by type: "color"

  Scenario: Spacing tokens drive a px number input
    Given TOKEN_MANIFEST is consumed by the platform branding form
    When a user edits a spacing token
    Then the platform renders a number/px input driven by type: "px"

  Scenario: Font-family tokens drive a font selector widget
    Given TOKEN_MANIFEST is consumed by the platform branding form
    When a user edits a font-family token
    Then the platform renders a font selector widget driven by type: "font-family"

  Scenario: Font-weight tokens drive a weight selector widget
    Given TOKEN_MANIFEST is consumed by the platform branding form
    When a user edits a font-weight token
    Then the platform renders a font-weight selector driven by type: "font-weight"

  Scenario: Z-index tokens drive a plain number input
    Given TOKEN_MANIFEST is consumed by the platform branding form
    When a user edits a z-index token
    Then the platform renders a plain number input driven by type: "number"

  Scenario: Transition duration tokens drive a duration input
    Given TOKEN_MANIFEST is consumed by the platform branding form
    When a user edits a transition duration token
    Then the platform renders a duration input in ms driven by type: "duration"

  Scenario: Transition easing tokens drive an easing text input
    Given TOKEN_MANIFEST is consumed by the platform branding form
    When a user edits a transition easing token
    Then the platform renders an easing/cubic-bezier input driven by type: "easing"

  # ---------------------------------------------------------------------------
  # Colour token default values — must be resolved hex, not var() references
  # ---------------------------------------------------------------------------

  Scenario: Colour token defaults are resolved hex strings
    Given I import TOKEN_MANIFEST from "@syntek/tokens"
    When I inspect the default value of a colour token
    Then the default is a hex colour string (e.g. "#2563eb")
    And it does not contain "var(--" references

  Scenario: COLOR_PRIMARY default is the blue-600 hex value
    Given I import TOKEN_MANIFEST from "@syntek/tokens"
    When I find the TOKEN_MANIFEST entry with key "COLOR_PRIMARY"
    Then its default value is "#2563eb"

  # ---------------------------------------------------------------------------
  # TAILWIND_COLOURS — Tailwind v4 palette map for swatch resolution
  # ---------------------------------------------------------------------------

  Scenario: TAILWIND_COLOURS exports a flat palette record
    Given I import TAILWIND_COLOURS from "@syntek/tokens"
    When I inspect the export
    Then it is a non-empty object with string keys and hex string values

  Scenario: TAILWIND_COLOURS resolves blue-600 to its hex value
    Given I import TAILWIND_COLOURS from "@syntek/tokens"
    When I look up "blue-600"
    Then the value is "#2563eb"

  Scenario: TAILWIND_COLOURS covers all 22 Tailwind v4 palette families
    Given I import TAILWIND_COLOURS from "@syntek/tokens"
    When I list the colour family prefixes
    Then it covers slate, gray, zinc, neutral, stone, red, orange, amber, yellow, lime,
      green, emerald, teal, cyan, sky, blue, indigo, violet, purple, fuchsia, pink, and rose

  Scenario: resolveTailwindColour looks up a palette name and returns hex
    Given I import resolveTailwindColour from "@syntek/tokens"
    When I call resolveTailwindColour("blue-600")
    Then it returns "#2563eb"

  Scenario: resolveTailwindColour returns undefined for unknown names
    Given I import resolveTailwindColour from "@syntek/tokens"
    When I call resolveTailwindColour("not-a-colour-999")
    Then it returns undefined

  # ---------------------------------------------------------------------------
  # Colour format validation — isValidCssColour utility
  # ---------------------------------------------------------------------------

  Scenario Outline: Valid CSS colour formats are accepted
    Given I import isValidCssColour from "@syntek/tokens"
    When I call isValidCssColour("<value>")
    Then it returns true

    Examples:
      | value                     |
      | #2563eb                   |
      | #fff                      |
      | #2563ebcc                 |
      | rgb(37, 99, 235)          |
      | rgba(37, 99, 235, 0.8)    |
      | hsl(221, 83%, 53%)        |
      | hsla(221, 83%, 53%, 0.8)  |
      | hwb(221 15% 8%)           |
      | lab(46 -8 -45)            |
      | lch(46 46 264)            |
      | oklab(0.55 -0.05 -0.15)   |
      | oklch(0.55 0.2 250)       |
      | white                     |
      | transparent               |
      | cornflowerblue            |

  Scenario Outline: Invalid colour strings are rejected
    Given I import isValidCssColour from "@syntek/tokens"
    When I call isValidCssColour("<value>")
    Then it returns false

    Examples:
      | value          |
      | blue-600       |
      | #xyz           |
      | not-a-colour   |
      |                |
      | 42             |

  # ---------------------------------------------------------------------------
  # TOKEN_MANIFEST is static and read-only
  # ---------------------------------------------------------------------------

  Scenario: TOKEN_MANIFEST is not mutated at runtime
    Given token overrides are stored in syntek-settings
    When the platform reads TOKEN_MANIFEST to build the branding form
    Then TOKEN_MANIFEST itself is not modified
    And the same manifest is returned on subsequent reads
