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
  roles: Role[];
  createdAt: Timestamp;
}

export interface Session {
  id: ID;
  userId: ID;
  expiresAt: Timestamp;
}
