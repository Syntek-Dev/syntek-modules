---
description: Build and publish prerelease packages to the staging registry
usage: /staging [package-name]
---

Build and publish a prerelease (staging) version of one or all packages.

**Run:** `./staging.sh`

This script will:

1. Run the full test suite (`./test.sh`)
2. Build all packages (Turborepo for JS/TS, cargo for Rust)
3. Bump prerelease version on affected packages
4. Publish to Forgejo staging registry with `--tag staging`

**Manual publish by layer:**

```bash
# Python package (prerelease)
uv build packages/backend/syntek-auth/
uv publish --index https://git.syntek-studio.com/... dist/*.whl

# TypeScript package (prerelease)
pnpm --filter @syntek/ui-auth version prerelease --preid=staging
pnpm --filter @syntek/ui-auth publish --tag staging

# Rust crate (prerelease)
cd rust/syntek-crypto
cargo publish --registry syntek --dry-run
```

Staging packages are installed in test projects with:

```bash
syntek add syntek-auth@staging
syntek add @syntek/ui-auth@staging
```

$ARGUMENTS
