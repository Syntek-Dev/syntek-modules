# Data Retention Policy - Global Default

**Effective Date:** 01.01.2026
**Version:** 1.0
**Applies To:** All regions unless superseded by regional policy

## Overview

This document defines the data retention and deletion policies for the Syntek authentication system. Regional variants (EU, USA) may override these defaults based on local legal requirements.

## Data Categories and Retention Periods

### 1. User Account Data

| Data Type                        | Retention Period                              | Deletion Trigger                                              |
| -------------------------------- | --------------------------------------------- | ------------------------------------------------------------- |
| Email (encrypted)                | Active account + 30 days after deletion       | Permanent deletion after 30-day grace period                  |
| Phone number (encrypted)         | Active account + 30 days after deletion       | Permanent deletion after 30-day grace period                  |
| Email hash                       | Active account + 30 days after deletion       | Permanent deletion after 30-day grace period                  |
| Phone hash                       | Active account + 30 days after deletion       | Permanent deletion after 30-day grace period                  |
| Password hash                    | Active account + 30 days after deletion       | Permanent deletion after 30-day grace period                  |
| First name, Last name            | Active account + 30 days after deletion       | Permanent deletion after 30-day grace period                  |
| Email verification status        | Active account only                           | Deleted immediately upon account deletion                     |
| Two-factor authentication (TOTP) | Active account only                           | Deleted immediately upon account deletion                     |
| Backup codes                     | Active account only                           | Deleted immediately upon account deletion                     |
| Recovery keys                    | 1 year or until used (whichever comes first)  | Deleted upon expiry or use                                    |
| Username                         | Active account + 30 days after deletion       | Permanent deletion after 30-day grace period                  |
| Organisation membership          | Active account + 30 days after deletion       | Permanent deletion after 30-day grace period                  |

### 2. Authentication Logs

| Data Type              | Retention Period                                        | Deletion Trigger                       |
| ---------------------- | ------------------------------------------------------- | -------------------------------------- |
| Login attempts         | 90 days                                                 | Automatic deletion via table partition |
| IP tracking entries    | 90 days                                                 | Automatic deletion via table partition |
| Session security logs  | 90 days                                                 | Automatic deletion via table partition |
| Password reset tokens  | 24 hours or until used (whichever comes first)          | Automatic expiry                       |
| Email verification     | 24 hours or until used (whichever comes first)          | Automatic expiry                       |
| Phone verification     | 15 minutes or until used (whichever comes first)        | Automatic expiry                       |
| Failed login logs      | 90 days                                                 | Automatic deletion via table partition |
| Successful login logs  | 90 days                                                 | Automatic deletion via table partition |

### 3. Security Data

| Data Type              | Retention Period                                        | Deletion Trigger                       |
| ---------------------- | ------------------------------------------------------- | -------------------------------------- |
| IP whitelist entries   | Until manually removed or expired                       | Manual removal or expiry               |
| IP blacklist entries   | 1 year (temporary) or permanent                         | Automatic expiry or manual removal     |
| Suspicious activity    | 90 days                                                 | Automatic deletion                     |
| Device fingerprints    | Active session + 30 days                                | Session expiry                         |

### 4. GDPR Compliance Logs

| Data Type                  | Retention Period                                | Deletion Trigger                                                                     |
| -------------------------- | ----------------------------------------------- | ------------------------------------------------------------------------------------ |
| Account deletion requests  | 3 years after completion                        | Automatic deletion 3 years after permanent deletion                                  |
| PII access logs            | 3 years                                         | Automatic deletion (required for audit trail)                                        |
| Consent logs               | 3 years after consent withdrawal                | Automatic deletion 3 years after withdrawal (required for proof of consent)          |
| Data export requests       | 3 years                                         | Automatic deletion (required for audit trail)                                        |

## Deletion Workflow

### Soft Delete (Grace Period)

1. User requests account deletion
2. `deleted_at` timestamp is set
3. `deletion_scheduled_date` is set to current date + 30 days
4. User account is marked as inactive but data retained
5. User can cancel deletion request within 30-day grace period

### Permanent Deletion

1. After 30-day grace period, scheduled deletion job runs
2. All PII is permanently deleted:
   - Encrypted email, phone, IP addresses
   - Email hash, phone hash
   - Password hash
   - Personal information (name, etc.)
3. Audit logs are anonymised:
   - User ID replaced with "DELETED_USER_{UUID}"
   - No PII remains in logs
4. `AccountDeletion` record marked as completed

## Automatic Cleanup Jobs

| Job Name                    | Frequency       | Action                                                    |
| --------------------------- | --------------- | --------------------------------------------------------- |
| Expire old tokens           | Every 1 hour    | Delete expired password reset, email, phone tokens        |
| Partition cleanup           | Daily at 2:00am | Drop old partitions for `auth_ip_tracking`, `auth_login_attempt` (90-day retention) |
| Permanent deletion          | Daily at 3:00am | Execute permanent deletions for accounts past grace period |
| GDPR log cleanup            | Weekly          | Delete PII access logs, consent logs older than 3 years   |
| Session cleanup             | Every 5 minutes | Delete expired sessions                                   |
| Recovery key expiry         | Daily           | Delete expired recovery keys (1 year old)                 |
| IP blacklist expiry         | Daily           | Delete expired temporary IP blacklist entries             |

## Legal Basis for Retention

- **Account data:** Necessary for contract performance (Terms of Service)
- **Security logs:** Legitimate interest (fraud prevention, security)
- **GDPR logs:** Legal obligation (proof of compliance)
- **Consent logs:** Legal obligation (proof of consent under GDPR Article 7)

## User Rights

Users can exercise the following rights:

1. **Right to Access:** Request copy of all data
2. **Right to Rectification:** Correct inaccurate data
3. **Right to Erasure:** Request account deletion (30-day grace period)
4. **Right to Restriction:** Restrict data processing
5. **Right to Data Portability:** Export data in machine-readable format
6. **Right to Object:** Object to data processing
7. **Right to Withdraw Consent:** Withdraw consent for phone/marketing

## Regional Variations

See regional policy documents for specific requirements:

- **EU/UK:** [DATA_RETENTION_POLICY_EU.md](./DATA_RETENTION_POLICY_EU.md)
- **USA:** [DATA_RETENTION_POLICY_USA.md](./DATA_RETENTION_POLICY_USA.md)

## Contact

For questions about data retention:

- **Data Protection Officer:** dpo@syntek.com
- **Privacy Team:** privacy@syntek.com
