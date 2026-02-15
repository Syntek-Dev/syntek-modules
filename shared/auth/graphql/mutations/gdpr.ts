/**
 * GraphQL mutations for GDPR compliance operations.
 *
 * Mutations for account deletion, data export, and consent management.
 */

import { gql } from '@apollo/client';

/**
 * Mutation to delete user account (GDPR Right to Erasure).
 *
 * Permanently deletes user account and all associated data.
 * Requires password confirmation and 14-day grace period.
 *
 * GDPR Article 17: Right to erasure ("right to be forgotten")
 *
 * @example
 * ```typescript
 * const [deleteAccount] = useMutation(DELETE_ACCOUNT);
 * await deleteAccount({
 *   variables: { password, reason: 'No longer needed' }
 * });
 * ```
 */
export const DELETE_ACCOUNT = gql`
  mutation DeleteAccount($password: String!, $reason: String) {
    deleteAccount(password: $password, reason: $reason) {
      success
      message
      scheduledDeletionDate
    }
  }
`;

/**
 * Mutation to cancel account deletion.
 *
 * Cancels scheduled account deletion within grace period (14 days).
 *
 * @example
 * ```typescript
 * const [cancelDeletion] = useMutation(CANCEL_ACCOUNT_DELETION);
 * await cancelDeletion();
 * ```
 */
export const CANCEL_ACCOUNT_DELETION = gql`
  mutation CancelAccountDeletion {
    cancelAccountDeletion {
      success
      message
    }
  }
`;

/**
 * Mutation to request data export (GDPR Right to Data Portability).
 *
 * Requests export of all user data in machine-readable format.
 * GDPR requires delivery within 30 days.
 *
 * GDPR Article 20: Right to data portability
 *
 * @example
 * ```typescript
 * const [exportData] = useMutation(EXPORT_DATA);
 * await exportData({
 *   variables: { format: 'JSON' }
 * });
 * ```
 */
export const EXPORT_DATA = gql`
  mutation ExportData($format: ExportFormat!) {
    exportData(format: $format) {
      success
      message
      estimatedCompletionDate
    }
  }
`;

/**
 * Mutation to grant consent for data processing.
 *
 * Records user consent for specific data processing activities.
 * GDPR requires explicit, informed consent.
 *
 * GDPR Article 7: Conditions for consent
 *
 * @example
 * ```typescript
 * const [grantConsent] = useMutation(GRANT_CONSENT);
 * await grantConsent({
 *   variables: {
 *     consentType: 'MARKETING_EMAILS',
 *     legalDocumentId: 'privacy-policy-v2'
 *   }
 * });
 * ```
 */
export const GRANT_CONSENT = gql`
  mutation GrantConsent($consentType: String!, $legalDocumentId: ID!) {
    grantConsent(consentType: $consentType, legalDocumentId: $legalDocumentId) {
      success
      message
      consent {
        id
        consentType
        granted
        grantedAt
      }
    }
  }
`;

/**
 * Mutation to withdraw consent (GDPR Right to Withdraw Consent).
 *
 * Withdraws previously granted consent for data processing.
 * GDPR requires consent withdrawal to be as easy as granting.
 *
 * GDPR Article 7(3): Right to withdraw consent
 *
 * @example
 * ```typescript
 * const [withdrawConsent] = useMutation(WITHDRAW_CONSENT);
 * await withdrawConsent({
 *   variables: { consentId }
 * });
 * ```
 */
export const WITHDRAW_CONSENT = gql`
  mutation WithdrawConsent($consentId: ID!) {
    withdrawConsent(consentId: $consentId) {
      success
      message
    }
  }
`;

/**
 * Mutation to accept legal document (Terms, Privacy Policy).
 *
 * Records user acceptance of legal documents.
 * Required during registration and when documents are updated.
 *
 * @example
 * ```typescript
 * const [acceptDocument] = useMutation(ACCEPT_LEGAL_DOCUMENT);
 * await acceptDocument({
 *   variables: {
 *     documentType: 'TERMS_OF_SERVICE',
 *     version: 'v2.1'
 *   }
 * });
 * ```
 */
export const ACCEPT_LEGAL_DOCUMENT = gql`
  mutation AcceptLegalDocument($documentType: String!, $version: String!) {
    acceptLegalDocument(documentType: $documentType, version: $version) {
      success
      message
    }
  }
`;
