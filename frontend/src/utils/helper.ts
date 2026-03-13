import clsx, { ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

/** Merge Tailwind classes handling conflicts. */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/** Generate random placeholder image URL. */
export function getAvatarUrl(agentId: string, size: number = 40) {
  return `https://api.dicebear.com/7.x/avataaars/svg?seed=${agentId}&backgroundColor=b6e3f7&size=${size}`
}

/** Check if array contains value. */
export function hasValue<T>(arr: T[] | null | undefined): arr is T[] {
  return Array.isArray(arr) && arr.length > 0
}

/** Format bytes to human readable size. */
export function formatBytes(bytes: number, decimals = 2) {
  if (bytes === 0) return '0 B'
  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`
}
