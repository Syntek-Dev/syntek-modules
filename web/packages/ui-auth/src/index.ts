/**
 * @syntek/ui-auth - Web Authentication UI Package
 *
 * Next.js/React authentication components with WebAuthn, MFA, GDPR compliance.
 * Maximizes code reuse from @syntek/shared-auth (70-80% shared).
 *
 * This package provides web-specific implementations built on top of the shared
 * authentication architecture. It includes Next.js page components, routing integration,
 * and web-specific adapters for storage and WebAuthn.
 */

// Re-export everything from shared (types, hooks, GraphQL, utilities)
export * from '@syntek/shared-auth';

// Export web-specific components
export * from './components';
export * from './hooks';
export * from './contexts';
export * from './pages';
export * from './lib';
