const DEFAULT_ENDPOINT = "http://localhost:8000/graphql";

export function fetcher<TData, TVariables>(
  query: string,
  variables?: TVariables,
  headers?: RequestInit["headers"],
): () => Promise<TData> {
  return async () => {
    const endpoint =
      typeof window !== "undefined"
        ? "/graphql"
        : (process.env["GRAPHQL_ENDPOINT"] ?? DEFAULT_ENDPOINT);

    const res = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...headers },
      body: JSON.stringify({ query, variables }),
    });

    const json = (await res.json()) as {
      data?: TData;
      errors?: Array<{ message: string }>;
    };

    if (json.errors?.[0]) throw new Error(json.errors[0].message);
    return json.data as TData;
  };
}
