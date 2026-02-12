# Changelog

All notable changes to `syntek-graphql-compliance` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-02-04

### Added

- Initial release of syntek-graphql-compliance
- GDPR Article 15 (Right of Access) data export operations
- GDPR Article 17 (Right to Erasure) account deletion operations
- GDPR Article 18 (Right to Restriction of Processing) operations
- Consent management for GDPR Article 7
- Legal document versioning and management
- Legal document acceptance tracking
- Compliance status queries
- Registration requirements queries
- IP address encryption for privacy
- Audit logging integration
- Rate limiting for data exports
- Email confirmation workflow for account deletion
- Support for JSON and CSV export formats
- Comprehensive documentation and examples

### Dependencies

- syntek-graphql-core>=1.0.0
- syntek-compliance>=1.0.0
- syntek-audit>=1.0.0
- strawberry-graphql>=0.291.0
- django>=6.0.2

## [Unreleased]

### Planned

- Additional export formats (XML, PDF)
- Scheduled data exports
- Bulk legal document operations
- Multi-tenancy support for legal documents
- Enhanced reporting for compliance officers
- GraphQL subscriptions for export status updates
