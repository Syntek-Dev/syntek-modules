/**
 * Date formatting utility (UK format: dd.mm.yyyy).
 *
 * Formats dates according to UK conventions.
 */

/**
 * Formats date to UK format (dd.mm.yyyy).
 *
 * @param date - Date to format
 * @returns Formatted date string
 *
 * @example
 * ```typescript
 * const formatted = formatDate(new Date('2026-02-15'));
 * // Returns: '15.02.2026'
 * ```
 */
export function formatDate(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date;

  const day = d.getDate().toString().padStart(2, '0');
  const month = (d.getMonth() + 1).toString().padStart(2, '0');
  const year = d.getFullYear();

  return `${day}.${month}.${year}`;
}

/**
 * Formats datetime to UK format (dd.mm.yyyy, HH:mm).
 *
 * @param date - Date to format
 * @returns Formatted datetime string
 *
 * @example
 * ```typescript
 * const formatted = formatDateTime(new Date('2026-02-15T14:30:00'));
 * // Returns: '15.02.2026, 14:30'
 * ```
 */
export function formatDateTime(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date;

  const datePart = formatDate(d);
  const hours = d.getHours().toString().padStart(2, '0');
  const minutes = d.getMinutes().toString().padStart(2, '0');

  return `${datePart}, ${hours}:${minutes}`;
}

/**
 * Formats relative time (e.g., '2 hours ago', 'just now').
 *
 * @param date - Date to format
 * @returns Relative time string
 *
 * @example
 * ```typescript
 * const formatted = formatRelativeTime(new Date(Date.now() - 3600000));
 * // Returns: '1 hour ago'
 * ```
 */
export function formatRelativeTime(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);

  if (diffSec < 60) return 'Just now';
  if (diffMin < 60) return `${diffMin} minute${diffMin > 1 ? 's' : ''} ago`;
  if (diffHour < 24) return `${diffHour} hour${diffHour > 1 ? 's' : ''} ago`;
  if (diffDay < 7) return `${diffDay} day${diffDay > 1 ? 's' : ''} ago`;

  return formatDate(d);
}
