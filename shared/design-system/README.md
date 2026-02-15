# Shared Design System

**Cross-platform design system using Tailwind v4 (web) and NativeWind 4 (mobile).**

## Overview

The shared design system provides consistent UI across web (Next.js) and mobile (React Native) platforms through:

- **Design Tokens** - Colours, typography, spacing, borders, shadows (100% shared)
- **Primitive Components** - Button, Input, Checkbox, Card, Alert, Badge, Spinner (100% shared)
- **Tailwind v4 Configuration** - CSS-first configuration for web
- **NativeWind 4 Configuration** - Config file for mobile
- **Unified Theme Object** - JavaScript/TypeScript access to design tokens

## Structure

```
shared/design-system/
├── tokens/                  # Design tokens (100% shared)
│   ├── colors.ts           # Brand + semantic colours
│   ├── typography.ts       # Fonts, sizes, weights, line heights
│   ├── spacing.ts          # 4px base scale
│   ├── borders.ts          # Border radius, widths
│   ├── shadows.ts          # Box shadows (web), elevation (mobile)
│   ├── breakpoints.ts      # Responsive breakpoints
│   ├── z-index.ts          # Stacking order
│   └── index.ts            # Central export
│
├── components/              # Primitive components (100% shared)
│   ├── Button.tsx          # Primary, secondary, danger, ghost
│   ├── Input.tsx           # Text, password, email, phone
│   ├── Checkbox.tsx        # GDPR consent checkboxes
│   ├── Card.tsx            # Elevated, flat containers
│   ├── Alert.tsx           # Success, error, warning, info alerts
│   ├── Badge.tsx           # Status badges
│   ├── Spinner.tsx         # Loading indicators
│   └── index.ts            # Central export
│
├── theme.css                # Tailwind v4 configuration (web)
├── nativewind.config.ts     # NativeWind 4 configuration (mobile)
├── theme.ts                 # Unified theme object
└── README.md                # This file
```

## Design Tokens

### Colours

All colours meet WCAG 2.1 AA contrast standards (4.5:1 for text).

```typescript
import { colors } from '@syntek/shared/design-system/tokens';

// Brand colours
colors.primary[500]; // #3b82f6

// Semantic colours
colors.success;      // { light: '#d1fae5', DEFAULT: '#10b981', dark: '#065f46' }
colors.warning;
colors.error;
colors.info;

// Authentication-specific
colors.auth.password.weak;       // #ef4444
colors.auth.password.strong;     // #059669
colors.auth.mfa.enabled;         // #10b981
colors.auth.session.active;      // #10b981
colors.auth.verification.verified; // #10b981

// Social providers
colors.social.google;   // #4285f4
colors.social.github;   // #24292e
```

### Spacing

4px base scale for consistency.

```typescript
import { spacing } from '@syntek/shared/design-system/tokens';

spacing[0];  // 0px
spacing[1];  // 4px
spacing[4];  // 16px
spacing[11]; // 44px (iOS minimum touch target)
```

### Typography

```typescript
import { typography } from '@syntek/shared/design-system/tokens';

typography.fontFamily.sans; // ['Inter', 'system-ui', ...]
typography.fontSize.base;   // 1rem (16px)
typography.fontWeight.semibold; // 600
```

## Components

### Button

Cross-platform button with variants and sizes.

```tsx
import { Button } from '@syntek/shared/design-system/components';

<Button variant="primary" size="md" onPress={handleSubmit}>
  Sign In
</Button>

<Button variant="danger" loading={isLoading}>
  Delete Account
</Button>
```

**Props:**
- `variant`: `primary` | `secondary` | `danger` | `ghost`
- `size`: `sm` | `md` (default) | `lg`
- `loading`: boolean
- `disabled`: boolean

### Input

Text input with validation states.

```tsx
import { Input } from '@syntek/shared/design-system/components';

<Input
  label="Email Address"
  type="email"
  placeholder="you@example.com"
  value={email}
  onChangeText={setEmail}
  error={errors.email}
/>

<Input
  label="Password"
  type="password"
  showPasswordToggle
/>
```

**Props:**
- `label`: string
- `type`: `text` | `password` | `email` | `phone` | `number`
- `error`: string
- `helperText`: string
- `showPasswordToggle`: boolean

### Checkbox

Checkbox for consents and selections.

```tsx
import { Checkbox } from '@syntek/shared/design-system/components';

<Checkbox
  label="I agree to the Terms and Conditions"
  checked={agreedToTerms}
  onChange={setAgreedToTerms}
  error={!agreedToTerms && submitted}
/>
```

### Card

Container component with elevation.

```tsx
import { Card } from '@syntek/shared/design-system/components';

<Card variant="elevated">
  <Text>Card content</Text>
</Card>
```

**Props:**
- `variant`: `elevated` (default) | `flat`

### Alert

Alert/banner for messages.

```tsx
import { Alert } from '@syntek/shared/design-system/components';

<Alert
  type="error"
  title="Authentication Failed"
  message="Invalid email or password"
/>
```

**Props:**
- `type`: `success` | `error` | `warning` | `info`
- `title`: string (optional)
- `message`: string

### Badge

Status badge with colour variants.

```tsx
import { Badge } from '@syntek/shared/design-system/components';

<Badge variant="success" label="Verified" />
<Badge variant="warning" label="Pending" />
<Badge variant="error" label="Suspended" />
```

### Spinner

Loading indicator.

```tsx
import { Spinner } from '@syntek/shared/design-system/components';

<Spinner size="medium" />
```

## Usage

### Web (Next.js)

1. Import the theme CSS in your app:

```tsx
// app/layout.tsx
import '@syntek/shared/design-system/theme.css';
```

2. Use components and tokens:

```tsx
import { Button, Input } from '@syntek/shared/design-system/components';
import { colors } from '@syntek/shared/design-system/tokens';
```

### Mobile (React Native)

1. Configure NativeWind in `tailwind.config.js`:

```js
import nativewindConfig from '@syntek/shared/design-system/nativewind.config';

export default nativewindConfig;
```

2. Use components and tokens:

```tsx
import { Button, Input } from '@syntek/shared/design-system/components';
import { colors } from '@syntek/shared/design-system/tokens';
```

## Accessibility

All components meet WCAG 2.1 AA standards:

- **Colour Contrast:** 4.5:1 for text, 3:1 for UI components
- **Touch Targets:** Minimum 44px (iOS) / 48dp (Android)
- **Keyboard Navigation:** All interactive elements focusable
- **Screen Readers:** ARIA labels and roles
- **Focus Indicators:** Visible focus states

## Customisation

### Extending Tokens

```typescript
// my-app/theme.ts
import { colors } from '@syntek/shared/design-system/tokens';

export const extendedColors = {
  ...colors,
  custom: {
    brand: '#ff0000',
  },
};
```

### Custom Components

Build on primitive components:

```tsx
import { Button } from '@syntek/shared/design-system/components';

export const PrimaryButton = (props) => (
  <Button variant="primary" size="lg" {...props} />
);
```

## Dependencies

```json
{
  "dependencies": {
    "tailwindcss": "^4.1.0",
    "nativewind": "^4.0.0",
    "react": "^19.2.1",
    "react-native": "^0.83.0"
  }
}
```

## Testing

Test components on both platforms:

```bash
# Test on web
cd web/packages/ui-auth && pnpm dev

# Test on mobile
cd mobile/packages/mobile-auth && pnpm start
```

## Related Documentation

- **Design Tokens:** `tokens/README.md`
- **Accessibility:** `docs/ACCESSIBILITY.md`
- **Tailwind v4:** https://tailwindcss.com/docs
- **NativeWind v4:** https://www.nativewind.dev/
