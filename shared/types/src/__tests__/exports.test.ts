/**
 * Unit tests — @syntek/types shape and export verification (US002).
 *
 * Uses Vitest's expectTypeOf API so failures are caught at both compile-time
 * (tsc / vitest typecheck) and runtime.
 *
 * Red phase: stubs define incomplete/permissive types so most assertions below
 * will fail until the real type definitions are written.
 */

import { describe, it, expectTypeOf } from 'vitest'
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
} from '../index.js'

// ---------------------------------------------------------------------------
// Base types
// ---------------------------------------------------------------------------

describe('ID', () => {
  it('is a string type', () => {
    expectTypeOf<ID>().toEqualTypeOf<string>()
  })

  it('accepts a UUID string', () => {
    const id: ID = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'
    expectTypeOf(id).toEqualTypeOf<ID>()
  })
})

describe('Timestamp', () => {
  it('is a string type', () => {
    expectTypeOf<Timestamp>().toEqualTypeOf<string>()
  })

  it('accepts an ISO 8601 date string', () => {
    const ts: Timestamp = '2026-03-06T16:00:00.000Z'
    expectTypeOf(ts).toEqualTypeOf<Timestamp>()
  })
})

describe('PaginatedResponse<T>', () => {
  it('data is T[]', () => {
    expectTypeOf<PaginatedResponse<User>['data']>().toEqualTypeOf<User[]>()
  })

  it('total is number', () => {
    expectTypeOf<PaginatedResponse<User>['total']>().toEqualTypeOf<number>()
  })

  it('page is number', () => {
    expectTypeOf<PaginatedResponse<User>['page']>().toEqualTypeOf<number>()
  })

  it('pageSize is number', () => {
    expectTypeOf<PaginatedResponse<User>['pageSize']>().toEqualTypeOf<number>()
  })

  it('is generic — works with any type parameter', () => {
    expectTypeOf<PaginatedResponse<Tenant>['data']>().toEqualTypeOf<Tenant[]>()
  })
})

describe('ApiError', () => {
  it('code is string', () => {
    expectTypeOf<ApiError['code']>().toEqualTypeOf<string>()
  })

  it('message is string', () => {
    expectTypeOf<ApiError['message']>().toEqualTypeOf<string>()
  })

  it('details is optional Record<string, unknown>', () => {
    expectTypeOf<ApiError['details']>().toEqualTypeOf<Record<string, unknown> | undefined>()
  })
})

// ---------------------------------------------------------------------------
// Auth types
// ---------------------------------------------------------------------------

describe('Permission', () => {
  it('name is string', () => {
    expectTypeOf<Permission['name']>().toEqualTypeOf<string>()
  })

  it('scope is string', () => {
    expectTypeOf<Permission['scope']>().toEqualTypeOf<string>()
  })
})

describe('Role', () => {
  it('id is ID', () => {
    expectTypeOf<Role['id']>().toEqualTypeOf<ID>()
  })

  it('name is string', () => {
    expectTypeOf<Role['name']>().toEqualTypeOf<string>()
  })

  it('permissions is Permission[]', () => {
    expectTypeOf<Role['permissions']>().toEqualTypeOf<Permission[]>()
  })
})

describe('User', () => {
  it('id is ID', () => {
    expectTypeOf<User['id']>().toEqualTypeOf<ID>()
  })

  it('email is string', () => {
    expectTypeOf<User['email']>().toEqualTypeOf<string>()
  })

  it('roles is Role[]', () => {
    expectTypeOf<User['roles']>().toEqualTypeOf<Role[]>()
  })

  it('createdAt is Timestamp', () => {
    expectTypeOf<User['createdAt']>().toEqualTypeOf<Timestamp>()
  })
})

describe('Session', () => {
  it('id is ID', () => {
    expectTypeOf<Session['id']>().toEqualTypeOf<ID>()
  })

  it('userId is ID', () => {
    expectTypeOf<Session['userId']>().toEqualTypeOf<ID>()
  })

  it('expiresAt is Timestamp', () => {
    expectTypeOf<Session['expiresAt']>().toEqualTypeOf<Timestamp>()
  })
})

// ---------------------------------------------------------------------------
// Tenant types
// ---------------------------------------------------------------------------

describe('Tenant', () => {
  it('id is ID', () => {
    expectTypeOf<Tenant['id']>().toEqualTypeOf<ID>()
  })

  it('slug is string', () => {
    expectTypeOf<Tenant['slug']>().toEqualTypeOf<string>()
  })

  it('name is string', () => {
    expectTypeOf<Tenant['name']>().toEqualTypeOf<string>()
  })
})

describe('TenantSettings', () => {
  it('tenantId is ID', () => {
    expectTypeOf<TenantSettings['tenantId']>().toEqualTypeOf<ID>()
  })

  it('settings is Record<string, unknown>', () => {
    expectTypeOf<TenantSettings['settings']>().toEqualTypeOf<Record<string, unknown>>()
  })
})

// ---------------------------------------------------------------------------
// Notification types
// ---------------------------------------------------------------------------

describe('NotificationChannel', () => {
  it('is the union: email | push | sms | in-app', () => {
    expectTypeOf<NotificationChannel>().toEqualTypeOf<'email' | 'push' | 'sms' | 'in-app'>()
  })

  it('does not accept arbitrary strings', () => {
    // @ts-expect-error — 'webhook' is not a valid NotificationChannel
    const invalid: NotificationChannel = 'webhook'
    void invalid
  })
})

describe('Notification', () => {
  it('id is ID', () => {
    expectTypeOf<Notification['id']>().toEqualTypeOf<ID>()
  })

  it('type is string', () => {
    expectTypeOf<Notification['type']>().toEqualTypeOf<string>()
  })

  it('title is string', () => {
    expectTypeOf<Notification['title']>().toEqualTypeOf<string>()
  })

  it('body is string', () => {
    expectTypeOf<Notification['body']>().toEqualTypeOf<string>()
  })

  it('channel is NotificationChannel', () => {
    expectTypeOf<Notification['channel']>().toEqualTypeOf<NotificationChannel>()
  })

  it('readAt is optional Timestamp', () => {
    expectTypeOf<Notification['readAt']>().toEqualTypeOf<Timestamp | undefined>()
  })
})
