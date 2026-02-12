# Syntek Compliance Bundle

## Overview

The Syntek Compliance bundle provides GDPR and legal document management modules for Django applications.
These modules help you maintain regulatory compliance for privacy laws and legal requirements.

## Modules

### GDPR (`syntek-gdpr`)

- Data export (right to portability)
- Account deletion (right to erasure)
- Processing restrictions (right to restriction)
- Consent management
- Audit trail for all GDPR operations

### Legal (`syntek-legal`)

- Terms of Service management
- Privacy Policy versioning
- Data Processing Agreements (DPA)
- Document acceptance tracking
- Version control for legal documents

## Installation

Install individual modules:

```bash
# GDPR compliance
uv pip install syntek-gdpr

# Legal document management
uv pip install syntek-legal

# Or install both (when bundle is available)
uv pip install syntek-compliance
```

## Quick Start

```python
# settings.py
INSTALLED_APPS = [
    ...
    'syntek_authentication',  # Required
    'syntek_gdpr',
    'syntek_legal',
]
```

## Use Cases

- **GDPR Compliance**: EU/UK/Global data protection regulations
- **Privacy Law Compliance**: CCPA, LGPD, etc.
- **Legal Document Management**: Terms, Privacy Policy, DPA
- **User Rights**: Data export, deletion, consent management
- **Audit Requirements**: Complete audit trail for compliance

## Documentation

See individual module READMEs:

- [GDPR Module](./gdpr/README.md)
- [Legal Module](./legal/README.md)

## License

MIT
