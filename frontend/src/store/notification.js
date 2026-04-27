import { defineStore } from "pinia";

export const useNotificationStore = defineStore("notification", {
  state: () => ({
    messages: []
  }),
  getters: {
    unreadCount: (state) => state.messages.filter((item) => !item.read).length,
    recentMessages: (state) => state.messages.slice(0, 10)
  },
  actions: {
    addMessage(message) {
      const item = {
        id: message.id || `${Date.now()}-${Math.random().toString(16).slice(2)}`,
        title: message.title || "系统通知",
        content: message.content || "",
        level: message.level || "info",
        role: message.role || "",
        createdAt: message.createdAt || message.sent_at || new Date().toISOString(),
        read: false
      };
      this.messages.unshift(item);
      if (this.messages.length > 100) {
        this.messages = this.messages.slice(0, 100);
      }
    },
    markAllRead() {
      this.messages = this.messages.map((item) => ({ ...item, read: true }));
    }
  }
});

