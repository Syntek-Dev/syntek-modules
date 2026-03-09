/**
 * Unit tests — @syntek/types shape and export verification (US002).
 *
 * Uses Vitest's expectTypeOf API so failures are caught at both compile-time
 * (tsc / vitest typecheck) and runtime.
 */

import { describe, it, expectTypeOf } from "vitest";

import type {
  ID,
  Timestamp,
  PaginatedResponse,
  ApiError,
  User,
  Session,
  Permission,
  Role,
  Tenant,
  TenantSettings,
  Notification,
  NotificationChannel,
} from "../index.js";

// ---------------------------------------------------------------------------
// Base types
// ---------------------------------------------------------------------------

describe("ID", () => {
  it("extends string", () => {
    expectTypeOf<ID>().toMatchTypeOf<string>();
  });

  it("is branded — not assignable from plain string without cast", () => {
    // A branded type should not equal plain string
    expectTypeOf<ID>().not.toEqualTypeOf<string>();
  });

  it("accepts a UUID string via cast", () => {
    const id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890" as ID;
    expectTypeOf(id).toMatchTypeOf<ID>();
  });
});

describe("Timestamp", () => {
  it("extends string", () => {
    expectTypeOf<Timestamp>().toMatchTypeOf<string>();
  });

  it("is branded — not assignable from plain string without cast", () => {
    expectTypeOf<Timestamp>().not.toEqualTypeOf<string>();
  });

  it("accepts an ISO 8601 date string via cast", () => {
    const ts = "2026-03-06T16:00:00.000Z" as Timestamp;
    expectTypeOf(ts).toMatchTypeOf<Timestamp>();
  });
});

describe("PaginatedResponse<T>", () => {
  it("data is T[]", () => {
    expectTypeOf<PaginatedResponse<User>["data"]>().toEqualTypeOf<User[]>();
  });

  it("total is number", () => {
    expectTypeOf<PaginatedResponse<User>["total"]>().toEqualTypeOf<number>();
  });

  it("page is number", () => {
    expectTypeOf<PaginatedResponse<User>["page"]>().toEqualTypeOf<number>();
  });

  it("pageSize is number", () => {
    expectTypeOf<PaginatedResponse<User>["pageSize"]>().toEqualTypeOf<number>();
  });

  it("is generic — works with any type parameter", () => {
    expectTypeOf<PaginatedResponse<Tenant>["data"]>().toEqualTypeOf<Tenant[]>();
  });
});

describe("ApiError", () => {
  it("code is string", () => {
    expectTypeOf<ApiError["code"]>().toEqualTypeOf<string>();
  });

  it("message is string", () => {
    expectTypeOf<ApiError["message"]>().toEqualTypeOf<string>();
  });

  it("details is optional Record<string, unknown>", () => {
    expectTypeOf<ApiError["details"]>().toEqualTypeOf<Record<string, unknown> | undefined>();
  });
});

// ---------------------------------------------------------------------------
// Auth types
// ---------------------------------------------------------------------------

describe("Permission", () => {
  it("name is string", () => {
    expectTypeOf<Permission["name"]>().toEqualTypeOf<string>();
  });

  it("scope is string", () => {
    expectTypeOf<Permission["scope"]>().toEqualTypeOf<string>();
  });
});

describe("Role", () => {
  it("id is ID", () => {
    expectTypeOf<Role["id"]>().toEqualTypeOf<ID>();
  });

  it("name is string", () => {
    expectTypeOf<Role["name"]>().toEqualTypeOf<string>();
  });

  it("permissions is Permission[]", () => {
    expectTypeOf<Role["permissions"]>().toEqualTypeOf<Permission[]>();
  });
});

describe("User", () => {
  it("id is ID", () => {
    expectTypeOf<User["id"]>().toEqualTypeOf<ID>();
  });

  it("email is string", () => {
    expectTypeOf<User["email"]>().toEqualTypeOf<string>();
  });

  it("displayName is string", () => {
    expectTypeOf<User["displayName"]>().toEqualTypeOf<string>();
  });

  it("isActive is boolean", () => {
    expectTypeOf<User["isActive"]>().toEqualTypeOf<boolean>();
  });

  it("roles is Role[]", () => {
    expectTypeOf<User["roles"]>().toEqualTypeOf<Role[]>();
  });

  it("createdAt is Timestamp", () => {
    expectTypeOf<User["createdAt"]>().toEqualTypeOf<Timestamp>();
  });

  it("updatedAt is Timestamp", () => {
    expectTypeOf<User["updatedAt"]>().toEqualTypeOf<Timestamp>();
  });
});

describe("Session", () => {
  it("id is ID", () => {
    expectTypeOf<Session["id"]>().toEqualTypeOf<ID>();
  });

  it("userId is ID", () => {
    expectTypeOf<Session["userId"]>().toEqualTypeOf<ID>();
  });

  it("tenantId is ID", () => {
    expectTypeOf<Session["tenantId"]>().toEqualTypeOf<ID>();
  });

  it("createdAt is Timestamp", () => {
    expectTypeOf<Session["createdAt"]>().toEqualTypeOf<Timestamp>();
  });

  it("expiresAt is Timestamp", () => {
    expectTypeOf<Session["expiresAt"]>().toEqualTypeOf<Timestamp>();
  });
});

// ---------------------------------------------------------------------------
// Tenant types
// ---------------------------------------------------------------------------

describe("Tenant", () => {
  it("id is ID", () => {
    expectTypeOf<Tenant["id"]>().toEqualTypeOf<ID>();
  });

  it("slug is string", () => {
    expectTypeOf<Tenant["slug"]>().toEqualTypeOf<string>();
  });

  it("name is string", () => {
    expectTypeOf<Tenant["name"]>().toEqualTypeOf<string>();
  });
});

describe("TenantSettings", () => {
  it("tenantId is ID", () => {
    expectTypeOf<TenantSettings["tenantId"]>().toEqualTypeOf<ID>();
  });

  it("settings is Record<string, unknown>", () => {
    expectTypeOf<TenantSettings["settings"]>().toEqualTypeOf<Record<string, unknown>>();
  });
});

// ---------------------------------------------------------------------------
// Notification types
// ---------------------------------------------------------------------------

describe("NotificationChannel", () => {
  it("is the union: email | push | sms | in-app", () => {
    expectTypeOf<NotificationChannel>().toEqualTypeOf<"email" | "push" | "sms" | "in-app">();
  });

  it("does not accept arbitrary strings", () => {
    // @ts-expect-error — 'webhook' is not a valid NotificationChannel
    const invalid: NotificationChannel = "webhook";
    void invalid;
  });
});

describe("Notification", () => {
  it("id is ID", () => {
    expectTypeOf<Notification["id"]>().toEqualTypeOf<ID>();
  });

  it("userId is ID", () => {
    expectTypeOf<Notification["userId"]>().toEqualTypeOf<ID>();
  });

  it("type is string", () => {
    expectTypeOf<Notification["type"]>().toEqualTypeOf<string>();
  });

  it("title is string", () => {
    expectTypeOf<Notification["title"]>().toEqualTypeOf<string>();
  });

  it("body is string", () => {
    expectTypeOf<Notification["body"]>().toEqualTypeOf<string>();
  });

  it("channel is NotificationChannel", () => {
    expectTypeOf<Notification["channel"]>().toEqualTypeOf<NotificationChannel>();
  });

  it("createdAt is Timestamp", () => {
    expectTypeOf<Notification["createdAt"]>().toEqualTypeOf<Timestamp>();
  });

  it("readAt is optional Timestamp", () => {
    expectTypeOf<Notification["readAt"]>().toEqualTypeOf<Timestamp | undefined>();
  });
});
