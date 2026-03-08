import type { ID, Timestamp } from "./base.js";

export interface Permission {
  name: string;
  scope: string;
}

export interface Role {
  id: ID;
  name: string;
  permissions: Permission[];
}

export interface User {
  id: ID;
  email: string;
  displayName: string;
  isActive: boolean;
  roles: Role[];
  createdAt: Timestamp;
  updatedAt: Timestamp;
}

export interface Session {
  id: ID;
  userId: ID;
  tenantId: ID;
  createdAt: Timestamp;
  expiresAt: Timestamp;
}
