# Global Design Token & Component Configuration Proposal

**Date:** 15.02.2026
**Status:** 📋 PROPOSAL - AWAITING REVIEW
**Impact:** HIGH - Enables full multi-tenant theming **across ALL modules**
**Effort:** 40-49 hours (phased implementation)
**Scope:** GLOBAL - Affects 40+ packages (authentication, profiles, media, payments, notifications, search, forms, comments, analytics, bookings, etc.)

---

## Executive Summary

**CRITICAL:** This is a **GLOBAL theming system** affecting ALL modules in syntek-modules, not just authentication.

**Current State:** Only **5 design token values** (basic colors) are Django-configurable - **affects ALL modules** (authentication, profiles, media, payments, notifications, etc.)

**Required:** **ALL 141 design tokens** + **7+ component configurations** must be Django-configurable for true multi-tenant theming **across ALL features**.

**Impact:** External projects currently cannot fully customize branding without modifying TypeScript source files and rebuilding applications. This affects **40+ packages** across backend, web, mobile, and shared codebases.

**Solution:** Implement comprehensive Django models with 150+ fields for all design tokens and component configurations - **used universally by ALL modules**.

---

## Token Coverage Analysis

| Category        | Token File       | Values  | Currently Configurable | Status          |
| --------------- | ---------------- | ------- | ---------------------- | --------------- |
| **Colors**      | `colors.ts`      | 60+     | ❌ 0/60 (0%)           | 🔴 CRITICAL     |
| **Typography**  | `typography.ts`  | 27      | ❌ 0/27 (0%)           | 🔴 CRITICAL     |
| **Spacing**     | `spacing.ts`     | 14      | ❌ 0/14 (0%)           | 🔴 CRITICAL     |
| **Borders**     | `borders.ts`     | 13      | ❌ 0/13 (0%)           | 🔴 CRITICAL     |
| **Shadows**     | `shadows.ts`     | 13      | ❌ 0/13 (0%)           | 🔴 CRITICAL     |
| **Breakpoints** | `breakpoints.ts` | 5       | ❌ 0/5 (0%)            | 🔴 CRITICAL     |
| **Z-Index**     | `z-index.ts`     | 9       | ❌ 0/9 (0%)            | 🔴 CRITICAL     |
| **TOTAL**       | **7 files**      | **141** | **0/141 (0%)**         | **🔴 CRITICAL** |

**Configurability Score:** **0%** ❌

---

## Detailed Token Inventory

### 1. Colors (60+ values)

#### Primary Brand Colors (10 shades)

```python
# Django model fields needed
primary_50 = models.CharField(max_length=7, default='#eff6ff')
primary_100 = models.CharField(max_length=7, default='#dbeafe')
primary_200 = models.CharField(max_length=7, default='#bfdbfe')
primary_300 = models.CharField(max_length=7, default='#93c5fd')
primary_400 = models.CharField(max_length=7, default='#60a5fa')
primary_500 = models.CharField(max_length=7, default='#3b82f6')  # Main brand color
primary_600 = models.CharField(max_length=7, default='#2563eb')
primary_700 = models.CharField(max_length=7, default='#1d4ed8')
primary_800 = models.CharField(max_length=7, default='#1e40af')
primary_900 = models.CharField(max_length=7, default='#1e3a8a')
```

#### Semantic Colors (12 values)

```python
# Success (3 values)
success_light = models.CharField(max_length=7, default='#d1fae5')
success_default = models.CharField(max_length=7, default='#10b981')
success_dark = models.CharField(max_length=7, default='#065f46')

# Warning (3 values)
warning_light = models.CharField(max_length=7, default='#fef3c7')
warning_default = models.CharField(max_length=7, default='#f59e0b')
warning_dark = models.CharField(max_length=7, default='#92400e')

# Error (3 values)
error_light = models.CharField(max_length=7, default='#fee2e2')
error_default = models.CharField(max_length=7, default='#ef4444')
error_dark = models.CharField(max_length=7, default='#991b1b')

# Info (3 values)
info_light = models.CharField(max_length=7, default='#dbeafe')
info_default = models.CharField(max_length=7, default='#3b82f6')
info_dark = models.CharField(max_length=7, default='#1e3a8a')
```

#### Neutral Colors (10 shades)

```python
neutral_50 = models.CharField(max_length=7, default='#fafafa')
neutral_100 = models.CharField(max_length=7, default='#f5f5f5')
neutral_200 = models.CharField(max_length=7, default='#e5e5e5')
neutral_300 = models.CharField(max_length=7, default='#d4d4d4')
neutral_400 = models.CharField(max_length=7, default='#a3a3a3')
neutral_500 = models.CharField(max_length=7, default='#737373')
neutral_600 = models.CharField(max_length=7, default='#525252')
neutral_700 = models.CharField(max_length=7, default='#404040')
neutral_800 = models.CharField(max_length=7, default='#262626')
neutral_900 = models.CharField(max_length=7, default='#171717')
```

#### Auth-Specific Colors (12 values)

```python
# Password strength (4 values)
auth_password_weak = models.CharField(max_length=7, default='#ef4444')
auth_password_fair = models.CharField(max_length=7, default='#f59e0b')
auth_password_good = models.CharField(max_length=7, default='#10b981')
auth_password_strong = models.CharField(max_length=7, default='#059669')

# MFA status (3 values)
auth_mfa_enabled = models.CharField(max_length=7, default='#10b981')
auth_mfa_disabled = models.CharField(max_length=7, default='#ef4444')
auth_mfa_pending = models.CharField(max_length=7, default='#f59e0b')

# Session status (3 values)
auth_session_active = models.CharField(max_length=7, default='#10b981')
auth_session_suspicious = models.CharField(max_length=7, default='#f59e0b')
auth_session_expired = models.CharField(max_length=7, default='#6b7280')

# Verification status (2 values)
auth_verification_verified = models.CharField(max_length=7, default='#10b981')
auth_verification_failed = models.CharField(max_length=7, default='#ef4444')
```

#### Social Provider Colors (4 values)

```python
social_google = models.CharField(max_length=7, default='#4285f4')
social_github = models.CharField(max_length=7, default='#24292e')
social_microsoft = models.CharField(max_length=7, default='#00a4ef')
social_apple = models.CharField(max_length=7, default='#000000')
```

**Total Color Fields:** 60+

---

### 2. Typography (27 values)

```python
# Font families (2 fields - TextField for font stacks)
font_family_sans = models.TextField(
    default='Inter, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif'
)
font_family_mono = models.TextField(
    default='JetBrains Mono, Monaco, Courier New, monospace'
)

# Font sizes (9 values)
font_size_xs = models.CharField(max_length=10, default='0.75rem')    # 12px
font_size_sm = models.CharField(max_length=10, default='0.875rem')   # 14px
font_size_base = models.CharField(max_length=10, default='1rem')     # 16px
font_size_lg = models.CharField(max_length=10, default='1.125rem')   # 18px
font_size_xl = models.CharField(max_length=10, default='1.25rem')    # 20px
font_size_2xl = models.CharField(max_length=10, default='1.5rem')    # 24px
font_size_3xl = models.CharField(max_length=10, default='1.875rem')  # 30px
font_size_4xl = models.CharField(max_length=10, default='2.25rem')   # 36px
font_size_5xl = models.CharField(max_length=10, default='3rem')      # 48px

# Font weights (4 values)
font_weight_normal = models.CharField(max_length=3, default='400')
font_weight_medium = models.CharField(max_length=3, default='500')
font_weight_semibold = models.CharField(max_length=3, default='600')
font_weight_bold = models.CharField(max_length=3, default='700')

# Line heights (6 values)
line_height_none = models.CharField(max_length=10, default='1')
line_height_tight = models.CharField(max_length=10, default='1.25')
line_height_snug = models.CharField(max_length=10, default='1.375')
line_height_normal = models.CharField(max_length=10, default='1.5')
line_height_relaxed = models.CharField(max_length=10, default='1.625')
line_height_loose = models.CharField(max_length=10, default='2')

# Letter spacing (6 values)
letter_spacing_tighter = models.CharField(max_length=10, default='-0.05em')
letter_spacing_tight = models.CharField(max_length=10, default='-0.025em')
letter_spacing_normal = models.CharField(max_length=10, default='0')
letter_spacing_wide = models.CharField(max_length=10, default='0.025em')
letter_spacing_wider = models.CharField(max_length=10, default='0.05em')
letter_spacing_widest = models.CharField(max_length=10, default='0.1em')
```

**Total Typography Fields:** 27

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

**Total Spacing Fields:** 14

---

### 4. Borders (13 values)

```python
# Border radius (8 values)
border_radius_none = models.CharField(max_length=10, default='0px')
border_radius_sm = models.CharField(max_length=10, default='4px')
border_radius_default = models.CharField(max_length=10, default='8px')
border_radius_md = models.CharField(max_length=10, default='12px')
border_radius_lg = models.CharField(max_length=10, default='16px')
border_radius_xl = models.CharField(max_length=10, default='24px')
border_radius_2xl = models.CharField(max_length=10, default='32px')
border_radius_full = models.CharField(max_length=10, default='9999px')

# Border width (5 values)
border_width_0 = models.CharField(max_length=10, default='0px')
border_width_default = models.CharField(max_length=10, default='1px')
border_width_2 = models.CharField(max_length=10, default='2px')
border_width_4 = models.CharField(max_length=10, default='4px')
border_width_8 = models.CharField(max_length=10, default='8px')
```

**Total Border Fields:** 13

---

### 5. Shadows (13 values)

```python
# Box shadows (7 values - TextField for long shadow strings)
box_shadow_none = models.CharField(max_length=10, default='none')
box_shadow_sm = models.TextField(default='0 1px 2px 0 rgba(0, 0, 0, 0.05)')
box_shadow_default = models.TextField(
    default='0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)'
)
box_shadow_md = models.TextField(
    default='0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)'
)
box_shadow_lg = models.TextField(
    default='0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)'
)
box_shadow_xl = models.TextField(
    default='0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)'
)
box_shadow_2xl = models.TextField(default='0 25px 50px -12px rgba(0, 0, 0, 0.25)')

# Elevation levels (7 values - for React Native)
elevation_0 = models.IntegerField(default=0)
elevation_1 = models.IntegerField(default=1)
elevation_2 = models.IntegerField(default=2)
elevation_3 = models.IntegerField(default=4)
elevation_4 = models.IntegerField(default=6)
elevation_5 = models.IntegerField(default=8)
elevation_6 = models.IntegerField(default=12)
```

**Total Shadow Fields:** 14 (7 TextField + 7 IntegerField)

---

### 6. Breakpoints (5 values)

```python
breakpoint_sm = models.CharField(max_length=10, default='640px')
breakpoint_md = models.CharField(max_length=10, default='768px')
breakpoint_lg = models.CharField(max_length=10, default='1024px')
breakpoint_xl = models.CharField(max_length=10, default='1280px')
breakpoint_2xl = models.CharField(max_length=10, default='1536px')
```

**Total Breakpoint Fields:** 5

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

**Total Z-Index Fields:** 9

---

## Component Configuration

### Component Inventory

| Component    | Configurable Properties             | Implementation |
| ------------ | ----------------------------------- | -------------- |
| **Button**   | Variants (4), Sizes (3), States (5) | JSONField      |
| **Input**    | States (4), Types (5)               | JSONField      |
| **Alert**    | Types (4), Icons (4)                | JSONField      |
| **Badge**    | Variants (5), Sizes (2)             | JSONField      |
| **Checkbox** | States, Sizes                       | JSONField      |
| **Card**     | Padding, Shadows, Borders           | JSONField      |
| **Spinner**  | Sizes, Colors, Speed                | JSONField      |

### ComponentConfiguration Model

```python
class ComponentConfiguration(models.Model):
    """Component-specific styling configuration."""

    theme = models.OneToOneField(
        ThemeConfiguration,
        on_delete=models.CASCADE,
        related_name='components'
    )

    # Button component
    button_variant_config = models.JSONField(
        default=dict,
        help_text="Button variant configurations"
    )
    # Example: {
    #   "primary": {
    #     "background": "primary-600",
    #     "hover": "primary-700",
    #     "active": "primary-700",
    #     "disabled": "primary-300",
    #     "text_color": "white"
    #   },
    #   "secondary": {...},
    #   "danger": {...},
    #   "ghost": {...}
    # }

    button_size_config = models.JSONField(
        default=dict,
        help_text="Button size configurations"
    )
    # Example: {
    #   "sm": {"padding_x": "3", "padding_y": "2", "font_size": "sm", "min_height": "8"},
    #   "md": {"padding_x": "4", "padding_y": "3", "font_size": "base", "min_height": "11"},
    #   "lg": {"padding_x": "6", "padding_y": "4", "font_size": "lg", "min_height": "14"}
    # }

    # Input component
    input_state_config = models.JSONField(default=dict)
    # Example: {
    #   "default": {"border": "neutral-300", "background": "white"},
    #   "focus": {"border": "primary-600"},
    #   "error": {"border": "error", "background": "error-light/10"},
    #   "disabled": {"background": "neutral-100", "text": "neutral-500"}
    # }

    # Alert component
    alert_type_config = models.JSONField(default=dict)
    # Example: {
    #   "success": {"background": "success-light", "border": "success", "text": "success-dark", "icon": "✓"},
    #   "error": {...},
    #   "warning": {...},
    #   "info": {...}
    # }

    # Badge component
    badge_variant_config = models.JSONField(default=dict)
    badge_size_config = models.JSONField(default=dict)

    # ... Other components

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

---

## Installation & Packaging Analysis

### Question: Do we need full Django/Next.js/React Native example apps?

#### Current: Library-Only Structure ✅

```
syntek-modules/
├── backend/                    # Django packages (pip installable)
├── web/packages/               # NPM packages (web)
├── mobile/packages/            # NPM packages (mobile)
└── shared/                     # Shared code
```

**Installation:**

```bash
uv pip install syntek-security-auth       # Django
npm install @syntek/ui-auth               # Web
npm install @syntek/mobile-auth           # Mobile
```

**Pros:**

- ✅ Clean library structure
- ✅ Users integrate into own apps
- ✅ No example app bloat

**Cons:**

- ❌ No reference implementation
- ❌ Harder to understand integration

---

#### Recommended: Hybrid Approach (Library + Minimal Examples) ✅

```
syntek-modules/
├── backend/                    # Django packages (libraries)
├── web/packages/               # NPM packages (libraries)
├── mobile/packages/            # NPM packages (libraries)
├── shared/                     # Shared code
└── examples/                   # ✅ NEW: Minimal example apps
    ├── django-minimal/         # Complete Django project
    │   ├── manage.py
    │   ├── settings.py         # Shows SYNTEK_AUTH configuration
    │   └── requirements.txt    # syntek-security-auth
    ├── nextjs-minimal/         # Complete Next.js project
    │   ├── app/
    │   ├── package.json        # @syntek/ui-auth
    │   └── tailwind.config.ts  # Shows theme integration
    └── react-native-minimal/   # Complete React Native project
        ├── App.tsx             # Shows @syntek/mobile-auth usage
        └── tailwind.config.js  # NativeWind 4 config
```

**Pros:**

- ✅ Reference implementation for developers
- ✅ Copy-paste configuration examples
- ✅ Faster onboarding
- ✅ Doesn't bloat published packages (examples separate)
- ✅ Low maintenance (minimal apps)

**Cons:**

- ⚠️ Requires maintaining example apps
- ⚠️ Slightly larger repo size

**Effort:** 6 hours (2 hours per example app)

**Recommendation:** **CREATE MINIMAL EXAMPLE APPS** ✅

---

## Implementation Plan

### Phase 1: Core Tokens (12-15 hours)

**Scope:**

- Colors (60+ fields)
- Typography (27 fields)
- Spacing (14 fields)

**Deliverables:**

- Django model with core token fields
- Basic Django admin interface
- Theme generator (CSS + JSON) for core tokens
- Testing

---

### Phase 2: Extended Tokens (10-12 hours)

**Scope:**

- Borders (13 fields)
- Shadows (14 fields)
- Breakpoints (5 fields)
- Z-Index (9 fields)

**Deliverables:**

- Extend Django model
- Update theme generator
- Extended testing

---

### Phase 3: Component Configurations (8-10 hours)

**Scope:**

- ComponentConfiguration model (7+ JSONField configs)
- Button, Input, Alert, Badge, Checkbox, Card, Spinner

**Deliverables:**

- Component configuration model
- Django admin for components
- Update theme generator to include component configs
- Testing

---

### Phase 4: Example Apps & Documentation (10-12 hours)

**Scope:**

- Django minimal example
- Next.js minimal example
- React Native minimal example
- Comprehensive documentation

**Deliverables:**

- 3 minimal example apps
- Setup guides
- Integration documentation

---

## Total Effort Summary

| Phase       | Tasks                   | Hours           |
| ----------- | ----------------------- | --------------- |
| **Phase 1** | Core Tokens             | 12-15           |
| **Phase 2** | Extended Tokens         | 10-12           |
| **Phase 3** | Component Configs       | 8-10            |
| **Phase 4** | Examples & Docs         | 10-12           |
| **TOTAL**   | **Full Implementation** | **40-49 hours** |

**Recommendation:** Start with **Phase 1** (core tokens) to validate approach before full implementation.

---

## Conclusion

### Key Findings

1. ✅ **Architecture is solid** - Static file generation approach is optimal
2. 🔴 **Token coverage is 0%** - All 141 tokens need Django models
3. 🔴 **Component configs missing** - All 7+ components hardcoded
4. ✅ **Installation structure works** - Library-only is fine
5. ✅ **Example apps recommended** - Minimal examples aid onboarding

### Recommendations

**Priority 1: Comprehensive Token Model**

- Implement 150+ Django model fields
- Cover all 7 token categories
- Effort: 20-27 hours (Phase 1 + Phase 2)

**Priority 2: Component Configuration**

- Implement JSONField-based component configs
- Cover 7+ components
- Effort: 8-10 hours (Phase 3)

**Priority 3: Example Apps**

- Create minimal Django/Next.js/React Native examples
- Effort: 10-12 hours (Phase 4)

**Total Recommended Effort:** 38-49 hours

---

## Next Steps

1. **Review this proposal** - Approve scope and phased approach
2. **Prioritize phases** - Decide which phases to implement
3. **Begin Phase 1** - Core token model (colors, typography, spacing)
4. **Validate approach** - Test theme generation with core tokens
5. **Iterate** - Implement remaining phases based on feedback

**Ready for approval?** Please review and provide feedback.
