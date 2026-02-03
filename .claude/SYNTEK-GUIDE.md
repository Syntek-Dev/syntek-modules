# Syntek Dev Suite - Command Reference

This guide covers all Syntek Dev Suite agents and tools available for your modular repository.

## Quick Start

```bash
# View available agents
/help

# Initialize a new module
/syntek-dev-suite:setup

# Plan a new feature
/syntek-dev-suite:plan

# Create user stories
/syntek-dev-suite:stories

# Generate tests
/syntek-dev-suite:test-writer
```

## Development Agents

### Planning & Architecture

#### `/syntek-dev-suite:plan`
High-level system architect for planning features.

**Use when:**
- Planning new modules
- Designing module APIs
- Planning cross-module integrations

**Example:**
```
/syntek-dev-suite:plan
I need to create a new "subscriptions" module that integrates with the payments module
```

#### `/syntek-dev-suite:stories`
Converts vague requirements into structured user stories.

**Use when:**
- Breaking down module requirements
- Creating tickets for new features

**Example:**
```
/syntek-dev-suite:stories
Users need to manage their payment methods and view billing history
```

#### `/syntek-dev-suite:sprint`
Organizes user stories into balanced sprints with MoSCoW prioritization.

**Use when:**
- Planning module development cycles
- Prioritizing features

### Code Development

#### `/syntek-dev-suite:backend`
Specialist in APIs, DB schemas, and server logic.

**Use when:**
- Creating Django modules
- Designing GraphQL schemas
- Implementing Rust encryption bindings

**Example:**
```
/syntek-dev-suite:backend
Create a Django app for managing user subscriptions with GraphQL mutations
```

#### `/syntek-dev-suite:frontend`
Expert in UI/UX, CSS, and accessibility.

**Use when:**
- Creating React/Next.js UI modules
- Creating React Native components
- Working on the shared UI library

**Example:**
```
/syntek-dev-suite:frontend
Create a subscription management component for the shared UI library
```

#### `/syntek-dev-suite:database`
Database administration, optimization, migrations, and query performance.

**Use when:**
- Designing module database schemas
- Creating Django migrations
- Optimizing PostgreSQL queries

#### `/syntek-dev-suite:test-writer`
Generates tests + minimal implementation stubs (TDD/BDD) for any stack.

**Use when:**
- Writing tests for modules
- Setting up test infrastructure
- Creating integration tests

**Example:**
```
/syntek-dev-suite:test-writer
Write tests for the authentication module's login flow
```

### Code Quality

#### `/syntek-dev-suite:review`
Expert code reviewer focusing on security, performance, and style.

**Use when:**
- Reviewing module code before release
- Checking for security issues
- Ensuring code quality

#### `/syntek-dev-suite:syntax`
Linter and language guru.

**Use when:**
- Fixing linting errors
- Enforcing code style
- Setting up linting configs

#### `/syntek-dev-suite:refactor`
Specialist in code modernization and technical debt.

**Use when:**
- Improving module code structure
- Removing technical debt
- Modernizing old modules

#### `/syntek-dev-suite:debug`
Deep-dive debugger for complex runtime issues and logic errors.

**Use when:**
- Debugging module issues
- Investigating integration problems
- Finding root causes

### Security & Compliance

#### `/syntek-dev-suite:security`
Implements site protection with unreplicable paths, permission-based access control, and security hardening.

**Use when:**
- Implementing module security
- Adding encryption/decryption
- Hardening Rust security layer

**Example:**
```
/syntek-dev-suite:security
Review the encryption module for security vulnerabilities
```

#### `/syntek-dev-suite:auth`
Implements secure authentication with MFA, strong password validation, and session management.

**Use when:**
- Working on the authentication module
- Implementing OAuth/SSO
- Adding MFA support

#### `/syntek-dev-suite:gdpr`
Implements GDPR compliance including data protection, consent management, and user rights.

**Use when:**
- Adding GDPR features to modules
- Implementing data export/deletion
- Managing user consent

### Integration & Infrastructure

#### `/syntek-dev-suite:cicd`
CI/CD specialist for GitHub Actions, AWS, Digital Ocean, Docker, and DDEV deployments.

**Use when:**
- Setting up module testing pipelines
- Configuring automated testing
- Publishing modules to registries

**Example:**
```
/syntek-dev-suite:cicd
Set up GitHub Actions to test all modules on every commit
```

#### `/syntek-dev-suite:logging`
Implements logging with Sentry for production and file-based logging for development.

**Use when:**
- Adding logging to modules
- Integrating with GlitchTip
- Setting up error tracking

#### `/syntek-dev-suite:notifications`
Implements notification systems with custom branding for emails, SMS, and push notifications.

**Use when:**
- Working on the notifications module
- Adding email/SMS capabilities
- Creating notification templates

### Documentation

#### `/syntek-dev-suite:docs`
Technical writer for developer documentation including READMEs, API docs, code comments, and contribution guides.

**Use when:**
- Writing module READMEs
- Documenting module APIs
- Creating installation guides

**Example:**
```
/syntek-dev-suite:docs
Write a comprehensive README for the payments module
```

#### `/syntek-dev-suite:support-articles`
Creates user-facing help documentation and support articles for website features.

**Use when:**
- Creating module usage guides
- Writing integration tutorials
- Documenting module features

### Version Control

#### `/syntek-dev-suite:git`
Git workflow specialist for branch management, commits, pull requests, and versioning.

**Use when:**
- Creating module releases
- Managing git workflows
- Creating pull requests

**Example:**
```
/syntek-dev-suite:git
Create a release branch for authentication module v2.0.0
```

#### `/syntek-dev-suite:version`
Version management specialist for semantic versioning, VERSION-HISTORY.md, CHANGELOG.md, RELEASES.md, and markdown metadata headers.

**Use when:**
- Bumping module versions
- Creating changelogs
- Managing releases

### Quality Assurance

#### `/syntek-dev-suite:qa-tester`
Hostile QA analysis to find bugs, security flaws, and edge cases.

**Use when:**
- Testing modules before release
- Finding edge cases
- Security testing

### Project Management

#### `/syntek-dev-suite:pm-setup`
Project management tool setup and integration specialist.

**Use when:**
- Setting up issue tracking
- Configuring project boards
- Integrating with PM tools

#### `/syntek-dev-suite:completion`
Tracks and marks user stories and sprints as complete per repository.

**Use when:**
- Marking modules as complete
- Tracking progress
- Closing sprints

### Reporting & Analytics

#### `/syntek-dev-suite:reporting`
Generates data queries and aggregations for system roles to produce reports.

**Use when:**
- Creating module analytics
- Generating usage reports
- Tracking module metrics

#### `/syntek-dev-suite:data`
Expert in Python, Pandas, SQL, and data visualization.

**Use when:**
- Analyzing module usage data
- Creating data visualizations
- Working with PostgreSQL

### Export Functionality

#### `/syntek-dev-suite:export`
Implements file export functionality in appropriate formats (PDF, Excel, CSV, JSON).

**Use when:**
- Adding export features to modules
- Creating report exports
- Implementing data downloads

### SEO (Web Modules Only)

#### `/syntek-dev-suite:seo`
Implements SEO optimization including meta tags, Open Graph, structured data, robots.txt, and sitemaps.

**Use when:**
- Adding SEO to web UI modules
- Creating meta tag components
- Implementing structured data

## Self-Learning System

### `/syntek-dev-suite:learning-feedback`
Provide feedback on the last agent response.

**Use when:**
- An agent response was particularly good or bad
- You want to improve agent performance
- You found a bug in agent behavior

**Options:**
- 👍 Good - Agent met expectations
- 👎 Bad - Agent didn't meet expectations
- 🐛 Bug - Agent had an error or unexpected behavior

**Example:**
```
/syntek-dev-suite:learning-feedback
👎 The backend agent didn't create proper GraphQL mutations for the module
```

### `/syntek-dev-suite:learning-optimise`
Review and apply prompt optimizations based on collected feedback.

**Use when:**
- You want to see pending optimizations
- You want to apply improvements manually
- Auto-optimization is disabled

**Example:**
```
/syntek-dev-suite:learning-optimise
Show me what improvements are available for the backend agent
```

### `/syntek-dev-suite:learning-ab-test`
Manage A/B tests for agent prompts.

**Use when:**
- Testing different agent approaches
- Comparing prompt variants
- Running experiments

## Python Plugin Tools

The following CLI tools are available in `.claude/plugins/`:

### Project Management
```bash
.claude/plugins/project-tool.py info        # Get project information
.claude/plugins/project-tool.py framework   # Detect framework
.claude/plugins/project-tool.py container   # Detect container type
```

### Environment Management
```bash
.claude/plugins/env-tool.py list           # List environment files
.claude/plugins/env-tool.py validate       # Validate .env files
.claude/plugins/env-tool.py create dev     # Create dev environment
```

### Git Operations
```bash
.claude/plugins/git-tool.py status         # Enhanced git status
.claude/plugins/git-tool.py branches       # List branches
.claude/plugins/git-tool.py conflicts      # Check for conflicts
```

### Docker Management
```bash
.claude/plugins/docker-tool.py status      # Container status
.claude/plugins/docker-tool.py logs        # View logs
.claude/plugins/docker-tool.py exec        # Execute commands
```

### Database Operations
```bash
.claude/plugins/db-tool.py status          # Database status
.claude/plugins/db-tool.py backup          # Create backup
.claude/plugins/db-tool.py restore         # Restore backup
```

### Quality Assurance
```bash
.claude/plugins/quality-tool.py lint       # Run linters
.claude/plugins/quality-tool.py test       # Run tests
.claude/plugins/quality-tool.py coverage   # Test coverage
```

### Logging
```bash
.claude/plugins/log-tool.py view           # View logs
.claude/plugins/log-tool.py search         # Search logs
.claude/plugins/log-tool.py export         # Export logs
```

### Metrics & Learning
```bash
.claude/plugins/metrics-tool.py record     # Record agent run
.claude/plugins/feedback-tool.py submit    # Submit feedback
.claude/plugins/optimiser-tool.py analyse  # Analyze performance
.claude/plugins/ab-test-tool.py create     # Create A/B test
```

## Module-Specific Workflows

### Creating a New Backend Module

1. Plan the module
   ```
   /syntek-dev-suite:plan
   Create a new subscriptions module with recurring billing
   ```

2. Create user stories
   ```
   /syntek-dev-suite:stories
   [Paste plan output]
   ```

3. Set up module structure
   ```
   /syntek-dev-suite:setup
   Initialize backend/subscriptions module
   ```

4. Write tests first
   ```
   /syntek-dev-suite:test-writer
   TDD for subscriptions module based on user stories
   ```

5. Implement backend logic
   ```
   /syntek-dev-suite:backend
   Implement the subscriptions module with GraphQL API
   ```

6. Add security
   ```
   /syntek-dev-suite:security
   Review security for subscriptions module
   ```

7. Document
   ```
   /syntek-dev-suite:docs
   Write README for subscriptions module
   ```

### Creating a New Frontend Module

1. Plan the UI
   ```
   /syntek-dev-suite:plan
   Create subscription UI components for web and mobile
   ```

2. Create in shared library first (if cross-platform)
   ```
   /syntek-dev-suite:frontend
   Create subscription components in shared/components
   ```

3. Platform-specific implementations
   ```
   /syntek-dev-suite:frontend
   Create Next.js wrapper for subscription components
   ```

4. Test
   ```
   /syntek-dev-suite:test-writer
   Write tests for subscription UI components
   ```

5. Accessibility review
   ```
   /syntek-dev-suite:frontend
   Review accessibility for subscription components
   ```

### Releasing a Module

1. Run QA
   ```
   /syntek-dev-suite:qa-tester
   Test subscriptions module for bugs and edge cases
   ```

2. Security review
   ```
   /syntek-dev-suite:security
   Final security review before release
   ```

3. Update version
   ```
   /syntek-dev-suite:version
   Bump subscriptions module to v1.0.0
   ```

4. Create changelog
   ```
   /syntek-dev-suite:version
   Generate CHANGELOG.md for subscriptions module
   ```

5. Git workflow
   ```
   /syntek-dev-suite:git
   Create release PR for subscriptions module v1.0.0
   ```

6. CI/CD
   ```
   /syntek-dev-suite:cicd
   Set up automated testing for subscriptions module
   ```

## Best Practices

### Module Independence
- Keep modules loosely coupled
- Use explicit dependencies in setup.py/package.json/Cargo.toml
- Don't assume other modules are installed

### Testing
- Write tests for each module
- Integration tests in `tests/` directory
- Use example apps to test real-world usage

### Documentation
- Every module needs a README
- Include installation instructions
- Show usage examples

### Security
- All sensitive data through Rust encryption layer
- Follow security guidelines in CLAUDE.md
- Regular security reviews

### Versioning
- Use semantic versioning
- Maintain changelogs
- Tag releases in git

## Getting Help

- Read `.claude/CLAUDE.md` for project context
- Check individual module READMEs
- Look at example applications
- Use `/syntek-dev-suite:plan` to plan complex work
- Use `/syntek-dev-suite:learning-feedback` to improve agents

## Configuration

Self-learning system configuration is in `docs/METRICS/config.json`:

```json
{
  "enabled": true,
  "auto_optimisation_enabled": true,
  "min_runs_for_analysis": 50
}
```

- **enabled:** Turn metrics collection on/off
- **auto_optimisation_enabled:** Apply improvements automatically
- **min_runs_for_analysis:** Minimum runs before suggesting optimizations
