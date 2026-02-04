# Syntek GraphQL Compliance

GDPR compliance and legal document management operations for Syntek GraphQL APIs.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration Reference](#configuration-reference)
- [Usage Examples](#usage-examples)
- [API Reference](#api-reference)
- [GDPR Compliance](#gdpr-compliance)
- [Security Considerations](#security-considerations)
- [Development](#development)
- [Testing](#testing)
- [License](#license)

---

## Overview

**syntek-graphql-compliance** provides GraphQL operations for GDPR compliance and legal document management. It implements GDPR Articles 15, 17, and 18, and provides comprehensive legal document versioning and acceptance tracking.

This package depends on `syntek-graphql-core` for security and error handling.

## Features

### GDPR Operations

- **Article 15 (Right of Access)**: Data export requests in JSON/CSV format
- **Article 17 (Right to Erasure)**: Account deletion with confirmation workflow
- **Article 18 (Right to Restriction of Processing)**: Processing restriction management
- **Consent Management**: Granular consent tracking for different processing types

### Legal Document Management

- **Document Versioning**: Semantic versioning with change summaries
- **Acceptance Tracking**: IP address, user agent, timestamp, and method recording
- **Multi-Document Registration**: Accept T&Cs + Privacy Policy together
- **Compliance Checking**: Query user's acceptance status and pending documents
- **Admin Operations**: Create new document versions (staff only)

### Security

- **Authentication Required**: All mutations and queries require valid JWT
- **IP Address Encryption**: Client IPs encrypted before storage
- **Audit Logging**: All GDPR operations logged via syntek-audit
- **Rate Limiting**: Data export requests limited to one per 24 hours
- **Confirmation Workflow**: Account deletion requires email confirmation

## Installation

### Using uv (Recommended)

```bash
uv pip install syntek-graphql-compliance
```

### Using pip

```bash
pip install syntek-graphql-compliance
```

### From Source

```bash
git clone https://github.com/syntek/syntek-modules.git
cd syntek-modules/graphql/syntek-graphql-compliance
uv pip install -e .
```

## Quick Start

### 1. Install Dependencies

```bash
uv pip install syntek-graphql-core syntek-graphql-compliance
```

### 2. Add to Django Settings

```python
INSTALLED_APPS = [
    # ... other apps
    'syntek_graphql_core',
    'syntek_compliance',  # Backend compliance module
    'syntek_audit',       # Backend audit module
    'strawberry.django',
]
```

### 3. Use in Your Schema

```python
import strawberry
from syntek_graphql_compliance.mutations import GDPRMutations, LegalMutations
from syntek_graphql_compliance.queries import GDPRQuery, LegalQuery

@strawberry.type
class Query(GDPRQuery, LegalQuery):
    pass

@strawberry.type
class Mutation(GDPRMutations, LegalMutations):
    pass

schema = strawberry.Schema(query=Query, mutation=Mutation)
```

### 4. Or Use Standalone Schema

```python
from syntek_graphql_compliance.schema import create_compliance_schema

schema = create_compliance_schema()
```

## Configuration Reference

### Backend Settings

Configure the backend compliance module in `settings.py`:

```python
# Compliance settings
COMPLIANCE = {
    'DATA_EXPORT': {
        'RATE_LIMIT_HOURS': 24,
        'EXPIRY_HOURS': 24,
        'FORMATS': ['json', 'csv'],
    },
    'ACCOUNT_DELETION': {
        'CONFIRMATION_TIMEOUT_HOURS': 24,
        'DATA_RETENTION_DAYS': 30,  # For legal/regulatory requirements
    },
    'PROCESSING_RESTRICTION': {
        'ALLOWED_PROCESSING': ['essential', 'legal_obligation'],
    },
}

# Celery tasks for async data export processing
CELERY_BEAT_SCHEDULE = {
    'process-data-exports': {
        'task': 'apps.core.tasks.process_data_export_task',
        'schedule': timedelta(minutes=5),
    },
}
```

## Usage Examples

### Data Export Request

```graphql
mutation RequestDataExport {
  requestDataExport(input: { format: JSON }) {
    success
    message
    exportRequest {
      id
      status
      format
      createdAt
      expiresAt
    }
  }
}
```

### Check Export Status

```graphql
query MyDataExports {
  myDataExports(limit: 10) {
    id
    status
    format
    downloadUrl
    expiresAt
    fileSize
    recordCounts
  }
}
```

### Account Deletion Request

```graphql
mutation RequestAccountDeletion {
  requestAccountDeletion(input: { reason: "No longer need the service" }) {
    success
    message
    deletionRequest {
      id
      status
      reason
      createdAt
    }
  }
}
```

### Confirm Account Deletion

```graphql
mutation ConfirmAccountDeletion {
  confirmAccountDeletion(
    input: {
      token: "confirmation-token-from-email"
      password: "user-password"
    }
  ) {
    success
    message
  }
}
```

### Processing Restriction

```graphql
mutation RestrictProcessing {
  updateProcessingRestriction(
    input: {
      restrict: true
      reason: "Contesting data accuracy"
    }
  ) {
    success
    message
    restriction {
      processingRestricted
      restrictionReason
      restrictedAt
      allowedProcessing
      restrictedProcessing
    }
  }
}
```

### Consent Management

```graphql
mutation UpdateConsent {
  updateConsent(
    input: {
      consentType: ANALYTICS
      granted: false
    }
  ) {
    success
    message
    consent {
      id
      consentType
      granted
      grantedAt
    }
  }
}

query MyConsents {
  myConsents {
    consentType
    granted
    version
    grantedAt
    withdrawnAt
  }
}
```

### Legal Documents

```graphql
query RegistrationRequirements {
  registrationRequirements {
    termsAndConditions {
      id
      version
      title
      contentUrl
      effectiveDate
    }
    privacyPolicy {
      id
      version
      title
      contentUrl
      effectiveDate
    }
    isComplete
    missingDocuments
  }
}
```

### Accept Legal Documents

```graphql
mutation AcceptLegalDocument {
  acceptLegalDocument(
    input: {
      documentId: "uuid"
      acceptanceMethod: CHECKBOX
    }
  ) {
    success
    acceptance {
      id
      document {
        documentType
        version
        title
      }
      acceptedAt
      acceptanceMethod
    }
    error
  }
}
```

### Compliance Status

```graphql
query MyComplianceStatus {
  myComplianceStatus {
    allAccepted
    requiresActionBeforeLogin
    pendingDocuments {
      documentType
      version
      title
      requiresReAcceptance
    }
    acceptedDocuments {
      documentType
      version
      title
    }
  }
}
```

## API Reference

### GDPR Mutations

| Mutation | Description | GDPR Article |
|----------|-------------|--------------|
| `requestDataExport` | Request data export | Article 15 |
| `requestAccountDeletion` | Request account deletion | Article 17 |
| `confirmAccountDeletion` | Confirm deletion via token | Article 17 |
| `cancelAccountDeletion` | Cancel pending deletion | Article 17 |
| `updateProcessingRestriction` | Restrict/unrestrict processing | Article 18 |
| `updateConsent` | Grant/withdraw consent | Article 7 |

### GDPR Queries

| Query | Description | Returns |
|-------|-------------|---------|
| `myDataExports` | List export requests | `[DataExportRequestType]` |
| `myDataExport(id)` | Get specific export | `DataExportRequestType` |
| `myDeletionRequests` | List deletion requests | `[AccountDeletionRequestType]` |
| `myProcessingRestriction` | Get restriction status | `ProcessingRestrictionType` |
| `myConsents` | List consent records | `[ConsentRecordType]` |

### Legal Mutations

| Mutation | Description | Access Level |
|----------|-------------|--------------|
| `acceptLegalDocument` | Accept a document | Authenticated |
| `acceptMultipleLegalDocuments` | Accept multiple docs | Authenticated |
| `createLegalDocument` | Create new version | Staff only |

### Legal Queries

| Query | Description | Returns |
|-------|-------------|---------|
| `registrationRequirements` | Get required docs for signup | `RegistrationRequirementsType` |
| `activeLegalDocuments` | List all active documents | `[LegalDocumentType]` |
| `legalDocument(id)` | Get specific document | `LegalDocumentType` |
| `legalDocumentByType(type)` | Get active doc by type | `LegalDocumentType` |
| `legalDocumentHistory(type)` | Get version history | `[LegalDocumentType]` |
| `myComplianceStatus` | Get user's compliance status | `ComplianceStatusType` |
| `myLegalAcceptances` | Get acceptance history | `[LegalAcceptanceType]` |

### Types

#### GDPR Types

- `DataExportRequestType`: Export request with status, format, URL, expiry
- `AccountDeletionRequestType`: Deletion request with status, reason, retention info
- `ConsentRecordType`: Consent record with type, granted status, timestamps
- `ProcessingRestrictionType`: Restriction status with allowed/restricted operations

#### Legal Types

- `LegalDocumentType`: Document version with type, version, title, URL, effective date
- `LegalAcceptanceType`: Acceptance record with document, method, timestamp
- `ComplianceStatusType`: User's compliance status with pending/accepted docs
- `RegistrationRequirementsType`: Documents required for registration

#### Enums

```python
# Export formats
ExportFormat: JSON | CSV

# Export status
ExportStatus: PENDING | PROCESSING | COMPLETED | FAILED | EXPIRED

# Deletion status
DeletionStatus: PENDING | CONFIRMED | PROCESSING | COMPLETED | CANCELLED

# Consent types
ConsentType: ESSENTIAL | FUNCTIONAL | ANALYTICS | MARKETING

# Document types
LegalDocumentKind: TERMS_AND_CONDITIONS | PRIVACY_POLICY | COOKIE_POLICY |
                   ACCEPTABLE_USE | DATA_PROCESSING_AGREEMENT |
                   SUB_PROCESSOR_LIST | SLA

# Acceptance methods
AcceptanceMethod: CHECKBOX | CLICK_WRAP | BROWSE_WRAP | SIGNED | API
```

## GDPR Compliance

This module implements key GDPR requirements:

### Article 15: Right of Access

Users can request a complete export of their personal data in JSON or CSV format. Exports are:
- Rate limited to one per 24 hours
- Processed asynchronously via Celery
- Available for download for 24 hours
- Include record counts per data category

### Article 17: Right to Erasure

Users can request account deletion with:
- Email confirmation required (24-hour window)
- Password verification on confirmation
- Audit trail of deletion request and completion
- Retention of legally required data (configurable)
- Irreversible deletion after confirmation

### Article 18: Right to Restriction of Processing

Users can restrict processing of their data:
- Reason required when restricting
- Essential processing always allowed
- Clear indication of allowed vs restricted operations
- Reversible restriction

### Article 7: Consent

Granular consent management:
- Essential consent cannot be withdrawn
- Separate tracking for functional, analytics, marketing
- Timestamped consent grants and withdrawals
- Version tracking
- IP address and user agent recording (encrypted)

### Legal Document Management

GDPR Article 7(1) requires demonstrating consent was given:
- IP address and timestamp recorded
- User agent captured
- Acceptance method tracked
- Document version captured
- Immutable audit trail

## Security Considerations

### Authentication

All mutations and queries require authentication via JWT token. Use the `syntek-graphql-core` middleware:

```python
from syntek_graphql_core.middleware import JWTAuthMiddleware

schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    extensions=[JWTAuthMiddleware],
)
```

### IP Address Encryption

Client IP addresses are encrypted before storage using the Rust encryption layer:

```python
from apps.core.utils.encryption import IPEncryption

encrypted_ip = IPEncryption.encrypt_ip(ip_address)
```

### Rate Limiting

Data export requests are rate limited to prevent abuse:
- Maximum one export per 24 hours per user
- Enforced at the service layer
- Clear error messages when limit exceeded

### Account Deletion Confirmation

Account deletion requires email confirmation to prevent unauthorized deletion:
- Confirmation token sent via email
- 24-hour expiry on confirmation token
- Password verification required
- Audit logging of all steps

### Data Retention

Some data must be retained for legal/regulatory compliance:
- Configurable retention periods
- Clear indication of what data is retained
- Returned in `AccountDeletionRequestType.data_retained`

### Audit Logging

All GDPR operations are automatically logged via `syntek-audit`:
- User ID
- Action performed
- Timestamp
- IP address (encrypted)
- Request metadata

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/syntek/syntek-modules.git
cd syntek-modules/graphql/syntek-graphql-compliance

# Install development dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check .

# Format code
black .

# Type checking
mypy syntek_graphql_compliance
```

### Project Structure

```
syntek-graphql-compliance/
├── syntek_graphql_compliance/
│   ├── __init__.py
│   ├── schema.py              # Standalone schema
│   ├── mutations/
│   │   ├── __init__.py
│   │   ├── gdpr.py            # GDPR mutations
│   │   └── legal.py           # Legal document mutations
│   ├── queries/
│   │   ├── __init__.py
│   │   ├── gdpr.py            # GDPR queries
│   │   └── legal.py           # Legal document queries
│   └── types/
│       ├── __init__.py
│       ├── gdpr.py            # GDPR types
│       └── legal.py           # Legal document types
├── tests/
│   ├── test_gdpr_mutations.py
│   ├── test_legal_mutations.py
│   ├── test_gdpr_queries.py
│   └── test_legal_queries.py
├── README.md
├── LICENSE
├── pyproject.toml
└── CHANGELOG.md
```

## Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=syntek_graphql_compliance --cov-report=html

# Specific test file
pytest tests/test_gdpr_mutations.py

# With verbose output
pytest -v
```

## License

MIT License - see LICENSE file for details.

## Related Modules

- `syntek-graphql-core` - Core security and utilities (required)
- `syntek-compliance` - Backend GDPR and legal document models/services (required)
- `syntek-audit` - Backend audit logging (required)
- `syntek-graphql-auth` - Authentication and user management
- `syntek-graphql-audit` - Audit log queries

## Support

- Documentation: https://docs.syntek.com/graphql-compliance
- Issues: https://github.com/syntek/syntek-modules/issues
- Email: support@syntek.com
