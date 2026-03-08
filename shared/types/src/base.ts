/**
 * Branded string type for unique identifiers.
 *
 * Uses a phantom `__brand` property to prevent accidental interchange of
 * different ID types at compile time. Use the domain-specific aliases
 * (`UserId`, `TenantId`, etc.) exported from their respective modules to
 * get full compile-time protection against IDOR.
 *
 * To create an ID value, cast from string: `const id = "abc" as ID;`
 */
export type ID = string & { readonly __brand: "ID" };

/**
 * ISO 8601 date-time string.
 *
 * Format: `YYYY-MM-DDTHH:mm:ss.sssZ` (e.g. `"2026-03-06T16:00:00.000Z"`).
 *
 * This is an unvalidated branded type alias. Callers are responsible for
 * ensuring the string conforms to ISO 8601 before casting. A runtime
 * validator can be added via Zod in consuming packages.
 */
export type Timestamp = string & { readonly __brand: "Timestamp" };

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
}

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}
