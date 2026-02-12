# Data Retention Policy - United States (CCPA/CPRA)

**Effective Date:** 01.01.2026
**Version:** 1.0-USA
**Applies To:** California residents (CCPA/CPRA), other US states
**Legal Basis:** California Consumer Privacy Act (CCPA) as amended by CPRA

## Overview

This document defines data retention and deletion policies for US users, with emphasis on California residents protected by CCPA/CPRA. Other US states may have additional rights (Virginia CDPA, Colorado CPA, Utah UCPA, Connecticut CTDPA).

## CCPA/CPRA-Specific Requirements

### Key Principles

1. **Notice at Collection** (CCPA §1798.100(b)) - Inform users what data is collected
2. **Right to Delete** (CCPA §1798.105) - Delete personal information upon request
3. **Right to Know** (CCPA §1798.110) - Disclose what data is collected/shared
4. **Right to Opt-Out** (CCPA §1798.120) - Opt-out of sale/sharing

### Business Purposes for Collection

| Data Type                 | Business Purpose                                          | CCPA Category             |
| ------------------------- | --------------------------------------------------------- | ------------------------- |
| Email, name               | Account creation, authentication, service provision       | Identifiers               |
| Phone number              | Two-factor authentication, account recovery (with consent) | Identifiers               |
| IP address                | Security, fraud prevention, geographic personalisation    | Internet/Network Activity |
| Login history             | Security monitoring, fraud prevention                     | Internet/Network Activity |
| Device information        | Session security, user experience optimization            | Internet/Network Activity |

**Note:** We do NOT sell personal information. We do NOT share personal information for cross-context behavioral advertising.

## Data Retention Periods (USA-Specific)

### 1. User Account Data

| Data Type                | Retention Period                         | CCPA Compliance                            |
| ------------------------ | ---------------------------------------- | ------------------------------------------ |
| Email (encrypted)        | Active account + 30 days after deletion  | CCPA §1798.105 (Right to Delete)           |
| Phone (encrypted)        | Active account + 30 days (with consent)  | CCPA §1798.105 (Right to Delete)           |
| Password hash            | Active account + 30 days                 | CCPA §1798.105 (Right to Delete)           |
| Email/Phone hashes       | Active account + 30 days                 | CCPA §1798.105 (Right to Delete)           |

**Note:** 30-day grace period allows users to cancel deletion request before permanent removal.

### 2. Authentication Logs

| Data Type             | Retention Period | Justification                                     |
| --------------------- | ---------------- | ------------------------------------------------- |
| Login attempts        | **90 days**      | Security and fraud prevention (business purpose)  |
| IP tracking entries   | **90 days**      | Security and fraud prevention (business purpose)  |
| Session security logs | **90 days**      | Security and fraud prevention (business purpose)  |

### 3. Compliance Audit Logs

| Data Type                  | Retention Period          | Legal Basis                                          |
| -------------------------- | ------------------------- | ---------------------------------------------------- |
| Consumer request logs      | **5 years**               | CCPA §1798.185 (recordkeeping for compliance verification) |
| Data deletion logs         | **5 years** after completion | Proof of compliance with deletion requests           |
| Data export logs           | **5 years**               | Proof of compliance with data portability requests   |
| Opt-out request logs       | **5 years**               | Proof of compliance with opt-out requests            |

**Note:** 5-year retention aligns with California Attorney General's recommended recordkeeping for CCPA compliance verification.

## Consumer Rights (CCPA/CPRA)

California residents have the following rights:

1. **Right to Know** (CCPA §1798.100) - Request disclosure of personal information collected (last 12 months)
2. **Right to Delete** (CCPA §1798.105) - Request deletion of personal information (30-day grace period)
3. **Right to Correct** (CPRA §1798.106) - Request correction of inaccurate information
4. **Right to Opt-Out of Sale/Sharing** (CCPA §1798.120) - We do NOT sell or share personal information
5. **Right to Limit Use of Sensitive Personal Information** (CPRA §1798.121) - Limit use of sensitive data
6. **Right to Non-Discrimination** (CCPA §1798.125) - Cannot discriminate for exercising rights
7. **Right to Data Portability** (CCPA §1798.100(d)) - Export data in portable format (JSON/CSV)

### Other US State Rights

- **Virginia (CDPA):** Right to access, delete, correct, data portability, opt-out
- **Colorado (CPA):** Right to access, delete, correct, data portability, opt-out
- **Utah (UCPA):** Right to access, delete, data portability, opt-out
- **Connecticut (CTDPA):** Right to access, delete, correct, data portability, opt-out

## Deletion Workflow (CCPA-Compliant)

### Consumer Deletion Request

1. User submits deletion request via account settings or email (privacy@syntek.com)
2. We verify identity using:
   - Email verification code (for low-risk requests)
   - Two-factor authentication (for high-risk requests)
3. Account marked as deleted (`deleted_at` timestamp set)
4. Deletion scheduled for 30 days later (grace period)
5. User receives confirmation email with request ID

### Permanent Deletion (After Grace Period)

1. After 30 days, automated job permanently deletes:
   - All encrypted PII (email, phone, IP addresses)
   - All hashes (email_hash, phone_hash, IP hashes)
   - Personal information (first name, last name, username)
   - Password hash
   - TOTP secrets, backup codes, recovery keys
2. Audit logs anonymised:
   - User ID replaced with `DELETED_USER_{UUID}`
   - No PII remains
3. Deletion confirmation email sent to user (if cancellation email available)
4. Deletion log entry created (retained 5 years for compliance verification)

## Exceptions to Deletion (CCPA §1798.105(d))

We may deny deletion requests if necessary to:

1. **Complete Transaction** - Complete the transaction for which information was collected
2. **Detect Security Incidents** - Detect security incidents, protect against malicious activity
3. **Debug** - Debug to identify and repair errors
4. **Exercise Free Speech** - Exercise free speech or legal rights
5. **Comply with Law** - Comply with California Electronic Communications Privacy Act
6. **Internal Uses** - Internal uses reasonably aligned with consumer expectations
7. **Legal Obligations** - Comply with legal obligations

**Note:** If deletion denied, we will provide explanation to consumer.

## Sensitive Personal Information

Under CPRA, the following is considered "sensitive personal information":

| Data Type                 | Sensitivity Level | Usage Limitation                                |
| ------------------------- | ----------------- | ----------------------------------------------- |
| Email                     | Standard          | Authentication, service provision only          |
| Phone number              | Sensitive (CPRA)  | Two-factor authentication only (with consent)   |
| Precise geolocation       | Sensitive (CPRA)  | **NOT COLLECTED** (IP-based geolocation only)   |
| Social Security Number    | Sensitive (CPRA)  | **NOT COLLECTED**                               |
| Government ID             | Sensitive (CPRA)  | **NOT COLLECTED**                               |

**Limitation:** We do NOT use sensitive personal information for purposes other than those disclosed at collection.

## Automated Cleanup Jobs (USA-Specific)

| Job Name                  | Frequency       | Compliance                                      |
| ------------------------- | --------------- | ----------------------------------------------- |
| Expire old tokens         | Every 1 hour    | Data minimisation                               |
| Partition cleanup         | Daily at 2:00am | **90-day retention** for IP tracking, login attempts |
| Permanent deletion        | Daily at 3:00am | CCPA §1798.105 (Right to Delete)                |
| CCPA audit log cleanup    | Annually        | **5-year retention** for compliance logs        |
| Session cleanup           | Every 5 minutes | Data minimisation                               |
| Recovery key expiry       | Daily           | 1-year expiry (data minimisation)               |

## Consumer Request Verification

To prevent fraudulent requests, we verify identity:

- **Low-Risk Requests** (data access): Email verification code
- **High-Risk Requests** (data deletion): Two-factor authentication or government-issued ID
- **Authorized Agents:** Power of attorney or written permission required

## Privacy Policy Notification

We notify California residents of material changes via:

1. Email notification (30 days before changes take effect)
2. In-app notification
3. Updated privacy policy at https://syntek.com/privacy-policy

## Contact Information

**California Privacy Rights:**
- Email: privacy@syntek.com (subject: "CCPA Request")
- Phone: 1-800-PRIVACY (1-800-774-8229)
- Mail: Syntek Inc., Privacy Rights Dept., 123 Main St, San Francisco, CA 94102

**Do Not Sell My Personal Information:**
- We do NOT sell personal information
- Opt-out link: https://syntek.com/do-not-sell

## State-Specific Contacts

- **Virginia (CDPA):** privacy-virginia@syntek.com
- **Colorado (CPA):** privacy-colorado@syntek.com
- **Utah (UCPA):** privacy-utah@syntek.com
- **Connecticut (CTDPA):** privacy-connecticut@syntek.com

## Additional Resources

- **CCPA Full Text:** https://leginfo.legislature.ca.gov/faces/codes_displayText.xhtml?division=3.&part=4.&lawCode=CIV&title=1.81.5
- **California AG Guidance:** https://oag.ca.gov/privacy/ccpa
- **IAPP Resources:** https://iapp.org/resources/article/us-state-privacy-legislation-tracker/

**Last Updated:** 01.01.2026
**Next Review:** 01.01.2027
