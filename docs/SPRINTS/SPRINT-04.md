# Sprint 04 — Rust: PyO3 Django Bindings

**Sprint Goal**: Build the PyO3 native extension exposing `encrypt_field`, `decrypt_field`,
`hash_password`, and `verify_password` to Django, and implement the `EncryptedField` descriptor so
application code handles plain Python strings with encryption transparent.

**Total Points**: 8 / 11 **MoSCoW Balance**: Must 100% **Status**: Completed

## Stories

| Story                        | Title                                | Points | MoSCoW | Status    | Dependencies Met |
| ---------------------------- | ------------------------------------ | ------ | ------ | --------- | ---------------- |
| [US007](../STORIES/US007.md) | `syntek-pyo3` — PyO3 Django Bindings | 8      | Must   | Completed | US006 ✓          |

## Sprint Status

**Overall Status:** Completed **Completion Date:** 09/03/2026

### Completion Summary

| Category         | Total | Completed | Remaining |
| ---------------- | ----- | --------- | --------- |
| Must Have        | 1     | 1         | 0         |
| Should Have      | 0     | 0         | 0         |
| Could Have       | 0     | 0         | 0         |
| **Total Points** | **8** | **8**     | **0**     |

### Stories Completed

| Story | Title                                | Points | Completed  | Tests                                      |
| ----- | ------------------------------------ | ------ | ---------- | ------------------------------------------ |
| US007 | `syntek-pyo3` — PyO3 Django Bindings | 8      | 09/03/2026 | 65/65 passing (cargo test + pytest, green) |

## Notes

- Strict dependency on US006 completing in Sprint 03.
- Requires `maturin` to build the Python extension into the active `.venv`.
- Sprint 04 completed on branch `us007/syntek-pyo3` — 09/03/2026. All 65 tests pass (12 Rust unit,
  53 Python). All 8 manual scenarios confirmed PASS. Clippy clean, fmt clean, no unsafe blocks.
  `EncryptedField` defence-in-depth guard validated — plaintext rejected before any DB write.
  `maturin develop` confirmed working in active `.venv`.
