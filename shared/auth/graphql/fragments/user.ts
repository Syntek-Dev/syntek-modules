/**
 * GraphQL fragments for User fields.
 *
 * Reusable fragments for user data across queries and mutations.
 */

import { gql } from '@apollo/client';

/**
 * Core user fields fragment.
 *
 * Minimal user information required across the application.
 * Use this for basic user display (avatar, name, email).
 */
export const USER_CORE_FIELDS = gql`
  fragment UserCoreFields on User {
    id
    email
    username
    firstName
    lastName
    isActive
    isVerified
    createdAt
    lastLogin
  }
`;

/**
 * User profile fields fragment.
 *
 * Extended user information including profile data.
 * Use this for profile pages and detailed user views.
 */
export const USER_PROFILE_FIELDS = gql`
  fragment UserProfileFields on User {
    ...UserCoreFields
    phoneNumber
    phoneVerified
    bio
    avatarUrl
    locale
    timezone
    dateFormat
    timeFormat
  }
  ${USER_CORE_FIELDS}
`;

/**
 * User security fields fragment.
 *
 * Security-related user information (MFA status, session count).
 * Use this for security dashboards and account settings.
 */
export const USER_SECURITY_FIELDS = gql`
  fragment UserSecurityFields on User {
    ...UserCoreFields
    totpEnabled
    passkeyCount
    activeSessions
    lastPasswordChange
    requirePasswordChange
  }
  ${USER_CORE_FIELDS}
`;

/**
 * Full user fields fragment.
 *
 * Complete user information including profile and security data.
 * Use sparingly (large payload) for comprehensive user views.
 */
export const USER_FULL_FIELDS = gql`
  fragment UserFullFields on User {
    ...UserCoreFields
    ...UserProfileFields
    ...UserSecurityFields
  }
  ${USER_CORE_FIELDS}
  ${USER_PROFILE_FIELDS}
  ${USER_SECURITY_FIELDS}
`;
