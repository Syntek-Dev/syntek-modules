# Implementation Plan: Global Design Token & Component Configuration System

**Date:** 15.02.2026
**Status:** 📋 AWAITING APPROVAL
**Effort:** 40-49 hours (phased implementation)
**Priority:** HIGH - Enables full multi-tenant theming across ALL modules

---

## Executive Summary

### Current State

- **0/141 design tokens** Django-configurable (0%)
- **0/7 components** have configurable styling
- External projects must modify TypeScript source files to customise branding
- No runtime theme updates possible (requires rebuild)
- **Every module** (authentication, profiles, media, payments, notifications, etc.) has hardcoded styling

### Proposed Solution

Implement comprehensive Django models for **all 141 design tokens** and **7+ component configurations** using a normalized database structure with static file generation.

**CRITICAL:** This is a **GLOBAL theming system** affecting:

- ✅ **Backend:** ALL 27+ feature modules (authentication, profiles, media, payments, notifications, search, forms, comments, analytics, bookings, etc.)
- ✅ **Web:** ALL ui-\* packages
- ✅ **Mobile:** ALL mobile-\* packages
- ✅ **Shared:** ALL shared components

### Key Benefits

- ✅ **100% token configurability** - All 141 tokens Django-managed, used by ALL modules
- ✅ **Runtime theme updates** - No rebuild required for ANY module
- ✅ **Multi-tenant support** - Each client gets branded theme across ALL features
- ✅ **Excellent performance** - Static files cached by Next.js/browser
- ✅ **Maintainable architecture** - Normalized models (~40-150 lines each)
- ✅ **Universal consistency** - Same theme tokens across authentication, profiles, media, payments, etc.

---

## Architectural Decisions

### 1. Normalized Database Structure ✅ APPROVED

**Architecture:** 9 separate Django models (1 parent + 8 children) instead of monolithic 150+ field model.

#### Parent Model: ThemeConfiguration

- **Fields:** 5 (client_id, name, description, is_active, timestamps)
- **Purpose:** Central metadata, references to all token categories
- **Relationships:** OneToOne to each child model

#### Child Models (OneToOneField to parent)

| Model                       | Fields | File Size  | Purpose                                                     |
| --------------------------- | ------ | ---------- | ----------------------------------------------------------- |
| **ColorConfiguration**      | 60+    | ~150 lines | All color tokens (primary, semantic, auth, social)          |
| **TypographyConfiguration** | 27     | ~80 lines  | Font families, sizes, weights, line heights, letter spacing |
| **SpacingConfiguration**    | 14     | ~40 lines  | Spacing scale (0, 1, 2, 3, 4, 6, 8, 12, 16, 20, 24, 32)     |
| **BorderConfiguration**     | 13     | ~40 lines  | Border radius (8 values), border width (5 values)           |
| **ShadowConfiguration**     | 14     | ~50 lines  | Box shadows (7 values), elevation levels (7 values)         |
| **BreakpointConfiguration** | 5      | ~30 lines  | Responsive breakpoints (sm, md, lg, xl, 2xl)                |
| **ZIndexConfiguration**     | 9      | ~35 lines  | Stacking order (dropdown, sticky, modal, toast, etc.)       |
| **ComponentConfiguration**  | 7+     | ~60 lines  | Component styling (JSONField-based)                         |

**Total:** ~485 lines across 9 files vs 1000+ in single monolithic model.

#### Benefits of Normalized Structure

- ✅ **Maintainability** - Each model ~40-150 lines (manageable)
- ✅ **Organization** - Clear separation of concerns
- ✅ **Django Admin** - Organized with TabularInline/StackedInline
- ✅ **Database design** - Follows normalization principles
- ✅ **Testing** - Test each token category independently
- ✅ **Extensibility** - Easy to add new token categories

---

### 2. Static File Generation ✅ APPROVED

**Critical Principle:** Django is source of truth, static files are delivery mechanism.

#### Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Django Admin - Client updates theme → Save to PostgreSQL     │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. Django Signal - Generate static files:                       │
│    • /tokens/{client-id}/theme.css (CSS custom properties)      │
│    • /tokens/{client-id}/theme.json (JSON for React Native)     │
│    Save to Django static files directory                        │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. Next.js Build - Optimize and cache in .next directory        │
│    • Minification and compression (gzip/brotli)                 │
│    • Code splitting and tree shaking                            │
│    • Cache-Control headers (immutable assets)                   │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. Frontend - Load static file (cached, no DB hit)              │
│    Web: <link href="/tokens/{client-id}/theme.css">             │
│    Mobile: Fetch JSON, cache in AsyncStorage                    │
└─────────────────────────────────────────────────────────────────┘
```

#### Performance Characteristics

| Approach                 | Database Calls     | Page Load Impact | Rebuild Required |
| ------------------------ | ------------------ | ---------------- | ---------------- |
| ❌ GraphQL on every load | 1 per page load    | +50-100ms        | No               |
| ✅ Static CSS file       | 0 (Next.js cached) | +0ms (cached)    | No               |
| ✅ Static JSON (mobile)  | 0 (device cached)  | +0ms (cached)    | No               |

**Static file approach is 50-100ms faster per page load** ✅

---

### 3. Valkey Caching Strategy ✅ APPROVED

**Critical Requirement:** Use **Valkey** for all caching, NOT Redis.

#### Why Valkey?

- ✅ **Open-source** - True OSS license (BSD 3-Clause)
- ✅ **Redis-compatible** - Drop-in replacement
- ✅ **Community-driven** - Linux Foundation project
- ✅ **Future-proof** - No corporate license changes

#### Valkey Use Cases

1. **Session caching** - Encrypted session data
2. **GraphQL query results** - Cache frequently accessed configuration
3. **Rate limiting** - Track request counts per IP/user
4. **CSRF tokens** - Store and validate tokens
5. **MFA codes** - Temporary TOTP/backup code storage (encrypted)

#### Data Flow Architecture (Encryption-at-Rest)

**CRITICAL:** All sensitive data encrypted BEFORE caching in Valkey or storing in PostgreSQL.

```
User Request (plaintext)
  ↓
Rust Layer (syntek-modules)
  • Encrypt using ChaCha20-Poly1305 or AES-256-GCM
  • Zeroise plaintext from memory (zeroize crate)
  • Keys fetched from OpenBao (ephemeral, in-memory only)
  ↓
Valkey (encrypted data in memory)
  • Stores encrypted blobs only (never plaintext)
  ↓
PostgreSQL (encrypted data at rest)
  • Stores encrypted blobs (passwords, PII, sessions)
```

**Compliance:**

- ✅ GDPR Article 32 - Encryption of personal data
- ✅ NIST 800-53 SC-28 - Protection of data at rest
- ✅ PCI DSS 3.2.1 - Encryption of cardholder data
- ✅ OWASP A02:2021 - Cryptographic failures prevention

---

## Complete Token Inventory (141 Values)

### 1. Colors (60+ values)

#### Primary Brand Colors (10 shades: 50, 100, 200, 300, 400, 500, 600, 700, 800, 900)

```python
primary_50 = models.CharField(max_length=7, default='#eff6ff')
primary_100 = models.CharField(max_length=7, default='#dbeafe')
# ... through primary_900
primary_900 = models.CharField(max_length=7, default='#1e3a8a')
```

#### Semantic Colors (12 values: success, warning, error, info × 3 variants each)

```python
# Success (3 values)
success_light = models.CharField(max_length=7, default='#d1fae5')
success_default = models.CharField(max_length=7, default='#10b981')
success_dark = models.CharField(max_length=7, default='#065f46')

# Warning, Error, Info follow same pattern
```

#### Neutral Colors (10 shades: 50 → 900)

```python
neutral_50 = models.CharField(max_length=7, default='#fafafa')
# ... through neutral_900
neutral_900 = models.CharField(max_length=7, default='#171717')
```

#### Status/State Colors (16 values - Used by ALL modules)

```python
# Status indicators (used across all features: auth, profiles, media, payments, etc.)
status_active = models.CharField(max_length=7, default='#10b981')
status_inactive = models.CharField(max_length=7, default='#6b7280')
status_pending = models.CharField(max_length=7, default='#f59e0b')
status_suspended = models.CharField(max_length=7, default='#ef4444')

# Progress indicators (strength meters, upload progress, verification steps)
progress_weak = models.CharField(max_length=7, default='#ef4444')
progress_fair = models.CharField(max_length=7, default='#f59e0b')
progress_good = models.CharField(max_length=7, default='#10b981')
progress_excellent = models.CharField(max_length=7, default='#059669')

# Verification states (email verification, payment verification, document verification)
verified = models.CharField(max_length=7, default='#10b981')
unverified = models.CharField(max_length=7, default='#6b7280')
verification_failed = models.CharField(max_length=7, default='#ef4444')

# Security levels (session security, file security, account security)
security_high = models.CharField(max_length=7, default='#10b981')
security_medium = models.CharField(max_length=7, default='#f59e0b')
security_low = models.CharField(max_length=7, default='#ef4444')
security_critical = models.CharField(max_length=7, default='#dc2626')
```

#### Third-Party Brand Colors (7 values - Used across social auth, integrations, payments)

```python
# Social providers (authentication, profile linking, sharing)
brand_google = models.CharField(max_length=7, default='#4285f4')
brand_github = models.CharField(max_length=7, default='#24292e')
brand_microsoft = models.CharField(max_length=7, default='#00a4ef')
brand_apple = models.CharField(max_length=7, default='#000000')

# Payment providers (checkout, invoices, subscriptions)
brand_stripe = models.CharField(max_length=7, default='#635bff')
brand_paypal = models.CharField(max_length=7, default='#0070ba')
brand_visa = models.CharField(max_length=7, default='#1a1f71')
```

---

### 2. Typography (27 values)

```python
# Font families (2 TextField for font stacks)
font_family_sans = models.TextField(
    default='Inter, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif'
)
font_family_mono = models.TextField(
    default='JetBrains Mono, Monaco, Courier New, monospace'
)

# Font sizes (9 values: xs, sm, base, lg, xl, 2xl, 3xl, 4xl, 5xl)
font_size_xs = models.CharField(max_length=10, default='0.75rem')    # 12px
font_size_sm = models.CharField(max_length=10, default='0.875rem')   # 14px
font_size_base = models.CharField(max_length=10, default='1rem')     # 16px
# ... through font_size_5xl
font_size_5xl = models.CharField(max_length=10, default='3rem')      # 48px

# Font weights (4 values: normal, medium, semibold, bold)
font_weight_normal = models.CharField(max_length=3, default='400')
font_weight_medium = models.CharField(max_length=3, default='500')
font_weight_semibold = models.CharField(max_length=3, default='600')
font_weight_bold = models.CharField(max_length=3, default='700')

# Line heights (6 values: none, tight, snug, normal, relaxed, loose)
line_height_none = models.CharField(max_length=10, default='1')
# ... through line_height_loose
line_height_loose = models.CharField(max_length=10, default='2')

# Letter spacing (6 values: tighter, tight, normal, wide, wider, widest)
letter_spacing_tighter = models.CharField(max_length=10, default='-0.05em')
# ... through letter_spacing_widest
letter_spacing_widest = models.CharField(max_length=10, default='0.1em')
```

---

### 3. Spacing (14 values)

```python
spacing_0 = models.CharField(max_length=10, default='0px')
spacing_1 = models.CharField(max_length=10, default='4px')      # Base scale
spacing_2 = models.CharField(max_length=10, default='8px')
spacing_3 = models.CharField(max_length=10, default='12px')
spacing_4 = models.CharField(max_length=10, default='16px')
spacing_5 = models.CharField(max_length=10, default='20px')
spacing_6 = models.CharField(max_length=10, default='24px')
spacing_8 = models.CharField(max_length=10, default='32px')
spacing_10 = models.CharField(max_length=10, default='40px')
spacing_11 = models.CharField(max_length=10, default='44px')    # iOS touch target
spacing_12 = models.CharField(max_length=10, default='48px')
spacing_16 = models.CharField(max_length=10, default='64px')
spacing_20 = models.CharField(max_length=10, default='80px')
spacing_24 = models.CharField(max_length=10, default='96px')
spacing_32 = models.CharField(max_length=10, default='128px')
```

---

### 4. Borders (13 values)

```python
# Border radius (8 values: none, sm, default, md, lg, xl, 2xl, full)
border_radius_none = models.CharField(max_length=10, default='0px')
border_radius_sm = models.CharField(max_length=10, default='4px')
border_radius_default = models.CharField(max_length=10, default='8px')
# ... through border_radius_full
border_radius_full = models.CharField(max_length=10, default='9999px')

# Border width (5 values: 0, default, 2, 4, 8)
border_width_0 = models.CharField(max_length=10, default='0px')
border_width_default = models.CharField(max_length=10, default='1px')
border_width_2 = models.CharField(max_length=10, default='2px')
border_width_4 = models.CharField(max_length=10, default='4px')
border_width_8 = models.CharField(max_length=10, default='8px')
```

---

### 5. Shadows (14 values)

```python
# Box shadows for web (7 values: none, sm, default, md, lg, xl, 2xl)
box_shadow_none = models.CharField(max_length=10, default='none')
box_shadow_sm = models.TextField(default='0 1px 2px 0 rgba(0, 0, 0, 0.05)')
box_shadow_default = models.TextField(
    default='0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)'
)
# ... through box_shadow_2xl
box_shadow_2xl = models.TextField(default='0 25px 50px -12px rgba(0, 0, 0, 0.25)')

# Elevation levels for React Native (7 values: 0 → 6)
elevation_0 = models.IntegerField(default=0)
elevation_1 = models.IntegerField(default=1)
elevation_2 = models.IntegerField(default=2)
elevation_3 = models.IntegerField(default=4)
elevation_4 = models.IntegerField(default=6)
elevation_5 = models.IntegerField(default=8)
elevation_6 = models.IntegerField(default=12)
```

---

### 6. Breakpoints (5 values)

```python
breakpoint_sm = models.CharField(max_length=10, default='640px')
breakpoint_md = models.CharField(max_length=10, default='768px')
breakpoint_lg = models.CharField(max_length=10, default='1024px')
breakpoint_xl = models.CharField(max_length=10, default='1280px')
breakpoint_2xl = models.CharField(max_length=10, default='1536px')
```

---

### 7. Z-Index (9 values)

```python
z_index_base = models.IntegerField(default=0)
z_index_dropdown = models.IntegerField(default=1000)
z_index_sticky = models.IntegerField(default=1100)
z_index_fixed = models.IntegerField(default=1200)
z_index_modal_backdrop = models.IntegerField(default=1300)
z_index_modal = models.IntegerField(default=1400)
z_index_popover = models.IntegerField(default=1500)
z_index_toast = models.IntegerField(default=1600)
z_index_tooltip = models.IntegerField(default=1700)
```

---

## Component Configuration (7+ Components)

### ComponentConfiguration Model

```python
class ComponentConfiguration(models.Model):
    """Component-specific styling configuration (JSONField-based)."""

    theme = models.OneToOneField(
        ThemeConfiguration,
        on_delete=models.CASCADE,
        related_name='components',
        primary_key=True,
    )

    # Button component
    button_variant_config = models.JSONField(
        default=dict,
        help_text="Button variant configurations (primary, secondary, danger, ghost)"
    )
    # Example: {
    #   "primary": {
    #     "background": "primary-600",
    #     "hover": "primary-700",
    #     "active": "primary-700",
    #     "disabled": "primary-300",
    #     "text_color": "white"
    #   }
    # }

    button_size_config = models.JSONField(
        default=dict,
        help_text="Button size configurations (sm, md, lg)"
    )

    # Input component
    input_state_config = models.JSONField(
        default=dict,
        help_text="Input state configurations (default, focus, error, disabled)"
    )

    # Alert component
    alert_type_config = models.JSONField(
        default=dict,
        help_text="Alert type configurations (success, error, warning, info)"
    )

    # Badge component
    badge_variant_config = models.JSONField(default=dict)
    badge_size_config = models.JSONField(default=dict)

    # Checkbox component
    checkbox_config = models.JSONField(default=dict)

    # Card component
    card_config = models.JSONField(default=dict)

    # Spinner component
    spinner_config = models.JSONField(default=dict)
```

---

## Cross-Module Token Usage Examples

**CRITICAL:** These design tokens are used by **ALL modules** in syntek-modules, not just authentication.

### Example 1: Authentication Module

```typescript
// web/packages/ui-auth/src/components/PasswordStrengthIndicator.tsx
import { useTheme } from '@syntek/shared/hooks/useTheme';

function PasswordStrengthIndicator({ strength }: Props) {
  const theme = useTheme();

  // Uses global progress colors
  const color = {
    weak: theme.colors.progress.weak,      // #ef4444
    fair: theme.colors.progress.fair,      // #f59e0b
    good: theme.colors.progress.good,      // #10b981
    excellent: theme.colors.progress.excellent, // #059669
  }[strength];

  return <div style={{ backgroundColor: color }} />;
}
```

### Example 2: Media Upload Module

```typescript
// web/packages/ui-media/src/components/UploadProgressBar.tsx
import { useTheme } from '@syntek/shared/hooks/useTheme';

function UploadProgressBar({ progress }: Props) {
  const theme = useTheme();

  // Uses SAME progress colors as password strength!
  const color = progress < 25
    ? theme.colors.progress.weak
    : progress < 50
    ? theme.colors.progress.fair
    : progress < 75
    ? theme.colors.progress.good
    : theme.colors.progress.excellent;

  return <ProgressBar color={color} value={progress} />;
}
```

### Example 3: Profile Verification Module

```typescript
// web/packages/ui-profiles/src/components/EmailVerificationBadge.tsx
import { useTheme } from '@syntek/shared/hooks/useTheme';

function EmailVerificationBadge({ isVerified }: Props) {
  const theme = useTheme();

  // Uses global verification status colors
  const badge = isVerified
    ? { color: theme.colors.verified, text: 'Verified' }
    : { color: theme.colors.unverified, text: 'Unverified' };

  return <Badge color={badge.color}>{badge.text}</Badge>;
}
```

### Example 4: Payment Status Module

```typescript
// web/packages/ui-payments/src/components/PaymentStatusIndicator.tsx
import { useTheme } from '@syntek/shared/hooks/useTheme';

function PaymentStatusIndicator({ status }: Props) {
  const theme = useTheme();

  // Uses global status colors
  const statusConfig = {
    completed: { color: theme.colors.status.active, text: 'Paid' },
    pending: { color: theme.colors.status.pending, text: 'Processing' },
    failed: { color: theme.colors.status.suspended, text: 'Failed' },
  }[status];

  return <StatusBadge color={statusConfig.color}>{statusConfig.text}</StatusBadge>;
}
```

### Example 5: Session Security (Backend)

```python
# backend/security-auth/sessions/models.py
from backend.security_core.theme.models import ThemeConfiguration

class Session(models.Model):
    security_level = models.CharField(max_length=20)  # 'high', 'medium', 'low', 'critical'

    def get_security_color(self, client_id: str) -> str:
        """Get security level color from theme configuration."""
        theme = ThemeConfiguration.objects.get(client_id=client_id)
        colors = theme.colors

        # All modules use the same security level colors
        return {
            'high': colors.security_high,
            'medium': colors.security_medium,
            'low': colors.security_low,
            'critical': colors.security_critical,
        }[self.security_level]
```

### Example 6: Multi-Module Dashboard

```typescript
// web/app/dashboard/page.tsx
import { useTheme } from '@syntek/shared/hooks/useTheme';

function Dashboard() {
  const theme = useTheme();

  return (
    <div>
      {/* Authentication widget - uses global status colors */}
      <SessionStatus color={theme.colors.status.active} />

      {/* Profile widget - uses global verification colors */}
      <EmailBadge color={theme.colors.verified} />

      {/* Payment widget - uses global status colors */}
      <SubscriptionStatus color={theme.colors.status.active} />

      {/* Media widget - uses global progress colors */}
      <UploadProgress color={theme.colors.progress.good} />

      {/* All widgets share the same theme! */}
    </div>
  );
}
```

**Key Insight:** All modules (authentication, profiles, media, payments, notifications, etc.) use the **SAME design tokens** from the Django theme configuration. This ensures visual consistency across the entire application.

---

## Implementation Phases

### Phase 1: Core Tokens (12-15 hours) 🔴 HIGH PRIORITY

**Scope:**

- ThemeConfiguration (parent model)
- ColorConfiguration (60+ fields) - **Used by ALL modules**
- TypographyConfiguration (27 fields) - **Used by ALL modules**
- SpacingConfiguration (14 fields) - **Used by ALL modules**

**Impact:**

- ✅ **Backend:** ALL 27+ feature modules get configurable colors, typography, spacing
- ✅ **Web:** ALL ui-\* packages get consistent theming
- ✅ **Mobile:** ALL mobile-\* packages get consistent theming
- ✅ **Shared:** ALL shared components use centralized tokens

**Deliverables:**

1. Django models with core token fields (global, not module-specific)
2. Django admin interface with organized inlines
3. Theme generator (CSS + JSON) for core tokens
4. Management command: `create_default_theme`
5. Unit tests for model validation
6. Integration tests for theme generation across multiple modules

**Success Criteria:**

- [ ] Models created and migrations run successfully
- [ ] Django admin accessible with organized fieldsets
- [ ] CSS file generated at `/tokens/{client-id}/theme.css` on save (usable by ALL modules)
- [ ] JSON file generated at `/tokens/{client-id}/theme.json` on save (usable by ALL modules)
- [ ] Default theme created with sensible values
- [ ] All tests passing
- [ ] Example usage in authentication, profiles, and media modules

**Effort Breakdown:**

- Models (3 core + parent): 4-5 hours
- Django admin configuration: 2-3 hours
- Theme generator (CSS + JSON): 3-4 hours
- Management command + tests: 3 hours

---

### Phase 2: Extended Tokens (10-12 hours) 🟡 MEDIUM PRIORITY

**Scope:**

- BorderConfiguration (13 fields)
- ShadowConfiguration (14 fields)
- BreakpointConfiguration (5 fields)
- ZIndexConfiguration (9 fields)

**Deliverables:**

1. Django models for extended tokens
2. Update Django admin with new inlines
3. Update theme generator to include extended tokens
4. Integration tests for complete theme generation

**Success Criteria:**

- [ ] All 4 extended token models created
- [ ] Admin interface updated with new fieldsets
- [ ] CSS output includes all extended tokens
- [ ] JSON output includes all extended tokens
- [ ] All 141 tokens represented in output files
- [ ] Tests covering all token categories

**Effort Breakdown:**

- Models (4 extended): 3-4 hours
- Admin updates: 1-2 hours
- Theme generator updates: 3-4 hours
- Testing: 3 hours

---

### Phase 3: Component Configurations (8-10 hours) 🟡 MEDIUM PRIORITY

**Scope:**

- ComponentConfiguration model (7+ JSONField configs)
- Button, Input, Alert, Badge, Checkbox, Card, Spinner

**Deliverables:**

1. ComponentConfiguration model with JSONFields
2. Django admin for component configs
3. Update theme generator to include component configs in JSON
4. Example component config defaults
5. Documentation for component config schema

**Success Criteria:**

- [ ] ComponentConfiguration model created
- [ ] Admin interface with JSON editor widgets
- [ ] Theme JSON includes component configurations
- [ ] Default component configs provided
- [ ] Documentation for each component config schema
- [ ] Tests for component config serialization

**Effort Breakdown:**

- Model + admin: 2-3 hours
- Theme generator updates: 2 hours
- Default configs + docs: 3-4 hours
- Testing: 1-2 hours

---

### Phase 4: Example Apps & Documentation (10-12 hours) 🟢 LOW PRIORITY

**Scope:**

- Django minimal example app
- Next.js minimal example app
- React Native minimal example app
- Comprehensive documentation

**Deliverables:**

1. **Django Example** (`examples/django-minimal/`)
   - Complete Django project with theme configuration
   - README with setup instructions
   - Shows INSTALLED_APPS, STATIC settings, URL configuration

2. **Next.js Example** (`examples/nextjs-minimal/`)
   - Complete Next.js project using `@syntek/ui-auth`
   - README with setup instructions
   - Shows layout.tsx theme loading, Tailwind v4 config

3. **React Native Example** (`examples/react-native-minimal/`)
   - Complete React Native project using `@syntek/mobile-auth`
   - README with setup instructions
   - Shows useTheme() hook, NativeWind 4 config

4. **Documentation**
   - Complete installation guide
   - Django model field reference
   - Theme generator API docs
   - Component config schema docs
   - Multi-tenant setup guide

**Success Criteria:**

- [ ] All 3 example apps functional and documented
- [ ] Each example app has step-by-step README
- [ ] Comprehensive docs covering all aspects
- [ ] Examples demonstrate multi-tenant theming
- [ ] Examples show web and mobile integration

**Effort Breakdown:**

- Django example: 2 hours
- Next.js example: 2 hours
- React Native example: 2 hours
- Documentation: 4-6 hours

---

## File Structure

```
backend/security-core/theme/
├── __init__.py
├── models/
│   ├── __init__.py              # Import all models
│   ├── theme.py                 # ThemeConfiguration (parent) ~50 lines
│   ├── colors.py                # ColorConfiguration ~150 lines
│   ├── typography.py            # TypographyConfiguration ~80 lines
│   ├── spacing.py               # SpacingConfiguration ~40 lines
│   ├── borders.py               # BorderConfiguration ~40 lines
│   ├── shadows.py               # ShadowConfiguration ~50 lines
│   ├── breakpoints.py           # BreakpointConfiguration ~30 lines
│   ├── zindex.py                # ZIndexConfiguration ~35 lines
│   └── components.py            # ComponentConfiguration ~60 lines
├── admin.py                     # Django admin with inlines ~150 lines
├── theme_generator.py           # ThemeGenerator class ~300 lines
├── management/
│   └── commands/
│       └── create_default_theme.py  # Management command ~80 lines
└── tests/
    ├── test_models.py           # Model validation tests
    ├── test_theme_generator.py  # Theme generation tests
    └── test_admin.py            # Admin interface tests

web/app/
├── layout.tsx                   # Load theme CSS (updated)

mobile/packages/mobile-auth/src/
├── hooks/
│   └── useTheme.ts              # Theme loading hook (new)
└── components/
    └── Button.tsx               # Use theme from hook (updated)

examples/
├── django-minimal/              # Django example app
├── nextjs-minimal/              # Next.js example app
└── react-native-minimal/        # React Native example app
```

**Total New Files:** ~20 files
**Total Modified Files:** ~5 files
**Total Lines of Code:** ~1,200 lines

---

## Django Admin Interface

### Parent Admin with Organized Inlines

```python
@admin.register(ThemeConfiguration)
class ThemeConfigurationAdmin(admin.ModelAdmin):
    list_display = ['client_id', 'name', 'is_active', 'updated_at']
    search_fields = ['client_id', 'name']
    list_filter = ['is_active', 'created_at']

    inlines = [
        ColorConfigurationInline,        # StackedInline with organized fieldsets
        TypographyConfigurationInline,   # StackedInline
        SpacingConfigurationInline,      # TabularInline (simple values)
        BorderConfigurationInline,       # TabularInline
        ShadowConfigurationInline,       # StackedInline (long values)
        BreakpointConfigurationInline,   # TabularInline
        ZIndexConfigurationInline,       # TabularInline
        ComponentConfigurationInline,    # StackedInline with JSON editor
    ]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Automatically generate theme files on save
        obj.generate_theme_files()
        self.message_user(request, f"Theme files generated for {obj.client_id}")
```

### ColorConfigurationInline Example

```python
class ColorConfigurationInline(admin.StackedInline):
    model = ColorConfiguration
    can_delete = False
    fieldsets = [
        ('Primary Brand Colours', {
            'fields': [
                ('primary_50', 'primary_100', 'primary_200'),
                ('primary_300', 'primary_400', 'primary_500'),
                ('primary_600', 'primary_700', 'primary_800', 'primary_900'),
            ],
            'description': 'Used across ALL modules: authentication, profiles, media, payments, etc.'
        }),
        ('Semantic Colours (Global)', {
            'fields': [
                ('success_light', 'success_default', 'success_dark'),
                ('warning_light', 'warning_default', 'warning_dark'),
                ('error_light', 'error_default', 'error_dark'),
                ('info_light', 'info_default', 'info_dark'),
            ],
            'description': 'Used by all features: form validation, notifications, alerts, status messages'
        }),
        ('Neutral Colours', {
            'fields': [
                ('neutral_50', 'neutral_100', 'neutral_200'),
                ('neutral_300', 'neutral_400', 'neutral_500'),
                ('neutral_600', 'neutral_700', 'neutral_800', 'neutral_900'),
            ],
            'description': 'Text, backgrounds, borders across all modules'
        }),
        ('Status/State Colours (Global)', {
            'fields': [
                ('status_active', 'status_inactive', 'status_pending', 'status_suspended'),
                ('progress_weak', 'progress_fair', 'progress_good', 'progress_excellent'),
                ('verified', 'unverified', 'verification_failed'),
                ('security_high', 'security_medium', 'security_low', 'security_critical'),
            ],
            'classes': ['collapse'],
            'description': 'Used by authentication, profiles, media uploads, payments, subscriptions, etc.'
        }),
        ('Third-Party Brand Colours', {
            'fields': [
                ('brand_google', 'brand_github', 'brand_microsoft', 'brand_apple'),
                ('brand_stripe', 'brand_paypal', 'brand_visa'),
            ],
            'classes': ['collapse'],
            'description': 'Social auth, profile linking, payment providers, integrations'
        }),
    ]
```

---

## Theme Generator

### ThemeGenerator Class

```python
class ThemeGenerator:
    """Generate static theme files from normalized Django models."""

    def __init__(self, theme: ThemeConfiguration):
        self.theme = theme
        self.client_id = theme.client_id

    def generate_css(self) -> str:
        """Generate comprehensive CSS from all related configurations."""
        # Fetch all related configurations (normalized structure)
        colors = self.theme.colors
        typography = self.theme.typography
        spacing = self.theme.spacing
        borders = self.theme.borders
        shadows = self.theme.shadows
        breakpoints = self.theme.breakpoints
        zindex = self.theme.zindex

        css_content = f"""/**
 * Syntek Theme: {self.client_id}
 * Generated: {self.theme.updated_at.isoformat()}
 */

:root {{
  /* Colors - Primary */
  --color-primary-50: {colors.primary_50};
  --color-primary-500: {colors.primary_500};
  /* ... all 60+ color values */

  /* Typography */
  --font-sans: {typography.font_family_sans};
  --font-size-base: {typography.font_size_base};
  /* ... all 27 typography values */

  /* Spacing */
  --spacing-1: {spacing.spacing_1};
  /* ... all 14 spacing values */

  /* Borders */
  --border-radius-default: {borders.border_radius_default};
  /* ... all 13 border values */

  /* Shadows */
  --box-shadow-md: {shadows.box_shadow_md};
  /* ... all 14 shadow values */

  /* Breakpoints */
  --breakpoint-md: {breakpoints.breakpoint_md};
  /* ... all 5 breakpoint values */

  /* Z-Index */
  --z-index-modal: {zindex.z_index_modal};
  /* ... all 9 z-index values */
}}
"""

        # Save to static storage
        file_path = f'tokens/{self.client_id}/theme.css'
        default_storage.save(file_path, ContentFile(css_content.encode()))
        return file_path

    def generate_json(self) -> str:
        """Generate comprehensive JSON from all related configurations."""
        # Fetch all related configurations
        colors = self.theme.colors
        typography = self.theme.typography
        # ... fetch all other configs

        theme_data = {
            'clientId': self.client_id,
            'updatedAt': self.theme.updated_at.isoformat(),
            'colors': {
                'primary': {
                    '50': colors.primary_50,
                    '500': colors.primary_500,
                    # ... all primary shades
                },
                # ... all color categories
            },
            'typography': {
                'fontFamily': {
                    'sans': typography.font_family_sans,
                    'mono': typography.font_family_mono,
                },
                # ... all typography values
            },
            # ... all other token categories
        }

        json_content = json.dumps(theme_data, indent=2)
        file_path = f'tokens/{self.client_id}/theme.json'
        default_storage.save(file_path, ContentFile(json_content.encode()))
        return file_path
```

---

## Database Schema

```sql
-- Parent table
CREATE TABLE syntek_theme_configuration (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Child tables (OneToOne relationship via primary key)
CREATE TABLE syntek_theme_colors (
    theme_id INTEGER PRIMARY KEY REFERENCES syntek_theme_configuration(id) ON DELETE CASCADE,
    primary_50 VARCHAR(7) DEFAULT '#eff6ff',
    primary_500 VARCHAR(7) DEFAULT '#3b82f6',
    -- ... 58 more color fields
);

CREATE TABLE syntek_theme_typography (
    theme_id INTEGER PRIMARY KEY REFERENCES syntek_theme_configuration(id) ON DELETE CASCADE,
    font_family_sans TEXT DEFAULT 'Inter, system-ui, sans-serif',
    font_size_base VARCHAR(10) DEFAULT '1rem',
    -- ... 25 more typography fields
);

-- ... 6 more token category tables (spacing, borders, shadows, breakpoints, zindex, components)
```

**Benefits:**

- ✅ **Normalized structure** - Each table has focused responsibility
- ✅ **Easy to query** - `theme.colors.primary_500` in Django ORM
- ✅ **Cascading deletes** - Delete theme → automatically delete all related configs
- ✅ **Indexing** - Can index specific token categories if needed

---

## Testing Strategy

### Unit Tests

**File:** `backend/security-core/theme/tests/test_models.py`

```python
class ThemeConfigurationTests(TestCase):
    def test_create_theme_with_defaults(self):
        """Test creating theme with default values."""
        theme = ThemeConfiguration.objects.create(client_id='test-client')
        self.assertEqual(theme.client_id, 'test-client')
        self.assertTrue(theme.is_active)

    def test_colors_created_with_theme(self):
        """Test ColorConfiguration automatically created with theme."""
        theme = ThemeConfiguration.objects.create(client_id='test-client')
        colors = ColorConfiguration.objects.get(theme=theme)
        self.assertEqual(colors.primary_500, '#3b82f6')  # Default value

    def test_typography_defaults(self):
        """Test TypographyConfiguration defaults."""
        theme = ThemeConfiguration.objects.create(client_id='test-client')
        typography = TypographyConfiguration.objects.get(theme=theme)
        self.assertIn('Inter', typography.font_family_sans)
        self.assertEqual(typography.font_size_base, '1rem')

    # ... tests for each token category
```

### Integration Tests

**File:** `backend/security-core/theme/tests/test_theme_generator.py`

```python
class ThemeGeneratorTests(TestCase):
    def test_generate_css_includes_all_tokens(self):
        """Test CSS generation includes all 141 tokens."""
        theme = ThemeConfiguration.objects.create(client_id='test-client')
        generator = ThemeGenerator(theme)
        css_path = generator.generate_css()

        # Read generated CSS
        css_content = default_storage.open(css_path).read().decode()

        # Verify all token categories present
        self.assertIn('--color-primary-500', css_content)
        self.assertIn('--font-sans', css_content)
        self.assertIn('--spacing-1', css_content)
        self.assertIn('--border-radius-default', css_content)
        self.assertIn('--box-shadow-md', css_content)
        self.assertIn('--breakpoint-md', css_content)
        self.assertIn('--z-index-modal', css_content)

    def test_generate_json_structure(self):
        """Test JSON generation has correct structure."""
        theme = ThemeConfiguration.objects.create(client_id='test-client')
        generator = ThemeGenerator(theme)
        json_path = generator.generate_json()

        # Read and parse generated JSON
        json_content = default_storage.open(json_path).read().decode()
        theme_data = json.loads(json_content)

        # Verify structure
        self.assertEqual(theme_data['clientId'], 'test-client')
        self.assertIn('colors', theme_data)
        self.assertIn('typography', theme_data)
        self.assertIn('spacing', theme_data)
        # ... verify all categories
```

---

## Migration Path

### Step 1: Create Models

```bash
python manage.py makemigrations theme
# Creates migrations for all 9 models (parent + 8 children)
```

### Step 2: Run Migrations

```bash
python manage.py migrate theme
# Creates all 9 tables (parent + 8 children)
```

### Step 3: Create Default Theme

```bash
python manage.py create_default_theme
# Creates ThemeConfiguration for 'default' client
# Automatically creates all 8 related configurations with default values
```

### Step 4: Generate Theme Files

```bash
# Signal handler automatically generates files on save
# Files created at:
# - /static/tokens/default/theme.css
# - /static/tokens/default/theme.json
```

---

## Success Criteria

### Phase 1 Success Criteria

- [ ] ThemeConfiguration model with 5 fields created
- [ ] ColorConfiguration with 60+ color fields created
- [ ] TypographyConfiguration with 27 fields created
- [ ] SpacingConfiguration with 14 fields created
- [ ] Django admin accessible with organized inlines
- [ ] CSS file generated on theme save
- [ ] JSON file generated on theme save
- [ ] Default theme created successfully
- [ ] All unit tests passing (models, validation)
- [ ] Integration tests passing (theme generation)

### Phase 2 Success Criteria

- [ ] BorderConfiguration with 13 fields created
- [ ] ShadowConfiguration with 14 fields created
- [ ] BreakpointConfiguration with 5 fields created
- [ ] ZIndexConfiguration with 9 fields created
- [ ] CSS output includes all 141 tokens
- [ ] JSON output includes all 141 tokens
- [ ] All token categories tested

### Phase 3 Success Criteria

- [ ] ComponentConfiguration with 7+ JSONFields created
- [ ] Component configs included in theme JSON
- [ ] Default component configs defined
- [ ] Component config schema documented

### Phase 4 Success Criteria

- [ ] Django example app functional
- [ ] Next.js example app functional
- [ ] React Native example app functional
- [ ] All examples have comprehensive READMEs
- [ ] Complete installation guide written

---

## Risks & Mitigation

| Risk                                | Likelihood | Impact | Mitigation                                            |
| ----------------------------------- | ---------- | ------ | ----------------------------------------------------- |
| **Model too complex**               | Low        | Medium | Normalized structure keeps each model ~40-150 lines   |
| **Django admin performance**        | Low        | Medium | Use TabularInline for simple fields, optimize queries |
| **CSS file too large**              | Low        | Low    | CSS variables are small (141 values ≈ 5-10KB)         |
| **JSON parsing on mobile**          | Low        | Low    | JSON is small, cached in AsyncStorage                 |
| **Migration conflicts**             | Medium     | Low    | Run migrations in development first, test thoroughly  |
| **Default values incorrect**        | Low        | Low    | Use current design system values, review before merge |
| **Component config schema changes** | Medium     | Medium | Version component configs, provide migration guide    |

---

## Effort Estimates

### Summary by Phase

| Phase       | Scope                                                    | Hours     | Priority  |
| ----------- | -------------------------------------------------------- | --------- | --------- |
| **Phase 1** | Core Tokens (colors, typography, spacing)                | 12-15     | 🔴 HIGH   |
| **Phase 2** | Extended Tokens (borders, shadows, breakpoints, z-index) | 10-12     | 🟡 MEDIUM |
| **Phase 3** | Component Configurations (Button, Input, Alert, etc.)    | 8-10      | 🟡 MEDIUM |
| **Phase 4** | Example Apps & Documentation                             | 10-12     | 🟢 LOW    |
| **TOTAL**   | Full Implementation                                      | **40-49** |           |

### Detailed Breakdown

**Phase 1 (12-15 hours):**

- Django models (parent + 3 core): 4-5 hours
- Django admin configuration: 2-3 hours
- Theme generator (CSS + JSON): 3-4 hours
- Management command + tests: 3 hours

**Phase 2 (10-12 hours):**

- Django models (4 extended): 3-4 hours
- Admin updates: 1-2 hours
- Theme generator updates: 3-4 hours
- Testing: 3 hours

**Phase 3 (8-10 hours):**

- ComponentConfiguration model + admin: 2-3 hours
- Theme generator updates: 2 hours
- Default configs + docs: 3-4 hours
- Testing: 1-2 hours

**Phase 4 (10-12 hours):**

- Django example: 2 hours
- Next.js example: 2 hours
- React Native example: 2 hours
- Documentation: 4-6 hours

---

## Dependencies

### Required

- Django 6.0.2 (already installed)
- PostgreSQL 18.1 (already installed)
- Valkey (must be configured - see Priority 2.5 in Action Items)

### Optional

- django-valkey (for Valkey caching)
- AWS S3 / CloudFront (for CDN deployment - optional)

---

## Recommended Implementation Order

1. **Immediate (Before Starting):**
   - Fix hardcoded `password_max_length` (5 minutes - Priority 1)
   - Configure Valkey caching (30 minutes - Priority 2.5)

2. **Phase 1 (Week 1):**
   - Implement core token models
   - Basic theme generator
   - Django admin setup
   - Create default theme

3. **Phase 2 (Week 2):**
   - Implement extended token models
   - Complete theme generator
   - Comprehensive testing

4. **Phase 3 (Week 3):**
   - Component configuration model
   - Component config defaults
   - Documentation

5. **Phase 4 (Week 4):**
   - Example applications
   - Comprehensive documentation
   - Final testing and polish

---

## Questions for Review

### 1. Approve comprehensive token model?

**Question:** Should we implement normalized Django models (9 models) with 150+ fields for all design tokens?

**Current:** 0/141 tokens configurable (0%)
**Proposed:** 141/141 tokens configurable (100%)
**Effort:** 22-27 hours (Phase 1 + 2)

**Your Decision:** ✅ YES / ❌ NO / 🔄 PHASE 1 ONLY

---

### 2. Approve component configuration model?

**Question:** Should we implement JSONField-based component configurations?

**Current:** All 7 components have hardcoded styling
**Proposed:** All components configurable via Django JSONFields
**Effort:** 8-10 hours (Phase 3)

**Your Decision:** ✅ YES / ❌ NO / 🔄 LATER

---

### 3. Create minimal example apps?

**Question:** Should we add examples/ directory with minimal Django/Next.js/React Native apps?

**Current:** No examples, harder to onboard
**Proposed:** Minimal example apps showing integration
**Effort:** 10-12 hours (Phase 4)

**Your Decision:** ✅ YES / ❌ NO / 🔄 LATER

---

### 4. Keep library-only structure?

**Question:** Should we keep current library-only structure or restructure into full apps?

**Current:** syntek-modules/ with backend/, web/, mobile/ as libraries
**Proposed:** Keep current structure (no restructuring needed)

**Your Decision:** ✅ KEEP LIBRARY STRUCTURE

---

## Next Steps

After approval:

1. **Review this plan** with team and stakeholders
2. **Approve specific phases** to implement
3. **Begin Phase 1 implementation** (if approved)
   - Create branch: `feature/comprehensive-design-tokens`
   - Create models and migrations
   - Implement theme generator
   - Create default theme
   - Write tests
4. **Validate approach** with Phase 1 before proceeding
5. **Iterate** based on feedback

---

## Modules Affected by This Implementation

**CRITICAL:** This is a **GLOBAL theming system** affecting ALL modules in syntek-modules.

### Backend Modules (27+)

All Django feature modules will use the same theme configuration:

**Security Bundles:**

- ✅ security-core (headers, middleware, rate limiting UI)
- ✅ security-auth (login forms, MFA screens, session management)
- ✅ security-input (form validation, error messages)
- ✅ security-network (IP filtering UI, OpenBao integration)

**Feature Modules:**

- ✅ authentication (login, register, password reset, MFA, passkeys, social auth)
- ✅ profiles (profile cards, avatar uploads, bio displays)
- ✅ media (upload progress, file type badges, media galleries)
- ✅ payments (checkout forms, invoice displays, subscription status)
- ✅ notifications (toast messages, notification badges, email templates)
- ✅ search (search bars, result cards, filters)
- ✅ forms (form inputs, validation messages, submit buttons)
- ✅ comments (comment cards, rating displays, moderation UI)
- ✅ analytics (charts, graphs, metric cards, dashboards)
- ✅ bookings (calendar widgets, time slots, booking confirmations)
- ✅ accounting (invoice tables, transaction lists, balance displays)
- ✅ email_marketing (email templates, campaign builders, subscriber lists)
- ✅ audit (audit log tables, timeline views, change indicators)
- ✅ webhooks (webhook status badges, event logs, retry buttons)
- ✅ i18n (language selectors, translation badges)
- ✅ cms_primitives (content blocks, rich text editors, page builders)
- ✅ feature_flags (toggle switches, flag status indicators)
- ✅ groups (group cards, member lists, permission displays)
- ✅ contact (contact forms, support tickets, chat widgets)
- ✅ uploads (drag-drop zones, upload progress, file previews)
- ✅ reporting (report builders, data visualizations, export buttons)
- ✅ logging (log level badges, error displays, debug panels)
- ✅ ai_integration (AI response cards, loading states, prompt inputs)

### Web Packages (ui-\*)

All Next.js UI packages will use the same theme:

- ✅ ui-auth (login forms, MFA screens, session management)
- ✅ ui-profiles (profile cards, settings pages)
- ✅ ui-media (upload widgets, media galleries)
- ✅ ui-payments (checkout flows, invoice displays)
- ✅ ui-notifications (toast messages, notification centers)
- ✅ ui-search (search bars, result grids)
- ✅ ui-forms (form builders, validation)
- ✅ ui-comments (comment threads, ratings)
- ✅ ui-analytics (dashboards, charts)
- ✅ ui-bookings (calendars, time pickers)
- ✅ **ALL future ui-\* packages**

### Mobile Packages (mobile-\*)

All React Native packages will use the same theme:

- ✅ mobile-auth (login screens, biometric prompts)
- ✅ mobile-profiles (profile screens, settings)
- ✅ mobile-media (camera uploads, galleries)
- ✅ mobile-payments (checkout flows, subscriptions)
- ✅ mobile-notifications (push notifications, badges)
- ✅ mobile-search (search screens, filters)
- ✅ mobile-bookings (calendars, appointment screens)
- ✅ **ALL future mobile-\* packages**

### Shared Components

ALL cross-platform components will use the same theme:

- ✅ shared/design-system/components/ (Button, Input, Alert, Badge, Modal, etc.)
- ✅ shared/auth/components/ (LoginForm, PasswordInput, MFAScreen, etc.)
- ✅ **ALL shared components across ALL modules**

**Total Impact:** 40+ packages/modules across backend, web, mobile, and shared codebases.

---

## Conclusion

This implementation plan provides a **comprehensive, phased approach** to achieving 100% design token configurability **across ALL modules** while maintaining:

- ✅ **Architectural consistency** - Follows Django best practices and normalized database design
- ✅ **Performance** - Static file generation (0ms cached loads)
- ✅ **Maintainability** - Organized, manageable code (~40-150 lines per model)
- ✅ **Testability** - Independent testing of each token category
- ✅ **Extensibility** - Easy to add new token categories or components
- ✅ **Multi-tenant support** - Each client gets branded theme **across all features**
- ✅ **Universal consistency** - Same tokens used by authentication, profiles, media, payments, notifications, etc.

**Total Effort:** 40-49 hours (phased over 4 weeks)
**Impact:** HIGH - Enables true multi-tenant theming for **ALL modules** in external projects

**Scope:** GLOBAL - Affects 40+ packages/modules across backend, web, mobile, and shared codebases

**Ready for approval** ✅
