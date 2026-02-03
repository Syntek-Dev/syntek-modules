# Syntek Rust Security Plugin Tools

This directory contains CLI tools for Rust security analysis, used by Claude Code's syntek-rust-security agents.

## Tools

### `cargo-metadata-tool`
Extracts Cargo.toml metadata and dependency information.

**Usage:**
```bash
cargo-metadata-tool [manifest-path]
```

**Output:**
```json
{
  "workspace_root": "/path/to/workspace",
  "packages": [
    {
      "name": "syntek-encryption",
      "version": "0.1.0",
      "edition": "2021",
      "rust_version": "1.92.0",
      "dependencies": [...]
    }
  ]
}
```

### `rustc-version-tool`
Detects installed Rust toolchain version and configuration.

**Usage:**
```bash
rustc-version-tool
```

**Output:**
```json
{
  "version": "1.92.0",
  "commit_hash": "...",
  "commit_date": "2024-01-15",
  "host": "x86_64-unknown-linux-gnu"
}
```

### `vuln-db-tool`
Manages RustSec vulnerability database and checks packages.

**Usage:**
```bash
# Fetch latest advisory database
vuln-db-tool fetch

# Check specific package
vuln-db-tool check <package-name> <version>
```

**Output:**
```json
{
  "package": "openssl",
  "version": "0.10.50",
  "vulnerabilities": [
    {
      "id": "RUSTSEC-2023-0001",
      "severity": "high",
      "description": "..."
    }
  ],
  "status": "vulnerable"
}
```

### `audit-tool`
Orchestrates cargo-audit security scanning.

**Usage:**
```bash
audit-tool [manifest-path]
```

**Output:**
```json
{
  "status": "success",
  "stdout": "...",
  "stderr": "...",
  "exit_code": 0
}
```

### `fuzzer-tool`
Manages fuzzing infrastructure setup.

**Usage:**
```bash
# Initialize fuzzing
fuzzer-tool init <project-path>

# Check fuzzing status
fuzzer-tool status <project-path>
```

**Output:**
```json
{
  "status": "initialized",
  "fuzz_directory": "/path/to/fuzz"
}
```

### `compliance-tool`
Generates compliance reports for security audits.

**Usage:**
```bash
compliance-tool <project-path>
```

**Output:**
```json
{
  "project_path": "/path/to/project",
  "compliance_checks": {
    "zeroize_dependency": true,
    "overflow_checks_enabled": true,
    "panic_abort_enabled": true
  },
  "security_metrics": {
    "unsafe_blocks": 5
  },
  "recommendations": [...]
}
```

## Building

```bash
# Build all tools
cargo build --release

# Build specific tool
cargo build --release --bin cargo-metadata-tool

# Install to system
cargo install --path .
```

## Development

```bash
# Run tests
cargo test

# Run a specific tool
cargo run --bin vuln-db-tool -- fetch
```

## Integration with Claude Code

These tools are automatically invoked by Claude Code security agents:

- `/vuln-scan` uses `vuln-db-tool` and `audit-tool`
- `/threat-model` uses `cargo-metadata-tool`
- `/crypto-review` uses `cargo-metadata-tool` and `compliance-tool`
- `/memory-audit` uses `compliance-tool`
- `/fuzz-setup` uses `fuzzer-tool`

## Dependencies

- `cargo_metadata` - Parse Cargo.toml files
- `reqwest` - HTTP client for RustSec database
- `serde_json` - JSON serialization
- `tokio` - Async runtime

## Security

All tools:
- Run read-only operations (no modifications)
- Output JSON for machine parsing
- Exit with non-zero code on errors
- Sanitize file paths before access

## License

MIT OR Apache-2.0
