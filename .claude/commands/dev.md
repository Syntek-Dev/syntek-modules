---
description: Start development mode across all package layers
usage: /dev [backend|web|mobile|rust|all]
---

Start the development environment for syntek-modules.

**Run:** `./dev.sh`

This script will:

1. Activate the Python virtual environment (uv venv)
2. Start Turborepo watch mode for all web and mobile packages
3. Start Rust build watcher via cargo-watch
4. Print available storybook commands

**Layer-specific commands:**

```bash
# Python (backend packages)
source .venv/bin/activate
uv pip install -e "packages/backend/syntek-<name>[dev]"

# TypeScript (web + mobile)
pnpm --filter @syntek/<name> dev

# Rust (encryption crates)
cargo watch -x build

# Storybook for UI components
pnpm --filter @syntek/ui storybook
```

**No Docker required** — this repo uses uv venv for Python and pnpm workspaces for TypeScript.

$ARGUMENTS
