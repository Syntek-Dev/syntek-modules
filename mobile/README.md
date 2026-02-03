# Mobile Packages (React Native)

This directory contains all mobile packages for React Native and Expo applications.

## Structure

```
mobile/
├── packages/
│   ├── security-core/          # Security bundle (cert pinning, secure storage, cache, jailbreak detection)
│   ├── security-auth/          # Auth bundle (sessions, biometrics, JWT, API keys, request signing)
│   ├── mobile-auth/            # Authentication flows
│   ├── mobile-profiles/        # Profile management
│   ├── mobile-media/           # Media handling
│   ├── mobile-notifications/   # Push notifications
│   ├── mobile-search/          # Search interface
│   ├── mobile-bookings/        # Booking and calendar
│   └── mobile-payments/        # Payment flows
```

## Development

### Install Dependencies

```bash
# From repository root
pnpm install
```

### Build All Mobile Packages

```bash
# Build all mobile packages
pnpm build:mobile

# Build specific package
pnpm --filter @syntek/mobile-security-core build
```

### Development Mode

```bash
# Watch mode for specific package
pnpm --filter @syntek/mobile-security-core dev
```

### Testing

```bash
# Test all mobile packages
pnpm test:mobile

# Test specific package
pnpm --filter @syntek/mobile-security-core test
```

### Native Module Setup

Some packages require native code (iOS/Android). After installing:

```bash
# iOS
cd ios && pod install

# Android (no additional steps needed)
```

### Adding a New Package

1. Create directory: `mobile/packages/<package-name>/`
2. Create `package.json` with name `@syntek/mobile-<package-name>`
3. Add source files in `src/`
4. If native code required:
   - Add iOS native module in `ios/`
   - Add Android native module in `android/`
   - Create `*.podspec` for iOS
5. Add tests in `__tests__/`
6. Export from `src/index.ts`

### Publishing

```bash
# Build and publish specific package
cd packages/<package-name>
pnpm build
pnpm publish
```

## Package Naming Convention

- **Security bundles**: `@syntek/mobile-security-<bundle>` (e.g., `@syntek/mobile-security-core`)
- **Feature modules**: `@syntek/mobile-<feature>` (e.g., `@syntek/mobile-auth`)

## Dependencies

### Shared Dependencies

All packages share these peer dependencies:
- `react@^19.0.0`
- `react-native@^0.83.0`

### Native Dependencies

Some packages require native modules:
- `react-native-keychain` (secure storage)
- `react-native-ssl-pinning` (certificate pinning)
- `react-native-biometrics` (Face ID, Touch ID, fingerprint)

## Platform Support

- **iOS**: 15.0+
- **Android**: API 24+ (Android 7.0+)

## Contributing

See main repository README for contribution guidelines.
