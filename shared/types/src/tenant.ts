import type { ID } from './base.js'

export interface Tenant {
  id: ID
  slug: string
  name: string
}

export interface TenantSettings {
  tenantId: ID
  settings: Record<string, unknown>
}
