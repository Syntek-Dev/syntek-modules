/**
 * GraphQL fragments for GDPR Consent fields.
 *
 * Reusable fragments for user consent and legal document data.
 */

import { gql } from '@apollo/client';

/**
 * Core consent fields fragment.
 *
 * Essential consent information for GDPR compliance display.
 */
export const CONSENT_CORE_FIELDS = gql`
  fragment ConsentCoreFields on Consent {
    id
    consentType
    granted
    grantedAt
    withdrawnAt
    ipAddress
  }
`;

/**
 * Legal document fields fragment.
 *
 * Legal document information (Terms of Service, Privacy Policy).
 */
export const LEGAL_DOCUMENT_FIELDS = gql`
  fragment LegalDocumentFields on LegalDocument {
    id
    documentType
    version
    effectiveDate
    content
    acceptedAt
  }
`;

/**
 * Full consent fields fragment.
 *
 * Complete consent information including legal document details.
 */
export const CONSENT_FULL_FIELDS = gql`
  fragment ConsentFullFields on Consent {
    ...ConsentCoreFields
    legalDocument {
      ...LegalDocumentFields
    }
  }
  ${CONSENT_CORE_FIELDS}
  ${LEGAL_DOCUMENT_FIELDS}
`;
