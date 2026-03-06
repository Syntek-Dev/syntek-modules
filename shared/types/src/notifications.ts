import type { ID, Timestamp } from './base.js'

export type NotificationChannel = 'email' | 'push' | 'sms' | 'in-app'

export interface Notification {
  id: ID
  type: string
  title: string
  body: string
  channel: NotificationChannel
  readAt?: Timestamp
}
