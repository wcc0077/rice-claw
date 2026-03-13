/** Utility functions for formatting and validation. */

import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'

dayjs.extend(relativeTime)

export const formatCurrency = (amount: number, currency: string = 'CNY') => {
  const symbols: Record<string, string> = {
    CNY: '¥',
    USD: '$',
    EUR: '€',
  }
  const symbol = symbols[currency] || currency
  return `${symbol}${amount.toLocaleString()}`
}

export const formatTime = (isoString: string) => {
  return dayjs(isoString).format('YYYY-MM-DD HH:mm')
}

export const formatDate = (isoString: string) => {
  return dayjs(isoString).format('YYYY-MM-DD')
}

export const timeAgo = (isoString: string) => {
  return dayjs(isoString).fromNow()
}

export const getStatusBadgeColor = (status: string) => {
  const colors: Record<string, string> = {
    OPEN: 'green',
    ACTIVE: 'blue',
    REVIEW: 'orange',
    CLOSED: 'gray',
    idle: 'green',
    busy: 'gold',
    offline: 'grey',
    PENDING: 'default',
    ACCEPTED: 'success',
    REJECTED: 'error',
  }
  return colors[status] || 'default'
}

export const generateId = (prefix: string = 'id') => {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

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