# Action Items: Authentication System Configurability

**Date:** 15.02.2026
**Related Review:** `REVIEW-PHASES-1-5-CONFIGURABILITY-ARCHITECTURE.md`
**Status:** 1 Critical Fix Required

---

## Priority 1: MUST FIX (5 Minutes)

### 🔴 Critical: Fix Hardcoded `password_max_length`

**Issue:** Hardcoded value in GraphQL configuration query

**File:** `graphql/auth/syntek_graphql_auth/queries/config.py`
**Line:** 42

**Current Code:**

```python
return AuthConfigType(
    # Password validation
    password_min_length=config.get('PASSWORD_LENGTH', 12),
    password_max_length=128,  # ❌ HARDCODED
```

**Fix:**

```python
return AuthConfigType(
    # Password validation
    password_min_length=config.get('PASSWORD_LENGTH', 12),
    password_max_length=config.get('PASSWORD_MAX_LENGTH', 128),  # ✅ FIXED
```

**Django Settings Example:**

```python
# backend/settings.py
SYNTEK_AUTH = {
    'PASSWORD_LENGTH': 12,
    'PASSWORD_MAX_LENGTH': 128,  # Add this line
    # ... other settings
}
```

**Impact:** HIGH - Configuration inconsistency
**Effort:** 5 minutes
**Testing:** Verify `authConfig` query returns configurable max length

---

## Priority 2: SHOULD FIX (4-6 Hours)

### 🟡 Enhancement: Implement Static Design Token Generation

**Issue:** Design tokens (colours, fonts, spacing, breakpoints) are TypeScript constants, cannot be changed without rebuilding

**Goal:** Allow external projects to customise branding via Django admin, delivered as static files (no database overhead)

**Critical Principle:** Django is the source of truth, but static files are the delivery mechanism. **DO NOT** fetch tokens via GraphQL on every page load.

---

#### Architecture Overview

```
1. CMS/Platform → Client updates brand in Django admin → Save to Postgres
2. Django Signal → Generate static files → Push to CDN
3. Frontend → Load static file (cached, no DB hit)
   - Web: /tokens/{client-id}/theme.css
   - Mobile: /tokens/{client-id}/theme.json (cached on device)
```

**Why Static Files?**

- ✅ Zero database calls (CDN-cached)
- ✅ Excellent performance (+0ms on cached loads vs +50-100ms GraphQL)
- ✅ Multi-tenant support (each client gets their own file)
- ✅ Runtime updates (no rebuild required)

---

#### Step 1: Create Django Theme Model (30 minutes)

**File:** `backend/security-core/theme/models.py` (NEW)

```python
"""Theme configuration models for multi-tenant branding."""

from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


class ThemeConfiguration(models.Model):
    """Theme configuration for multi-tenant branding.

    Each client (identified by client_id) can have custom brand colours,
    typography, spacing, and breakpoints.

    When saved, automatically generates static CSS and JSON files and
    pushes them to CDN for frontend consumption.
    """

    client_id = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Client identifier (e.g., 'acme-corp', 'globex')"
    )

    # Brand Colours
    primary_color = models.CharField(
        max_length=7,
        default='#3b82f6',
        help_text="Primary brand colour (hex format: #RRGGBB)"
    )
    success_color = models.CharField(max_length=7, default='#10b981')
    warning_color = models.CharField(max_length=7, default='#f59e0b')
    error_color = models.CharField(max_length=7, default='#ef4444')
    neutral_color = models.CharField(max_length=7, default='#737373')

    # Typography
    font_family_sans = models.CharField(
        max_length=255,
        default='Inter, system-ui, -apple-system, BlinkMacSystemFont, sans-serif',
        help_text="Sans-serif font stack"
    )
    font_family_mono = models.CharField(
        max_length=255,
        default='JetBrains Mono, Monaco, Courier New, monospace',
        help_text="Monospace font stack"
    )

    # Spacing Scale
    spacing_scale = models.IntegerField(
        default=4,
        help_text="Base spacing scale in pixels (e.g., 4 → 4px, 8px, 12px, 16px)"
    )

    # Breakpoints (responsive design)
    breakpoint_sm = models.IntegerField(default=640, help_text="Small devices (px)")
    breakpoint_md = models.IntegerField(default=768, help_text="Medium devices (px)")
    breakpoint_lg = models.IntegerField(default=1024, help_text="Large devices (px)")
    breakpoint_xl = models.IntegerField(default=1280, help_text="Extra large devices (px)")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'syntek_theme_configuration'
        verbose_name = 'Theme Configuration'
        verbose_name_plural = 'Theme Configurations'
        ordering = ['client_id']

    def __str__(self):
        return f"Theme: {self.client_id}"


@receiver(post_save, sender=ThemeConfiguration)
def generate_theme_files_on_save(sender, instance, **kwargs):
    """Automatically generate static theme files when theme is saved.

    Generates:
    - CSS file: /tokens/{client-id}/theme.css (for web)
    - JSON file: /tokens/{client-id}/theme.json (for mobile)

    Files are pushed to CDN/static storage for frontend consumption.
    """
    from .theme_generator import ThemeGenerator

    generator = ThemeGenerator(instance)
    generator.generate_css()   # Generate CSS custom properties
    generator.generate_json()  # Generate JSON for React Native
    generator.push_to_cdn()    # Push to CDN (if using S3/CloudFront/Cloudflare)
```

**File:** `backend/security-core/theme/admin.py` (NEW)

```python
"""Django admin for theme configuration."""

from django.contrib import admin
from .models import ThemeConfiguration


@admin.register(ThemeConfiguration)
class ThemeConfigurationAdmin(admin.ModelAdmin):
    """Admin interface for theme configuration."""

    list_display = ['client_id', 'primary_color', 'updated_at']
    search_fields = ['client_id']
    list_filter = ['created_at', 'updated_at']

    fieldsets = [
        ('Client', {
            'fields': ['client_id']
        }),
        ('Brand Colours', {
            'fields': ['primary_color', 'success_color', 'warning_color', 'error_color', 'neutral_color']
        }),
        ('Typography', {
            'fields': ['font_family_sans', 'font_family_mono']
        }),
        ('Spacing & Breakpoints', {
            'fields': ['spacing_scale', 'breakpoint_sm', 'breakpoint_md', 'breakpoint_lg', 'breakpoint_xl'],
            'classes': ['collapse']
        }),
    ]

    readonly_fields = ['created_at', 'updated_at']

    def save_model(self, request, obj, form, change):
        """Save and trigger static file generation."""
        super().save_model(request, obj, form, change)
        self.message_user(request, f"Theme files generated for {obj.client_id}")
```

---

#### Step 2: Create Theme Generator Service (1 hour)

**File:** `backend/security-core/theme/theme_generator.py` (NEW)

```python
"""Theme generator service - converts Django models to static CSS/JSON files."""

import json
from pathlib import Path
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage


class ThemeGenerator:
    """Generate static theme files from Django theme configuration.

    Converts ThemeConfiguration model instances into:
    - CSS custom properties (/tokens/{client-id}/theme.css)
    - JSON theme data (/tokens/{client-id}/theme.json)

    Files are saved to Django static storage (local or S3/CDN).
    """

    def __init__(self, theme_config):
        """Initialize generator with theme configuration.

        Args:
            theme_config: ThemeConfiguration model instance
        """
        self.config = theme_config
        self.client_id = theme_config.client_id

    def generate_css(self) -> str:
        """Generate CSS custom properties file.

        Returns:
            str: Path to generated file (e.g., 'tokens/acme-corp/theme.css')
        """
        css_content = f"""/**
 * Syntek Theme: {self.client_id}
 * Generated: {self.config.updated_at.isoformat()}
 * DO NOT EDIT MANUALLY - Generated from Django admin
 *
 * Load this file in your HTML <head>:
 * <link rel="stylesheet" href="/tokens/{self.client_id}/theme.css">
 */

:root {{
  /* Brand Colours */
  --color-primary: {self.config.primary_color};
  --color-success: {self.config.success_color};
  --color-warning: {self.config.warning_color};
  --color-error: {self.config.error_color};
  --color-neutral: {self.config.neutral_color};

  /* Typography */
  --font-sans: {self.config.font_family_sans};
  --font-mono: {self.config.font_family_mono};

  /* Spacing Scale (based on {self.config.spacing_scale}px) */
  --spacing-scale: {self.config.spacing_scale}px;
  --spacing-1: calc(var(--spacing-scale) * 1);    /* {self.config.spacing_scale}px */
  --spacing-2: calc(var(--spacing-scale) * 2);    /* {self.config.spacing_scale * 2}px */
  --spacing-3: calc(var(--spacing-scale) * 3);    /* {self.config.spacing_scale * 3}px */
  --spacing-4: calc(var(--spacing-scale) * 4);    /* {self.config.spacing_scale * 4}px */
  --spacing-6: calc(var(--spacing-scale) * 6);    /* {self.config.spacing_scale * 6}px */
  --spacing-8: calc(var(--spacing-scale) * 8);    /* {self.config.spacing_scale * 8}px */
  --spacing-12: calc(var(--spacing-scale) * 12);  /* {self.config.spacing_scale * 12}px */
  --spacing-16: calc(var(--spacing-scale) * 16);  /* {self.config.spacing_scale * 16}px */

  /* Breakpoints (responsive design) */
  --breakpoint-sm: {self.config.breakpoint_sm}px;
  --breakpoint-md: {self.config.breakpoint_md}px;
  --breakpoint-lg: {self.config.breakpoint_lg}px;
  --breakpoint-xl: {self.config.breakpoint_xl}px;
}}

/* Example usage in Tailwind v4:
 * <button className="bg-[var(--color-primary)] text-white">
 *   Primary Button
 * </button>
 */
"""

        # Save to static storage
        file_path = f'tokens/{self.client_id}/theme.css'
        default_storage.save(file_path, ContentFile(css_content.encode('utf-8')))

        return file_path

    def generate_json(self) -> str:
        """Generate JSON theme file for React Native.

        Returns:
            str: Path to generated file (e.g., 'tokens/acme-corp/theme.json')
        """
        theme_data = {
            'clientId': self.client_id,
            'updatedAt': self.config.updated_at.isoformat(),
            'colors': {
                'primary': self.config.primary_color,
                'success': self.config.success_color,
                'warning': self.config.warning_color,
                'error': self.config.error_color,
                'neutral': self.config.neutral_color,
            },
            'typography': {
                'fontFamilySans': self.config.font_family_sans,
                'fontFamilyMono': self.config.font_family_mono,
            },
            'spacing': {
                'scale': self.config.spacing_scale,
                '1': self.config.spacing_scale * 1,
                '2': self.config.spacing_scale * 2,
                '3': self.config.spacing_scale * 3,
                '4': self.config.spacing_scale * 4,
                '6': self.config.spacing_scale * 6,
                '8': self.config.spacing_scale * 8,
                '12': self.config.spacing_scale * 12,
                '16': self.config.spacing_scale * 16,
            },
            'breakpoints': {
                'sm': self.config.breakpoint_sm,
                'md': self.config.breakpoint_md,
                'lg': self.config.breakpoint_lg,
                'xl': self.config.breakpoint_xl,
            },
        }

        json_content = json.dumps(theme_data, indent=2)

        # Save to static storage
        file_path = f'tokens/{self.client_id}/theme.json'
        default_storage.save(file_path, ContentFile(json_content.encode('utf-8')))

        return file_path

    def optimize_for_nextjs(self):
        """Optimize generated files for Next.js consumption.

        Next.js handles all caching and minification via .next directory.
        No external CDN needed - Next.js build process handles optimization.

        Django Configuration:

        STATIC_URL = '/static/'
        STATIC_ROOT = BASE_DIR / 'staticfiles'

        Next.js serves files from:
        - Development: Django static files via proxy
        - Production: .next/static directory (optimized and minified)

        Next.js automatically provides:
        - Minification and compression (gzip/brotli)
        - Cache-Control headers (immutable assets)
        - Code splitting and tree shaking
        - Static optimization and ISR (Incremental Static Regeneration)

        Generated URLs (served by Next.js):
        - http://localhost:3000/tokens/acme-corp/theme.css
        - http://localhost:3000/tokens/acme-corp/theme.json

        Production URLs:
        - https://app.syntek.com/tokens/acme-corp/theme.css (cached by browser)
        - https://app.syntek.com/tokens/acme-corp/theme.json (cached by AsyncStorage)
        """
        # Files served by Next.js - no additional CDN configuration needed
        # Next.js handles all optimization, caching, and compression
        pass
```

---

#### Step 3: Frontend - Web (Load CSS) (1 hour)

**File:** `web/app/layout.tsx`

```tsx
import { headers } from "next/headers";

export default async function RootLayout({ children }) {
  // Extract client ID from subdomain or header
  const headersList = await headers();
  const host = headersList.get("host") || "";
  const clientId = extractClientId(host);

  return (
    <html lang="en">
      <head>
        {/* Load client-specific theme from Next.js static files */}
        {/* Served from .next/static (optimized by Next.js build) */}
        {/* Cached by browser - NO database hit */}
        <link rel="stylesheet" href={`/tokens/${clientId}/theme.css`} />
      </head>
      <body>{children}</body>
    </html>
  );
}

/**
 * Extract client ID from hostname.
 *
 * Examples:
 * - acme-corp.syntek.com → 'acme-corp'
 * - globex.syntek.com → 'globex'
 * - www.syntek.com → 'default'
 * - localhost:3000 → 'default'
 */
function extractClientId(host: string): string {
  const subdomain = host.split(".")[0];
  const isDefaultSubdomain = ["www", "localhost", "localhost:3000"].includes(
    subdomain,
  );
  return isDefaultSubdomain ? "default" : subdomain;
}
```

**File:** `web/packages/ui-auth/src/components/Button.tsx`

```tsx
/**
 * Button component using CSS custom properties from theme.css
 *
 * CSS variables are set by /tokens/{client-id}/theme.css
 * No runtime database calls - theme loaded once and cached by browser
 */
export function Button({ children, variant = "primary" }) {
  return (
    <button
      className={`
        px-4 py-2 rounded font-medium transition-colors
        ${variant === "primary" ? "bg-[var(--color-primary)] hover:opacity-90 text-white" : ""}
        ${variant === "success" ? "bg-[var(--color-success)] hover:opacity-90 text-white" : ""}
        ${variant === "warning" ? "bg-[var(--color-warning)] hover:opacity-90 text-white" : ""}
        ${variant === "error" ? "bg-[var(--color-error)] hover:opacity-90 text-white" : ""}
      `}
    >
      {children}
    </button>
  );
}
```

---

#### Step 4: Frontend - Mobile (Load JSON) (1.5 hours)

**File:** `mobile/packages/mobile-auth/src/hooks/useTheme.ts` (NEW)

```typescript
/**
 * Theme hook for React Native
 *
 * Fetches theme JSON from CDN on app launch and caches locally on device.
 * No database calls - theme served as static JSON file from CDN.
 */

import AsyncStorage from "@react-native-async-storage/async-storage";
import { useEffect, useState } from "react";
import Config from "react-native-config"; // For environment variables

interface ThemeColors {
  primary: string;
  success: string;
  warning: string;
  error: string;
  neutral: string;
}

interface ThemeTypography {
  fontFamilySans: string;
  fontFamilyMono: string;
}

interface ThemeSpacing {
  scale: number;
  "1": number;
  "2": number;
  "3": number;
  "4": number;
  "6": number;
  "8": number;
  "12": number;
  "16": number;
}

interface Theme {
  clientId: string;
  updatedAt: string;
  colors: ThemeColors;
  typography: ThemeTypography;
  spacing: ThemeSpacing;
  breakpoints: Record<string, number>;
}

const THEME_CACHE_KEY = "@syntek/theme";
const API_BASE_URL = Config.API_BASE_URL || "http://localhost:3000";
const CLIENT_ID = Config.CLIENT_ID || "default";

export function useTheme() {
  const [theme, setTheme] = useState<Theme | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    loadTheme();
  }, []);

  async function loadTheme() {
    try {
      // 1. Try to load from local cache first (instant)
      const cachedTheme = await AsyncStorage.getItem(THEME_CACHE_KEY);
      if (cachedTheme) {
        const parsedTheme = JSON.parse(cachedTheme);
        setTheme(parsedTheme);
        setLoading(false);

        // 2. Fetch fresh theme in background and update cache if changed
        fetchAndCacheTheme(parsedTheme.updatedAt);
      } else {
        // 3. No cache - fetch immediately
        await fetchAndCacheTheme();
        setLoading(false);
      }
    } catch (err) {
      console.error("Failed to load theme:", err);
      setError(err as Error);
      setLoading(false);
    }
  }

  async function fetchAndCacheTheme(cachedUpdatedAt?: string) {
    try {
      const themeUrl = `${API_BASE_URL}/tokens/${CLIENT_ID}/theme.json`;
      const response = await fetch(themeUrl);

      if (!response.ok) {
        throw new Error(`Failed to fetch theme: ${response.status}`);
      }

      const themeData: Theme = await response.json();

      // Only update if theme has changed
      if (!cachedUpdatedAt || themeData.updatedAt !== cachedUpdatedAt) {
        setTheme(themeData);
        await AsyncStorage.setItem(THEME_CACHE_KEY, JSON.stringify(themeData));
      }
    } catch (err) {
      console.error("Failed to fetch theme from CDN:", err);
      // Keep using cached theme if fetch fails
    }
  }

  return { theme, loading, error, refetch: loadTheme };
}
```

**File:** `mobile/packages/mobile-auth/src/components/Button.tsx`

```tsx
import { Pressable, Text, ActivityIndicator } from "react-native";
import { useTheme } from "../hooks/useTheme";

interface ButtonProps {
  children: React.ReactNode;
  variant?: "primary" | "success" | "warning" | "error";
  onPress?: () => void;
}

export function Button({
  children,
  variant = "primary",
  onPress,
}: ButtonProps) {
  const { theme, loading } = useTheme();

  if (loading || !theme) {
    return <ActivityIndicator />;
  }

  const backgroundColor = theme.colors[variant] || theme.colors.primary;

  return (
    <Pressable
      onPress={onPress}
      style={{
        backgroundColor,
        paddingHorizontal: theme.spacing["4"],
        paddingVertical: theme.spacing["2"],
        borderRadius: 8,
      }}
    >
      <Text style={{ color: "white", fontWeight: "500" }}>{children}</Text>
    </Pressable>
  );
}
```

---

#### Step 5: Django Settings Configuration (15 minutes)

**File:** `backend/settings.py`

```python
# Add to INSTALLED_APPS
INSTALLED_APPS = [
    # ... existing apps
    'backend.security_core.theme',  # Theme configuration
]

# Configure static file storage (local or S3/CDN)

# Option 1: Local development (files in /static/)
if DEBUG:
    STATIC_URL = '/static/'
    STATIC_ROOT = BASE_DIR / 'staticfiles'

# Option 2: Production with S3/CloudFront
else:
    STORAGES = {
        'staticfiles': {
            'BACKEND': 'storages.backends.s3boto3.S3Boto3Storage',
            'OPTIONS': {
                'bucket_name': 'syntek-static-assets',
                'custom_domain': 'cdn.syntek.com',
                'querystring_auth': False,  # Public read
                'default_acl': 'public-read',
                'object_parameters': {
                    'CacheControl': 'max-age=31536000, immutable',  # Cache 1 year
                },
            },
        },
    }
```

---

#### Step 6: Create Default Theme (15 minutes)

**File:** `backend/security-core/theme/management/commands/create_default_theme.py` (NEW)

```python
"""Management command to create default theme."""

from django.core.management.base import BaseCommand
from backend.security_core.theme.models import ThemeConfiguration


class Command(BaseCommand):
    help = 'Create default theme configuration'

    def handle(self, *args, **options):
        theme, created = ThemeConfiguration.objects.get_or_create(
            client_id='default',
            defaults={
                'primary_color': '#3b82f6',
                'success_color': '#10b981',
                'warning_color': '#f59e0b',
                'error_color': '#ef4444',
                'neutral_color': '#737373',
                'font_family_sans': 'Inter, system-ui, -apple-system, sans-serif',
                'font_family_mono': 'JetBrains Mono, Monaco, monospace',
                'spacing_scale': 4,
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS('✓ Created default theme'))
        else:
            self.stdout.write(self.style.WARNING('⚠ Default theme already exists'))
```

**Run command:**

```bash
python manage.py create_default_theme
```

---

#### Testing Checklist

After implementation:

**Backend:**

- [ ] Run migrations: `python manage.py makemigrations && python manage.py migrate`
- [ ] Create default theme: `python manage.py create_default_theme`
- [ ] Access Django admin at `/admin/theme/themeconfiguration/`
- [ ] Create theme for client "acme-corp" with custom colours
- [ ] Verify CSS file generated at `/static/tokens/acme-corp/theme.css`
- [ ] Verify JSON file generated at `/static/tokens/acme-corp/theme.json`

**Frontend - Web:**

- [ ] Load page, verify CSS file loaded in Network tab
- [ ] Open DevTools, check `:root` has `--color-primary` variable
- [ ] Verify button uses `var(--color-primary)` colour
- [ ] Change theme colour in Django admin, verify CSS file updates
- [ ] Reload page, verify new colour applied (may need to clear cache)

**Frontend - Mobile:**

- [ ] Launch app, verify theme JSON fetched from CDN
- [ ] Check `AsyncStorage` has cached theme
- [ ] Verify button uses theme colour from JSON
- [ ] Close and reopen app, verify theme loaded from cache (instant)
- [ ] Change theme in Django admin, verify app fetches update

**Performance:**

- [ ] Web: Measure page load time (should be +0ms after CSS cached)
- [ ] Mobile: Measure app launch time (should be instant with cached theme)
- [ ] Verify no database queries for theme data (check Django Debug Toolbar)

---

**Impact:** MEDIUM-HIGH - Enables runtime theme customisation without rebuild, excellent performance
**Effort:** 4-6 hours (full implementation)
**Testing:** Change Django theme settings, verify UI updates without rebuild

---

## Priority 2.5: CRITICAL - Valkey Configuration (30 Minutes)

### 🔴 Critical: Use Valkey Instead of Redis

**Issue:** Ensure all caching uses Valkey (NOT Redis) for session storage, GraphQL caching, and rate limiting.

**Why Valkey?**

- ✅ **Open-source** - True OSS license (BSD 3-Clause), no licensing restrictions
- ✅ **Redis-compatible** - Drop-in replacement for Redis
- ✅ **Community-driven** - Linux Foundation project
- ✅ **Future-proof** - No corporate license changes

---

#### Step 1: Install Valkey Client (5 minutes)

**File:** `backend/pyproject.toml`

```toml
[project]
dependencies = [
    "django>=6.0.2",
    "django-valkey>=0.2.0",  # Valkey client for Django
    # ... other dependencies
]
```

**Run:**

```bash
uv pip install django-valkey
```

---

#### Step 2: Configure Valkey Cache (10 minutes)

**File:** `backend/settings.py`

```python
# Valkey Configuration (NOT Redis)
CACHES = {
    'default': {
        'BACKEND': 'django_valkey.cache.ValkeyCache',
        'LOCATION': 'valkey://localhost:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_valkey.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'socket_keepalive': True,
                'socket_keepalive_options': {
                    socket.TCP_KEEPIDLE: 1,
                    socket.TCP_KEEPCNT: 3,
                    socket.TCP_KEEPINTVL: 1,
                },
            },
            'COMPRESSOR': 'django_valkey.compressors.zlib.ZlibCompressor',
            'PARSER_CLASS': 'redis.connection.PythonParser',
        }
    },
    'sessions': {
        'BACKEND': 'django_valkey.cache.ValkeyCache',
        'LOCATION': 'valkey://localhost:6379/2',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_valkey.client.DefaultClient',
        }
    },
}

# Session Backend (Valkey)
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'sessions'
SESSION_COOKIE_AGE = 1800  # 30 minutes
SESSION_COOKIE_SECURE = True  # HTTPS only
SESSION_COOKIE_HTTPONLY = True  # No JS access
SESSION_COOKIE_SAMESITE = 'Lax'

# Rate Limiting (via Valkey)
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'
```

---

#### Step 3: Configure Valkey for Encryption (10 minutes)

**Important:** Valkey stores encrypted data only (see Data Flow Architecture).

**File:** `backend/syntek_auth/middleware/session_encryption.py` (NEW)

```python
"""Session encryption middleware - encrypts session data before Valkey storage."""

from django.contrib.sessions.backends.cache import SessionStore as CacheSessionStore
from rust.encryption import encrypt_field, decrypt_field  # PyO3 bindings


class EncryptedSessionStore(CacheSessionStore):
    """Session store that encrypts data before writing to Valkey."""

    def encode(self, session_dict):
        """Encrypt session data before storing in Valkey."""
        # Serialize session to JSON
        serialized = super().encode(session_dict)

        # Encrypt serialized session data (Rust layer)
        encrypted = encrypt_field(
            plaintext=serialized,
            field_name='session_data',
            key_source='openbao',  # Fetch key from OpenBao
        )

        # Valkey stores encrypted blob only
        return encrypted

    def decode(self, session_data):
        """Decrypt session data after reading from Valkey."""
        try:
            # Decrypt encrypted session data (Rust layer)
            decrypted = decrypt_field(
                ciphertext=session_data,
                field_name='session_data',
                key_source='openbao',
            )

            # Deserialize JSON
            return super().decode(decrypted)
        except Exception as e:
            # Invalid/corrupted session - return empty
            return {}
```

**File:** `backend/settings.py`

```python
# Use encrypted session backend
SESSION_ENGINE = 'backend.syntek_auth.middleware.session_encryption'
```

---

#### Step 4: Data Flow Architecture (Reference)

**Critical:** Follow this pattern for all sensitive data:

```
┌─────────────────────────────────────────────────────────────────┐
│ User Request (plaintext)                                        │
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

**Key Principles:**

1. **Plaintext only in memory** - User data exists as plaintext ONLY in Rust process memory
2. **Encrypt before cache** - All data encrypted BEFORE writing to Valkey
3. **Encrypt before database** - All sensitive fields encrypted BEFORE PostgreSQL insert
4. **Memory zeroing** - Plaintext zeroed from memory after encryption (zeroize crate)
5. **Ephemeral keys** - Encryption keys fetched from OpenBao, never persisted
6. **No disk writes** - Plaintext NEVER written to disk (logs, cache files, temp files)

---

#### Step 5: Testing Checklist (5 minutes)

**Valkey Configuration:**

- [ ] Install `django-valkey` package
- [ ] Configure `CACHES` with Valkey backend
- [ ] Configure `SESSION_ENGINE` to use Valkey cache
- [ ] Verify Valkey running: `valkey-cli ping` → `PONG`
- [ ] Test session creation: Login and verify session in Valkey
- [ ] Verify encrypted session data: `valkey-cli GET <session_key>` (should be encrypted blob)

**Data Flow:**

- [ ] Verify plaintext never written to Valkey (check with `valkey-cli MONITOR`)
- [ ] Verify session decryption works (logout/login cycle)
- [ ] Verify encryption keys fetched from OpenBao (check logs)
- [ ] Verify memory zeroing (no plaintext in memory dumps)

**Compliance:**

- [ ] GDPR Article 32: Encryption of personal data ✅
- [ ] NIST 800-53 SC-28: Protection of data at rest ✅
- [ ] PCI DSS 3.2.1: Encryption of cardholder data ✅

---

**Impact:** HIGH - Security compliance (encryption-at-rest)
**Effort:** 30 minutes (configuration + testing)
**Priority:** CRITICAL (must use Valkey, not Redis)

---

## Priority 3: SHOULD FIX (1 Hour)

### 🟡 Security: Add Subresource Integrity (SRI) for External Scripts

**Issue:** reCAPTCHA and hCAPTCHA scripts loaded without integrity verification

**File:** `web/packages/ui-auth/src/lib/captcha-loader.ts`

**Current Code:**

```typescript
const script = document.createElement("script");
script.src = "https://www.google.com/recaptcha/api.js";
script.async = true;
document.head.appendChild(script);
```

**Fix:**

```typescript
const script = document.createElement("script");
script.src = "https://www.google.com/recaptcha/api.js";
script.integrity = "sha384-..."; // Add SRI hash
script.crossOrigin = "anonymous";
script.async = true;
document.head.appendChild(script);
```

**How to Generate SRI Hash:**

```bash
curl -s https://www.google.com/recaptcha/api.js | openssl dgst -sha384 -binary | openssl base64 -A
```

**Impact:** MEDIUM - Security hardening (prevents script tampering)
**Effort:** 1 hour
**Testing:** Verify CAPTCHA still loads and works

---

## Priority 4: NICE TO HAVE (30 Minutes)

### 🟢 Developer Experience: Add ESLint Rule for Deprecated Constants

**Issue:** Developers might accidentally use deprecated constants instead of `useAuthConfig()`

**File:** `.eslintrc.js` or `eslint.config.js`

**Add Rule:**

```javascript
module.exports = {
  rules: {
    "no-restricted-imports": [
      "warn",
      {
        paths: [
          {
            name: "@syntek/shared-auth/constants",
            importNames: [
              "SESSION_TIMEOUT",
              "SESSION_TIMEOUT_REMEMBER_ME",
              "MAX_LOGIN_ATTEMPTS",
              "LOCKOUT_DURATION",
              "AUTO_LOGOUT_WARNING_TIME",
              "SESSION_ACTIVITY_CHECK_INTERVAL",
              "PASSWORD_MIN_LENGTH",
              "PASSWORD_MAX_LENGTH",
            ],
            message: "Use useAuthConfig() hook instead of deprecated constants",
          },
        ],
      },
    ],
  },
};
```

**Impact:** LOW - Developer experience
**Effort:** 30 minutes
**Testing:** Verify ESLint warns when importing deprecated constants

---

## Priority 5: NICE TO HAVE (1 Hour)

### 🟢 Performance: Add Turborepo for Build Optimisation

**Issue:** Building all packages sequentially is slow

**File:** `turbo.json` (NEW)

```json
{
  "$schema": "https://turbo.build/schema.json",
  "pipeline": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": ["dist/**", ".next/**"]
    },
    "dev": {
      "cache": false
    },
    "lint": {
      "outputs": []
    },
    "test": {
      "dependsOn": ["build"],
      "outputs": ["coverage/**"]
    }
  }
}
```

**File:** `package.json`

```json
{
  "scripts": {
    "build": "turbo run build",
    "dev": "turbo run dev",
    "lint": "turbo run lint",
    "test": "turbo run test"
  },
  "devDependencies": {
    "turbo": "^2.3.3"
  }
}
```

**Impact:** LOW - Build performance (5-10x faster on large codebases)
**Effort:** 1 hour
**Testing:** Run `pnpm build`, verify all packages build in parallel

---

## Testing Checklist

After implementing Priority 1 fix:

- [ ] Django settings include `PASSWORD_MAX_LENGTH`
- [ ] GraphQL query uses `config.get('PASSWORD_MAX_LENGTH', 128)`
- [ ] Frontend receives configurable max length via `useAuthConfig()`
- [ ] Password validation uses config value (no hardcoded 128)
- [ ] Changing Django setting updates validation rules

After implementing Priority 2 (theme configuration):

- [ ] Django settings include `SYNTEK_THEME`
- [ ] GraphQL query exposes theme configuration
- [ ] Frontend `ThemeProvider` applies CSS custom properties
- [ ] Changing brand colour in Django updates UI without rebuild
- [ ] Web and mobile both use theme configuration

---

## Summary

| Priority | Issue                                    | Effort  | Impact |
| -------- | ---------------------------------------- | ------- | ------ |
| 🔴 P1    | Fix hardcoded password_max_length        | 5 min   | HIGH   |
| 🟡 P2    | Externalise design tokens                | 2-4 hrs | MEDIUM |
| 🟡 P3    | Add SRI for external scripts             | 1 hr    | MEDIUM |
| 🟢 P4    | Add ESLint rule for deprecated constants | 30 min  | LOW    |
| 🟢 P5    | Add Turborepo for build optimisation     | 1 hr    | LOW    |

**Total Effort:** 5 minutes (P1 only) to 8.5 hours (all priorities)

**Recommendation:** Fix P1 immediately (before production), schedule P2-P3 for post-MVP, and consider P4-P5 for future sprints.
