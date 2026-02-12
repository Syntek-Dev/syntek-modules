# Syntek Legal - Legal Document Management

## Overview

Syntek Legal provides comprehensive legal document management including Terms of Service, Privacy Policy, and Data Processing Agreements with versioning, acceptance tracking, and requirement enforcement.

## Features

- **Document Versioning**: Track multiple versions of legal documents
- **Acceptance Tracking**: Record when users accept each document version
- **Document Types**: Terms of Service, Privacy Policy, DPA, Cookie Policy
- **Required Documents**: Enforce acceptance of specific documents
- **Active/Inactive Status**: Control which document versions are shown
- **IP Address Logging**: Track acceptance IP for legal compliance
- **Audit Trail**: Full history of document acceptances

## Installation

```bash
uv pip install syntek-legal
```

## Configuration

Add to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    'syntek_authentication',  # Required dependency
    'syntek_legal',
]
```

Settings:

```python
SYNTEK_LEGAL = {
    'REQUIRE_ACCEPTANCE': True,
    'REQUIRED_DOCUMENTS': ['terms_of_service', 'privacy_policy'],
    'TRACK_IP_ADDRESS': True,
}
```

## Usage

### Create Legal Documents

```python
from syntek_legal.services.legal_document_service import LegalDocumentService

# Create Terms of Service
tos = LegalDocumentService.create_document(
    document_type='terms_of_service',
    version='1.0',
    content='Terms content...',
    effective_date='2024-01-01',
    is_required=True
)

# Create Privacy Policy
privacy = LegalDocumentService.create_document(
    document_type='privacy_policy',
    version='1.0',
    content='Privacy policy content...',
    effective_date='2024-01-01',
    is_required=True
)
```

### Record User Acceptance

```python
# User accepts documents during registration
LegalDocumentService.record_acceptance(
    user=user,
    document=tos,
    ip_address='192.168.1.1'
)

LegalDocumentService.record_acceptance(
    user=user,
    document=privacy,
    ip_address='192.168.1.1'
)
```

### Check Document Acceptance

```python
# Check if user has accepted required documents
has_accepted = LegalDocumentService.has_accepted_required_documents(user)

# Get documents user needs to accept
pending_docs = LegalDocumentService.get_pending_acceptances(user)

# Check specific document acceptance
has_tos = LegalDocumentService.has_accepted_document(user, 'terms_of_service')
```

### Update Documents

```python
# Publish new version of Terms of Service
new_tos = LegalDocumentService.create_document(
    document_type='terms_of_service',
    version='2.0',
    content='Updated terms...',
    effective_date='2024-06-01',
    is_required=True
)

# Deactivate old version
LegalDocumentService.deactivate_document(old_tos)
```

## API Reference

### Services

#### LegalDocumentService

- `create_document(document_type, version, content, effective_date, is_required)`: Create a new legal document version
- `get_active_document(document_type)`: Get currently active document of a type
- `get_all_active_documents()`: Get all active documents
- `deactivate_document(document)`: Mark a document as inactive
- `record_acceptance(user, document, ip_address)`: Record user acceptance
- `has_accepted_document(user, document_type)`: Check if user accepted a document
- `has_accepted_required_documents(user)`: Check if user accepted all required documents
- `get_pending_acceptances(user)`: Get documents user needs to accept
- `get_acceptance_history(user)`: Get user's full acceptance history

### Models

#### LegalDocument

- `document_type`: Type (terms_of_service, privacy_policy, dpa, cookie_policy)
- `version`: Version string (e.g., "1.0", "2.0")
- `content`: Full document text
- `effective_date`: When document becomes effective
- `is_required`: Whether acceptance is mandatory
- `is_active`: Whether this version is currently shown
- `created_at`: Document creation timestamp

#### LegalAcceptance

- `user`: ForeignKey to User
- `document`: ForeignKey to LegalDocument
- `accepted_at`: Timestamp of acceptance
- `ip_address`: IP address where acceptance occurred
- `user_agent`: Browser user agent string

## Testing

```bash
pytest tests/
```

## Security Considerations

- IP addresses are logged for legal compliance
- Acceptance records are immutable (no deletion)
- Document versions are preserved for audit trail
- Required documents enforced at authentication layer
- User agent strings captured for proof of acceptance

## Legal Compliance

This module helps you comply with:

- Terms of Service enforcement
- Privacy policy acceptance tracking
- GDPR Article 7 (consent conditions)
- Data Processing Agreement management
- Audit trail for legal disputes

## License

MIT
