/**
 * Integration tests — @syntek/types build output verification (US002).
 *
 * Checks that `tsc --project tsconfig.build.json` has been run and produced
 * declaration files (.d.ts) for every source module.
 *
 * Red phase: dist/ does not exist → all assertions fail.
 * To reach green phase, run: pnpm --filter @syntek/types build
 */

import { existsSync, readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, it, expect } from 'vitest'

const ROOT = resolve(fileURLToPath(new URL('../..', import.meta.url)))
const DIST = resolve(ROOT, 'dist')

describe('Build output — declaration files', () => {
  it('dist/ directory exists (run: pnpm --filter @syntek/types build)', () => {
    expect(existsSync(DIST)).toBe(true)
  })

  it('index.d.ts is present', () => {
    expect(existsSync(resolve(DIST, 'index.d.ts'))).toBe(true)
  })

  it('base.d.ts is present', () => {
    expect(existsSync(resolve(DIST, 'base.d.ts'))).toBe(true)
  })

  it('auth.d.ts is present', () => {
    expect(existsSync(resolve(DIST, 'auth.d.ts'))).toBe(true)
  })

  it('tenant.d.ts is present', () => {
    expect(existsSync(resolve(DIST, 'tenant.d.ts'))).toBe(true)
  })

  it('notifications.d.ts is present', () => {
    expect(existsSync(resolve(DIST, 'notifications.d.ts'))).toBe(true)
  })

  it('index.d.ts.map declaration sourcemap is present', () => {
    expect(existsSync(resolve(DIST, 'index.d.ts.map'))).toBe(true)
  })
})

describe('Build output — JS modules', () => {
  it('index.js is present', () => {
    expect(existsSync(resolve(DIST, 'index.js'))).toBe(true)
  })

  it('index.js is a valid ES module (contains export keyword)', () => {
    const indexPath = resolve(DIST, 'index.js')
    if (!existsSync(indexPath)) {
      expect.fail('index.js not found — run: pnpm --filter @syntek/types build')
    }
    const content = readFileSync(indexPath, 'utf8')
    expect(content).toMatch(/export\s/)
  })
})
