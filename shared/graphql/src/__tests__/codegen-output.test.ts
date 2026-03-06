/**
 * Integration tests — @syntek/graphql codegen output verification (US004).
 *
 * Checks that `pnpm codegen` has been run and produced `src/generated/graphql.ts`
 * with all required exports for auth and tenant operations.
 *
 * Red phase:  src/generated/graphql.ts does not exist → all assertions fail.
 * Green phase: run `pnpm --filter @syntek/graphql codegen` then re-run tests.
 */

import { existsSync, readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, it, expect } from 'vitest'

const ROOT = resolve(fileURLToPath(new URL('../..', import.meta.url)))
const GENERATED_FILE = resolve(ROOT, 'src/generated/graphql.ts')

// ---------------------------------------------------------------------------
// File existence
// ---------------------------------------------------------------------------

describe('Codegen output — file existence', () => {
  it('src/generated/graphql.ts exists (run: pnpm --filter @syntek/graphql codegen)', () => {
    expect(existsSync(GENERATED_FILE)).toBe(true)
  })
})

// ---------------------------------------------------------------------------
// Auth hook exports
// ---------------------------------------------------------------------------

describe('Codegen output — auth hooks', () => {
  it('exports useLoginMutation', () => {
    if (!existsSync(GENERATED_FILE)) {
      expect.fail('src/generated/graphql.ts not found — run: pnpm --filter @syntek/graphql codegen')
    }
    const content = readFileSync(GENERATED_FILE, 'utf8')
    expect(content).toMatch(/export\s+(?:function|const)\s+useLoginMutation/)
  })

  it('exports useCurrentUserQuery', () => {
    if (!existsSync(GENERATED_FILE)) {
      expect.fail('src/generated/graphql.ts not found — run: pnpm --filter @syntek/graphql codegen')
    }
    const content = readFileSync(GENERATED_FILE, 'utf8')
    expect(content).toMatch(/export\s+(?:function|const)\s+useCurrentUserQuery/)
  })

  it('exports LoginMutationVariables type', () => {
    if (!existsSync(GENERATED_FILE)) {
      expect.fail('src/generated/graphql.ts not found — run: pnpm --filter @syntek/graphql codegen')
    }
    const content = readFileSync(GENERATED_FILE, 'utf8')
    expect(content).toMatch(/export\s+type\s+LoginMutationVariables/)
  })

  it('exports LoginMutation type', () => {
    if (!existsSync(GENERATED_FILE)) {
      expect.fail('src/generated/graphql.ts not found — run: pnpm --filter @syntek/graphql codegen')
    }
    const content = readFileSync(GENERATED_FILE, 'utf8')
    expect(content).toMatch(/export\s+type\s+LoginMutation\b/)
  })

  it('exports CurrentUserQuery type', () => {
    if (!existsSync(GENERATED_FILE)) {
      expect.fail('src/generated/graphql.ts not found — run: pnpm --filter @syntek/graphql codegen')
    }
    const content = readFileSync(GENERATED_FILE, 'utf8')
    expect(content).toMatch(/export\s+type\s+CurrentUserQuery\b/)
  })

  it('LoginMutationVariables contains email field', () => {
    if (!existsSync(GENERATED_FILE)) {
      expect.fail('src/generated/graphql.ts not found — run: pnpm --filter @syntek/graphql codegen')
    }
    const content = readFileSync(GENERATED_FILE, 'utf8')
    expect(content).toMatch(/email\s*:\s*Scalars\[["']String["']\]|email\s*:\s*string/)
  })

  it('LoginMutationVariables contains password field', () => {
    if (!existsSync(GENERATED_FILE)) {
      expect.fail('src/generated/graphql.ts not found — run: pnpm --filter @syntek/graphql codegen')
    }
    const content = readFileSync(GENERATED_FILE, 'utf8')
    expect(content).toMatch(/password\s*:\s*Scalars\[["']String["']\]|password\s*:\s*string/)
  })
})

// ---------------------------------------------------------------------------
// Tenant hook exports
// ---------------------------------------------------------------------------

describe('Codegen output — tenant hooks', () => {
  it('exports useCurrentTenantQuery', () => {
    if (!existsSync(GENERATED_FILE)) {
      expect.fail('src/generated/graphql.ts not found — run: pnpm --filter @syntek/graphql codegen')
    }
    const content = readFileSync(GENERATED_FILE, 'utf8')
    expect(content).toMatch(/export\s+(?:function|const)\s+useCurrentTenantQuery/)
  })

  it('exports CurrentTenantQuery type', () => {
    if (!existsSync(GENERATED_FILE)) {
      expect.fail('src/generated/graphql.ts not found — run: pnpm --filter @syntek/graphql codegen')
    }
    const content = readFileSync(GENERATED_FILE, 'utf8')
    expect(content).toMatch(/export\s+type\s+CurrentTenantQuery\b/)
  })
})

// ---------------------------------------------------------------------------
// Module structure
// ---------------------------------------------------------------------------

describe('Codegen output — module structure', () => {
  it('generated file is a valid ES module (contains export keyword)', () => {
    if (!existsSync(GENERATED_FILE)) {
      expect.fail('src/generated/graphql.ts not found — run: pnpm --filter @syntek/graphql codegen')
    }
    const content = readFileSync(GENERATED_FILE, 'utf8')
    expect(content).toMatch(/export\s/)
  })

  it('generated file contains a GraphQL document (gql tag or DocumentNode)', () => {
    if (!existsSync(GENERATED_FILE)) {
      expect.fail('src/generated/graphql.ts not found — run: pnpm --filter @syntek/graphql codegen')
    }
    const content = readFileSync(GENERATED_FILE, 'utf8')
    expect(content).toMatch(/export const \w+Document\s*=/)
  })
})
