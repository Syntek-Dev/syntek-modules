/**
 * Session device information formatting utility.
 *
 * Formats device and browser information for session displays.
 */

/**
 * Formats device type for display.
 *
 * @param deviceType - Device type from session
 * @returns Formatted device type
 *
 * @example
 * ```typescript
 * const formatted = formatDeviceType('MOBILE');
 * // Returns: 'Mobile'
 * ```
 */
export function formatDeviceType(
  deviceType: 'DESKTOP' | 'MOBILE' | 'TABLET' | 'UNKNOWN'
): string {
  const labels: Record<string, string> = {
    DESKTOP: 'Desktop',
    MOBILE: 'Mobile',
    TABLET: 'Tablet',
    UNKNOWN: 'Unknown Device',
  };

  return labels[deviceType] || 'Unknown Device';
}

/**
 * Formats browser information for display.
 *
 * @param browser - Browser name
 * @param version - Browser version
 * @returns Formatted browser string
 *
 * @example
 * ```typescript
 * const formatted = formatBrowser('Chrome', '120.0.0');
 * // Returns: 'Chrome 120'
 * ```
 */
export function formatBrowser(browser: string, version?: string): string {
  if (!version) return browser;

  // Extract major version only
  const majorVersion = version.split('.')[0];
  return `${browser} ${majorVersion}`;
}

/**
 * Formats operating system information for display.
 *
 * @param os - Operating system name
 * @param version - OS version
 * @returns Formatted OS string
 *
 * @example
 * ```typescript
 * const formatted = formatOS('macOS', '14.2');
 * // Returns: 'macOS 14'
 * ```
 */
export function formatOS(os: string, version?: string): string {
  if (!version) return os;

  // Extract major version only
  const majorVersion = version.split('.')[0];
  return `${os} ${majorVersion}`;
}

/**
 * Formats location information for display.
 *
 * @param city - City name
 * @param region - Region/state
 * @param country - Country name
 * @returns Formatted location string
 *
 * @example
 * ```typescript
 * const formatted = formatLocation('London', 'England', 'United Kingdom');
 * // Returns: 'London, England, United Kingdom'
 * ```
 */
export function formatLocation(
  city?: string,
  region?: string,
  country?: string
): string {
  const parts = [city, region, country].filter(Boolean);
  return parts.length > 0 ? parts.join(', ') : 'Unknown Location';
}

/**
 * Formats complete device information for display.
 *
 * @param session - Session object with device information
 * @returns Formatted device description
 *
 * @example
 * ```typescript
 * const formatted = formatDeviceInfo({
 *   browser: 'Chrome',
 *   browserVersion: '120.0.0',
 *   os: 'macOS',
 *   osVersion: '14.2',
 *   deviceType: 'DESKTOP'
 * });
 * // Returns: 'Chrome 120 on macOS 14 (Desktop)'
 * ```
 */
export function formatDeviceInfo(session: {
  browser?: string;
  browserVersion?: string;
  os?: string;
  osVersion?: string;
  deviceType?: 'DESKTOP' | 'MOBILE' | 'TABLET' | 'UNKNOWN';
}): string {
  const browserInfo = session.browser
    ? formatBrowser(session.browser, session.browserVersion)
    : 'Unknown Browser';

  const osInfo = session.os
    ? formatOS(session.os, session.osVersion)
    : 'Unknown OS';

  const deviceType = session.deviceType
    ? formatDeviceType(session.deviceType)
    : 'Unknown Device';

  return `${browserInfo} on ${osInfo} (${deviceType})`;
}
