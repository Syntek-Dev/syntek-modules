/**
 * GraphQL fetcher for @syntek/graphql.
 *
 * Used by generated React Query hooks to execute GraphQL operations against
 * the Django/Strawberry backend.
 *
 * Endpoint resolution:
 *   - Browser (window defined): uses relative `/graphql` path
 *   - SSR (no window): requires `GRAPHQL_ENDPOINT` env var — throws if unset
 *
 * CSRF: Django Strawberry GraphQL views are expected to be CSRF-exempt for
 * token-authenticated requests. If CSRF enforcement is enabled, the consuming
 * application must pass the CSRF token via the `headers` parameter.
 */

/** Custom error class for GraphQL responses containing multiple errors. */
export class GraphQLError extends Error {
  public readonly errors: ReadonlyArray<{ message: string }>;

  constructor(errors: Array<{ message: string }>) {
    const messages = errors.map((e) => e.message).join("; ");
    super(messages);
    this.name = "GraphQLError";
    this.errors = errors;
  }
}

/** Custom error class for non-OK HTTP responses. */
export class HttpError extends Error {
  public readonly status: number;
  public readonly statusText: string;

  constructor(status: number, statusText: string) {
    super(`HTTP ${status}: ${statusText}`);
    this.name = "HttpError";
    this.status = status;
    this.statusText = statusText;
  }
}

export function fetcher<TData, TVariables>(
  query: string,
  variables?: TVariables,
  headers?: RequestInit["headers"],
): () => Promise<TData> {
  return async () => {
    let endpoint: string;

    if (typeof window !== "undefined") {
      endpoint = "/graphql";
    } else {
      const envEndpoint = process.env["GRAPHQL_ENDPOINT"];
      if (!envEndpoint) {
        throw new Error(
          "GRAPHQL_ENDPOINT environment variable is not set. " +
            "This is required for server-side rendering. " +
            "Set it to the full URL of the GraphQL backend " +
            '(e.g. "https://api.example.com/graphql").',
        );
      }
      endpoint = envEndpoint;
    }

    const res = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...headers },
      credentials: "include",
      body: JSON.stringify({ query, variables }),
    });

    if (!res.ok) {
      throw new HttpError(res.status, res.statusText);
    }

    const json = (await res.json()) as {
      data?: TData;
      errors?: Array<{ message: string }>;
    };

    if (json.errors && json.errors.length > 0) {
      throw new GraphQLError(json.errors);
    }

    return json.data as TData;
  };
}
