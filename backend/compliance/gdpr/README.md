# Syntek GDPR - GDPR Compliance Module

## Overview

Syntek GDPR provides comprehensive GDPR compliance features including data export (right to portability), account deletion (right to erasure), processing restrictions, and consent management for Django applications.

## Features

- **Data Export**: Export all user data in machine-readable JSON format
- **Account Deletion**: Complete account erasure with grace period
- **Processing Restrictions**: Allow users to restrict data processing
- **Consent Management**: Track and manage user consent for data processing
- **Audit Trail**: Log all GDPR-related operations
- **Grace Period**: Configurable deletion grace period

## Installation

```bash
uv pip install syntek-gdpr
```

## Configuration

Add to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    'syntek_authentication',  # Required dependency
    'syntek_gdpr',
]
```

Settings:

```python
SYNTEK_GDPR = {
    'DELETION_GRACE_PERIOD_DAYS': 30,
    'DATA_EXPORT_FORMATS': ['json'],  # Future: 'csv', 'xml'
    'REQUIRE_CONSENT': True,
    'CONSENT_TYPES': ['marketing', 'analytics', 'third_party'],
}
```

## Usage

### Export User Data

```python
from syntek_gdpr.services.data_export_service import DataExportService

# Export all user data
export_data = DataExportService.export_user_data(user)
# Returns dict with all personal data
```

### Request Account Deletion

```python
from syntek_gdpr.services.account_deletion_service import AccountDeletionService

# Schedule account deletion (with grace period)
AccountDeletionService.request_deletion(user, reason="User request")

# Cancel deletion during grace period
AccountDeletionService.cancel_deletion(user)

# Immediately delete account (admin only)
AccountDeletionService.delete_immediately(user)
```

### Manage Processing Restrictions

```python
from syntek_gdpr.services.processing_restriction_service import ProcessingRestrictionService

# Restrict data processing
ProcessingRestrictionService.restrict_processing(user, scope="marketing")

# Lift restriction
ProcessingRestrictionService.lift_restriction(user, scope="marketing")

# Check if processing is restricted
is_restricted = ProcessingRestrictionService.is_restricted(user, scope="marketing")
```

### Manage Consent

```python
from syntek_gdpr.services.consent_service import ConsentService

# Record user consent
ConsentService.record_consent(
    user,
    consent_type="marketing",
    granted=True,
    purpose="Email newsletter"
)

# Check consent status
has_consent = ConsentService.has_consent(user, "marketing")

# Withdraw consent
ConsentService.withdraw_consent(user, "marketing")
```

## API Reference

### Services

#### DataExportService

- `export_user_data(user)`: Export all user data to JSON
- `get_related_data(user)`: Get all related model data for a user

#### AccountDeletionService

- `request_deletion(user, reason)`: Schedule account deletion
- `cancel_deletion(user)`: Cancel pending deletion
- `delete_immediately(user)`: Immediate deletion (no grace period)
- `process_pending_deletions()`: Process accounts past grace period

#### ProcessingRestrictionService

- `restrict_processing(user, scope)`: Restrict data processing
- `lift_restriction(user, scope)`: Remove processing restriction
- `is_restricted(user, scope)`: Check restriction status

#### ConsentService

- `record_consent(user, consent_type, granted, purpose)`: Record consent
- `has_consent(user, consent_type)`: Check if user has given consent
- `withdraw_consent(user, consent_type)`: Withdraw previously given consent
- `get_consent_history(user)`: Get full consent history

### Models

#### ConsentRecord

- `user`: ForeignKey to User
- `consent_type`: Type of consent (marketing, analytics, etc.)
- `granted`: Boolean indicating consent status
- `purpose`: Description of what data is used for
- `granted_at`: Timestamp when consent was given
- `withdrawn_at`: Timestamp when consent was withdrawn

## Testing

```bash
pytest tests/
```

## Security Considerations

- Account deletion is logged in audit trail
- Grace period prevents accidental deletions
- Data exports are sanitized and only include user's own data
- Processing restrictions are enforced at service layer
- Consent changes are logged with timestamps

## GDPR Compliance

This module helps you comply with:

- **Article 15**: Right of access (data export)
- **Article 16**: Right to rectification
- **Article 17**: Right to erasure (deletion)
- **Article 18**: Right to restriction of processing
- **Article 20**: Right to data portability (export)
- **Article 7**: Consent conditions

## License

MIT
