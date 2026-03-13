/** Bid types and interfaces. */

export interface Quote {
  amount: number
  currency: string
  delivery_days: number
}

export interface Bid {
  bid_id: string
  job_id: string
  worker_id: string
  worker_name?: string
  worker_rating?: number
  proposal: string
  quote: Quote
  portfolio_links?: string[]
  is_hired: boolean
  status: 'PENDING' | 'ACCEPTED' | 'REJECTED'
  submitted_at: string
}

export interface BidFormValues {
  worker_id: string
  proposal: string
  quote: Quote
  portfolio_links?: string[]
}

export interface BidStats {
  id: string
  worker: string
  rating: number
  proposal: string
  quote: string
  hired: boolean
}
