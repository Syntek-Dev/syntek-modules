# Syntek Dev Suite - Plugin Usage Guide

**Version:** 1.1.0
**Plugin:** syntek-dev-suite
**Maintained by:** Syntek Developers

---

## Table of Contents

- [Table of Contents](#table-of-contents)
- [Quick Start](#quick-start)
  - [Basic Usage](#basic-usage)
- [Complete Development Workflow](#complete-development-workflow)
  - [Phase 1: Project Initialisation](#phase-1-project-initialisation)
  - [Phase 2: Project Planning](#phase-2-project-planning)
  - [Phase 3: User Stories and Sprint Planning](#phase-3-user-stories-and-sprint-planning)
  - [Phase 4: Pre-Development Review](#phase-4-pre-development-review)
  - [Phase 5: PM Tool Integration (Optional)](#phase-5-pm-tool-integration-optional)
  - [Phase 6: Git Setup](#phase-6-git-setup)
  - [Phase 7: User Story Implementation](#phase-7-user-story-implementation)
  - [Phase 8: Coding](#phase-8-coding)
  - [Phase 9: Quality Assurance](#phase-9-quality-assurance)
  - [Phase 10: Final Verification](#phase-10-final-verification)
  - [Phase 11: Commit and Document](#phase-11-commit-and-document)
  - [Phase 12: PR to Testing](#phase-12-pr-to-testing)
  - [Workflow Summary](#workflow-summary)
- [Command Reference](#command-reference)
- [Agent Commands](#agent-commands)
  - [Planning \& Architecture](#planning--architecture)
  - [Development](#development)
  - [Quality \& Testing](#quality--testing)
  - [Refactoring \& Maintenance](#refactoring--maintenance)
  - [Infrastructure](#infrastructure)
  - [Specialised](#specialised)
- [Plugin Commands](#plugin-commands)
- [Learning Commands](#learning-commands)
- [Version Management](#version-management)
  - [Version Commands](#version-commands)
  - [Version Files Managed](#version-files-managed)
  - [Markdown Metadata Headers](#markdown-metadata-headers)
- [Skills Reference](#skills-reference)
  - [Stack Skills](#stack-skills)
  - [Global Skill](#global-skill)
- [Self-Learning and A/B Testing](#self-learning-and-ab-testing)
  - [How It Works](#how-it-works)
  - [A/B Testing](#ab-testing)
  - [Giving Feedback](#giving-feedback)
  - [Project-Specific Learning](#project-specific-learning)
  - [Learning Best Practices](#learning-best-practices)
- [Markdown All in One Extension](#markdown-all-in-one-extension)
  - [Key Features](#key-features)
  - [Keyboard Shortcuts](#keyboard-shortcuts)
  - [Table of Contents](#table-of-contents-1)
- [Best Practices](#best-practices)
  - [1. Always Start with `/syntek-dev-suite:plan`](#1-always-start-with-syntek-dev-suiteplan)
  - [2. Use `/syntek-dev-suite:qa-tester` Before Merging](#2-use-syntek-dev-suiteqa-tester-before-merging)
  - [3. Keep CLAUDE.md Updated](#3-keep-claudemd-updated)
  - [4. Let Agents Read Files](#4-let-agents-read-files)
  - [5. Use the Right Model](#5-use-the-right-model)
  - [6. Chain Commands Logically](#6-chain-commands-logically)
  - [7. Commit After Each Step](#7-commit-after-each-step)
  - [8. Give Feedback](#8-give-feedback)
- [Environment Commands](#environment-commands)
- [Browser Configuration](#browser-configuration)
  - [Browser Environment Variable](#browser-environment-variable)
  - [Launching Chrome](#launching-chrome)
  - [Claude Code Chrome Integration](#claude-code-chrome-integration)
  - [E2E Test Configuration](#e2e-test-configuration)
- [Getting Help](#getting-help)


---

## Quick Start

The Syntek Dev Suite provides specialised AI agents for full-stack development. Each agent has domain expertise and understands your project's stack through the `CLAUDE.md` file.

### Basic Usage

```bash
# Plan a new feature
/syntek-dev-suite:plan Add user authentication with social login

# Implement backend
/syntek-dev-suite:backend Create the User model and auth endpoints

# Implement frontend
/syntek-dev-suite:frontend Create the login form component

# Write tests
/syntek-dev-suite:test-writer Write tests for the auth flow

# Review code
/syntek-dev-suite:qa-tester Review the auth implementation

# Give feedback to improve the agent
/syntek-dev-suite:learning-feedback good
```

---

## Complete Development Workflow

This section walks through a complete development cycle from project setup to PR submission.

> **Note:** All commands use the `/syntek-dev-suite:` prefix.

### Phase 1: Project Initialisation

```bash
# 1. Initialise Claude Code to work with Syntek Dev Suite
/syntek-dev-suite:init

# 2. Set up all project files using the setup agent
/syntek-dev-suite:setup

# 3. Set up dot files (.gitignore, .editorconfig, etc.)
/syntek-dev-suite:setup .files

# 4. Commit initialisation work
/syntek-dev-suite:git
```

### Phase 2: Project Planning

```bash
# 5. Plan the project architecture
/syntek-dev-suite:plan X project that will [describe what the project does]
# Example: /syntek-dev-suite:plan E-commerce project that will allow users to browse products and checkout

# 6. Commit the plan
/syntek-dev-suite:git
```

### Phase 3: User Stories and Sprint Planning

```bash
# 7. Generate user stories from the plan
/syntek-dev-suite:stories

# 8. Commit user stories
/syntek-dev-suite:git

# 9. Organise user stories into sprints
/syntek-dev-suite:sprint

# 10. Commit sprints
/syntek-dev-suite:git
```

### Phase 4: Pre-Development Review

```bash
# 11. Review all setup before coding begins
/syntek-dev-suite:review
# Reviews: init, plan, .files, stories, and sprints

# 12. Commit any review changes
/syntek-dev-suite:git
```

### Phase 5: PM Tool Integration (Optional)

```bash
# 13. Link with project management software
/syntek-dev-suite:pm-setup
# Creates integration with ClickUp, Linear, Jira, etc.
# Sets up git workflow to sync user stories and sprints

# 14. Commit PM setup
/syntek-dev-suite:git
```

### Phase 6: Git Branch Setup

```bash
# 15. Push setup to main and create branches
/syntek-dev-suite:git
# Pushes to main branch
# Creates staging, dev, and testing branches from main via PR

# 16. Create user story branch from dev
/syntek-dev-suite:git
# Creates us001/name branch for the first user story from dev branch
```

### Phase 7: User Story Planning

```bash
# 17. Plan the specific user story
/syntek-dev-suite:plan user story X
# Example: /syntek-dev-suite:plan user story 1

# 18. Commit the user story plan
/syntek-dev-suite:git
```

### Phase 8: Test-Driven Development

```bash
# 19. Write TDD/BDD tests (tests should fail initially)
/syntek-dev-suite:test-writer
# Writes tests scoped ONLY to the user story
# Creates minimal code stubs to ensure tests fail

# 20. Commit tests
/syntek-dev-suite:git
```

### Phase 9: Coding

```bash
# 21. Implement the user story using relevant agents
# Commit after EACH piece of work for proper version control

/syntek-dev-suite:backend    # For API, database, server logic
/syntek-dev-suite:git        # Commit backend work

/syntek-dev-suite:frontend   # For UI components, styling
/syntek-dev-suite:git        # Commit frontend work

/syntek-dev-suite:database   # For migrations, schemas
/syntek-dev-suite:git        # Commit database work

/syntek-dev-suite:data       # For data analysis, Python/SQL
/syntek-dev-suite:git        # Commit data work

# Use whichever agents are relevant to the user story
# Goal: Pass tests and satisfy acceptance criteria
# IMPORTANT: Always commit after each agent completes their work
```

### Phase 10: Quality Assurance

```bash
# 22. Run QA to ensure tests pass
/syntek-dev-suite:qa-tester
/syntek-dev-suite:git        # Commit QA fixes

# 23. Generate bug report and fix issues
/syntek-dev-suite:debug
/syntek-dev-suite:git        # Commit bug fixes

# 24. Review the code
/syntek-dev-suite:review
/syntek-dev-suite:git        # Commit review changes

# 25. Refactor if needed
/syntek-dev-suite:refactor
/syntek-dev-suite:git        # Commit refactoring

# 26. Fix syntax and linting issues
/syntek-dev-suite:syntax
/syntek-dev-suite:git        # Commit syntax fixes

# 27. Security audit
/syntek-dev-suite:security
/syntek-dev-suite:git        # Commit security fixes
```

### Phase 11: Final Verification

```bash
# 28. Final QA check - ensure tests still pass
/syntek-dev-suite:qa-tester
/syntek-dev-suite:git        # Commit any final QA fixes

# 29. Final checks cycle (commit after each if changes made)
/syntek-dev-suite:debug      # Final bug check
/syntek-dev-suite:git

/syntek-dev-suite:review     # Final code review
/syntek-dev-suite:git

/syntek-dev-suite:refactor   # Final refactoring pass
/syntek-dev-suite:git

/syntek-dev-suite:syntax     # Final syntax check
/syntek-dev-suite:git

/syntek-dev-suite:security   # Final security check
/syntek-dev-suite:git
```

### Phase 12: Documentation

```bash
# 30. Write documentation
/syntek-dev-suite:docs
/syntek-dev-suite:git        # Commit documentation

# 31. Update version files
/syntek-dev-suite:version
/syntek-dev-suite:git        # Commit version updates
```

### Phase 13: Completion and PR

```bash
# 32. Mark work as complete
/syntek-dev-suite:completion
/syntek-dev-suite:git        # Commit completion status

# 33. Create PR to testing branch for review
/syntek-dev-suite:git
# Creates PR from user story branch to testing for review
```

### Workflow Summary

```
SETUP PHASE
───────────────────────────────────────────────────────────
init → setup → setup .files → git
plan project → git
stories → git → sprint → git
review → git

PM & GIT SETUP
───────────────────────────────────────────────────────────
pm-setup → git
git (main + branches) → git (user story branch)

USER STORY PLANNING
───────────────────────────────────────────────────────────
plan user story → git
test-writer → git

IMPLEMENTATION (commit after each agent)
───────────────────────────────────────────────────────────
backend → git → frontend → git → database → git → data → git

QUALITY ASSURANCE (commit after each step)
───────────────────────────────────────────────────────────
qa-tester → git → debug → git → review → git → refactor → git → syntax → git → security → git

FINAL VERIFICATION (commit after each step)
───────────────────────────────────────────────────────────
qa-tester → git → debug → git → review → git → refactor → git → syntax → git → security → git

DOCUMENTATION & COMPLETION
───────────────────────────────────────────────────────────
docs → git → version → git → completion → git → git (PR to testing)
```

---

## Command Reference

All Syntek Dev Suite commands use the `/syntek-dev-suite:` prefix:

```bash
/syntek-dev-suite:<command> [arguments]
```

---

## Agent Commands

### Planning & Architecture

| Command                        | Model  | Description                                     |
| ------------------------------ | ------ | ----------------------------------------------- |
| `/syntek-dev-suite:plan`       | Opus   | Create architectural plans, break down features |
| `/syntek-dev-suite:stories`    | Haiku  | Generate user stories from requirements         |
| `/syntek-dev-suite:sprint`     | Sonnet | Organise stories into balanced sprints          |
| `/syntek-dev-suite:completion` | Sonnet | Track story and sprint completion               |

### Development

| Command                      | Model  | Description                               |
| ---------------------------- | ------ | ----------------------------------------- |
| `/syntek-dev-suite:setup`    | Sonnet | Project initialisation and configuration  |
| `/syntek-dev-suite:backend`  | Sonnet | Backend development, APIs, database       |
| `/syntek-dev-suite:frontend` | Sonnet | UI/UX, components, accessibility          |
| `/syntek-dev-suite:database` | Sonnet | Database design, migrations, optimisation |
| `/syntek-dev-suite:auth`     | Sonnet | Authentication, MFA, session management   |

### Quality & Testing

| Command                         | Model  | Description                      |
| ------------------------------- | ------ | -------------------------------- |
| `/syntek-dev-suite:test-writer` | Sonnet | TDD test suites and stubs        |
| `/syntek-dev-suite:qa-tester`   | Sonnet | Hostile QA, security, edge cases |
| `/syntek-dev-suite:review`      | Sonnet | Code review, SOLID, security     |
| `/syntek-dev-suite:debug`       | Opus   | Root cause analysis, debugging   |

### Refactoring & Maintenance

| Command                      | Model  | Description                         |
| ---------------------------- | ------ | ----------------------------------- |
| `/syntek-dev-suite:refactor` | Sonnet | Code cleanup without changing logic |
| `/syntek-dev-suite:syntax`   | Haiku  | Fix syntax and linting errors       |
| `/syntek-dev-suite:docs`     | Haiku  | Technical documentation             |

### Infrastructure

| Command                      | Model  | Description                            |
| ---------------------------- | ------ | -------------------------------------- |
| `/syntek-dev-suite:cicd`     | Sonnet | CI/CD pipelines, deployments           |
| `/syntek-dev-suite:security` | Sonnet | Access control, headers, rate limiting |
| `/syntek-dev-suite:logging`  | Sonnet | Logging, Sentry, audit trails          |
| `/syntek-dev-suite:git`      | Sonnet | Branch management, versioning          |

### Specialised

| Command                              | Model  | Description                      |
| ------------------------------------ | ------ | -------------------------------- |
| `/syntek-dev-suite:gdpr`             | Sonnet | GDPR compliance, data protection |
| `/syntek-dev-suite:seo`              | Sonnet | SEO, meta tags, structured data  |
| `/syntek-dev-suite:notifications`    | Sonnet | Email, SMS, push notifications   |
| `/syntek-dev-suite:export`           | Sonnet | PDF, Excel, CSV, JSON exports    |
| `/syntek-dev-suite:reporting`        | Sonnet | Data queries, report services    |
| `/syntek-dev-suite:data`             | Sonnet | Data analysis, Python, SQL       |
| `/syntek-dev-suite:support-articles` | Sonnet | Help documentation               |

---

## Plugin Commands

| Command                  | Description                               |
| ------------------------ | ----------------------------------------- |
| `/syntek-dev-suite:init` | Initialise Syntek Dev Suite for a project |

---

## Learning Commands

The learning system helps agents improve over time based on your feedback.

| Command                                               | Description                                       |
| ----------------------------------------------------- | ------------------------------------------------- |
| `/syntek-dev-suite:learning-feedback good`            | Mark the last run as successful                   |
| `/syntek-dev-suite:learning-feedback bad [comment]`   | Mark as needing improvement with optional comment |
| `/syntek-dev-suite:learning-ab-test list`             | List active A/B tests                             |
| `/syntek-dev-suite:learning-ab-test status <agent>`   | Show test results for an agent                    |
| `/syntek-dev-suite:learning-optimise status`          | Show optimisation system status                   |
| `/syntek-dev-suite:learning-optimise analyse <agent>` | Analyse an agent's performance                    |
| `/syntek-dev-suite:learning-optimise apply <id>`      | Apply a pending optimisation                      |

---

## Version Management

The version agent manages semantic versioning, changelogs, and markdown headers across your project.

### Version Commands

| Command                                 | Description                                |
| --------------------------------------- | ------------------------------------------ |
| `/syntek-dev-suite:version bump <type>` | Increment version (major, minor, patch)    |
| `/syntek-dev-suite:version update`      | Update all version files and documentation |
| `/syntek-dev-suite:version headers`     | Update metadata headers in all .md files   |
| `/syntek-dev-suite:version init`        | Initialise version files for a new project |
| `/syntek-dev-suite:version status`      | Show current version and pending changes   |
| `/syntek-dev-suite:version history`     | Show version history summary               |

### Version Files Managed

| File                   | Purpose                                | Audience      |
| ---------------------- | -------------------------------------- | ------------- |
| **Version files**      | Semantic version (package.json, etc.)  | Build systems |
| **VERSION-HISTORY.md** | Technical change log with code details | Developers    |
| **CHANGELOG.md**       | Brief developer-focused summary        | Developers    |
| **RELEASES.md**        | User-facing feature highlights         | End users     |

### Markdown Metadata Headers

All `.md` files include a metadata header maintained by the version agent:

```markdown
# Document Title

**Last Updated**: DD/MM/YYYY
**Version**: X.Y.Z
**Maintained By**: Development Team
**Language**: British English (en_GB)
**Timezone**: Europe/London

---
```

---

## Skills Reference

Skills are loaded automatically based on your project's `Skill Target` in `CLAUDE.md`.

### Stack Skills

| Skill              | Target         | Applied To                           |
| ------------------ | -------------- | ------------------------------------ |
| `stack-tall`       | TALL Stack     | Laravel, Livewire, Alpine, Tailwind  |
| `stack-django`     | Django Stack   | Django, Wagtail, PostgreSQL, GraphQL |
| `stack-react`      | React Stack    | React, Next.js, TypeScript, Tailwind |
| `stack-mobile`     | Mobile Stack   | React Native, Expo, NativeWind       |
| `stack-shared-lib` | Shared Library | NPM packages for web/mobile          |

### Global Skill

The `global-workflow` skill is always loaded and provides:
- British English localisation
- Date format: DD/MM/YYYY
- Time format: 24-hour clock (14:30)
- Timezone: Europe/London
- Currency: GBP (£)
- Git commit message standards
- Documentation formatting rules
- Browser configuration (Chrome/Chrome Beta)

---

## Self-Learning and A/B Testing

The plugin includes a self-learning system that improves agent performance based on your feedback. Each project develops its own optimised prompts over time.

### How It Works

1. **Feedback Collection** - After each agent run, rate the output
2. **Metrics Recording** - Run duration, outcomes, and errors are tracked
3. **Pattern Analysis** - The system identifies what works and what doesn't
4. **A/B Testing** - Prompt variants are tested to find the best approach
5. **Prompt Optimisation** - Winning prompts are applied automatically

### A/B Testing

Each agent can run A/B tests on prompt variants to discover what works best for your specific project:

```bash
# List active A/B tests
/syntek-dev-suite:learning-ab-test list

# Check test status for an agent
/syntek-dev-suite:learning-ab-test status backend

# The system automatically:
# - Randomly assigns variants to runs
# - Tracks success/failure rates
# - Identifies statistically significant winners
# - Applies winning prompts automatically
```

### Giving Feedback

After each agent run, provide feedback to improve future runs:

```bash
# If the output was good
/syntek-dev-suite:learning-feedback good

# If the output needs improvement
/syntek-dev-suite:learning-feedback bad The output didn't follow the coding style

# If you can't evaluate yet
# (skip feedback - just don't run the command)
```

### Project-Specific Learning

- All feedback and metrics are stored in your project's `docs/METRICS/` folder
- Data is committed to Git, so the whole team benefits from improvements
- Each project develops its own optimised prompts over time
- No external API calls - learning uses Claude Code CLI directly
- The more feedback you provide, the better the agents become for your project

### Learning Best Practices

1. **Be consistent** - Always provide feedback after significant agent runs
2. **Be specific** - When marking as "bad", explain what was wrong
3. **Trust the process** - Improvements take time and multiple data points
4. **Check A/B tests** - Review test status periodically to see improvements

---

## Markdown All in One Extension

The Syntek Dev Suite is configured for optimal use with the **Markdown All in One** VS Code extension.

### Key Features

| Feature            | Description                                   |
| ------------------ | --------------------------------------------- |
| Auto-updating TOCs | Table of Contents stays in sync with headings |
| Smart Lists        | Auto-renumbering and intelligent indentation  |
| Table Formatting   | GFM tables auto-align on save                 |
| Task Lists         | Toggle checkboxes with `Alt+C`                |
| Math Support       | Render LaTeX-style math expressions           |

### Keyboard Shortcuts

| Shortcut           | Action               |
| ------------------ | -------------------- |
| `Ctrl+B` / `Cmd+B` | Toggle bold          |
| `Ctrl+I` / `Cmd+I` | Toggle italic        |
| `Tab`              | Indent list item     |
| `Shift+Tab`        | Un-indent list item  |
| `Alt+C`            | Toggle task checkbox |

### Table of Contents

TOCs auto-update when you save. To exclude a heading from the TOC:

```markdown
## Internal Notes <!-- omit in toc -->
```

**Installation:** When opening a Syntek Dev Suite project in VS Code, you'll be prompted to install recommended extensions.

**Extension ID:** `yzhang.markdown-all-in-one`

For the complete guide, see [docs/GUIDES/MARKDOWN-ALL-IN-ONE.md](docs/GUIDES/MARKDOWN-ALL-IN-ONE.md).

---

## Best Practices

### 1. Always Start with `/syntek-dev-suite:plan`

For any non-trivial feature, get a roadmap before coding:

```bash
/syntek-dev-suite:plan Add password reset functionality
```

### 2. Use `/syntek-dev-suite:qa-tester` Before Merging

Catch issues early with hostile QA:

```bash
/syntek-dev-suite:qa-tester Review my changes before PR
```

### 3. Keep CLAUDE.md Updated

When you add dependencies or change frameworks, update `.claude/CLAUDE.md`:

```markdown
## Key Dependencies
- PDF: `barryvdh/laravel-dompdf`
- AI: `openai-php/laravel`  # Add new ones here
```

### 4. Let Agents Read Files

Don't paste code into commands. The agent will read files:

```bash
# Good
/syntek-dev-suite:backend Fix the UserController

# Less good
/syntek-dev-suite:backend Fix this code: [pasted code]
```

### 5. Use the Right Model

- **Opus** (complex): `/syntek-dev-suite:plan`, `/syntek-dev-suite:debug`, `/syntek-dev-suite:data`
- **Sonnet** (balanced): `/syntek-dev-suite:backend`, `/syntek-dev-suite:frontend`, `/syntek-dev-suite:qa-tester`
- **Haiku** (fast): `/syntek-dev-suite:docs`, `/syntek-dev-suite:syntax`, `/syntek-dev-suite:stories`

### 6. Chain Commands Logically

Follow the natural development flow:

```
plan → stories → sprint → backend → frontend → test → qa → review → complete
```

### 7. Commit After Each Step

Small, focused commits after each agent interaction:

```bash
/syntek-dev-suite:backend Create the User model
git commit -m "feat: add User model"

/syntek-dev-suite:test-writer Write tests for User model
git commit -m "test: add User model tests"
```

### 8. Give Feedback

Help agents improve by providing feedback:

```bash
/syntek-dev-suite:learning-feedback good   # When output is correct
/syntek-dev-suite:learning-feedback bad    # When output needs improvement
```

---

## Environment Commands

Each project has environment-specific scripts:

| Script            | Purpose           | Command                             |
| ----------------- | ----------------- | ----------------------------------- |
| `./dev.sh`        | Start development | `ddev start` or `docker-compose up` |
| `./test.sh`       | Run tests         | Test suite with test database       |
| `./staging.sh`    | Staging build     | Build + cache for staging           |
| `./production.sh` | Production build  | Build + optimise for production     |

---

## Browser Configuration

**CRITICAL:** Always use Chrome for testing, debugging, and E2E tests. Never use Firefox unless explicitly requested.

### Browser Environment Variable

| Variable      | Purpose                    | Detection                         |
| ------------- | -------------------------- | --------------------------------- |
| `CHROME_PATH` | Primary Chrome binary path | `./plugins/chrome-tool.py detect` |

```bash
# Detect Chrome and generate .env.chrome
./plugins/chrome-tool.py write
```

### Launching Chrome

```bash
# Standard Chrome for manual testing
$CHROME_PATH http://localhost:3000

# Chrome with DevTools for debugging
$CHROME_PATH --auto-open-devtools-for-tabs http://localhost:3000

# Chrome with specific viewport for responsive testing
$CHROME_PATH --window-size=375,812 http://localhost:3000  # iPhone X
$CHROME_PATH --window-size=768,1024 http://localhost:3000  # iPad

# Headless Chrome for automated tests
$CHROME_PATH --headless --disable-gpu --no-sandbox http://localhost:3000

# Chrome with remote debugging enabled
$CHROME_PATH --remote-debugging-port=9222 http://localhost:3000
```

### Claude Code Chrome Integration

Use `claude --chrome` to enable browser automation from the terminal:

```bash
# Start Claude Code with Chrome enabled
claude --chrome

# Check connection status
/chrome

# Enable Chrome by default
# Run /chrome and select "Enable by default"
```

### E2E Test Configuration

| Framework    | Chrome Configuration                                             |
| ------------ | ---------------------------------------------------------------- |
| Playwright   | `channel: 'chrome'` or `executablePath: process.env.CHROME_PATH` |
| Cypress      | `browser: 'chrome'` in config or `--browser chrome` CLI flag     |
| Puppeteer    | `executablePath: process.env.PUPPETEER_EXECUTABLE_PATH`          |
| Selenium     | `options.binary_location = os.environ.get('CHROME_PATH')`        |
| Laravel Dusk | Uses `DUSK_CHROME_BINARY` env var automatically                  |

---

## Getting Help

- **Plugin Issues:** https://github.com/syntek-developers/syntek-dev-suite/issues
- **Documentation:** See `examples/` folder in the plugin directory
- **Reset to Default:** Delete `.claude/` folder and run `/syntek-dev-suite:init` again

---

**Happy coding with Syntek Dev Suite!**