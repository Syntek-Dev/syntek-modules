Feature: Monorepo Workspace Resolution
  As a module contributor
  I want a fully configured monorepo workspace
  So that I can develop any package layer from a single root with consistent tooling

  Background:
    Given I have a fresh clone of the repository

  Scenario: TypeScript packages are resolvable via pnpm
    When I run pnpm install from the root
    Then all TypeScript workspace packages are linked

  Scenario: Backend package installs via uv
    When I activate the uv virtual environment
    And I install syntek-auth with dev dependencies
    Then the package installs without errors

  Scenario: Rust crates compile via cargo
    When I run cargo build from the root
    Then all Rust crates compile without errors

  Scenario: Dev watch mode is available via the CLI
    When I query the syntek-dev CLI help
    Then the up subcommand is listed

  Scenario: Test runner is available via the CLI
    When I query the syntek-dev CLI help
    Then the test subcommand is listed
