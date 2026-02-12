# Changelog

All notable changes to syntek-graphql-audit will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-02-04

### Added

- Initial release of syntek-graphql-audit package
- GraphQL queries for audit logging:
  - `myAuditLogs` - User-specific audit logs with filtering
  - `organisationAuditLogs` - Organisation-wide audit logs (with permission checks)
  - `mySessions` - Active session management
  - `availableAuditActions` - List of audit action types
- GraphQL types:
  - `AuditLogType` - Audit log entries with encrypted IP addresses
  - `SessionTokenType` - Session information
  - `AuditLogConnection` - Paginated audit log results
  - `SessionManagementInfo` - Session management status
  - `AuditLogFilterInput` - Filter options for audit queries
  - `PaginationInput` - Pagination parameters
- Organisation boundary enforcement
- Permission-based access control for organisation logs
- Pagination support (max 100 items per page)
- Filtering by action, user, and date range
- Session management information with limits

### Security

- Organisation boundaries strictly enforced
- Permission checks for organisation-wide logs
- IP addresses remain encrypted in audit log responses
- Session token hashes not exposed via GraphQL
- Authenticated users only (IsAuthenticated permission)
- Pagination limits prevent data exfiltration

### Dependencies

- Requires syntek-graphql-core>=1.0.0 for core functionality
- Integrates with syntek-audit for audit log models
- Integrates with syntek-sessions for session management

## [Unreleased]

### Planned

- Export audit logs to CSV/JSON
- Advanced filtering (by IP range, action category)
- Audit log retention policies
- Real-time audit log subscriptions via GraphQL
- Audit log statistics and analytics queries
