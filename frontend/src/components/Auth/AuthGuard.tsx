import { Navigate, useLocation } from 'react-router-dom'
import { memo } from 'react'

/**
 * Check if user is authenticated
 */
const isAuthenticated = (): boolean => {
  return !!localStorage.getItem('auth_token')
}

/**
 * AuthGuard - Protects routes from unauthenticated access
 *
 * If user is not authenticated, redirects to /login with the
 * current path stored in the redirect query parameter.
 */
const AuthGuard = memo(({ children }: { children: React.ReactNode }) => {
  const location = useLocation()

  if (!isAuthenticated()) {
    // Redirect to login with the current path as redirect param
    const redirectPath = encodeURIComponent(location.pathname + location.search)
    return <Navigate to={`/login?redirect=${redirectPath}`} replace />
  }

  return <>{children}</>
})

AuthGuard.displayName = 'AuthGuard'

export default AuthGuard