# Design Token Architecture Summary

**Date:** 15.02.2026
**Status:** ✅ RECOMMENDED ARCHITECTURE
**Related Documents:**

- `REVIEW-PHASES-1-5-CONFIGURABILITY-ARCHITECTURE.md`
- `ACTION-ITEMS-CONFIGURABILITY.md`

---

## Executive Summary

Design tokens (colours, typography, spacing, breakpoints) will follow a **static file generation** architecture:

1. **Source of Truth:** Django/Postgres (via CMS/Platform)
2. **Delivery Mechanism:** Static files (CSS + JSON), NOT GraphQL queries
3. **Performance:** Zero database calls, CDN-cached, +0ms on cached loads

---

## Architecture Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. CMS/Platform (Django Admin)                                  │
│    Client updates brand overrides → saved to Django/Postgres    │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. Django Signal Handler (on save)                              │
│    Generate static token files:                                 │
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
│ 4. Frontend (Web/Mobile)                                        │
│    Load static file (cached by Next.js/.next, no DB hit)        │
│    - Web: <link rel="stylesheet" href="/tokens/{id}/theme.css"> │
│           (served from .next/static, cached by browser)         │
│    - Mobile: Fetch JSON on app launch, cache in AsyncStorage    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Why Static Files Instead of GraphQL?

### ❌ WRONG: Fetch tokens via GraphQL on every page load

```typescript
// DON'T DO THIS - Database call on every load
const { themeColors } = useAuthConfig();
// Result: +50-100ms on every page load
```

### ✅ CORRECT: Load static file once, cache aggressively

```html
<!-- Load CSS file in <head> - cached by Next.js and browser -->
<link rel="stylesheet" href="/tokens/{client-id}/theme.css" />
<!-- Result: +0ms on cached loads (after initial load) -->
<!-- Next.js serves from .next/static (optimized and minified) -->
```

---

## Performance Comparison

| Approach                 | Database Calls     | Page Load Impact | Cache Duration            |
| ------------------------ | ------------------ | ---------------- | ------------------------- |
| ❌ GraphQL on every load | 1 per page load    | +50-100ms        | 5 minutes (Apollo cache)  |
| ✅ Static CSS file       | 0 (Next.js cached) | +0ms (cached)    | Browser cache (immutable) |
| ✅ Static JSON (mobile)  | 0 (device cached)  | +0ms (cached)    | Until app update          |

**Static file approach is 50-100ms faster per page load** ✅

---

## Implementation Components

### 1. Django Backend (2 hours)

**Files Created:**

- `backend/security-core/theme/models.py` - ThemeConfiguration model
- `backend/security-core/theme/admin.py` - Django admin interface
- `backend/security-core/theme/theme_generator.py` - Static file generator
- `backend/security-core/theme/management/commands/create_default_theme.py` - Default theme

**Key Features:**

- Multi-tenant support (each client gets unique theme)
- Automatic static file generation on save (Django signals)
- CDN push integration (S3/CloudFront/Cloudflare)

### 2. Web Frontend (1 hour)

**Files Modified:**

- `web/app/layout.tsx` - Load client-specific CSS file
- `web/packages/ui-auth/src/components/Button.tsx` - Use CSS custom properties

**Key Features:**

- Extract client ID from subdomain (e.g., `acme-corp.syntek.com`)
- Load CSS file: `/tokens/{client-id}/theme.css`
- Use CSS variables: `bg-[var(--color-primary)]`

### 3. Mobile Frontend (1.5 hours)

**Files Created:**

- `mobile/packages/mobile-auth/src/hooks/useTheme.ts` - Theme loading hook
- `mobile/packages/mobile-auth/src/components/Button.tsx` - Use JSON theme data

**Key Features:**

- Fetch JSON on app launch: `/tokens/{client-id}/theme.json`
- Cache locally in AsyncStorage (instant on relaunch)
- Background refresh if theme updated

---

## Multi-Tenant Example

**Client 1:** `acme-corp.syntek.com` → Loads `/tokens/acme-corp/theme.css`

- Primary colour: `#FF5733` (Acme Corp orange)
- Font: `Roboto, sans-serif`

**Client 2:** `globex.syntek.com` → Loads `/tokens/globex/theme.css`

- Primary colour: `#2ECC71` (Globex green)
- Font: `Open Sans, sans-serif`

**Default:** `www.syntek.com` → Loads `/tokens/default/theme.css`

- Primary colour: `#3b82f6` (Syntek blue)
- Font: `Inter, sans-serif`

Each client gets their own branded theme, delivered as static files from CDN.

---

## Design Tokens Included

### Colours

- `--color-primary` - Primary brand colour
- `--color-success` - Success feedback (#10b981)
- `--color-warning` - Warning feedback (#f59e0b)
- `--color-error` - Error feedback (#ef4444)
- `--color-neutral` - Neutral UI elements (#737373)

### Typography

- `--font-sans` - Sans-serif font stack (Inter, system-ui, sans-serif)
- `--font-mono` - Monospace font stack (JetBrains Mono, Monaco, monospace)

### Spacing Scale (based on 4px)

- `--spacing-1` → 4px
- `--spacing-2` → 8px
- `--spacing-3` → 12px
- `--spacing-4` → 16px
- `--spacing-6` → 24px
- `--spacing-8` → 32px
- `--spacing-12` → 48px
- `--spacing-16` → 64px

### Breakpoints

- `--breakpoint-sm` → 640px
- `--breakpoint-md` → 768px
- `--breakpoint-lg` → 1024px
- `--breakpoint-xl` → 1280px

---

## Usage Examples

### Web (Tailwind v4)

```tsx
export function Button({ variant = "primary" }) {
  return (
    <button
      className={`
        px-4 py-2 rounded
        bg-[var(--color-${variant})] text-white
        hover:opacity-90 transition-colors
      `}
    >
      Click Me
    </button>
  );
}
```

### Mobile (React Native)

```tsx
export function Button({ variant = "primary" }) {
  const { theme } = useTheme();

  return (
    <Pressable
      style={{
        backgroundColor: theme.colors[variant],
        paddingHorizontal: theme.spacing["4"],
        paddingVertical: theme.spacing["2"],
        borderRadius: 8,
      }}
    >
      <Text style={{ color: "white" }}>Click Me</Text>
    </Pressable>
  );
}
```

---

## Caching Strategy: Valkey (NOT Redis)

**Critical Requirement:** Use **Valkey** for all caching, NOT Redis.

### Why Valkey?

- ✅ **Open-source** - True OSS license (BSD 3-Clause), no licensing restrictions
- ✅ **Redis-compatible** - Drop-in replacement for Redis
- ✅ **Community-driven** - Linux Foundation project
- ✅ **Future-proof** - No corporate license changes

### Valkey Use Cases

1. **Session caching** - Encrypted session data (see Data Flow Architecture)
2. **GraphQL query results** - Cache frequently accessed configuration
3. **Rate limiting** - Track request counts per IP/user
4. **CSRF tokens** - Store and validate tokens
5. **MFA codes** - Temporary TOTP/backup code storage (encrypted)

### Django Configuration

```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django_valkey.cache.ValkeyCache',
        'LOCATION': 'valkey://localhost:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_valkey.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
            },
        }
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
```

---

## Data Flow Architecture (Encryption-at-Rest)

**Critical Security Pattern:** All sensitive data must be encrypted before caching in Valkey or storing in PostgreSQL.

### Architecture Overview

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

1. **Plaintext Only in Memory:** User data exists as plaintext ONLY in Rust process memory
2. **Encrypt Before Cache:** All data encrypted BEFORE writing to Valkey
3. **Encrypt Before Database:** All sensitive fields encrypted BEFORE PostgreSQL insert
4. **Memory Zeroing:** Plaintext zeroed from memory after encryption (zeroize crate)
5. **Ephemeral Keys:** Encryption keys fetched from OpenBao, never persisted
6. **No Disk Writes:** Plaintext NEVER written to disk (logs, cache files, temp files)

### Example Flow (User Login)

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

### Compliance

- ✅ **GDPR Article 32** - Encryption of personal data
- ✅ **NIST 800-53 SC-28** - Protection of data at rest
- ✅ **PCI DSS 3.2.1** - Encryption of cardholder data
- ✅ **OWASP A02:2021** - Cryptographic failures prevention

---

## Benefits

### Performance ✅

- **Zero database overhead:** Static files cached by Next.js and browser
- **Instant page loads:** +0ms after initial CSS load
- **Mobile app launch:** Instant with cached JSON
- **Next.js optimization:** Automatic minification, code splitting, compression
- **Valkey caching:** Encrypted session/config data cached in-memory (μs access)

### Developer Experience ✅

- **Runtime updates:** Change theme without rebuilding application
- **Multi-tenant support:** Each client gets their own theme file
- **Type safety:** CSS custom properties + TypeScript types for mobile

### Scalability ✅

- **Next.js-optimized:** Static files served from .next/static (built-in optimization)
- **No backend load:** No database queries for theme data
- **Excellent caching:** Browser cache + Next.js static optimization
- **Valkey scalability:** In-memory cache scales horizontally (Redis-compatible clustering)

### Maintainability ✅

- **Django as source of truth:** All authoring in Django admin
- **Automatic generation:** Static files generated on save
- **Version tracking:** `updatedAt` timestamp in theme files
- **Valkey compatibility:** Drop-in replacement for Redis (existing tooling works)

### Security ✅

- **Encryption-at-rest:** All sensitive data encrypted before Valkey/PostgreSQL
- **Memory safety:** Rust layer ensures no memory leaks of plaintext data
- **Ephemeral keys:** Encryption keys from OpenBao, never persisted
- **Compliance:** GDPR, NIST, PCI DSS compliant data flow

---

## Implementation Priority

**Priority 2:** SHOULD FIX (4-6 hours)

**Effort Breakdown:**

- Django backend (models, admin, generator): 2 hours
- Web frontend (CSS loading, component updates): 1 hour
- Mobile frontend (JSON loading, hook, components): 1.5 hours
- Testing and documentation: 1 hour
- **Total:** 5.5 hours

**Dependencies:**

- None (can be implemented independently)

**Impact:**

- MEDIUM-HIGH - Enables runtime theme customisation
- Excellent performance (no database overhead)
- Multi-tenant support for external projects

---

## Testing Checklist

### Backend ✅

- [ ] Create ThemeConfiguration model and run migrations
- [ ] Access Django admin at `/admin/theme/themeconfiguration/`
- [ ] Create theme for "acme-corp" with custom colours
- [ ] Verify CSS file generated at `/static/tokens/acme-corp/theme.css`
- [ ] Verify JSON file generated at `/static/tokens/acme-corp/theme.json`
- [ ] Update theme colour, verify files regenerate

### Web ✅

- [ ] Load page for `acme-corp.syntek.com`
- [ ] Verify CSS file loaded in Network tab
- [ ] Open DevTools, check `:root` has `--color-primary` variable
- [ ] Verify button uses `var(--color-primary)` colour
- [ ] Change theme in Django admin, clear cache, reload
- [ ] Verify new colour applied

### Mobile ✅

- [ ] Launch app, verify theme JSON fetched
- [ ] Check AsyncStorage has cached theme
- [ ] Verify button uses theme colour from JSON
- [ ] Close and reopen app, verify instant load from cache
- [ ] Change theme in Django, verify app fetches update

### Performance ✅

- [ ] Web: CSS file cached for 1 year (check Cache-Control header)
- [ ] Mobile: Theme loaded instantly from cache on relaunch
- [ ] Verify NO database queries for theme data (Django Debug Toolbar)

---

## Conclusion

The **static file generation architecture** for design tokens provides:

- ✅ **Django as source of truth** (CMS authoring)
- ✅ **Static files as delivery mechanism** (excellent performance)
- ✅ **Zero database overhead** (CDN-cached)
- ✅ **Runtime updates** (no rebuild required)
- ✅ **Multi-tenant support** (each client gets their own theme)

This approach balances **configurability, performance, and maintainability** perfectly.

---

**Recommendation:** Implement in Priority 2 (post-MVP, 4-6 hours effort)

**Alternative:** If multi-tenant branding is not required immediately, this can be deferred to a future release. Current TypeScript constants work fine for single-tenant deployments.
