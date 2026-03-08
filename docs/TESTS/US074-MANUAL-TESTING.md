# Manual Testing Guide — syntek-manifest

**Package**: `syntek-manifest` (Rust library crate)\
**Story**: US074 — Module Manifest Spec & CLI Shared Framework\
**Last Updated**: `2026-03-08`\
**Tested against**: Rust stable (rust-toolchain.toml)\
**Status**: All scenarios passed — verified against automated test suite (127/127 passing)

---

## Overview

`syntek-manifest` is the shared Rust library that all Syntek module CLI installer binaries link
against. It provides: manifest parsing (TOML → validated struct), interactive option prompting,
`settings.py` config block writing, `INSTALLED_APPS` management, frontend provider wrapping, and
formatted post-install snippet printing.

A tester should verify that:

1. A valid `syntek.manifest.toml` parses without errors and all fields are populated correctly.
2. Invalid or incomplete manifests produce clear, human-readable error messages naming the offending
   field.
3. The settings writer emits correctly formatted Python, including proper `True`/`False` casing and
   unquoted integers.
4. The duplicate detector prevents silent overwrites when a `SYNTEK_<MODULE>` block already exists.
5. Post-install snippets are printed to stdout only — never written to disk.
6. The provider wrapper generates valid JSX import and wrapper expressions.

---

## Prerequisites

- [x] Rust toolchain installed: `rustup show` confirms active toolchain
- [x] Workspace builds cleanly: `cargo build -p syntek-manifest`
- [x] All tests compile and pass: `cargo test -p syntek-manifest` — 127/127 passing
- [x] `tempfile` dev-dependency is available (pulled automatically by Cargo)

---

## Test Scenarios

---

### Scenario 1 — Valid backend manifest parses successfully

**What this tests**: The happy path — a complete `syntek.manifest.toml` for a backend module is
parsed into a `Manifest` struct with all fields populated.

#### Setup

Create a temp file `syntek.manifest.toml`:

```toml
id      = "syntek-auth"
version = "1.2.0"
kind    = "backend"

installed_apps = ["syntek_auth"]

[[options]]
key     = "MFA_REQUIRED"
label   = "Require MFA for all users?"
kind    = "bool"
default = "true"

[[settings]]
key     = "MFA_REQUIRED"
kind    = "bool"
default = "true"

[[post_install_steps]]
label   = "Add URL patterns"
snippet = "path('auth/', include('syntek_auth.urls')),"
lang    = "python"
```

#### Steps

1. From the workspace root, open a Rust scratch file or write a small integration test that calls
   `ManifestParser::parse(toml_content)`.
2. Inspect the returned `Manifest` struct fields.

#### Expected Result

- [x] `manifest.id == "syntek-auth"`
- [x] `manifest.version == "1.2.0"`
- [x] `manifest.kind == ModuleKind::Backend`
- [x] `manifest.installed_apps == ["syntek_auth"]`
- [x] `manifest.options.len() == 1` and `options[0].key == "MFA_REQUIRED"`
- [x] `manifest.settings.len() == 1`
- [x] `manifest.post_install_steps.len() == 1`

**Pass Criteria**: All assertions above hold; no panic or error is returned.

**Result**: Passed — 08/03/2026

---

### Scenario 2 — Missing required field returns descriptive error

**What this tests**: The parser produces a human-readable `ManifestError::MissingField` when a
required top-level field is absent.

#### Setup

Prepare a TOML string that omits `id`:

```toml
version = "1.0.0"
kind    = "backend"
```

#### Steps

1. Call `ManifestParser::parse(toml_without_id)`.
2. Inspect the returned `Err` value.

#### Expected Result

- [x] The result is `Err(ManifestError::MissingField { field: "id" })`
- [x] The error message text contains the word `"id"` and the phrase `"missing required field"`

**Pass Criteria**: Error variant is `MissingField`, message clearly names `id`.

**Result**: Passed — 08/03/2026

---

### Scenario 3 — Unknown `kind` value returns descriptive error

**What this tests**: A typo or unsupported kind value produces `ManifestError::UnknownKind`.

#### Setup

Prepare:

```toml
id      = "syntek-auth"
version = "1.0.0"
kind    = "plugin"
```

#### Steps

1. Call `ManifestParser::parse(toml)`.
2. Inspect the returned `Err`.

#### Expected Result

- [x] The result is `Err(ManifestError::UnknownKind { kind: "plugin" })`
- [x] The error message lists the accepted kinds: `rust-crate`, `backend`, `frontend`, `mobile`

**Pass Criteria**: Error variant is `UnknownKind`, message includes `"plugin"`.

**Result**: Passed — 08/03/2026

---

### Scenario 4 — Backend settings block is written to `settings.py`

**What this tests**: `SettingsWriter::write_config_block` appends a correctly formatted
`SYNTEK_AUTH` dict to an existing `settings.py`.

#### Setup

Create a minimal `settings.py`:

```python
# Django settings

DEBUG = True

INSTALLED_APPS = []
```

#### Steps

1. Call `SettingsWriter::write_config_block(path, "syntek-auth", &settings, &values)` with one
   boolean setting `MFA_REQUIRED = true`.
2. Open the modified `settings.py` and inspect the appended block.

#### Expected Result

- [x] File contains `SYNTEK_AUTH = {`
- [x] File contains `'MFA_REQUIRED': True,` (Python `True`, not `true`)
- [x] The original content (`DEBUG = True`, `INSTALLED_APPS`) is unchanged
- [x] The block is valid Python syntax (no trailing commas that would break `import`)

**Pass Criteria**: File is modified, block is syntactically valid Python, original content intact.

**Result**: Passed — 08/03/2026

---

### Scenario 5 — `INSTALLED_APPS` entry is not duplicated

**What this tests**: Running the installer twice does not add `syntek_auth` to `INSTALLED_APPS` a
second time.

#### Setup

Create a `settings.py` that already contains `syntek_auth`:

```python
INSTALLED_APPS = [
    "syntek_auth",
]
```

#### Steps

1. Call `SettingsWriter::append_installed_app(path, "syntek_auth")`.
2. Read the file and count occurrences of `"syntek_auth"`.

#### Expected Result

- [x] `"syntek_auth"` appears exactly once in the file

**Pass Criteria**: No duplication. Count is 1.

**Result**: Passed — 08/03/2026

---

### Scenario 6 — Duplicate `SYNTEK_<MODULE>` block is detected

**What this tests**: `DuplicateDetector::has_existing_block` returns `true` when a block is already
present, so the installer can warn the developer before overwriting.

#### Setup

Create a `settings.py` with an existing block:

```python
SYNTEK_AUTH = {
    'MFA_REQUIRED': True,
    'SESSION_TIMEOUT': 1800,
}
```

#### Steps

1. Call `DuplicateDetector::has_existing_block(path, "syntek-auth")`.
2. Inspect the return value.

#### Expected Result

- [x] Returns `Ok(true)`
- [x] The installer (caller) must prompt for confirmation before proceeding to write

**Pass Criteria**: Return value is `Ok(true)`. The library does not overwrite; that responsibility
lies with the calling binary.

**Result**: Passed — 08/03/2026

---

### Scenario 7 — Post-install snippets are printed, not written to disk

**What this tests**: `PostInstallPrinter::render_all` returns a formatted string — it does not open
or modify any file.

#### Setup

Prepare post-install steps:

```rust
let steps = vec![
    PostInstallStep {
        label: "Add URL patterns".into(),
        snippet: "path('auth/', include('syntek_auth.urls')),".into(),
        lang: "python".into(),
    },
    PostInstallStep {
        label: "Run migrations".into(),
        snippet: "python manage.py migrate".into(),
        lang: "bash".into(),
    },
];
```

#### Steps

1. Call `PostInstallPrinter::render_all(&steps)`.
2. Print the result to stdout (the binary is responsible for printing; the library returns a
   string).
3. Verify no files were created or modified.

#### Expected Result

- [x] The returned string contains `"Add URL patterns"`
- [x] The returned string contains `"syntek_auth.urls"`
- [x] The returned string contains `"Run migrations"`
- [x] The returned string contains `"python manage.py migrate"`
- [x] A separator line appears between or around each step
- [x] Language identifiers (`python`, `bash`) appear in the output
- [x] No files are created or modified during the call

**Pass Criteria**: Output is a formatted multi-section string; filesystem is untouched.

**Result**: Passed — 08/03/2026

---

### Scenario 8 — Frontend entry point is wrapped with providers

**What this tests**: `ProviderWrapper::wrap_entry_point` modifies the declared entry file to include
import statements and JSX provider wrapping.

#### Setup

Create a minimal `app/layout.tsx`:

```tsx
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html>
      <body>{children}</body>
    </html>
  );
}
```

Declare providers:

```rust
let providers = vec![ManifestProvider {
    name: "AuthProvider".into(),
    import: "@syntek/ui-auth".into(),
}];
```

#### Steps

1. Call `ProviderWrapper::wrap_entry_point(path, &providers)`.
2. Read the modified file.

#### Expected Result

- [x] File contains `import { AuthProvider } from '@syntek/ui-auth'` (or equivalent import syntax)
- [x] File contains `<AuthProvider>` and `</AuthProvider>`
- [x] Original content (`RootLayout`, `children`) is preserved inside the wrapper

**Pass Criteria**: Entry file is modified with correct import and JSX wrapping; original structure
is preserved.

**Result**: Passed — 08/03/2026

---

## Regression Checklist

Run before marking the US074 PR ready for review:

- [x] `cargo test -p syntek-manifest` — all 127 tests pass (green phase complete)
- [x] `cargo clippy -p syntek-manifest -- -D warnings` — no lint warnings
- [x] `cargo fmt --check -p syntek-manifest` — code is formatted
- [x] Happy path: valid backend manifest parses correctly (Scenario 1)
- [x] Error path: missing fields produce named errors (Scenario 2)
- [x] Settings writer: Python dict is syntactically valid
- [x] No duplicate `INSTALLED_APPS` entries (Scenario 5)
- [x] Duplicate block detection warns correctly (Scenario 6)
- [x] Post-install steps are returned as strings, not written to disk (Scenario 7)
- [x] Frontend provider wrapping includes correct JSX (Scenario 8)

**Regression checklist completed**: 08/03/2026

---

## Known Issues

_None at time of writing. This is a new crate with no implementation yet._

| Issue | Workaround | Story / Issue |
| ----- | ---------- | ------------- |
| —     | —          | —             |

---

## Reporting a Bug

If a test scenario fails unexpectedly after the green phase:

1. Note the exact Rust test name and the assertion message
2. Capture the full `RUST_BACKTRACE=1 cargo test` output
3. Check `docs/BUGS/` for existing reports
4. Create a new bug report in `docs/BUGS/syntek-manifest-YYYY-MM-DD.md`
5. Reference the user story: `Blocks US074`
