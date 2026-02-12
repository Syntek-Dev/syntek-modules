# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-02-04

### Added

- Initial release of syntek-graphql-auth
- User registration with email verification
- Login/logout with JWT tokens (access + refresh)
- Password reset with secure token hashing
- Password change with session revocation
- Email verification enforcement
- CAPTCHA protection (Google reCAPTCHA v3)
- Two-factor authentication (TOTP)
  - Multiple TOTP devices per user
  - QR code generation
  - Backup codes with secure hashing
  - Secret encryption at rest
  - Time window tolerance (±1 window)
- Session management
  - Concurrent session limiting (max 5)
  - Session revocation (individual or all)
  - Device fingerprinting
  - Refresh token rotation with replay detection
- GDPR compliance
  - Data export (Article 15)
  - Account deletion (Article 17)
  - Processing restriction (Article 18)
  - Consent management
  - Legal document acceptance tracking
- Security features
  - Query depth limiting
  - Query complexity analysis
  - Rate limiting
  - CSRF protection
  - Introspection disabled in production
  - Organisation boundary enforcement
  - Comprehensive audit logging

### Security

- All passwords hashed with Argon2
- TOTP secrets encrypted at rest
- JWT tokens signed with RS256
- Refresh token rotation with replay detection
- Password reset tokens hashed with SHA-256
- Backup codes hashed with Argon2
- Rate limiting on all authentication endpoints
- CAPTCHA protection on registration and login
- Organisation-based data isolation

[1.0.0]: https://github.com/syntek/syntek-modules/releases/tag/graphql-v1.0.0
