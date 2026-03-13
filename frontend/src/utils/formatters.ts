/** Utility functions for formatting and validation. */

import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'

dayjs.extend(relativeTime)

/**
 * Format currency with proper symbol and locale
 */
export const formatCurrency = (amount: number, currency: string = 'CNY') => {
  const symbols: Record<string, string> = {
    CNY: '¥',
    USD: '$',
    EUR: '€',
    JPY: '¥',
  }
  const symbol = symbols[currency] || currency
  return `${symbol}${amount.toLocaleString('zh-CN')}`
}

/**
 * Format timestamp to readable time
 */
export const formatTime = (isoString: string) => {
  return dayjs(isoString).format('YYYY-MM-DD HH:mm')
}

/**
 * Format date only
 */
export const formatDate = (isoString: string) => {
  return dayjs(isoString).format('YYYY-MM-DD')
}

/**
 * Get relative time (e.g., "2 hours ago")
 */
export const timeAgo = (isoString: string) => {
  return dayjs(isoString).fromNow()
}

/**
 * Status badge color mapping for Ant Design
 * @deprecated Use statusConfig objects for trust-focused badges
 */
export const getStatusBadgeColor = (status: string) => {
  const colors: Record<string, string> = {
    // Job statuses
    OPEN: 'green',
    ACTIVE: 'blue',
    REVIEW: 'orange',
    CLOSED: 'gray',
    // Agent statuses
    idle: 'green',
    busy: 'gold',
    offline: 'grey',
    // Bid statuses
    PENDING: 'default',
    ACCEPTED: 'success',
    REJECTED: 'error',
  }
  return colors[status] || 'default'
}

/**
 * Generate unique ID with prefix
 */
export const generateId = (prefix: string = 'id') => {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

/**
 * Debounce function for performance
 */
export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: ReturnType<typeof setTimeout> | null = null
  return (...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout)
    timeout = setTimeout(() => func(...args), wait)
  }
}

/**
 * Throttle function for performance
 */
export const throttle = <T extends (...args: any[]) => any>(
  func: T,
  limit: number
): ((...args: Parameters<T>) => void) => {
  let inThrottle = false
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args)
      inThrottle = true
      setTimeout(() => (inThrottle = false), limit)
    }
  }
}

/**
 * Format file size for display
 */
export const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`
}

/**
 * Truncate text with ellipsis
 */
export const truncateText = (text: string, maxLength: number) => {
  if (text.length <= maxLength) return text
  return `${text.slice(0, maxLength)}...`
}

/**
 * Format percentage with sign
 */
export const formatPercentage = (value: number, decimals: number = 1) => {
  const sign = value >= 0 ? '+' : ''
  return `${sign}${value.toFixed(decimals)}%`
}

/**
 * Get initials from name
 */
export const getInitials = (name: string) => {
  return name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

/**
 * Validate email format
 */
export const isValidEmail = (email: string) => {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return re.test(email)
}

/**
 * Calculate time remaining until deadline
 * Returns formatted string with trust indicators
 */
export const getTimeRemaining = (deadline: string): { text: string; isUrgent: boolean; isExpired: boolean } => {
  const now = new Date()
  const end = new Date(deadline)
  const diffMs = end.getTime() - now.getTime()

  if (diffMs < 0) {
    return { text: '已过期', isUrgent: false, isExpired: true }
  }

  const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24))
  const diffHours = Math.ceil(diffMs / (1000 * 60 * 60))

  if (diffDays <= 1) {
    return { text: `${diffHours} 小时`, isUrgent: true, isExpired: false }
  }

  return { text: `${diffDays} 天`, isUrgent: diffDays <= 3, isExpired: false }
}

/**
 * Get rating color based on score
 * Trust indicator for quality assessment
 */
export const getRatingColor = (rating: number): { text: string; bg: string; border: string } => {
  if (rating >= 4.5) {
    return {
      text: 'text-amber-400',
      bg: 'bg-amber-500/10',
      border: 'border-amber-500/20',
    }
  }
  if (rating >= 4.0) {
    return {
      text: 'text-emerald-400',
      bg: 'bg-emerald-500/10',
      border: 'border-emerald-500/20',
    }
  }
  if (rating >= 3.0) {
    return {
      text: 'text-cyan-400',
      bg: 'bg-cyan-500/10',
      border: 'border-cyan-500/20',
    }
  }
  return {
    text: 'text-slate-400',
    bg: 'bg-slate-500/10',
    border: 'border-slate-500/20',
  }
}
