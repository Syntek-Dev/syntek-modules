/**
 * GraphQL queries for session security operations.
 *
 * Queries for session management, history, and suspicious activity detection.
 */

import { gql } from '@apollo/client';
import { SESSION_FULL_FIELDS } from '../fragments';

/**
 * Query to get all active sessions for the current user.
 *
 * Returns list of active sessions across all devices.
 * Always fetches fresh data (not cached) for security.
 *
 * @example
 * ```typescript
 * const { data } = useQuery(GET_ACTIVE_SESSIONS);
 * const sessions = data.getActiveSessions;
 * ```
 */
export const GET_ACTIVE_SESSIONS = gql`
  query GetActiveSessions {
    getActiveSessions {
      ...SessionFullFields
    }
  }
  ${SESSION_FULL_FIELDS}
`;

/**
 * Query to get session history for the current user.
 *
 * Returns paginated list of past sessions (including terminated sessions).
 * Always fetches fresh data (not cached).
 *
 * @example
 * ```typescript
 * const { data } = useQuery(SESSION_HISTORY, {
 *   variables: { limit: 20, offset: 0 }
 * });
 * const history = data.sessionHistory;
 * ```
 */
export const SESSION_HISTORY = gql`
  query SessionHistory($limit: Int, $offset: Int) {
    sessionHistory(limit: $limit, offset: $offset) {
      sessions {
        ...SessionFullFields
      }
      totalCount
      hasMore
    }
  }
  ${SESSION_FULL_FIELDS}
`;

/**
 * Query to get suspicious sessions for the current user.
 *
 * Returns sessions flagged as potentially malicious (high risk score).
 * Always fetches fresh data (not cached).
 *
 * @example
 * ```typescript
 * const { data } = useQuery(GET_SUSPICIOUS_SESSIONS);
 * const suspiciousSessions = data.getSuspiciousSessions;
 * ```
 */
export const GET_SUSPICIOUS_SESSIONS = gql`
  query GetSuspiciousSessions {
    getSuspiciousSessions {
      ...SessionFullFields
    }
  }
  ${SESSION_FULL_FIELDS}
`;

/**
 * Query to get detailed session information by ID.
 *
 * Returns complete session data including security metadata.
 * Use for session detail views and security analysis.
 *
 * @example
 * ```typescript
 * const { data } = useQuery(GET_SESSION_DETAIL, {
 *   variables: { sessionId }
 * });
 * const session = data.getSessionDetail;
 * ```
 */
export const GET_SESSION_DETAIL = gql`
  query GetSessionDetail($sessionId: ID!) {
    getSessionDetail(sessionId: $sessionId) {
      ...SessionFullFields
      loginEvents {
        timestamp
        success
        mfaUsed
        ipAddress
      }
      activityLog {
        timestamp
        action
        ipAddress
        userAgent
      }
    }
  }
  ${SESSION_FULL_FIELDS}
`;
