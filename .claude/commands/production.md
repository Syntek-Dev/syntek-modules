---
description: Build and publish production release packages
usage: /production [package-name]
---

Build and publish a production release of one or all packages.

**Run:** `./production.sh`

This script will:

1. Prompt for confirmation (safety check)
2. Run the full test suite (`./test.sh`)
3. Build all packages
4. Bump version (patch/minor/major — prompted)
5. Publish to Forgejo production registry
6. Tag the release in Forgejo

**Manual publish by layer:**

```bash
# Python package
cd packages/backend/syntek-auth
uv build
uv publish --index https://git.syntek-studio.com/... dist/*.whl

# TypeScript package
pnpm --filter @syntek/ui-auth version patch   # or minor/major
pnpm --filter @syntek/ui-auth publish

# Rust crate
cd rust/syntek-crypto
cargo publish --registry syntek
```

**Version bump rules:**

- `patch` — bug fixes, no API changes
- `minor` — new features, backwards compatible
- `major` — breaking API changes

After publishing, run `/syntek-dev-suite:version` to update changelogs and version history.

$ARGUMENTS
