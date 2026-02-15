/**
 * utils/index.ts
 *
 * Exports all mobile security utilities.
 */

export {
  detectRootedDevice,
  isEmulator,
  type RootDetectionResult,
} from './rootDetection';

export {
  configureCertificatePinning,
  validateCertificate,
  DEFAULT_CERTIFICATE_PINS,
  type CertificatePinningConfig,
} from './certificatePinning';

export {
  preventScreenCapture,
  allowScreenCapture,
  usePreventScreenCapture,
} from './screenCapture';

export {
  useAppStateTracking,
  useBackgroundTimeTracking,
  type AppStateTrackingConfig,
} from './appStateTracking';
