# Data Retention Policy - European Union (GDPR)

**Effective Date:** 01.01.2026
**Version:** 1.0-EU
**Applies To:** EU, UK, EEA member states
**Legal Basis:** GDPR (Regulation (EU) 2016/679)

## Overview

This document defines data retention and deletion policies for EU/UK users in compliance with GDPR requirements. This policy overrides the global default where stricter requirements apply.

## GDPR-Specific Requirements

### Key Principles

1. **Data Minimisation** (Article 5(1)(c)) - Only collect necessary data
2. **Storage Limitation** (Article 5(1)(e)) - Retain only as long as necessary
3. **Purpose Limitation** (Article 5(1)(b)) - Use data only for stated purposes
4. **Lawfulness** (Article 6) - Legal basis for all processing

### Legal Bases for Processing

| Data Type                      | Legal Basis                                          | GDPR Article   |
| ------------------------------ | ---------------------------------------------------- | -------------- |
| Account data (email, name)     | Contract performance (Terms of Service)              | Article 6(1)(b) |
| Phone number                   | Consent (user must opt-in)                           | Article 6(1)(a) |
| Security logs                  | Legitimate interest (fraud prevention, security)     | Article 6(1)(f) |
| Login attempts, IP tracking    | Legitimate interest (security, fraud prevention)     | Article 6(1)(f) |
| GDPR audit logs                | Legal obligation (proof of compliance)               | Article 6(1)(c) |
| Consent logs                   | Legal obligation (proof of consent)                  | Article 6(1)(c) |

## Data Retention Periods (EU-Specific)

### 1. User Account Data

| Data Type              | Retention Period                        | GDPR Requirement                           |
| ---------------------- | --------------------------------------- | ------------------------------------------ |
| Email (encrypted)      | Active account + 30 days after deletion | Article 17 (Right to Erasure)              |
| Phone (encrypted)      | Active account + 30 days (with consent) | Article 7 (Consent), Article 17 (Erasure)  |
| Password hash          | Active account + 30 days                | Article 17 (Right to Erasure)              |
| Email/Phone hashes     | Active account + 30 days                | Article 17 (Right to Erasure)              |

**Note:** 30-day grace period allows users to cancel deletion request (GDPR Recital 39 - reasonable period).

### 2. Authentication Logs (Reduced Retention)

| Data Type             | Retention Period | GDPR Compliance                                    |
| --------------------- | ---------------- | -------------------------------------------------- |
| Login attempts        | **60 days**      | Shorter than global (legitimate interest balancing) |
| IP tracking entries   | **60 days**      | Article 5(1)(e) (storage limitation)               |
| Session security logs | **60 days**      | Minimised retention for privacy                    |

**Justification:** EU retention periods are shorter (60 days vs 90 days globally) to align with GDPR data minimisation principles while maintaining security capabilities.

### 3. GDPR Audit Logs

| Data Type                 | Retention Period          | GDPR Requirement                             |
| ------------------------- | ------------------------- | -------------------------------------------- |
| PII access logs           | **7 years**               | Article 30 (Records of processing activities) |
| Consent logs              | **7 years** after withdrawal | Article 7(1) (Proof of consent)              |
| Data export requests      | **7 years**               | Article 30 (Records of processing activities) |
| Account deletion requests | **7 years** after completion | Article 30 (Records of processing activities) |

**Note:** 7-year retention for audit logs aligns with EU financial record-keeping requirements and provides sufficient evidence for regulatory investigations.

## User Rights (GDPR Articles 15-22)

EU/UK users have the following rights:

1. **Right to Access** (Article 15) - Obtain copy of personal data within 30 days
2. **Right to Rectification** (Article 16) - Correct inaccurate data
3. **Right to Erasure** (Article 17) - Request deletion with 30-day grace period
4. **Right to Restriction** (Article 18) - Restrict processing while verifying accuracy
5. **Right to Data Portability** (Article 20) - Export data in machine-readable format (JSON/CSV)
6. **Right to Object** (Article 21) - Object to processing based on legitimate interest
7. **Right to Withdraw Consent** (Article 7(3)) - Withdraw phone/marketing consent any time
8. **Right to Lodge Complaint** (Article 77) - Complain to supervisory authority

## Deletion Workflow (GDPR-Compliant)

### Soft Delete (30-Day Grace Period)

1. User submits deletion request via account settings
2. Account marked as deleted (`deleted_at` timestamp set)
3. Deletion scheduled for 30 days later (GDPR Recital 39)
4. User receives confirmation email with cancellation instructions
5. Data processing restricted during grace period (Article 18)

### Permanent Deletion (After Grace Period)

1. After 30 days, automated job permanently deletes:
   - All encrypted PII (email, phone, IP addresses)
   - All hashes (email_hash, phone_hash, IP hashes)
   - Personal information (first name, last name, username)
   - Password hash
   - TOTP secrets, backup codes, recovery keys
2. Audit logs anonymised:
   - User ID replaced with `DELETED_USER_{UUID}`
   - No PII remains (GDPR Article 17)
3. `AccountDeletion` record marked as completed
4. Confirmation email sent to user (if cancellation email available)

## Cross-Border Data Transfers

For EU/UK users, data transfers outside the EU/EEA require:

1. **Adequacy Decision** (Article 45) - Transfer to countries with adequate protection
2. **Standard Contractual Clauses** (Article 46) - For transfers to non-adequate countries
3. **Explicit Consent** (Article 49) - If no other safeguard available

**Current Safeguards:**

- All user data stored in EU data centres (Frankfurt, Paris, Dublin)
- No cross-border transfers to non-adequate countries
- Cloudinary (media storage): EU region, GDPR-compliant
- GlitchTip (logging): EU-hosted instance

## Automated Cleanup Jobs (EU-Specific)

| Job Name                  | Frequency       | GDPR Compliance                              |
| ------------------------- | --------------- | -------------------------------------------- |
| Expire old tokens         | Every 1 hour    | Article 5(1)(e) (storage limitation)         |
| Partition cleanup         | Daily at 2:00am | **60-day retention** for IP tracking, login attempts |
| Permanent deletion        | Daily at 3:00am | Article 17 (Right to Erasure)                |
| GDPR audit log cleanup    | Annually        | **7-year retention** for PII access, consent logs    |
| Session cleanup           | Every 5 minutes | Article 5(1)(e) (storage limitation)         |
| Recovery key expiry       | Daily           | 1-year expiry (Article 5(1)(e))              |

## Supervisory Authorities

EU/UK users can lodge complaints with:

- **UK:** Information Commissioner's Office (ICO) - https://ico.org.uk
- **Ireland:** Data Protection Commission (DPC) - https://dataprotection.ie
- **Germany:** State data protection authorities - https://www.bfdi.bund.de
- **France:** CNIL - https://www.cnil.fr
- **Other EU countries:** See https://edpb.europa.eu/about-edpb/about-edpb/members_en

## Data Protection Officer

**DPO Contact:**
- Email: dpo@syntek.eu
- Phone: +44 20 1234 5678 (UK), +353 1 234 5678 (Ireland)
- Address: Syntek EU Data Protection, 123 Privacy Street, Dublin 2, Ireland

## Changes to This Policy

We will notify EU/UK users of material changes via:

1. Email notification (30 days before changes take effect)
2. In-app notification
3. Updated privacy policy with version history

## Additional Resources

- **GDPR Full Text:** https://gdpr-info.eu/
- **ICO Guidance:** https://ico.org.uk/for-organisations/
- **EDPB Guidelines:** https://edpb.europa.eu/our-work-tools/general-guidance_en

**Last Updated:** 01.01.2026
**Next Review:** 01.01.2027