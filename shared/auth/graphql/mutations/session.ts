/**
 * GraphQL mutations for session security operations.
 *
 * Mutations for session termination and fingerprint updates.
 */

import { gql } from '@apollo/client';

/**
 * Mutation to terminate a specific session.
 *
 * Logs out a session by ID (e.g., remote device logout).
 * Cannot terminate the current session (use logout mutation instead).
 *
 * @example
 * ```typescript
 * const [terminateSession] = useMutation(TERMINATE_SESSION);
 * await terminateSession({
 *   variables: { sessionId }
 * });
 * ```
 */
export const TERMINATE_SESSION = gql`
  mutation TerminateSession($sessionId: ID!) {
    terminateSession(sessionId: $sessionId) {
      success
      message
    }
  }
`;

/**
 * Mutation to terminate all sessions except the current one.
 *
 * Logs out all other devices/sessions.
 * Useful when user suspects account compromise.
 *
 * @example
 * ```typescript
 * const [terminateAllSessions] = useMutation(TERMINATE_ALL_SESSIONS);
 * await terminateAllSessions();
 * ```
 */
export const TERMINATE_ALL_SESSIONS = gql`
  mutation TerminateAllSessions {
    terminateAllSessions {
      success
      message
      terminatedCount
    }
  }
`;

/**
 * Mutation to update session fingerprint.
 *
 * Updates device fingerprint for the current session.
 * Used to detect session hijacking (fingerprint mismatch).
 *
 * @example
 * ```typescript
 * const [updateFingerprint] = useMutation(UPDATE_FINGERPRINT);
 * await updateFingerprint({
 *   variables: {
 *     fingerprint: await generateFingerprint()
 *   }
 * });
 * ```
 */
export const UPDATE_FINGERPRINT = gql`
  mutation UpdateFingerprint($fingerprint: String!) {
    updateFingerprint(fingerprint: $fingerprint) {
      success
      message
    }
  }
`;

/**
 * Mutation to mark session as trusted.
 *
 * Marks current session as trusted device (reduces security prompts).
 * Requires MFA verification to mark as trusted.
 *
 * @example
 * ```typescript
 * const [markTrustedDevice] = useMutation(MARK_TRUSTED_DEVICE);
 * await markTrustedDevice({
 *   variables: { totpCode: '123456' }
 * });
 * ```
 */
export const MARK_TRUSTED_DEVICE = gql`
  mutation MarkTrustedDevice($totpCode: String!) {
    markTrustedDevice(totpCode: $totpCode) {
      success
      message
    }
  }
`;
