# Web Packages (Next.js/React)

This directory contains all web-based packages for Next.js and React applications.

## Structure

```
web/
├── packages/
│   ├── security-core/         # Security bundle (headers, CORS, CSRF, XSS, cache, middleware)
│   ├── security-auth/          # Auth bundle (sessions, cookies, JWT, API keys, request signing)
│   ├── security-input/         # Input bundle (validation, rate limiting)
│   ├── ui-auth/                # Authentication UI components
│   ├── ui-profiles/            # Profile management UI
│   ├── ui-media/               # Media display components
│   ├── ui-notifications/       # Notification components
│   ├── ui-search/              # Search interface
│   ├── ui-forms/               # Form rendering components
│   ├── ui-comments/            # Comments and ratings UI
│   ├── ui-analytics/           # Analytics dashboard
│   ├── ui-bookings/            # Booking and calendar UI
│   ├── ui-payments/            # Payment flow UI
│   ├── ui-webhooks/            # Webhook management UI
│   └── ui-feature-flags/       # Feature flag UI
```

## Development

### Install Dependencies

```bash
# From repository root
pnpm install
```

### Build All Web Packages

```bash
# Build all web packages
pnpm build:web

# Build specific package
pnpm --filter @syntek/security-core build
```

### Development Mode

```bash
# Watch mode for specific package
pnpm --filter @syntek/security-core dev
```

### Testing

```bash
# Test all web packages
pnpm test:web

# Test specific package
pnpm --filter @syntek/security-core test
```

### Adding a New Package

1. Create directory: `web/packages/<package-name>/`
2. Create `package.json` with name `@syntek/<package-name>`
3. Add source files in `src/`
4. Add tests in `__tests__/` or `*.test.ts`
5. Export from `src/index.ts`

### Publishing

```bash
# Build and publish specific package
cd packages/<package-name>
pnpm build
pnpm publish
```

## Package Naming Convention

- **Security bundles**: `@syntek/security-<bundle-name>` (e.g., `@syntek/security-core`)
- **UI components**: `@syntek/ui-<feature>` (e.g., `@syntek/ui-auth`)
- **Utilities**: `@syntek/<feature>` (e.g., `@syntek/jwt`)

## Dependencies

### Shared Dependencies

All packages share these peer dependencies:
- `react@^19.0.0`
- `next@^16.0.0` (for Next.js specific packages)

### Security Bundles

Security bundles automatically include all their sub-modules as dependencies.

## Contributing

See main repository README for contribution guidelines.
