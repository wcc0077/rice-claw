import { create } from 'zustand'

/** Auth store for managing login state. */
interface AuthState {
  token: string | null
  agentId: string | null
  isLoggedIn: boolean
  login: (token: string, agentId: string) => void
  logout: () => void
  setToken: (token: string) => void
}

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  agentId: null,
  isLoggedIn: false,
  login: (token, agentId) => set({ token, agentId, isLoggedIn: true }),
  logout: () => set({ token: null, agentId: null, isLoggedIn: false }),
  setToken: (token) => set({ token }),
}))
