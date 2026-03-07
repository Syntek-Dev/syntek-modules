---
description: Build all packages across all layers
usage: /build [backend|web|mobile|rust|all]
---

Build all packages for distribution.

**TypeScript (all packages via Turborepo):**

```bash
pnpm build
```

**Single web/mobile package:**

```bash
pnpm --filter @syntek/ui build
pnpm --filter @syntek/mobile-auth build
```

**Python packages:**

```bash
uv build packages/backend/syntek-auth/
# Output: packages/backend/syntek-auth/dist/*.whl
```

**Rust crates:**

```bash
cargo build --release
# PyO3 extension (installs into active .venv)
cd rust/syntek-pyo3 && maturin develop
```

**All layers:**

```bash
./production.sh   # Runs tests then builds all
```

$ARGUMENTS
