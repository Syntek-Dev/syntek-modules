/**
 * Unit tests — @syntek/graphql fetcher (US004).
 *
 * Verifies endpoint selection, HTTP error handling, GraphQL error aggregation,
 * and credentials configuration.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// We need to test the fetcher module, which reads process.env and checks
// typeof window. We use dynamic imports and vi.stubGlobal to control these.

describe("fetcher", () => {
  const originalWindow = globalThis.window;
  const originalEnv = { ...process.env };

  beforeEach(() => {
    vi.restoreAllMocks();
    process.env = { ...originalEnv };
  });

  afterEach(() => {
    // Restore window
    if (originalWindow !== undefined) {
      globalThis.window = originalWindow;
    }
    process.env = originalEnv;
  });

  describe("endpoint selection", () => {
    it("throws when GRAPHQL_ENDPOINT is not set in SSR context", async () => {
      // Remove window to simulate SSR
      // @ts-expect-error — deliberately removing window for SSR simulation
      delete globalThis.window;
      delete process.env["GRAPHQL_ENDPOINT"];

      // Dynamic import to get fresh module state
      const { fetcher } = await import("../lib/fetcher.js");
      const fn = fetcher("query { me { id } }");

      await expect(fn()).rejects.toThrow("GRAPHQL_ENDPOINT");
    });

    it("uses GRAPHQL_ENDPOINT env var in SSR context when set", async () => {
      // @ts-expect-error — deliberately removing window for SSR simulation
      delete globalThis.window;
      process.env["GRAPHQL_ENDPOINT"] = "https://api.test.com/graphql";

      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ data: { me: { id: "1" } } }),
      });
      vi.stubGlobal("fetch", mockFetch);

      const { fetcher } = await import("../lib/fetcher.js");
      const fn = fetcher("query { me { id } }");
      await fn();

      expect(mockFetch).toHaveBeenCalledWith("https://api.test.com/graphql", expect.any(Object));
    });
  });

  describe("HTTP error handling", () => {
    it("throws HttpError on non-OK response", async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        statusText: "Internal Server Error",
      });
      vi.stubGlobal("fetch", mockFetch);

      // Simulate browser context
      vi.stubGlobal("window", {});

      const { fetcher, HttpError } = await import("../lib/fetcher.js");
      const fn = fetcher("query { me { id } }");

      await expect(fn()).rejects.toBeInstanceOf(HttpError);
      await expect(fn()).rejects.toThrow("HTTP 500");
    });

    it("throws HttpError on 401 Unauthorized", async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 401,
        statusText: "Unauthorized",
      });
      vi.stubGlobal("fetch", mockFetch);
      vi.stubGlobal("window", {});

      const { fetcher } = await import("../lib/fetcher.js");
      const fn = fetcher("query { me { id } }");

      await expect(fn()).rejects.toThrow("HTTP 401");
    });

    it("throws HttpError on 403 Forbidden", async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 403,
        statusText: "Forbidden",
      });
      vi.stubGlobal("fetch", mockFetch);
      vi.stubGlobal("window", {});

      const { fetcher } = await import("../lib/fetcher.js");
      const fn = fetcher("query { me { id } }");

      await expect(fn()).rejects.toThrow("HTTP 403");
    });
  });

  describe("GraphQL error handling", () => {
    it("throws GraphQLError with all error messages when multiple errors returned", async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () =>
          Promise.resolve({
            data: null,
            errors: [
              { message: "Field 'name' is required" },
              { message: "Field 'email' must be valid" },
            ],
          }),
      });
      vi.stubGlobal("fetch", mockFetch);
      vi.stubGlobal("window", {});

      const { fetcher, GraphQLError } = await import("../lib/fetcher.js");
      const fn = fetcher("mutation { createUser { id } }");

      try {
        await fn();
        expect.fail("Expected GraphQLError to be thrown");
      } catch (error) {
        expect(error).toBeInstanceOf(GraphQLError);
        const gqlError = error as InstanceType<typeof GraphQLError>;
        expect(gqlError.errors).toHaveLength(2);
        expect(gqlError.message).toContain("Field 'name' is required");
        expect(gqlError.message).toContain("Field 'email' must be valid");
      }
    });

    it("returns data when no errors present", async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () =>
          Promise.resolve({
            data: { me: { id: "123", email: "test@example.com" } },
          }),
      });
      vi.stubGlobal("fetch", mockFetch);
      vi.stubGlobal("window", {});

      const { fetcher } = await import("../lib/fetcher.js");
      const fn = fetcher<{ me: { id: string; email: string } }, never>("query { me { id email } }");
      const result = await fn();

      expect(result.me.id).toBe("123");
      expect(result.me.email).toBe("test@example.com");
    });
  });

  describe("credentials", () => {
    it("sends credentials: include for cross-origin cookie support", async () => {
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ data: { me: null } }),
      });
      vi.stubGlobal("fetch", mockFetch);
      vi.stubGlobal("window", {});

      const { fetcher } = await import("../lib/fetcher.js");
      const fn = fetcher("query { me { id } }");
      await fn();

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({ credentials: "include" }),
      );
    });
  });
});
