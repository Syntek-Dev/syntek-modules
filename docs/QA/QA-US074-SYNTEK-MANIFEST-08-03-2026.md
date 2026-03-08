# QA Report: US074 — `syntek-manifest` Module Manifest Spec & CLI Shared Framework

**Date:** 08/03/2026 **Analyst:** QA Agent (The Breaker) **Branch:**
`us074/module-manifest-spec-cli-shared-framework` **Status:** CRITICAL ISSUES

---

## Summary

The `rust/syntek-manifest` crate implements a manifest parser and installer helper library. Analysis
reveals one critical data-corruption path, six high-severity logic errors that will produce silent
wrong behaviour on realistic inputs, and a significant gap between the acceptance criteria in US074
and what the test suite actually covers. The duplicate-detection guard — the primary safety
mechanism preventing settings.py corruption — can be bypassed through multiple routes.

---

## CRITICAL (Blocks deployment)

### C1 — `write_config_block` has no atomic write — power loss or process kill corrupts `settings.py`

**File:** `rust/syntek-manifest/src/settings_writer.rs` lines 45–58

**Description:** `write_config_block` reads the file with `fs::read_to_string`, builds the new
content in memory, then calls `fs::write` to overwrite the original. There is no intermediate
temporary file and no `fsync`. If the process is killed between the `read` and the `write` (or if
`fs::write` returns an error mid-write — which is possible on a full disk), the file is either
partially written or left in an undefined state. On a full disk the partial-write scenario is
especially dangerous: `fs::write` internally opens the file with `O_TRUNC` before any bytes are
written, so a write failure leaves the file empty (zero bytes), erasing the developer's entire
`settings.py`.

The same risk applies to `append_installed_app` (lines 77–92) and
`ProviderWrapper::wrap_entry_point` (lines 73–83 of `provider_wrapper.rs`).

- **Impact:** Complete loss of the developer's `settings.py` if a disk-full condition or process
  interruption occurs during write. Silent corruption if partial bytes are flushed.
- **Reproduce:** Fill the filesystem to near-capacity, run the installer; `fs::write` will fail
  after truncating the original file, leaving it empty.

### C2 — `append_installed_app` uses raw `contains()` — any substring match silently skips the write

**File:** `rust/syntek-manifest/src/settings_writer.rs` line 83

**Description:** The duplicate guard for `INSTALLED_APPS` is:

```rust
if content.contains(app_label) {
    return Ok(());
}
```

`app_label` is an arbitrary string that comes from the manifest. The check is a plain substring
search over the entire file content. The following inputs all cause a false positive (the app is
never added even though it is not in `INSTALLED_APPS`):

1. `app_label = "syntek_auth"` — skipped if a comment says `# syntek_auth is required`.
2. `app_label = "auth"` — skipped because Django's own `django.contrib.auth` is present in every
   `settings.py`.
3. `app_label = "syntek"` — skipped if any other Syntek app is already installed.
4. `app_label = ""` — `"".contains("")` is always `true` in Rust, so an empty label is silently
   skipped every time. The app is never added to `INSTALLED_APPS`.

- **Impact:** Silent installation failure. The module's Django app is never registered. The
  developer sees no error and assumes the install succeeded. The application crashes at runtime with
  `AppRegistryNotReady` or missing-model errors.
- **Reproduce:** (a) Add a comment `# syntek_auth handles auth` to `settings.py`, then install
  `syntek-auth` — the app label is never appended. (b) Set `app_label = "auth"` in a manifest;
  install always silently no-ops.

---

## HIGH (Must fix before production)

### H1 — `content_has_block` can be fooled by the pattern appearing in a comment

**File:** `rust/syntek-manifest/src/duplicate_detector.rs` lines 71–75

**Description:** The detection pattern is a plain substring scan for `SYNTEK_KEY =`. A developer who
has commented out a previous config block:

```python
# SYNTEK_AUTH = {
#     'MFA_REQUIRED': True,
# }
```

will trigger the detector. The installer prints the "existing block" warning and refuses to write,
even though the key is not active. The developer must manually delete the comment or pass
confirmation. This is arguably annoying but defensible.

The inverse is the more dangerous case: a string value elsewhere in the file can contain the pattern
and cause a false positive:

```python
LOGGING = {
    'message': 'Set SYNTEK_AUTH = {} in settings',
}
```

This causes the detector to report an existing block when there is none, permanently blocking the
installer for that module (unless the developer knows to grep the file by hand).

- **Impact:** Installer permanently blocked for a module that has never been installed. Developer
  has no actionable error message pointing to the false-positive source.
- **Reproduce:** Add any string literal containing `SYNTEK_AUTH =` to `settings.py`; run the
  `syntek-auth` installer.

### H2 — `normalise_inline_toml` silently mangles TOML strings containing a closing quote followed by an identifier

**File:** `rust/syntek-manifest/src/parser.rs` lines 110–153

**Description:** The normaliser fires whenever it sees a closing `"` character followed (after
optional spaces) by something that looks like an identifier-then-`=`. This is applied
indiscriminately to the entire input, including string _values_. Consider:

```toml
snippet = "path('auth/', include('syntek_auth.urls')),"
label   = "true or false"
```

None of these trigger the normaliser because no identifier-`=` pattern follows a closing quote in
context. However the following _does_ trigger it:

```toml
label = "Enable feature x=1 type=custom"
```

After the inner `"`, the normaliser sees `type` then `=` and inserts a newline _inside the string
value_, corrupting the TOML to:

```toml
label = "Enable feature x=1
type=custom"
```

which is now invalid (bare newline inside a basic string). The second parse attempt then fails and
the error is reported as `TomlParse`, giving the author no indication that their label string was
the cause.

Additionally the normaliser does not track whether it is inside a TOML string. Any closing `"`
followed by `identifier =` anywhere in the input — including inside multi-line strings, table
headers, or array of tables entries — will cause a spurious newline insertion.

- **Impact:** Valid manifests with certain string values fail to parse with an opaque error. Module
  authors will not understand why their manifest is rejected.
- **Reproduce:** Set `label = "kind = optional"` in an `[[options]]` block; parsing fails.

### H3 — Provider name containing `<`, `>`, or `"` produces invalid TypeScript output

**File:** `rust/syntek-manifest/src/provider_wrapper.rs` lines 53–59, 98–110

**Description:** `build_jsx_wrapper` interpolates `p.name` directly into JSX tag syntax:

```rust
format!("<{name}>{acc}</{name}>", name = p.name)
```

`build_imports` interpolates both `p.name` and `p.import` directly into an import statement:

```rust
format!("import {{ {} }} from \"{}\";", p.name, p.import)
```

Neither field is validated or sanitised. A manifest with:

```toml
[[providers]]
name   = "Auth</script><script>alert(1)</script>"
import = "@syntek/ui-auth"
```

produces a usage stub containing literal script-injection text that is written to the developer's
entry file. While this is not a browser XSS (the output is a `.tsx` source file, not a served HTML
page), it still silently corrupts the generated source file in ways that are hard to debug.

More realistically, a provider name of `"Auth Provider"` (with a space, which is not a valid JSX
component identifier) produces syntactically invalid TypeScript that will fail at build time with no
indication that the manifest was the source of the problem.

- **Impact:** Invalid TypeScript written to the developer's entry file. Build fails with a compiler
  error that points to the generated file, not to the manifest.
- **Reproduce:** Set `name = "My Provider"` (space) in a `[[providers]]` block; the generated
  `<My Provider>` JSX is invalid TypeScript.

### H4 — `render_value` for `kind = "bool"` writes non-`true`/`false` values as raw unquoted Python

**File:** `rust/syntek-manifest/src/settings_writer.rs` lines 110–118

**Description:** The `bool` arm of `render_value` is:

```rust
"bool" => match value {
    "true" => "True".to_string(),
    "false" => "False".to_string(),
    other => other.to_string(),   // ← raw passthrough, unquoted
},
```

If a user passes `"True"` (capital T, which is how Python represents true), `"1"`, `"yes"`, or any
other truthy string, the value is written verbatim and unquoted into the Python dict:

```python
SYNTEK_AUTH = {
    'MFA_REQUIRED': True,    # user typed "True"  — happens to be valid Python
    'ENABLED': yes,          # user typed "yes"   — NameError at runtime
    'FLAG': 1,               # user typed "1"     — writes integer, not bool
}
```

The generated `settings.py` is syntactically invalid Python (or silently wrong) and Django fails to
start.

- **Impact:** Silent generation of invalid Python. Django fails to import `settings.py` at startup
  with a `NameError` pointing to the generated block.
- **Reproduce:** Set an option `default = "True"` (capital T) and run the installer; the block
  contains `'MFA_REQUIRED': True,` which happens to work, but `default = "yes"` produces a
  `NameError`.

### H5 — `write_config_block` does not check for a pre-existing block before writing

**File:** `rust/syntek-manifest/src/settings_writer.rs` lines 39–58

**Description:** `write_config_block` unconditionally appends the config block. The
`DuplicateDetector` exists as a separate struct and is never called inside `write_config_block`. The
caller is expected to call `DuplicateDetector::has_existing_block` before calling
`write_config_block`, but there is no enforcement. Any caller that omits the detector call —
including any future module binary that links against this crate — will silently write a second
`SYNTEK_AUTH = { ... }` block to `settings.py`. Django will raise an exception about duplicate
variable assignment on startup.

The acceptance criterion ("detects the existing block, warns the developer, and does not overwrite
without explicit confirmation") is a library-level responsibility but is not enforced at the API
boundary.

- **Impact:** A module binary that calls `write_config_block` without first calling the detector
  produces a `settings.py` with two `SYNTEK_AUTH = { ... }` blocks. Python's `settings.py` is not a
  dict — later assignments silently override earlier ones, meaning partially-correct settings from
  the first install are lost without warning.
- **Reproduce:** Call `SettingsWriter::write_config_block` on a `settings.py` that already contains
  `SYNTEK_AUTH = { ... }`.

### H6 — `wrap_entry_point` unconditionally overwrites the entry file with no backup

**File:** `rust/syntek-manifest/src/provider_wrapper.rs` lines 73–84

**Description:** `wrap_entry_point` calls `fs::write`, which opens the file with `O_TRUNC` and
overwrites all existing content. The acceptance criterion says "a minimal usage stub is written to
the declared entry file", which implies the file may already contain developer-authored code
(routing logic, metadata exports, etc.). That code is silently discarded with no warning and no
backup. There is no check for whether the file already contains provider wrapping, no confirmation
prompt, and no rollback path.

- **Impact:** Permanent, silent loss of developer-authored content in `app/layout.tsx` (or whatever
  `entry_point` declares). The content is replaced with the generated stub. If the developer is not
  watching git diff, this data loss may not be noticed until a later session.
- **Reproduce:** Create `app/layout.tsx` with custom routing code; run the installer; all custom
  code is gone.

---

## MEDIUM (Should fix)

### M1 — `settings_key` transforms any Unicode input including non-ASCII hyphens

**File:** `rust/syntek-manifest/src/duplicate_detector.rs` lines 55–57

**Description:** `settings_key` calls `replace('-', "_").to_uppercase()`. The `id` field is read
directly from the TOML manifest without validation. A module ID like `"syntek‑auth"` (using a
Unicode non-breaking hyphen U+2011 rather than an ASCII hyphen U+002D) would not have its hyphen
replaced, producing `"SYNTEK‑AUTH"` — an invalid Python identifier. The generated settings key would
cause a `SyntaxError` in Django's `settings.py`. There is no validation that `id` is a valid module
identifier.

- **Impact:** Generated `settings.py` contains a syntactically invalid key. Django fails to start.
- **Reproduce:** Use a non-ASCII hyphen in the manifest `id` field.

### M2 — `step_header` uses `.chars().count()` — multi-byte characters in labels produce misaligned output

**File:** `rust/syntek-manifest/src/post_install.rs` lines 70–76

**Description:** The header padding calculation uses:

```rust
let remaining = SEPARATOR_WIDTH.saturating_sub(prefix.chars().count());
```

`chars().count()` counts Unicode scalar values (code points), not display columns. For labels
containing CJK characters, emoji, or other wide characters (e.g. `"安装 URL patterns"`), each wide
character occupies two terminal columns but counts as one in `chars().count()`. The header line will
appear shorter than `SEPARATOR_WIDTH` columns in the terminal, breaking the visual alignment with
the footer line. This is a display issue, not a correctness issue, but it undermines the "formatted
copy-paste snippet" goal of the acceptance criterion.

- **Impact:** Visually misaligned output in any terminal for labels containing wide Unicode
  characters.
- **Reproduce:** Create a `PostInstallStep` with a CJK character in the `label` field.

### M3 — `build_config_block` silently omits settings with no resolved value and no default

**File:** `rust/syntek-manifest/src/settings_writer.rs` lines 143–152

**Description:** When a setting has no entry in `values` and no `default`, it is silently skipped:

```rust
if let Some(v) = value {
    lines.push(Self::render_value(&setting.key, &setting.kind, v));
}
```

A manifest that declares a required setting (e.g. `STRIPE_SECRET_KEY`) will produce a `settings.py`
block that simply omits that key. The developer has no indication that a required configuration
value is missing. Django will fail at runtime with a `KeyError` when the module code tries to read
`settings.SYNTEK_PAYMENTS['STRIPE_SECRET_KEY']`.

- **Impact:** Silently incomplete `settings.py` block. Runtime failure with no build-time
  indication.
- **Reproduce:** Declare a setting with no `default` and do not include it in the `values` map; the
  generated block omits the key entirely.

### M4 — `render_value` for `kind = "int"` does not validate that the value is numeric

**File:** `rust/syntek-manifest/src/settings_writer.rs` lines 115–116

**Description:** For `kind = "int"`, the value is written directly without any numeric validation:

```rust
"int" => value.to_string(),
```

If the user types `"1800s"` or `"thirty"` at an interactive prompt, the generated Python is:

```python
'SESSION_TIMEOUT': 1800s,
```

which is a `SyntaxError`. There is no guard at the prompt layer or the render layer.

- **Impact:** Invalid Python written to `settings.py`.
- **Reproduce:** Pass a non-numeric string as the value for a setting with `kind = "int"`.

### M5 — `render_value` for `kind = "str"` does not escape single quotes in the value

**File:** `rust/syntek-manifest/src/settings_writer.rs` lines 117–118

**Description:** String values are rendered as:

```rust
_ => format!("'{value}'"),
```

If the value contains a single quote (e.g. `"O'Brien"` or `env('SECRET')`), the generated Python is:

```python
'API_OWNER': 'O'Brien',
```

which is a `SyntaxError`. The test at line 114 of `settings_writer_tests.rs` actually uses
`env('SYNTEK_API_KEY')` as a test value, which contains single quotes — if that test checks the
exact output, it would catch this, but the test only checks for the presence of `'API_KEY'` or `"`
in the output, not the correctness of the full line.

- **Impact:** Syntactically invalid Python in `settings.py` whenever a string value contains a
  single quote character.
- **Reproduce:** Set any string option default to `"env('MY_SECRET')"` and run the installer.

### M6 — `append_installed_app` writes the label outside `INSTALLED_APPS` list, breaking Django

**File:** `rust/syntek-manifest/src/settings_writer.rs` lines 87–88

**Description:** The implementation appends the label at the end of the file:

```rust
let updated = format!("{content}\n# Added by syntek-manifest\n'{app_label}',\n");
```

This writes the app label as a bare top-level string literal outside any list structure, not inside
the `INSTALLED_APPS = [...]` list. Django reads `INSTALLED_APPS` as a Python list; a bare string
literal at module level is not parsed as part of that list. Django will not register the app.

Valid Django `settings.py` requires the label to be inserted _inside_ the `INSTALLED_APPS` list:

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'syntek_auth',   # ← must be here
]
```

Not as a trailing dangling string literal after the closing `]`.

- **Impact:** The module's Django app is silently not registered. All model imports and URL routing
  depending on that app fail at runtime.
- **Reproduce:** Run `append_installed_app` on any real `settings.py`; check that `INSTALLED_APPS`
  is a list — the label will be appended after the file, not inside the list.

---

## LOW (Consider fixing)

### L1 — `ManifestError` derives `PartialEq` but `Io` wraps an OS `message: String` — fragile test equality

**File:** `rust/syntek-manifest/src/error.rs` lines 6–31

**Description:** The `Io` variant holds `path: String` and `message: String`. The `message` comes
from `e.to_string()` where `e` is a `std::io::Error`. The OS error message is platform-dependent
(Linux vs macOS) and can differ by kernel version. Tests that use
`assert_eq!(err, ManifestError::Io { path: ..., message: ... })` will be brittle across platforms.
The current tests use `matches!(result, Err(ManifestError::Io { .. }))` which is correct, but the
`PartialEq` derive invites future authors to write fragile equality assertions.

### L2 — `build_jsx_wrapper` with empty providers returns `"{children}"` including the surrounding quotes

**File:** `rust/syntek-manifest/src/provider_wrapper.rs` lines 53–59

**Description:** When `providers` is empty, `build_jsx_wrapper` returns `"{children}"` (the initial
`inner` value). The docstring says `An empty provider list returns "{children}"`. However the
returned string includes the outer double-quote characters, making it `"{children}"` not
`{children}`. When embedded in the usage stub:

```tsx
return "{children}";
```

This returns a string literal `"{children}"`, not the `children` prop. The component renders the
literal text `{children}` instead of its children. This is a zero-provider edge case but the
returned string is semantically wrong TypeScript.

### L3 — Empty string `id` or `version` passes validation

**File:** `rust/syntek-manifest/src/parser.rs` lines 68–78

**Description:** The validator checks only that `id` and `version` are `Some(_)`, not that they are
non-empty strings. `id = ""` and `version = ""` both pass validation. An empty `id` causes
`DuplicateDetector::settings_key("")` to return `""`, and `build_config_block` produces the Python
fragment `= {` — a syntax error in `settings.py`.

### L4 — `render_all` joins steps with `"\n"` — creates a double blank line between footer and header

**File:** `rust/syntek-manifest/src/post_install.rs` lines 56–58

**Description:** `render_step` already ends with a trailing `\n`. Joining with `"\n"` produces
`footer\n\nheader` — two newlines, meaning a blank line separates the steps. This is cosmetic but
creates inconsistent spacing: the label-to-snippet gap within a step is single-spaced, while the
between-step gap is double-spaced.

### L5 — No validation that `version` conforms to SemVer or any recognised format

**File:** `rust/syntek-manifest/src/parser.rs` lines 72–75

**Description:** `version` is accepted as any non-empty string. A manifest with `version = "potato"`
parses successfully. While the library itself does not use the version field, downstream tooling
(the `syntek add` CLI, the Forgejo registry) will likely require a valid SemVer string.

### L6 — `normalise_inline_toml` allocates a `Vec<char>` of the full input — no size limit

**File:** `rust/syntek-manifest/src/parser.rs` lines 112–113

**Description:** The normaliser converts the full input to `Vec<char>` before iteration. A
pathologically large manifest file (e.g. an accidentally included binary blob) will allocate a
`Vec<char>` proportional to the input size. There is no file size guard before calling
`ManifestParser::parse`. For a crate installed as a library in a CLI binary this is unlikely to be
exploited in practice, but it is worth noting.

---

## Missing Test Coverage — Acceptance Criteria with No Tests

The following acceptance criteria from `docs/STORIES/US074.md` have no corresponding test:

### MC1 — Interactive prompt actually collects user input (AC2)

**Criterion:** "it presents an interactive prompt for each install option declared in the manifest"

The `prompter_tests.rs` file only tests `prompt_labels`, `prompt_count`, and `apply_defaults`. There
is no test for the actual interactive prompt flow — no test exercises reading from stdin, handling
invalid input, handling Ctrl-C, or confirming that the prompter falls back to defaults in CI mode.
`apply_defaults` is tested but the mechanism that _detects_ CI / non-interactive mode is entirely
absent from both implementation and tests.

### MC2 — Developer is warned and asked for confirmation before overwriting (AC6)

**Criterion:** "it detects the existing block, warns the developer, and does not overwrite without
explicit confirmation"

`duplicate_detector_tests.rs` verifies that `content_has_block` returns `true` for an existing
block, and one integration test documents that the installer "must not overwrite silently". However:

- There is no test that the installer actually emits a human-readable warning message to
  stdout/stderr.
- There is no test that without confirmation the write is blocked.
- There is no test that with confirmation the write proceeds.
- The confirmation mechanism does not exist in any source file in the crate.

### MC3 — Post-install steps are printed to stdout, never written to files (AC5)

**Criterion:** "they are printed as formatted copy-paste snippets — never written to files
automatically"

`post_install_tests.rs` tests `render_step` and `render_all` return strings. There is no test that
`PostInstallPrinter` actually writes to stdout (via `println!` or equivalent), and no test that it
never writes to the filesystem. The acceptance criterion's "never written to files automatically"
guarantee is untested.

### MC4 — Frontend provider wrapping preserves existing entry file content (AC4)

**Criterion:** "the project's app root is wrapped with required providers and a minimal usage stub
is written to the declared entry file"

`wrap_entry_point` unconditionally overwrites the file (see H6 above). No test verifies that
existing file content is preserved, merged, or backed up. The test at line 165 of
`provider_wrapper_tests.rs` verifies only that the file contains `AuthProvider` after wrapping — it
passes even if the original content is completely discarded.

### MC5 — `INSTALLED_APPS` entry is inserted _inside_ the list, not appended to the file (AC3)

**Criterion:** "the app is added to `INSTALLED_APPS` with no duplicate entries"

No test verifies that the app label ends up syntactically inside the `INSTALLED_APPS` list.
`append_installed_app_adds_app_when_not_present` only checks `content.contains("syntek_auth")`,
which passes even when the label is written as a dangling string literal outside the list (see M6).

### MC6 — Settings block is written with correct Python dict syntax end-to-end

**Criterion:** AC3 requires the `SYNTEK_<MODULE>` config block to be correct and complete.

No test parses the generated Python or validates its syntax. Tests check only for substring presence
of keys and values. Invalid Python (e.g. from unescaped quotes — see M5, or from passthrough of
invalid bool values — see H4) passes all existing tests.

### MC7 — Error recovery: what happens if `settings.py` does not exist

No test exercises the error path when `settings_path` points to a non-existent file for
`write_config_block` or `append_installed_app`.
`has_existing_block_returns_io_error_for_nonexistent_file` covers the detector, but the writer
functions are untested for the missing-file case.

---

## Handoff Recommendations

- Run `/syntek-dev-suite:backend` to implement atomic file writes (write to temp file, then
  `rename`) for `write_config_block`, `append_installed_app`, and `wrap_entry_point`.
- Run `/syntek-dev-suite:backend` to fix `append_installed_app` to parse and insert into the
  `INSTALLED_APPS` list rather than appending a bare string at end of file (M6 — this is the most
  impactful functional bug after the atomic write issue).
- Run `/syntek-dev-suite:backend` to add input validation for `id`, `version`, provider `name`, and
  `app_label` values before any file I/O.
- Run `/syntek-dev-suite:test-writer` to add tests for MC1 through MC7 and for the bug scenarios
  described in H4, H5, H6, M3, M5, and M6.
- Run `/syntek-dev-suite:debug` to investigate whether the `normalise_inline_toml` function is truly
  needed in production (real manifests are multi-line) — if it exists only for test convenience it
  should be removed from production code.
