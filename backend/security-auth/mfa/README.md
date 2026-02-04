# Syntek MFA - Multi-Factor Authentication

## Overview

Syntek MFA provides TOTP-based two-factor authentication with backup codes for Django applications. This module implements secure 2FA with device management, QR code generation, and recovery mechanisms.

## Features

- **TOTP 2FA**: Time-based One-Time Password authentication
- **Multi-Device Support**: Users can register multiple TOTP devices
- **Backup Codes**: One-time recovery codes for account access
- **QR Code Generation**: Easy device enrollment via QR codes
- **Encrypted Storage**: TOTP secrets encrypted at rest
- **Device Management**: Name, track, and remove trusted devices

## Installation

```bash
uv pip install syntek-mfa
```

## Configuration

Add to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    'syntek_authentication',  # Required dependency
    'syntek_mfa',
]
```

Settings:

```python
SYNTEK_MFA = {
    'TOTP_ISSUER': 'YourApp',
    'TOTP_PERIOD': 30,  # seconds
    'BACKUP_CODE_COUNT': 10,
    'REQUIRE_MFA': False,  # Optional: make MFA mandatory
}
```

## Usage

### Enable TOTP for a User

```python
from syntek_mfa.services.totp_service import TOTPService

# Generate QR code for user enrollment
qr_code, secret = TOTPService.enable_totp(user, device_name="My Phone")

# User scans QR code and verifies with a TOTP code
is_verified = TOTPService.verify_totp_setup(user, totp_code, secret)
```

### Verify TOTP During Login

```python
# After username/password authentication
is_valid = TOTPService.verify_totp(user, totp_code)
```

### Generate Backup Codes

```python
backup_codes = TOTPService.generate_backup_codes(user)
# Display these to the user for safekeeping
```

## API Reference

### Services

#### TOTPService

- `enable_totp(user, device_name)`: Initialize TOTP for a user
- `verify_totp(user, code)`: Verify a TOTP code
- `verify_totp_setup(user, code, secret)`: Verify initial TOTP setup
- `generate_backup_codes(user, count)`: Generate one-time backup codes
- `verify_backup_code(user, code)`: Use a backup code for authentication
- `list_devices(user)`: Get all TOTP devices for a user
- `remove_device(user, device_id)`: Remove a specific TOTP device

### Models

#### TOTPDevice

- `user`: ForeignKey to User
- `name`: Device name (e.g., "My Phone")
- `secret`: Encrypted TOTP secret
- `confirmed`: Whether device setup is complete
- `last_used`: Last successful authentication time

#### BackupCode

- `user`: ForeignKey to User
- `code`: Hashed backup code
- `used`: Whether code has been consumed
- `used_at`: When code was used

## Testing

```bash
pytest tests/
```

## Security Considerations

- TOTP secrets are encrypted using the Rust encryption layer
- Backup codes are hashed using Argon2
- Rate limiting should be applied to TOTP verification endpoints
- Failed TOTP attempts are logged for security monitoring

## License

MIT
