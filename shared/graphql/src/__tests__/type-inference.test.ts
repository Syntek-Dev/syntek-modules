/**
 * Unit tests — @syntek/graphql type inference verification (US004).
 *
 * Uses Vitest's expectTypeOf API to assert that generated operation types have
 * the exact shapes required by the acceptance criteria.
 *
 * Red phase:  The stub types in src/index.ts are `Record<string, unknown>` —
 *             every toEqualTypeOf assertion below will fail with tsc --noEmit,
 *             surfacing as type errors when running `pnpm test`.
 *
 * Green phase: After `pnpm codegen` + updating src/index.ts to:
 *                export * from './generated/graphql.js'
 *              all assertions pass.
 */

import { describe, it, expectTypeOf } from "vitest";

import type {
  LoginMutation,
  LoginMutationVariables,
  CurrentUserQuery,
  CurrentUserQueryVariables,
  CurrentTenantQuery,
  CurrentTenantQueryVariables,
} from "../index.js";

// ---------------------------------------------------------------------------
// Login mutation — variables
// ---------------------------------------------------------------------------

describe("LoginMutationVariables", () => {
  it("has email as a required string", () => {
    expectTypeOf<LoginMutationVariables["email"]>().toEqualTypeOf<string>();
  });

  it("has password as a required string", () => {
    expectTypeOf<LoginMutationVariables["password"]>().toEqualTypeOf<string>();
  });

  it("does not allow extra arbitrary keys to be typed as string", () => {
    // Record<string, unknown> would pass arbitrary key access — the generated type must not.
    // This assertion checks the generated type is a closed object, not an index signature.
    expectTypeOf<LoginMutationVariables>().not.toEqualTypeOf<Record<string, unknown>>();
  });
});

// ---------------------------------------------------------------------------
// Login mutation — result
// ---------------------------------------------------------------------------

describe("LoginMutation", () => {
  it("has a login field", () => {
    expectTypeOf<LoginMutation>().toHaveProperty("login");
  });

  it("login.token is a string", () => {
    expectTypeOf<NonNullable<LoginMutation["login"]>["token"]>().toEqualTypeOf<string>();
  });

  it("login.user.id is a string", () => {
    expectTypeOf<
      NonNullable<NonNullable<LoginMutation["login"]>["user"]>["id"]
    >().toEqualTypeOf<string>();
  });

  it("login.user.email is a string", () => {
    expectTypeOf<
      NonNullable<NonNullable<LoginMutation["login"]>["user"]>["email"]
    >().toEqualTypeOf<string>();
  });
});

// ---------------------------------------------------------------------------
// CurrentUser query
// ---------------------------------------------------------------------------

describe("CurrentUserQueryVariables", () => {
  it("is an empty object type (no variables required)", () => {
    expectTypeOf<CurrentUserQueryVariables>().toEqualTypeOf<Record<string, never>>();
  });
});

describe("CurrentUserQuery", () => {
  it("has a me field", () => {
    expectTypeOf<CurrentUserQuery>().toHaveProperty("me");
  });

  it("me.id is a string", () => {
    expectTypeOf<NonNullable<CurrentUserQuery["me"]>["id"]>().toEqualTypeOf<string>();
  });

  it("me.email is a string", () => {
    expectTypeOf<NonNullable<CurrentUserQuery["me"]>["email"]>().toEqualTypeOf<string>();
  });

  it("me.createdAt is a string (ISO timestamp)", () => {
    expectTypeOf<NonNullable<CurrentUserQuery["me"]>["createdAt"]>().toEqualTypeOf<string>();
  });
});

// ---------------------------------------------------------------------------
// CurrentTenant query
// ---------------------------------------------------------------------------

describe("CurrentTenantQueryVariables", () => {
  it("is an empty object type (no variables required)", () => {
    expectTypeOf<CurrentTenantQueryVariables>().toEqualTypeOf<Record<string, never>>();
  });
});

describe("CurrentTenantQuery", () => {
  it("has a currentTenant field", () => {
    expectTypeOf<CurrentTenantQuery>().toHaveProperty("currentTenant");
  });

  it("currentTenant.id is a string", () => {
    expectTypeOf<NonNullable<CurrentTenantQuery["currentTenant"]>["id"]>().toEqualTypeOf<string>();
  });

  it("currentTenant.slug is a string", () => {
    expectTypeOf<
      NonNullable<CurrentTenantQuery["currentTenant"]>["slug"]
    >().toEqualTypeOf<string>();
  });

  it("currentTenant.name is a string", () => {
    expectTypeOf<
      NonNullable<CurrentTenantQuery["currentTenant"]>["name"]
    >().toEqualTypeOf<string>();
  });
});
