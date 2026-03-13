import { create } from 'zustand'

/** Auth store for managing login state. */
interface AuthState {
  token: string | null
  agentId: string | null
  isLoggedIn: () => boolean
  login: (token: string, agentId: string) => void
  logout: () => void
  setToken: (token: string) => void
}

export const useAuthStore = create<AuthState>((set, get) => ({
  token: null,
  agentId: null,
  isLoggedIn: () => get().token !== null,
  login: (token, agentId) => set({ token, agentId }),
  logout: () => set({ token: null, agentId: null }),
  setToken: (token) => set({ token }),
}))
