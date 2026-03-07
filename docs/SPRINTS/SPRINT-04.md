# Sprint 04 — Rust: PyO3 Django Bindings

**Sprint Goal**: Build the PyO3 native extension exposing `encrypt_field`, `decrypt_field`,
`hash_password`, and `verify_password` to Django, and implement the `EncryptedField` descriptor so
application code handles plain Python strings with encryption transparent.

**Total Points**: 8 / 11 **MoSCoW Balance**: Must 100% **Status**: Planned

## Stories

| Story                        | Title                                | Points | MoSCoW | Dependencies Met |
| ---------------------------- | ------------------------------------ | ------ | ------ | ---------------- |
| [US007](../STORIES/US007.md) | `syntek-pyo3` — PyO3 Django Bindings | 8      | Must   | US006 ✓          |

## Notes

- Strict dependency on US006 completing in Sprint 03.
- Requires `maturin` to build the Python extension into the active `.venv`.
