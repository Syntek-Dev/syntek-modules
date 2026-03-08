# Feature: Design Token System
# US003 — As a frontend developer, I want a canonical set of design tokens so
# that all UI packages use consistent, overridable values for colour,
# typography, spacing, and shadow without hardcoding.

Feature: Design Token System

  Background:
    Given the @syntek/tokens package is installed

  # ---------------------------------------------------------------------------
  # AC1 — CSS variable resolution
  # ---------------------------------------------------------------------------

  Scenario: Default token value resolves via CSS custom property
    Given the tokens package is installed
    When I reference "var(--color-primary)" in any component
    Then the value resolves to the default token value defined in tokens.css

  # ---------------------------------------------------------------------------
  # AC2 — Token override at :root
  # ---------------------------------------------------------------------------

  Scenario: Consuming project overrides a token at :root
    Given a consuming project sets "--color-primary" to "#FF0000" at ":root"
    When the component renders using "var(--color-primary)"
    Then the rendered colour is "#FF0000" without any code change to the component

  # ---------------------------------------------------------------------------
  # AC3 — Lint enforcement prevents hardcoded values
  # ---------------------------------------------------------------------------

  Scenario: Hardcoded colour causes lint failure
    Given a new component is added to any UI package
    When the component contains a hardcoded colour like "#3B82F6"
    And I run the linter
    Then the lint check reports an error for the hardcoded colour

  Scenario: Hardcoded spacing causes lint failure
    Given a new component is added to any UI package
    When the component contains a hardcoded spacing value like "16px"
    And I run the linter
    Then the lint check reports an error for the hardcoded spacing

  Scenario: Hardcoded font-size causes lint failure
    Given a new component is added to any UI package
    When the component contains a hardcoded font-size like "14px"
    And I run the linter
    Then the lint check reports an error for the hardcoded font-size

  # ---------------------------------------------------------------------------
  # AC4 — TypeScript constants
  # ---------------------------------------------------------------------------

  Scenario: TypeScript constants are available with correct types
    When I import from "@syntek/tokens"
    Then COLOR_PRIMARY is a string equal to "var(--color-primary)"
    And BREAKPOINT_SM is the number 640
    And FONT_SANS is a string equal to "var(--font-sans)"

  # ---------------------------------------------------------------------------
  # AC5 — NativeWind integration
  # ---------------------------------------------------------------------------

  Scenario: NativeWind preset applies design token values on iOS
    Given a token value is referenced in a NativeWind class
    When the mobile component renders on iOS
    Then the correct design token value is applied

  Scenario: NativeWind preset applies design token values on Android
    Given a token value is referenced in a NativeWind class
    When the mobile component renders on Android
    Then the correct design token value is applied

  # ---------------------------------------------------------------------------
  # AC6 — Font token resolution
  # ---------------------------------------------------------------------------

  Scenario: Font family tokens are applied without hardcoded font names
    Given the font tokens are defined in "tokens.css"
    When a consuming project loads the page
    Then the font family is applied from "--font-sans"
    And no hardcoded font name appears in any component file

  Scenario: Font serif token resolves correctly
    Given the font tokens are defined in "tokens.css"
    When a consuming project loads the page
    Then the font family is applied from "--font-serif"

  Scenario: Font mono token resolves correctly
    Given the font tokens are defined in "tokens.css"
    When a consuming project loads the page
    Then the font family is applied from "--font-mono"
