/**
 * User type definitions
 *
 * Types for user profiles, roles, and account status.
 */

export type UserRole = 'user' | 'admin' | 'moderator' | 'guest';

export type AccountStatus = 'active' | 'suspended' | 'pending_verification' | 'deleted';

export interface User {
  id: string;
  email: string;
  username: string;
  emailVerified: boolean;
  phoneVerified: boolean;
  role: UserRole;
  accountStatus: AccountStatus;
  createdAt: string;
  updatedAt: string;
}

export interface UserProfile extends User {
  firstName: string;
  lastName: string;
  phone?: string;
  avatar?: string;
  bio?: string;
  language: string;
  timezone: string;
}

export interface UpdateProfileInput {
  firstName?: string;
  lastName?: string;
  phone?: string;
  avatar?: string;
  bio?: string;
  language?: string;
  timezone?: string;
}
