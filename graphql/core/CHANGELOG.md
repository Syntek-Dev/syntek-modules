# Changelog

All notable changes to syntek-graphql-core will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-02-04

### Added

- Initial release of syntek-graphql-core package
- Core security components:
  - Standardized error codes and exceptions (errors.py)
  - Permission classes for access control (permissions.py)
  - Security extensions for query protection (security.py)
- Authentication middleware:
  - JWT token extraction and verification (middleware/auth.py)
- Utility functions:
  - Request context helpers (utils/context.py)
  - Type guards for authentication (utils/typing.py)
- Security extensions:
  - Query depth limiting (max 10 levels by default)
  - Query complexity analysis (max 1000 complexity by default)
  - Introspection control (disabled in production)
- Comprehensive error code system:
  - 26 predefined error codes across 6 categories
  - User-friendly error messages
  - Structured error responses
- Permission classes:
  - IsAuthenticated - Require authenticated user
  - HasPermission - Require specific Django permission
  - IsOrganisationOwner - Require organisation owner role
- Context utilities:
  - get_request - Extract Django request from GraphQL context
  - get_ip_address - Get client IP with proxy support
  - get_user_agent - Extract user agent string
  - get_authorization_header - Get Authorization header
  - get_bearer_token - Extract Bearer token
- Type utilities:
  - is_authenticated_user - Type guard for authenticated users
  - get_authenticated_user - Get authenticated user or None
  - require_authenticated_user - Get authenticated user or raise error

### Security

- Query depth limiting prevents deeply nested query attacks
- Query complexity analysis prevents expensive query DoS
- Introspection disabled by default in production
- JWT token authentication via middleware
- Organisation boundary enforcement in permission classes
- OWASP Top 10 compliant error handling

## [Unreleased]

### Planned

- Additional permission classes for fine-grained access control
- Custom error code registration API
- Performance metrics and logging integration
- Rate limiting integration with Redis
- GraphQL subscription security extensions
