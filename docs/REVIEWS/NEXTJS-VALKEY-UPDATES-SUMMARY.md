# Next.js and Valkey Architecture Updates

**Date:** 15.02.2026
**Status:** ✅ REVIEW DOCUMENTS UPDATED
**Related Documents:**

- `REVIEW-PHASES-1-5-CONFIGURABILITY-ARCHITECTURE.md` (Updated)
- `ACTION-ITEMS-CONFIGURABILITY.md` (Updated)
- `DESIGN-TOKENS-ARCHITECTURE-SUMMARY.md` (Updated)

---

## Executive Summary

All review documents have been updated to reflect:

1. **Next.js Built-in Caching** - Use `.next` directory for optimization/minification (no external CDN needed)
2. **Valkey Instead of Redis** - Use Valkey for all caching (OSS, Redis-compatible, future-proof)
3. **Data Flow Architecture** - Follow syntek-infrastructure encryption-at-rest pattern

---

## 1. Next.js Caching and Optimization

### What Changed

**Before (CDN-based):**

```
Django → Generate static files → Push to S3/CloudFront → Frontend loads from CDN
```

**After (Next.js-based):**

```
Django → Generate static files → Next.js build (.next) → Frontend loads from .next/static
```

### Key Updates

#### Architecture Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Django Admin - Client updates theme → Save to Postgres       │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. Django Signal - Generate static files:                       │
│    - /tokens/{client-id}/theme.css (CSS custom properties)      │
│    - /tokens/{client-id}/theme.json (JSON for React Native)     │
│    Save to Django static files directory                        │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. Next.js Build Process (.next directory)                      │
│    - Optimizes and minifies CSS/JS                              │
│    - Generates static pages and assets                          │
│    - Caches built assets for fast serving                       │
│    - Automatic code splitting and compression                   │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. Frontend Serving                                             │
│    Web: Served from .next/static (cached by browser)            │
│    Mobile: Fetch JSON from API, cache in AsyncStorage           │
└─────────────────────────────────────────────────────────────────┘
```

#### Code Changes

**Web - Loading Theme CSS:**

```tsx
// web/app/layout.tsx
export default async function RootLayout({ children }) {
  const clientId = extractClientId(host);

  return (
    <html lang="en">
      <head>
        {/* ✅ NEW: Load from Next.js static files */}
        <link rel="stylesheet" href={`/tokens/${clientId}/theme.css`} />
        {/* Served from .next/static (optimized by Next.js) */}
      </head>
      <body>{children}</body>
    </html>
  );
}
```

**Mobile - Loading Theme JSON:**

```typescript
// mobile/packages/mobile-auth/src/hooks/useTheme.ts
const API_BASE_URL = Config.API_BASE_URL || "http://localhost:3000";
const CLIENT_ID = Config.CLIENT_ID || "default";
const THEME_URL = `${API_BASE_URL}/tokens/${CLIENT_ID}/theme.json`;

// Fetch from Next.js API, cache in AsyncStorage
```

**Django - Theme Generator:**

```python
# backend/security-core/theme/theme_generator.py
class ThemeGenerator:
    def optimize_for_nextjs(self):
        """Optimize generated files for Next.js consumption.

        Next.js handles all caching and minification via .next directory.
        No external CDN needed - Next.js build process handles optimization.
        """
        # Files served by Next.js - no additional CDN configuration needed
        # Next.js handles all optimization, caching, and compression
        pass
```

### Benefits

- ✅ **No external CDN required** - Next.js handles optimization
- ✅ **Automatic minification** - Built into Next.js build process
- ✅ **Code splitting** - Next.js automatically splits code
- ✅ **Browser caching** - Cache-Control headers set by Next.js
- ✅ **Compression** - gzip/brotli handled by Next.js
- ✅ **ISR support** - Incremental Static Regeneration for updates

---

## 2. Valkey Instead of Redis

### Why Valkey?

| Feature           | Redis                                        | Valkey                        |
| ----------------- | -------------------------------------------- | ----------------------------- |
| **License**       | Redis Source Available License (restrictive) | BSD 3-Clause (true OSS)       |
| **Compatibility** | N/A                                          | Drop-in replacement for Redis |
| **Governance**    | Redis Ltd (corporate)                        | Linux Foundation (community)  |
| **Future-proof**  | Risk of license changes                      | Stable OSS license            |
| **Cost**          | Enterprise features require license          | Fully open-source             |

### Configuration

**Django Settings:**

```python
# backend/settings.py
CACHES = {
    'default': {
        'BACKEND': 'django_valkey.cache.ValkeyCache',  # ✅ Valkey
        'LOCATION': 'valkey://localhost:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_valkey.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
            },
        }
    },
}

# Session Backend (Valkey)
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
```

### Use Cases

1. **Session caching** - Encrypted session data (see Data Flow Architecture)
2. **GraphQL query results** - Cache frequently accessed configuration
3. **Rate limiting** - Track request counts per IP/user
4. **CSRF tokens** - Store and validate tokens
5. **MFA codes** - Temporary TOTP/backup code storage (encrypted)

---

## 3. Data Flow Architecture (Encryption-at-Rest)

### Critical Security Pattern

All sensitive data must be **encrypted before caching in Valkey or storing in PostgreSQL**.

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ User Request (plaintext)                                        │
│  • Password, email, session data, personal information          │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ GraphQL Layer (Rust - syntek-modules)                           │
│  • Receive plaintext in memory (never written to disk)          │
│  • Process in Rust (memory-safe, no leaks)                      │
│  • Encrypt using ChaCha20-Poly1305 or AES-256-GCM               │
│  • Zeroise plaintext from memory (SecretBox/zeroize crate)      │
│  • Keys fetched from OpenBao (ephemeral, in-memory only)        │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ Valkey (encrypted data in memory)                               │
│  • Stores encrypted blobs only (never plaintext)                │
│  • Fast in-memory cache for encrypted session data              │
│  • Persistence (AOF/RDB) writes encrypted data to disk          │
│  • Keys fetched from OpenBao, never stored in Valkey            │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ PostgreSQL (encrypted data at rest)                             │
│  • Stores encrypted blobs (passwords, PII, sessions)            │
│  • Minimal plaintext (only non-sensitive metadata)              │
│  • TDE (Transparent Data Encryption) for additional layer       │
│  • Rust encryption layer handles all sensitive fields           │
└─────────────────────────────────────────────────────────────────┘
```

### Key Security Principles

1. **Plaintext Only in Memory** - User data exists as plaintext ONLY in Rust process memory
2. **Encrypt Before Cache** - All data encrypted BEFORE writing to Valkey
3. **Encrypt Before Database** - All sensitive fields encrypted BEFORE PostgreSQL insert
4. **Memory Zeroing** - Plaintext zeroed from memory after encryption (zeroize crate)
5. **Ephemeral Keys** - Encryption keys fetched from OpenBao, never persisted
6. **No Disk Writes** - Plaintext NEVER written to disk (logs, cache files, temp files)

### Example: User Login Flow

```
1. User submits password (plaintext)
   ↓
2. Rust receives password in memory
   ↓
3. Rust compares with Argon2 hash (memory only)
   ↓
4. Generate session token (plaintext in memory)
   ↓
5. Fetch encryption key from OpenBao (in-memory)
   ↓
6. Encrypt session token with ChaCha20-Poly1305
   ↓
7. Zeroise plaintext session token from memory
   ↓
8. Store encrypted session in Valkey
   ↓
9. Store encrypted session in PostgreSQL (if persisting)
   ↓
10. Return session cookie to user (plaintext session ID, encrypted data in backend)
```

### Implementation

**Encrypted Session Store:**

```python
# backend/syntek_auth/middleware/session_encryption.py
from django.contrib.sessions.backends.cache import SessionStore as CacheSessionStore
from rust.encryption import encrypt_field, decrypt_field  # PyO3 bindings


class EncryptedSessionStore(CacheSessionStore):
    """Session store that encrypts data before writing to Valkey."""

    def encode(self, session_dict):
        """Encrypt session data before storing in Valkey."""
        serialized = super().encode(session_dict)

        # Encrypt with Rust layer (keys from OpenBao)
        encrypted = encrypt_field(
            plaintext=serialized,
            field_name='session_data',
            key_source='openbao',
        )

        # Valkey stores encrypted blob only
        return encrypted

    def decode(self, session_data):
        """Decrypt session data after reading from Valkey."""
        try:
            # Decrypt with Rust layer
            decrypted = decrypt_field(
                ciphertext=session_data,
                field_name='session_data',
                key_source='openbao',
            )
            return super().decode(decrypted)
        except Exception:
            return {}  # Invalid/corrupted session
```

### Compliance

- ✅ **GDPR Article 32** - Encryption of personal data
- ✅ **NIST 800-53 SC-28** - Protection of data at rest
- ✅ **PCI DSS 3.2.1** - Encryption of cardholder data
- ✅ **OWASP A02:2021** - Cryptographic failures prevention

---

## Documents Updated

### 1. REVIEW-PHASES-1-5-CONFIGURABILITY-ARCHITECTURE.md

**Sections Added:**

- **4.5 Caching Strategy (Valkey)** - Why Valkey, configuration, use cases
- **4.6 Data Flow Architecture** - Encryption-at-rest pattern, compliance

**Sections Updated:**

- **2.2 Recommended Design Token Architecture** - Next.js build process instead of CDN
- **4.4 Performance** - Added Next.js optimizations
- Theme generator code examples - `optimize_for_nextjs()` instead of `push_to_cdn()`
- Frontend code examples - Load from `/tokens/` instead of `https://cdn.syntek.com/tokens/`

### 2. ACTION-ITEMS-CONFIGURABILITY.md

**Sections Added:**

- **Priority 2.5: CRITICAL - Valkey Configuration** (30 minutes)
  - Install Valkey client
  - Configure Valkey cache
  - Configure Valkey for encryption
  - Data flow architecture reference
  - Testing checklist

**Sections Updated:**

- **Priority 2: Design Token Generation** - Next.js optimization instead of CDN push
- Theme generator code - `optimize_for_nextjs()` method
- Web frontend code - Load from `/tokens/` (Next.js static files)
- Mobile frontend code - Fetch from API base URL (not hardcoded CDN)

### 3. DESIGN-TOKENS-ARCHITECTURE-SUMMARY.md

**Sections Added:**

- **Caching Strategy: Valkey** - Why Valkey, use cases, configuration
- **Data Flow Architecture** - Encryption-at-rest pattern, security principles, compliance

**Sections Updated:**

- **Architecture Flow** - Added "Next.js Build Process" step
- **Performance Comparison** - Updated cache mechanism (Next.js instead of CDN)
- **Benefits** - Added Next.js optimization and Valkey benefits
- **Multi-Tenant Example** - Updated URLs (no CDN references)

---

## Action Items

### Immediate (Priority 1)

1. **Fix hardcoded `password_max_length`** (5 minutes)
   - Change: `password_max_length=128` → `password_max_length=config.get('PASSWORD_MAX_LENGTH', 128)`
   - File: `graphql/auth/syntek_graphql_auth/queries/config.py:42`

### Critical (Priority 2.5)

2. **Configure Valkey** (30 minutes)
   - Install `django-valkey` package
   - Configure `CACHES` with Valkey backend
   - Configure `SESSION_ENGINE` to use Valkey
   - Implement encrypted session store (optional - for compliance)
   - Test Valkey connection and session storage

### Should Fix (Priority 2)

3. **Implement Design Token Generation** (4-6 hours)
   - Create Django `ThemeConfiguration` model
   - Implement theme generator service (CSS + JSON)
   - Update web frontend to load CSS from Next.js static files
   - Update mobile frontend to fetch JSON and cache in AsyncStorage
   - Test theme generation and Next.js serving

---

## Testing Checklist

### Next.js Caching ✅

- [ ] Theme CSS files served from `/tokens/{client-id}/theme.css`
- [ ] Files cached by browser (check Network tab - 200 then 304)
- [ ] Next.js build optimizes and minifies CSS (check `.next/static/`)
- [ ] Mobile JSON fetched from API and cached in AsyncStorage
- [ ] No CDN URLs in code (all use relative paths or API base URL)

### Valkey Configuration ✅

- [ ] Valkey running: `valkey-cli ping` → `PONG`
- [ ] Django CACHES configured with `ValkeyCache` backend
- [ ] Sessions stored in Valkey: `valkey-cli KEYS 'django.contrib.sessions*'`
- [ ] Session data encrypted (check with `valkey-cli GET <key>` - should be blob)
- [ ] Login/logout cycle works with Valkey sessions
- [ ] Rate limiting uses Valkey cache

### Data Flow Architecture ✅

- [ ] Plaintext never written to Valkey (monitor with `valkey-cli MONITOR`)
- [ ] Session decryption works (logout/login cycle successful)
- [ ] Encryption keys fetched from OpenBao (check Django logs)
- [ ] Memory zeroing implemented (Rust zeroize crate used)
- [ ] Compliance verified (GDPR, NIST, PCI DSS)

---

## Performance Impact

### Next.js vs CDN

| Metric           | CDN                        | Next.js           | Difference  |
| ---------------- | -------------------------- | ----------------- | ----------- |
| **Initial Load** | ~50ms                      | ~50ms             | Same        |
| **Cached Load**  | ~0ms                       | ~0ms              | Same        |
| **Complexity**   | High (S3/CloudFront setup) | Low (built-in)    | **Simpler** |
| **Cost**         | $$ (CDN fees)              | $ (hosting only)  | **Cheaper** |
| **Build Time**   | +5-10s (CDN upload)        | +0s (local build) | **Faster**  |

**Verdict:** Next.js provides same performance with lower complexity and cost ✅

### Redis vs Valkey

| Metric            | Redis            | Valkey    | Difference          |
| ----------------- | ---------------- | --------- | ------------------- |
| **Performance**   | ~1ms             | ~1ms      | Same                |
| **Compatibility** | N/A              | 100%      | Drop-in replacement |
| **License**       | Restrictive      | OSS (BSD) | **Better**          |
| **Cost**          | $$$ (Enterprise) | Free      | **Cheaper**         |
| **Future-proof**  | Risk             | Stable    | **Safer**           |

**Verdict:** Valkey provides same performance with better licensing ✅

---

## Conclusion

All review documents have been updated to reflect:

1. ✅ **Next.js built-in caching** - Simpler, cheaper, same performance as CDN
2. ✅ **Valkey instead of Redis** - Better licensing, future-proof, drop-in replacement
3. ✅ **Data flow architecture** - Encryption-at-rest for GDPR/NIST/PCI DSS compliance

**No breaking changes** - Updates are architectural improvements that align with syntek-infrastructure patterns.

**Next Steps:**

1. Review updated documents
2. Fix Priority 1 (hardcoded password_max_length)
3. Configure Valkey (Priority 2.5)
4. Implement design token generation (Priority 2)
