import { useEffect, useRef } from 'react'

/**
 * A custom hook that prevents duplicate async execution in React StrictMode.
 *
 * In React 18 StrictMode, useEffect runs twice in development with cleanup in between.
 * This hook prevents duplicate API calls by tracking dependency changes.
 *
 * How it works:
 * - On first effect run: execute callback, save deps
 * - On StrictMode second run: same deps, skip execution
 * - On actual deps change: different deps, execute callback
 *
 * @param callback - The async function to execute
 * @param deps - Dependency array (same as useEffect)
 *
 * @example
 * ```tsx
 * useAsyncEffect(async () => {
 *   const data = await fetchData();
 *   setState(data);
 * }, [dependency]);
 * ```
 */
export function useAsyncEffect(
  callback: () => Promise<void> | void,
  deps: React.DependencyList
) {
  const lastDeps = useRef<React.DependencyList | null>(null)
  const isExecuting = useRef(false)

  useEffect(() => {
    // Check if deps actually changed
    const depsChanged = !lastDeps.current || !shallowEqual(deps, lastDeps.current)

    if (!depsChanged) {
      // Same deps = StrictMode double execution, skip
      return
    }

    // New deps = actual change, execute
    lastDeps.current = deps

    // Also skip if already executing (for rapid dependency changes)
    if (isExecuting.current) {
      return
    }

    isExecuting.current = true
    Promise.resolve(callback()).finally(() => {
      isExecuting.current = false
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)
}

/**
 * Shallow equality check for dependency arrays
 */
function shallowEqual(a: React.DependencyList, b: React.DependencyList): boolean {
  if (a.length !== b.length) return false
  for (let i = 0; i < a.length; i++) {
    if (a[i] !== b[i]) return false
  }
  return true
}

/**
 * Hook to track if component is mounted (useful for async operations)
 */
export function useIsMounted() {
  const isMounted = useRef(true)

  useEffect(() => {
    return () => {
      isMounted.current = false
    }
  }, [])

  return () => isMounted.current
}