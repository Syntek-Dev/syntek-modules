/**
 * GraphQL queries for GDPR compliance operations.
 *
 * Queries for user consent, data export, and legal documents.
 */

import { gql } from '@apollo/client';
import { CONSENT_FULL_FIELDS, LEGAL_DOCUMENT_FIELDS } from '../fragments';

/**
 * Query to get consent status for the current user.
 *
 * Returns all consent records (granted and withdrawn).
 * Always fetches fresh data (not cached).
 *
 * @example
 * ```typescript
 * const { data } = useQuery(GET_CONSENT_STATUS);
 * const consents = data.getConsentStatus;
 * ```
 */
export const GET_CONSENT_STATUS = gql`
  query GetConsentStatus {
    getConsentStatus {
      ...ConsentFullFields
    }
  }
  ${CONSENT_FULL_FIELDS}
`;

/**
 * Query to get data export status for the current user.
 *
 * Returns status of pending/completed data export requests.
 * GDPR requires data export within 30 days of request.
 *
 * @example
 * ```typescript
 * const { data } = useQuery(EXPORT_DATA_STATUS);
 * const { status, downloadUrl } = data.exportDataStatus;
 * ```
 */
export const EXPORT_DATA_STATUS = gql`
  query ExportDataStatus {
    exportDataStatus {
      requestedAt
      status
      downloadUrl
      expiresAt
      fileSize
    }
  }
`;

/**
 * Query to get current legal documents (Terms, Privacy Policy).
 *
 * Returns latest versions of legal documents.
 * Cached for 5 minutes to reduce API calls.
 *
 * @example
 * ```typescript
 * const { data } = useQuery(GET_LEGAL_DOCUMENTS);
 * const { termsOfService, privacyPolicy } = data.getLegalDocuments;
 * ```
 */
export const GET_LEGAL_DOCUMENTS = gql`
  query GetLegalDocuments {
    getLegalDocuments {
      termsOfService {
        ...LegalDocumentFields
      }
      privacyPolicy {
        ...LegalDocumentFields
      }
      cookiePolicy {
        ...LegalDocumentFields
      }
    }
  }
  ${LEGAL_DOCUMENT_FIELDS}
`;

/**
 * Query to get user's accepted legal document versions.
 *
 * Returns which versions of Terms/Privacy Policy the user has accepted.
 * Used to determine if user needs to re-accept updated documents.
 *
 * @example
 * ```typescript
 * const { data } = useQuery(GET_ACCEPTED_DOCUMENTS);
 * const accepted = data.getAcceptedDocuments;
 * ```
 */
export const GET_ACCEPTED_DOCUMENTS = gql`
  query GetAcceptedDocuments {
    getAcceptedDocuments {
      documentType
      version
      acceptedAt
      ipAddress
    }
  }
`;
