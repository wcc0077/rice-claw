import { create } from 'zustand'

/** Message store for managing conversations and unread counts. */
interface MessageState {
  conversations: any[]
  currentChat: any | null
  unreadCounts: Record<string, number>
  addConversation: (conv: any) => void
  updateUnreadCount: (jobId: string, count: number) => void
  setCurrentChat: (chat: any | null) => void
  markAsRead: (jobId: string) => void
}

export const useMessageStore = create<MessageState>((set) => ({
  conversations: [],
  currentChat: null,
  unreadCounts: {},
  addConversation: (conv) =>
    set((state) => ({
      conversations: [conv, ...state.conversations],
    })),
  updateUnreadCount: (jobId, count) =>
    set((state) => ({
      unreadCounts: { ...state.unreadCounts, [jobId]: count },
    })),
  setCurrentChat: (chat) => set({ currentChat: chat }),
  markAsRead: (jobId) =>
    set((state) => ({
      unreadCounts: { ...state.unreadCounts, [jobId]: 0 },
    })),
}))
