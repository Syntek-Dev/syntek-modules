# Changelog

All notable changes to `syntek-graphql-auth` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Preparing for modular architecture migration

---

## [2.0.0] - 2026-02-04

### Changed - BREAKING
- **Modular Architecture**: Split from monolithic `syntek-graphql-auth@1.x` into focused authentication module
- **Dependency Updates**: Now requires `syntek-graphql-core>=1.0.0` for shared functionality
- **Import Paths**: Core utilities moved to `syntek-graphql-core` package
  - Errors: `syntek_graphql_auth.errors` → `syntek_graphql_core.errors`
  - Permissions: `syntek_graphql_auth.permissions` → `syntek_graphql_core.permissions`
  - Security: `syntek_graphql_auth.security` → `syntek_graphql_core.security`
  - Middleware: `syntek_graphql_auth.middleware` → `syntek_graphql_core.middleware`
  - Utils: `syntek_graphql_auth.utils` → `syntek_graphql_core.utils`

### Added
- Comprehensive README with installation, configuration, and usage examples
- Type annotations throughout the codebase
- Enhanced documentation for all mutations and queries
- Support for email verification during registration
- Concurrent session limiting
- Token rotation on password change
- CAPTCHA protection support

### Removed
- Audit logging functionality (moved to `syntek-graphql-audit`)
- GDPR operations (moved to `syntek-graphql-compliance`)
- Legal document management (moved to `syntek-graphql-compliance`)
- Core error handling (moved to `syntek-graphql-core`)
- Permission classes (moved to `syntek-graphql-core`)
- Security extensions (moved to `syntek-graphql-core`)

### Migration Guide
See [MIGRATION_GUIDE.md](../../MIGRATION_GUIDE.md) for detailed migration instructions from v1.x to v2.0.

---

## [1.0.0] - 2025-12-15

### Added
- Initial monolithic release
- Authentication mutations (register, login, logout, password management)
- TOTP/2FA support with backup codes
- Session management
- User queries with organisation boundaries
- Audit logging integration
- GDPR compliance features
- Legal document management
- JWT authentication middleware
- Query depth and complexity limiting
- Introspection control

---

[Unreleased]: https://github.com/syntek/syntek-modules/compare/graphql-auth-v2.0.0...HEAD
[2.0.0]: https://github.com/syntek/syntek-modules/compare/graphql-auth-v1.0.0...graphql-auth-v2.0.0
[1.0.0]: https://github.com/syntek/syntek-modules/releases/tag/graphql-auth-v1.0.0
