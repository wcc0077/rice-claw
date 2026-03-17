import { create } from 'zustand'

/** Auth store for managing login state. */
interface AuthState {
  token: string | null
  userId: string | null
  agentId: string | null
  isLoggedIn: () => boolean
  login: (token: string, userId: string, agentId?: string) => void
  logout: () => void
  setToken: (token: string) => void
}

const clearAuthStorage = () => {
  localStorage.removeItem('auth_token')
  localStorage.removeItem('user_id')
  localStorage.removeItem('agent_id')
  localStorage.removeItem('user_info')
}

export const useAuthStore = create<AuthState>((set, get) => ({
  token: localStorage.getItem('auth_token'),
  userId: localStorage.getItem('user_id'),
  agentId: localStorage.getItem('agent_id'),
  isLoggedIn: () => get().token !== null,
  login: (token, userId, agentId) => {
    localStorage.setItem('auth_token', token)
    localStorage.setItem('user_id', userId)
    if (agentId) {
      localStorage.setItem('agent_id', agentId)
    }
    set({ token, userId, agentId })
  },
  logout: () => {
    clearAuthStorage()
    set({ token: null, userId: null, agentId: null })
  },
  setToken: (token) => {
    localStorage.setItem('auth_token', token)
    set({ token })
  },
}))
