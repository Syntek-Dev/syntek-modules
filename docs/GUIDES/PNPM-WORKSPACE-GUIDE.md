# pnpm Workspace Guide

This guide explains how to use pnpm workspaces in the syntek-modules monorepo.

## Installation

### Install pnpm

```bash
# Using npm
npm install -g pnpm@10.28.2

# Using curl (Linux/macOS)
curl -fsSL https://get.pnpm.io/install.sh | sh -

# Verify installation
pnpm --version  # Should show 10.28.2
```

### Install All Dependencies

```bash
# From repository root
pnpm install
```

This will install dependencies for all packages in the workspace.

## Workspace Structure

```
syntek-modules/
├── pnpm-workspace.yaml       # Workspace configuration
├── package.json              # Root package.json with scripts
├── .npmrc                    # pnpm configuration
├── turbo.json                # Turbo configuration for build orchestration
├── web/                      # Next.js/React packages
│   └── packages/
│       ├── security-core/
│       ├── security-auth/
│       └── ui-*/
├── mobile/                   # React Native packages
│   └── packages/
│       ├── security-core/
│       ├── security-auth/
│       └── mobile-*/
├── shared/                   # Shared cross-platform UI
└── examples/                 # Example applications
```

## Common Commands

### Build Commands

```bash
# Build all packages
pnpm build

# Build only web packages
pnpm build:web

# Build only mobile packages
pnpm build:mobile

# Build specific package
pnpm --filter @syntek/security-core build

# Build specific package and its dependencies
pnpm --filter @syntek/security-core... build
```

### Development Commands

```bash
# Run all example apps in dev mode
pnpm dev

# Watch mode for specific package
pnpm --filter @syntek/security-core dev

# Run multiple packages in parallel
pnpm --filter @syntek/security-core --filter @syntek/ui-auth dev
```

### Testing Commands

```bash
# Test all packages
pnpm test

# Test web packages only
pnpm test:web

# Test mobile packages only
pnpm test:mobile

# Test specific package
pnpm --filter @syntek/security-core test

# Watch mode
pnpm --filter @syntek/security-core test:watch
```

### Linting and Formatting

```bash
# Lint all packages
pnpm lint

# Fix linting issues
pnpm lint:fix

# Format all files
pnpm format

# Check formatting
pnpm format:check

# Typecheck all packages
pnpm typecheck
```

### Dependency Management

```bash
# Add dependency to specific package
pnpm --filter @syntek/security-core add dompurify

# Add dev dependency
pnpm --filter @syntek/security-core add -D vitest

# Add workspace dependency (internal package)
pnpm --filter @syntek/ui-auth add @syntek/security-core --workspace

# Remove dependency
pnpm --filter @syntek/security-core remove dompurify

# Update dependencies
pnpm --filter @syntek/security-core update

# Update all dependencies in workspace
pnpm -r update
```

### Clean Commands

```bash
# Clean build artifacts
pnpm clean:build

# Clean everything (including node_modules)
pnpm clean

# Clean specific package
pnpm --filter @syntek/security-core clean
```

## Creating a New Package

### 1. Create Directory Structure

```bash
# For web package
mkdir -p web/packages/my-package/src

# For mobile package
mkdir -p mobile/packages/mobile-my-feature/src
```

### 2. Create package.json

```json
{
  "name": "@syntek/my-package",
  "version": "1.0.0",
  "description": "Description of my package",
  "main": "./dist/index.js",
  "module": "./dist/index.mjs",
  "types": "./dist/index.d.ts",
  "exports": {
    ".": {
      "import": "./dist/index.mjs",
      "require": "./dist/index.js",
      "types": "./dist/index.d.ts"
    }
  },
  "files": ["dist", "README.md"],
  "scripts": {
    "build": "tsup",
    "dev": "tsup --watch",
    "clean": "rm -rf dist .turbo node_modules",
    "lint": "eslint .",
    "typecheck": "tsc --noEmit",
    "test": "vitest run"
  },
  "devDependencies": {
    "tsup": "^8.3.5",
    "typescript": "^5.9.0",
    "vitest": "^3.0.0"
  },
  "peerDependencies": {
    "react": "^19.0.0"
  }
}
```

### 3. Create Source Files

```bash
# src/index.ts
export * from './my-feature'
```

### 4. Build Configuration

Copy `tsup.config.ts` from repository root or customize as needed.

### 5. Install and Build

```bash
# Install dependencies
pnpm install

# Build the package
pnpm --filter @syntek/my-package build
```

## Using Internal Packages

### Installing Workspace Packages

```bash
# Add internal package as dependency
pnpm --filter @syntek/ui-auth add @syntek/security-core --workspace
```

This will add to package.json:
```json
{
  "dependencies": {
    "@syntek/security-core": "workspace:*"
  }
}
```

### Importing Workspace Packages

```typescript
// In @syntek/ui-auth/src/LoginForm.tsx
import { useCSRF } from '@syntek/security-core'

export function LoginForm() {
  const { token } = useCSRF()
  // ...
}
```

## Publishing Packages

### Manual Publishing

```bash
# Build the package
pnpm --filter @syntek/security-core build

# Publish to npm
cd web/packages/security-core
pnpm publish
```

### Using Changesets (Recommended)

Changesets help manage versioning and changelogs.

```bash
# Create a changeset
pnpm changeset

# Version packages (updates package.json versions)
pnpm changeset:version

# Publish to npm
pnpm changeset:publish
```

## Filtering Packages

### Filter Patterns

```bash
# Single package
pnpm --filter @syntek/security-core <command>

# Multiple packages
pnpm --filter @syntek/security-core --filter @syntek/ui-auth <command>

# All packages in directory
pnpm --filter './web/**' <command>

# Package and its dependencies
pnpm --filter @syntek/security-core... <command>

# Package and its dependents
pnpm --filter ...@syntek/security-core <command>
```

### Parallel Execution

```bash
# Run command in parallel across all packages
pnpm -r --parallel <command>

# Example: parallel builds
pnpm -r --parallel build
```

## Troubleshooting

### Clear Cache

```bash
# Clear pnpm store cache
pnpm store prune

# Remove all node_modules and reinstall
pnpm clean && pnpm install
```

### Dependency Issues

```bash
# Check for phantom dependencies
pnpm -r exec pnpm why <package-name>

# Update lockfile
pnpm install --lockfile-only
```

### Build Issues

```bash
# Clean and rebuild
pnpm clean:build && pnpm build

# Build with verbose output
pnpm --filter @syntek/security-core build --verbose
```

## Configuration Files

### pnpm-workspace.yaml

Defines which directories contain packages:

```yaml
packages:
  - 'web/packages/*'
  - 'mobile/packages/*'
  - 'shared'
  - 'examples/*'
```

### .npmrc

Configures pnpm behavior:

```ini
strict-peer-dependencies=true
shamefully-hoist=false
link-workspace-packages=true
save-exact=true
```

### turbo.json

Configures task orchestration and caching:

```json
{
  "tasks": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": ["dist/**"]
    }
  }
}
```

## Best Practices

1. **Use workspace protocol** - Always use `workspace:*` for internal dependencies
2. **Build order** - Let turbo handle build dependencies automatically
3. **Parallel execution** - Use `--parallel` for independent tasks
4. **Filtering** - Use filters to work on specific packages
5. **Clean builds** - Run `pnpm clean:build` before publishing
6. **Version management** - Use changesets for consistent versioning
7. **Peer dependencies** - Mark framework dependencies (react, next) as peer deps
8. **Lock versions** - Use `save-exact=true` to lock versions in package.json

## Additional Resources

- [pnpm Documentation](https://pnpm.io/)
- [pnpm Workspaces](https://pnpm.io/workspaces)
- [Turbo Documentation](https://turbo.build/)
- [Changesets Documentation](https://github.com/changesets/changesets)
