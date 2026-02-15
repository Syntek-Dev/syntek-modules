# Normalized Django Model Architecture for Design Tokens

**Date:** 15.02.2026
**Status:** ✅ RECOMMENDED ARCHITECTURE
**Improvement:** Normalized models instead of monolithic 150+ field model

---

## Executive Summary

**Original Proposal:** Single `ThemeConfiguration` model with 150+ fields

**Revised Proposal:** Normalized structure with **8 separate models** (parent + 7 token categories)

**Benefits:**

- ✅ **Better database design** - Follows normalization principles
- ✅ **Easier maintenance** - Each model ~50-100 lines
- ✅ **Better Django Admin** - TabularInline/StackedInline organization
- ✅ **Easier testing** - Test each token category independently
- ✅ **Future-proof** - Easy to add new token categories

---

## Model Structure

### Parent Model: ThemeConfiguration

**Purpose:** Central theme metadata and client identifier

**Fields:** Minimal - just client info and timestamps

**Relationships:** OneToOne to each token category model

```python
# backend/security-core/theme/models/theme.py

from django.db import models


class ThemeConfiguration(models.Model):
    """Central theme configuration - parent model.

    Contains only metadata. All actual token values are in related models:
    - ColorConfiguration (60+ fields)
    - TypographyConfiguration (27 fields)
    - SpacingConfiguration (14 fields)
    - BorderConfiguration (13 fields)
    - ShadowConfiguration (14 fields)
    - BreakpointConfiguration (5 fields)
    - ZIndexConfiguration (9 fields)
    - ComponentConfiguration (7+ JSONFields)
    """

    client_id = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Client identifier (e.g., 'acme-corp', 'globex')"
    )

    name = models.CharField(
        max_length=200,
        help_text="Human-readable theme name (e.g., 'Acme Corp Brand Theme')"
    )

    description = models.TextField(
        blank=True,
        help_text="Theme description and notes"
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Whether this theme is currently active"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'syntek_theme_configuration'
        verbose_name = 'Theme Configuration'
        verbose_name_plural = 'Theme Configurations'
        ordering = ['client_id']

    def __str__(self):
        return f"{self.name} ({self.client_id})"

    def generate_theme_files(self):
        """Generate CSS and JSON theme files from all related configurations."""
        from ..theme_generator import ThemeGenerator

        generator = ThemeGenerator(self)
        generator.generate_css()
        generator.generate_json()
        generator.optimize_for_nextjs()
```

---

### 1. ColorConfiguration Model

**Purpose:** All color tokens (60+ fields)

**Relationship:** OneToOne to ThemeConfiguration

```python
# backend/security-core/theme/models/colors.py

from django.db import models
from .theme import ThemeConfiguration


class ColorConfiguration(models.Model):
    """Color token configuration.

    Contains all color values:
    - Primary brand colors (10 shades)
    - Semantic colors (12 values: success, warning, error, info)
    - Neutral colors (10 shades)
    - Auth-specific colors (12 values)
    - Social provider colors (4 values)
    """

    theme = models.OneToOneField(
        ThemeConfiguration,
        on_delete=models.CASCADE,
        related_name='colors',
        primary_key=True,
    )

    # ========================================
    # PRIMARY BRAND COLORS (10 shades)
    # ========================================

    primary_50 = models.CharField(max_length=7, default='#eff6ff')
    primary_100 = models.CharField(max_length=7, default='#dbeafe')
    primary_200 = models.CharField(max_length=7, default='#bfdbfe')
    primary_300 = models.CharField(max_length=7, default='#93c5fd')
    primary_400 = models.CharField(max_length=7, default='#60a5fa')
    primary_500 = models.CharField(max_length=7, default='#3b82f6')  # Main brand
    primary_600 = models.CharField(max_length=7, default='#2563eb')
    primary_700 = models.CharField(max_length=7, default='#1d4ed8')
    primary_800 = models.CharField(max_length=7, default='#1e40af')
    primary_900 = models.CharField(max_length=7, default='#1e3a8a')

    # ========================================
    # SEMANTIC COLORS (12 values)
    # ========================================

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

    # ========================================
    # NEUTRAL COLORS (10 shades)
    # ========================================

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

    # ========================================
    # AUTH-SPECIFIC COLORS (12 values)
    # ========================================

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

    # ========================================
    # SOCIAL PROVIDER COLORS (4 values)
    # ========================================

    social_google = models.CharField(max_length=7, default='#4285f4')
    social_github = models.CharField(max_length=7, default='#24292e')
    social_microsoft = models.CharField(max_length=7, default='#00a4ef')
    social_apple = models.CharField(max_length=7, default='#000000')

    class Meta:
        db_table = 'syntek_theme_colors'
        verbose_name = 'Color Configuration'
        verbose_name_plural = 'Color Configurations'

    def __str__(self):
        return f"Colors: {self.theme.client_id}"
```

**File Size:** ~150 lines (manageable!)

---

### 2. TypographyConfiguration Model

```python
# backend/security-core/theme/models/typography.py

from django.db import models
from .theme import ThemeConfiguration


class TypographyConfiguration(models.Model):
    """Typography token configuration.

    Contains:
    - Font families (2 stacks)
    - Font sizes (9 values)
    - Font weights (4 values)
    - Line heights (6 values)
    - Letter spacing (6 values)
    """

    theme = models.OneToOneField(
        ThemeConfiguration,
        on_delete=models.CASCADE,
        related_name='typography',
        primary_key=True,
    )

    # Font families
    font_family_sans = models.TextField(
        default='Inter, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif'
    )
    font_family_mono = models.TextField(
        default='JetBrains Mono, Monaco, Courier New, monospace'
    )

    # Font sizes
    font_size_xs = models.CharField(max_length=10, default='0.75rem')
    font_size_sm = models.CharField(max_length=10, default='0.875rem')
    font_size_base = models.CharField(max_length=10, default='1rem')
    font_size_lg = models.CharField(max_length=10, default='1.125rem')
    font_size_xl = models.CharField(max_length=10, default='1.25rem')
    font_size_2xl = models.CharField(max_length=10, default='1.5rem')
    font_size_3xl = models.CharField(max_length=10, default='1.875rem')
    font_size_4xl = models.CharField(max_length=10, default='2.25rem')
    font_size_5xl = models.CharField(max_length=10, default='3rem')

    # Font weights
    font_weight_normal = models.CharField(max_length=3, default='400')
    font_weight_medium = models.CharField(max_length=3, default='500')
    font_weight_semibold = models.CharField(max_length=3, default='600')
    font_weight_bold = models.CharField(max_length=3, default='700')

    # Line heights
    line_height_none = models.CharField(max_length=10, default='1')
    line_height_tight = models.CharField(max_length=10, default='1.25')
    line_height_snug = models.CharField(max_length=10, default='1.375')
    line_height_normal = models.CharField(max_length=10, default='1.5')
    line_height_relaxed = models.CharField(max_length=10, default='1.625')
    line_height_loose = models.CharField(max_length=10, default='2')

    # Letter spacing
    letter_spacing_tighter = models.CharField(max_length=10, default='-0.05em')
    letter_spacing_tight = models.CharField(max_length=10, default='-0.025em')
    letter_spacing_normal = models.CharField(max_length=10, default='0')
    letter_spacing_wide = models.CharField(max_length=10, default='0.025em')
    letter_spacing_wider = models.CharField(max_length=10, default='0.05em')
    letter_spacing_widest = models.CharField(max_length=10, default='0.1em')

    class Meta:
        db_table = 'syntek_theme_typography'
        verbose_name = 'Typography Configuration'

    def __str__(self):
        return f"Typography: {self.theme.client_id}"
```

**File Size:** ~80 lines

---

### 3-7. Other Token Models (Similar Structure)

```python
# backend/security-core/theme/models/spacing.py
class SpacingConfiguration(models.Model):  # 14 fields
    theme = models.OneToOneField(ThemeConfiguration, ...)
    spacing_0 = models.CharField(max_length=10, default='0px')
    # ... 13 more spacing fields

# backend/security-core/theme/models/borders.py
class BorderConfiguration(models.Model):  # 13 fields
    theme = models.OneToOneField(ThemeConfiguration, ...)
    border_radius_none = models.CharField(...)
    # ... 12 more border fields

# backend/security-core/theme/models/shadows.py
class ShadowConfiguration(models.Model):  # 14 fields
    theme = models.OneToOneField(ThemeConfiguration, ...)
    box_shadow_none = models.CharField(...)
    elevation_0 = models.IntegerField(...)
    # ... 12 more shadow fields

# backend/security-core/theme/models/breakpoints.py
class BreakpointConfiguration(models.Model):  # 5 fields
    theme = models.OneToOneField(ThemeConfiguration, ...)
    breakpoint_sm = models.CharField(...)
    # ... 4 more breakpoint fields

# backend/security-core/theme/models/zindex.py
class ZIndexConfiguration(models.Model):  # 9 fields
    theme = models.OneToOneField(ThemeConfiguration, ...)
    z_index_base = models.IntegerField(...)
    # ... 8 more z-index fields
```

---

### 8. ComponentConfiguration Model

```python
# backend/security-core/theme/models/components.py

from django.db import models
from .theme import ThemeConfiguration


class ComponentConfiguration(models.Model):
    """Component styling configuration (JSONField-based)."""

    theme = models.OneToOneField(
        ThemeConfiguration,
        on_delete=models.CASCADE,
        related_name='components',
        primary_key=True,
    )

    # Button component
    button_variant_config = models.JSONField(default=dict)
    button_size_config = models.JSONField(default=dict)

    # Input component
    input_state_config = models.JSONField(default=dict)

    # Alert component
    alert_type_config = models.JSONField(default=dict)

    # Badge component
    badge_variant_config = models.JSONField(default=dict)
    badge_size_config = models.JSONField(default=dict)

    # ... Other components

    class Meta:
        db_table = 'syntek_theme_components'
        verbose_name = 'Component Configuration'

    def __str__(self):
        return f"Components: {self.theme.client_id}"
```

---

## Django Admin Integration

### Parent Admin with Inlines

```python
# backend/security-core/theme/admin.py

from django.contrib import admin
from .models import (
    ThemeConfiguration,
    ColorConfiguration,
    TypographyConfiguration,
    SpacingConfiguration,
    BorderConfiguration,
    ShadowConfiguration,
    BreakpointConfiguration,
    ZIndexConfiguration,
    ComponentConfiguration,
)


class ColorConfigurationInline(admin.StackedInline):
    model = ColorConfiguration
    can_delete = False
    fieldsets = [
        ('Primary Brand Colors', {
            'fields': [
                ('primary_50', 'primary_100', 'primary_200'),
                ('primary_300', 'primary_400', 'primary_500'),
                ('primary_600', 'primary_700', 'primary_800', 'primary_900'),
            ]
        }),
        ('Semantic Colors', {
            'fields': [
                ('success_light', 'success_default', 'success_dark'),
                ('warning_light', 'warning_default', 'warning_dark'),
                ('error_light', 'error_default', 'error_dark'),
                ('info_light', 'info_default', 'info_dark'),
            ]
        }),
        # ... other color groups
    ]


class TypographyConfigurationInline(admin.StackedInline):
    model = TypographyConfiguration
    can_delete = False
    fieldsets = [
        ('Font Families', {
            'fields': ['font_family_sans', 'font_family_mono']
        }),
        ('Font Sizes', {
            'fields': [
                ('font_size_xs', 'font_size_sm', 'font_size_base'),
                ('font_size_lg', 'font_size_xl', 'font_size_2xl'),
                ('font_size_3xl', 'font_size_4xl', 'font_size_5xl'),
            ]
        }),
        # ... other typography groups
    ]


# Similar inlines for other token categories...


@admin.register(ThemeConfiguration)
class ThemeConfigurationAdmin(admin.ModelAdmin):
    list_display = ['client_id', 'name', 'is_active', 'updated_at']
    search_fields = ['client_id', 'name']
    list_filter = ['is_active', 'created_at']

    inlines = [
        ColorConfigurationInline,
        TypographyConfigurationInline,
        SpacingConfigurationInline,
        BorderConfigurationInline,
        ShadowConfigurationInline,
        BreakpointConfigurationInline,
        ZIndexConfigurationInline,
        ComponentConfigurationInline,
    ]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Generate theme files after save
        obj.generate_theme_files()
        self.message_user(request, f"Theme files generated for {obj.client_id}")
```

**Result:** Clean, organized admin interface with collapsible sections for each token category.

---

## Theme Generator Integration

```python
# backend/security-core/theme/theme_generator.py

class ThemeGenerator:
    """Generate CSS/JSON from normalized theme models."""

    def __init__(self, theme: ThemeConfiguration):
        self.theme = theme
        self.client_id = theme.client_id

    def generate_css(self) -> str:
        """Generate comprehensive CSS from all related configurations."""

        # Fetch all related configurations
        colors = self.theme.colors
        typography = self.theme.typography
        spacing = self.theme.spacing
        borders = self.theme.borders
        shadows = self.theme.shadows
        breakpoints = self.theme.breakpoints
        zindex = self.theme.zindex
        components = self.theme.components

        css_content = f"""/**
 * Syntek Theme: {self.theme.client_id}
 * Generated: {self.theme.updated_at.isoformat()}
 */

:root {{
  /* Colors - Primary */
  --color-primary-50: {colors.primary_50};
  --color-primary-500: {colors.primary_500};
  /* ... all color values */

  /* Typography */
  --font-sans: {typography.font_family_sans};
  --font-size-base: {typography.font_size_base};
  /* ... all typography values */

  /* Spacing */
  --spacing-1: {spacing.spacing_1};
  /* ... all spacing values */

  /* Borders */
  --border-radius-default: {borders.border_radius_default};
  /* ... all border values */

  /* Shadows */
  --box-shadow-md: {shadows.box_shadow_md};
  /* ... all shadow values */

  /* Breakpoints */
  --breakpoint-md: {breakpoints.breakpoint_md};
  /* ... all breakpoint values */

  /* Z-Index */
  --z-index-modal: {zindex.z_index_modal};
  /* ... all z-index values */
}}
"""

        # Save CSS file
        file_path = f'tokens/{self.client_id}/theme.css'
        default_storage.save(file_path, ContentFile(css_content.encode()))

        return file_path

    def generate_json(self) -> str:
        """Generate comprehensive JSON from all related configurations."""

        # Fetch all related configurations
        colors = self.theme.colors
        typography = self.theme.typography
        # ... other configs

        theme_data = {
            'clientId': self.client_id,
            'updatedAt': self.theme.updated_at.isoformat(),
            'colors': {
                'primary': {
                    '50': colors.primary_50,
                    '500': colors.primary_500,
                    # ... all primary shades
                },
                'success': {
                    'light': colors.success_light,
                    'default': colors.success_default,
                    'dark': colors.success_dark,
                },
                # ... all color categories
            },
            'typography': {
                'fontFamily': {
                    'sans': typography.font_family_sans,
                    'mono': typography.font_family_mono,
                },
                'fontSize': {
                    'base': typography.font_size_base,
                    # ... all font sizes
                },
                # ... all typography values
            },
            # ... all other token categories
        }

        json_content = json.dumps(theme_data, indent=2)

        # Save JSON file
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

-- Child tables (OneToOne relationship)
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

## Model File Organization

```
backend/security-core/theme/
├── models/
│   ├── __init__.py           # Import all models
│   ├── theme.py              # ThemeConfiguration (parent)
│   ├── colors.py             # ColorConfiguration (~150 lines)
│   ├── typography.py         # TypographyConfiguration (~80 lines)
│   ├── spacing.py            # SpacingConfiguration (~40 lines)
│   ├── borders.py            # BorderConfiguration (~40 lines)
│   ├── shadows.py            # ShadowConfiguration (~50 lines)
│   ├── breakpoints.py        # BreakpointConfiguration (~30 lines)
│   ├── zindex.py             # ZIndexConfiguration (~35 lines)
│   └── components.py         # ComponentConfiguration (~60 lines)
├── admin.py                  # Django admin configuration
├── theme_generator.py        # ThemeGenerator class
└── management/
    └── commands/
        └── create_default_theme.py
```

**Total lines:** ~600 lines spread across 9 files (vs 1000+ in single file)

---

## Benefits Summary

| Aspect               | Monolithic Model (150+ fields) | Normalized Models (8 models) |
| -------------------- | ------------------------------ | ---------------------------- |
| **Maintainability**  | ❌ Hard to find tokens         | ✅ Organized by category     |
| **File Size**        | ❌ 1000+ lines                 | ✅ ~60-150 lines per file    |
| **Django Admin**     | ❌ Long scrolling form         | ✅ Organized inlines         |
| **Database Design**  | ❌ Denormalized                | ✅ Normalized                |
| **Testing**          | ❌ Test entire model           | ✅ Test each category        |
| **Extensibility**    | ❌ Adding tokens bloats model  | ✅ Easy to add categories    |
| **Code Readability** | ❌ Hard to navigate            | ✅ Clear separation          |

---

## Migration Path

### Step 1: Create Models

```bash
python manage.py makemigrations theme
# Creates migrations for all 8 models
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

---

## Conclusion

**Recommendation:** ✅ **USE NORMALIZED MODEL STRUCTURE**

**Rationale:**

- ✅ **Better database design** - Follows best practices
- ✅ **Easier to maintain** - Each model is focused and manageable
- ✅ **Better UX** - Django admin with organized inlines
- ✅ **Future-proof** - Easy to extend with new token categories
- ✅ **No downsides** - Only benefits compared to monolithic model

**Next Steps:**

1. Approve normalized structure
2. Implement ThemeConfiguration + 8 child models
3. Implement Django admin with inlines
4. Update ThemeGenerator to fetch all related configs
5. Test theme generation with normalized models
