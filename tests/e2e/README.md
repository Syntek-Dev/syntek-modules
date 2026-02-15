# End-to-End Testing Infrastructure

Comprehensive E2E testing for authentication flows across web (Playwright) and mobile (Detox).

## Overview

E2E tests validate complete authentication flows from user perspective:
- Registration → Email verification → Login
- MFA setup → TOTP verification
- Passkey registration → Passkey authentication
- Social OAuth flows (7 providers)
- Password reset → Account recovery
- Auto-logout → Session management

## Tech Stack

### Web (Next.js)
- **Playwright** - Browser automation
- **@playwright/test** - Test runner
- **playwright-expect** - Assertions

### Mobile (React Native)
- **Detox** - React Native E2E testing
- **Jest** - Test runner
- **detox-cli** - CLI tool

## Installation

### Web E2E Tests

\`\`\`bash
cd web
pnpm add -D @playwright/test playwright
npx playwright install chromium firefox webkit
\`\`\`

### Mobile E2E Tests

\`\`\`bash
cd mobile
pnpm add -D detox jest
npx detox init

# iOS
brew tap wix/brew
brew install applesimutils

# Android
# Ensure Android SDK and emulator installed
\`\`\`

## Project Structure

\`\`\`
tests/e2e/
├── web/                    # Playwright tests
│   ├── auth/
│   │   ├── registration.spec.ts
│   │   ├── login.spec.ts
│   │   ├── mfa-setup.spec.ts
│   │   ├── passkey.spec.ts
│   │   ├── social-auth.spec.ts
│   │   ├── password-reset.spec.ts
│   │   └── auto-logout.spec.ts
│   ├── fixtures/
│   │   └── auth.fixture.ts
│   ├── helpers/
│   │   └── auth.helper.ts
│   └── playwright.config.ts
│
├── mobile/                 # Detox tests
│   ├── auth/
│   │   ├── registration.e2e.ts
│   │   ├── login.e2e.ts
│   │   ├── biometric.e2e.ts
│   │   ├── social-auth.e2e.ts
│   │   └── auto-logout.e2e.ts
│   ├── helpers/
│   │   └── auth.helper.ts
│   └── .detoxrc.js
│
└── shared/                 # Shared test data
    ├── test-users.json
    └── test-data.ts
\`\`\`

## Running Tests

### Web E2E Tests

\`\`\`bash
# Run all tests
cd web && pnpm test:e2e

# Run specific test file
pnpm test:e2e tests/e2e/web/auth/registration.spec.ts

# Run in headed mode (see browser)
pnpm test:e2e --headed

# Run in specific browser
pnpm test:e2e --project=chromium
pnpm test:e2e --project=firefox
pnpm test:e2e --project=webkit

# Debug mode
pnpm test:e2e --debug
\`\`\`

### Mobile E2E Tests

\`\`\`bash
# iOS
cd mobile
pnpm test:e2e:ios

# Android
pnpm test:e2e:android

# Debug mode
pnpm test:e2e:ios --debug-synchronization
\`\`\`

## Test Examples

### Web: Registration Flow

\`\`\`typescript
// tests/e2e/web/auth/registration.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Registration Flow', () => {
  test('complete registration with email verification', async ({ page }) => {
    // Navigate to registration page
    await page.goto('/auth/register');

    // Fill registration form
    await page.fill('[name="email"]', 'test@example.com');
    await page.fill('[name="password"]', 'SecureP@ssw0rd123!');
    await page.fill('[name="confirmPassword"]', 'SecureP@ssw0rd123!');

    // Accept legal terms
    await page.check('[name="acceptTerms"]');
    await page.check('[name="acceptPrivacy"]');

    // Submit form
    await page.click('button[type="submit"]');

    // Verify redirect to email verification
    await expect(page).toHaveURL('/auth/verify-email');
    await expect(page.locator('h1')).toContainText('Check Your Email');

    // Simulate email verification (get code from test inbox)
    const verificationCode = await getTestEmailVerificationCode('test@example.com');
    await page.fill('[name="code"]', verificationCode);
    await page.click('button[type="submit"]');

    // Verify successful login
    await expect(page).toHaveURL('/dashboard');
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
  });

  test('password strength validation', async ({ page }) => {
    await page.goto('/auth/register');
    
    // Try weak password
    await page.fill('[name="password"]', '123456');
    await page.blur('[name="password"]');
    
    // Verify error message
    await expect(page.locator('.password-error')).toContainText('Password too weak');
    
    // Submit should be disabled
    await expect(page.locator('button[type="submit"]')).toBeDisabled();
  });
});
\`\`\`

### Web: MFA Setup

\`\`\`typescript
// tests/e2e/web/auth/mfa-setup.spec.ts
import { test, expect } from '@playwright/test';
import { authenticator } from 'otplib';

test.describe('MFA Setup', () => {
  test.beforeEach(async ({ page }) => {
    // Login first
    await loginAsTestUser(page, 'test@example.com', 'SecureP@ssw0rd123!');
  });

  test('setup TOTP authenticator', async ({ page }) => {
    // Navigate to MFA setup
    await page.goto('/settings/security');
    await page.click('[data-testid="setup-mfa-button"]');

    // Get TOTP secret from QR code
    const totpSecret = await page.getAttribute('[data-testid="totp-secret"]', 'value');
    
    // Generate TOTP code
    const totpCode = authenticator.generate(totpSecret);
    
    // Enter TOTP code
    await page.fill('[name="totpCode"]', totpCode);
    await page.click('button[type="submit"]');

    // Verify MFA enabled
    await expect(page.locator('[data-testid="mfa-status"]')).toContainText('Enabled');

    // Download recovery keys
    await page.click('[data-testid="download-recovery-keys"]');
    
    // Verify download
    const download = await page.waitForEvent('download');
    expect(download.suggestedFilename()).toMatch(/recovery-keys.*\.txt/);
  });

  test('login with MFA', async ({ page }) => {
    // Setup MFA first
    const totpSecret = await setupMFA(page);

    // Logout
    await page.click('[data-testid="logout-button"]');

    // Login again
    await page.goto('/auth/login');
    await page.fill('[name="email"]', 'test@example.com');
    await page.fill('[name="password"]', 'SecureP@ssw0rd123!');
    await page.click('button[type="submit"]');

    // Should redirect to MFA verification
    await expect(page).toHaveURL('/auth/verify-mfa');

    // Generate and enter TOTP
    const totpCode = authenticator.generate(totpSecret);
    await page.fill('[name="totpCode"]', totpCode);
    await page.click('button[type="submit"]');

    // Verify successful login
    await expect(page).toHaveURL('/dashboard');
  });
});
\`\`\`

### Mobile: Biometric Authentication

\`\`\`typescript
// tests/e2e/mobile/auth/biometric.e2e.ts
import { device, element, by, expect as detoxExpect } from 'detox';

describe('Biometric Authentication', () => {
  beforeAll(async () => {
    await device.launchApp();
  });

  it('should enable biometric login', async () => {
    // Login first
    await loginAsTestUser('test@example.com', 'SecureP@ssw0rd123!');

    // Navigate to settings
    await element(by.id('settings-tab')).tap();
    await element(by.id('security-settings')).tap();

    // Enable biometric
    await element(by.id('enable-biometric-toggle')).tap();

    // iOS: Simulate Face ID
    if (device.getPlatform() === 'ios') {
      await device.matchFace();
    }

    // Android: Simulate fingerprint
    if (device.getPlatform() === 'android') {
      await device.selectBiometric('fingerprint');
    }

    // Verify enabled
    await detoxExpect(element(by.id('biometric-status'))).toHaveText('Enabled');

    // Logout
    await element(by.id('logout-button')).tap();

    // Login with biometric
    await element(by.id('biometric-login-button')).tap();

    // iOS: Match Face ID
    if (device.getPlatform() === 'ios') {
      await device.matchFace();
    }

    // Android: Match fingerprint
    if (device.getPlatform() === 'android') {
      await device.matchBiometric();
    }

    // Verify logged in
    await detoxExpect(element(by.id('dashboard-screen'))).toBeVisible();
  });
});
\`\`\`

## CI/CD Integration

### GitHub Actions

\`\`\`yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  web-e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v2
      - name: Install dependencies
        run: cd web && pnpm install
      - name: Install Playwright browsers
        run: cd web && npx playwright install --with-deps
      - name: Start backend
        run: cd backend && python manage.py runserver &
      - name: Start Next.js
        run: cd web && pnpm dev &
      - name: Run E2E tests
        run: cd web && pnpm test:e2e
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-results
          path: web/playwright-report/

  mobile-e2e-ios:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install dependencies
        run: cd mobile && pnpm install
      - name: Build iOS app
        run: cd mobile && pnpm detox build --configuration ios.sim.release
      - name: Run iOS E2E tests
        run: cd mobile && pnpm test:e2e:ios
\`\`\`

## Best Practices

1. **Test Data Isolation** - Each test creates/cleans up its own data
2. **Page Object Model** - Encapsulate page interactions in helper classes
3. **Stable Selectors** - Use data-testid attributes, avoid CSS selectors
4. **Wait for Elements** - Use Playwright/Detox auto-waiting
5. **Screenshot on Failure** - Capture screenshots for debugging
6. **Video Recording** - Record test runs in CI
7. **Parallel Execution** - Run tests in parallel for speed

## Troubleshooting

**Playwright: Timeout errors**
- Increase timeout: \`test.setTimeout(60000)\`
- Check network requests: \`page.on('request', ...)\`

**Detox: Synchronization issues**
- Add \`await device.disableSynchronization()\` for animations
- Use \`waitFor(element).toBeVisible()\`

**Both: Flaky tests**
- Add explicit waits
- Check for race conditions
- Verify element visibility before interaction

## References

- [Playwright Docs](https://playwright.dev/)
- [Detox Docs](https://wix.github.io/Detox/)
- [Testing Best Practices](https://martinfowler.com/articles/practical-test-pyramid.html)
