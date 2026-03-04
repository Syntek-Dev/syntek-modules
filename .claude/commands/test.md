---
description: Run the full test suite across all package layers
usage: /test [backend|web|mobile|rust|all]
---

Run all tests across all layers.

**Run:** `./test.sh`

This script will:
1. Run `pytest` for all Python backend packages
2. Run `pnpm test` (via Turborepo) for all web and mobile packages
3. Run `cargo test` for all Rust crates
4. Run type checks: `mypy`, `tsc --noEmit`, `cargo clippy`
5. Run linting: `ruff check`, `eslint`, `cargo fmt --check`

**Layer-specific:**

```bash
# Backend package tests
pytest packages/backend/syntek-auth/tests/ -v

# Single web package
pnpm --filter @syntek/ui-auth test

# All web/mobile (Turborepo)
pnpm test

# Rust
cargo test

# With coverage
pytest --cov packages/backend/syntek-auth/
pnpm --filter @syntek/ui test -- --coverage
cargo tarpaulin
```

**CI gate requirements:**
- Python: 80% line coverage minimum
- TypeScript: 80% line coverage minimum
- Rust: all tests pass, clippy clean
- mypy --strict passing
- tsc --noEmit passing

$ARGUMENTS
