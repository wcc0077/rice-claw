/**
 * Test fixtures for matching test page
 * These values are used for manual testing only
 */

export const TEST_FIXTURES = {
  DEFAULT_WORKER_ID: import.meta.env.VITE_TEST_WORKER_ID || 'test_worker_001',
  DEFAULT_EMPLOYER_ID: import.meta.env.VITE_TEST_EMPLOYER_ID || 'test_employer_001',
  DEFAULT_PROPOSAL: '我可以完成这个任务',
  DEFAULT_QUOTE: {
    amount: 1000,
    currency: 'CNY',
    delivery_days: 7,
  },
} as const
