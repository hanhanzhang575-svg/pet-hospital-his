import { computed, onBeforeUnmount, ref } from "vue";
import { ElNotification } from "element-plus";
import { buildWsUrl, getSessionUserId } from "../api/ws";
import { useNotificationStore } from "../store/notification";

const notifications = ref([]);
const warningBanners = ref([]);
const unread = ref(0);
const connected = ref(false);
const connectionState = ref("disconnected");

let socket = null;
let reconnectTimer = null;
let heartbeatTimer = null;
let manualClosed = false;
let reconnectAttempts = 0;

const HEARTBEAT_MS = 30000;
const MAX_RECONNECT_DELAY_MS = 30000;

async function resolveUserId() {
  let userId = window.sessionStorage.getItem("user_id");
  if (userId) return String(userId);

  // 兜底1：从 user_profile 里取 id
  try {
    const rawProfile = window.sessionStorage.getItem("user_profile");
    if (rawProfile) {
      const profile = JSON.parse(rawProfile);
      if (profile?.id !== undefined && profile?.id !== null) {
        userId = String(profile.id);
        window.sessionStorage.setItem("user_id", userId);
        return userId;
      }
    }
  } catch {
    // ignore
  }

  // 兜底2：从 /auth/me 拉取当前用户
  const token = window.sessionStorage.getItem("access_token");
  if (token) {
    try {
      const res = await fetch("/api/v1/auth/me", {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const payload = await res.json();
        const id = payload?.data?.id;
        if (id !== undefined && id !== null) {
          userId = String(id);
          window.sessionStorage.setItem("user_id", userId);
          return userId;
        }
      }
    } catch {
      // ignore
    }
  }
  return "";
}

function pushMessage(message) {
  const notificationStore = useNotificationStore();
  const item = {
    id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
    title: message.title || "系统通知",
    content: message.content || "",
    level: message.level || "info",
    role: message.role || "",
    createdAt: message.sent_at || new Date().toISOString()
  };
  notifications.value.unshift(item);
  notificationStore.addMessage(item);
  unread.value += 1;

  if (item.level === "warning") {
    ElNotification({
      title: item.title,
      message: item.content,
      type: "warning",
      duration: 5000,
      position: "bottom-right"
    });
  }
  if (item.level === "error") {
    warningBanners.value.unshift(item);
  }
}

function clearUnread() {
  unread.value = 0;
}

function closeBanner(id) {
  warningBanners.value = warningBanners.value.filter((x) => x.id !== id);
}

function clearHeartbeat() {
  if (heartbeatTimer) {
    window.clearInterval(heartbeatTimer);
    heartbeatTimer = null;
  }
}

function scheduleReconnect() {
  if (manualClosed || reconnectTimer) return;
  const delay = Math.min(1000 * (2 ** reconnectAttempts), MAX_RECONNECT_DELAY_MS);
  reconnectAttempts += 1;
  reconnectTimer = window.setTimeout(() => {
    reconnectTimer = null;
    connect();
  }, delay);
}

function startHeartbeat() {
  clearHeartbeat();
  heartbeatTimer = window.setInterval(() => {
    if (!socket || socket.readyState !== WebSocket.OPEN) return;
    try {
      socket.send(JSON.stringify({ type: "ping", ts: Date.now() }));
    } catch {
      // ignore
    }
  }, HEARTBEAT_MS);
}

async function connect() {
  if (window.sessionStorage.getItem("static_demo") === "1" || import.meta.env.VITE_STATIC_DEMO === "1") {
    connectionState.value = "disconnected";
    return;
  }
  if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) return;
  let userId = await resolveUserId();
  if (!userId) {
    userId = String(getSessionUserId() || "");
  }
  if (!userId) return;
  window.sessionStorage.setItem("user_id", String(userId));
  manualClosed = false;
  connectionState.value = connected.value ? "connected" : "reconnecting";
  const url = buildWsUrl(`/ws/${userId}`);
  if (!url) return;
  socket = new WebSocket(url);
  socket.onopen = () => {
    reconnectAttempts = 0;
    connected.value = true;
    connectionState.value = "connected";
    startHeartbeat();
  };
  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.type === "pong") return;
      if (data.type === "notification") {
        pushMessage(data);
      }
    } catch {
      // ignore
    }
  };
  socket.onclose = () => {
    clearHeartbeat();
    connected.value = false;
    socket = null;
    connectionState.value = manualClosed ? "disconnected" : "reconnecting";
    if (!manualClosed) {
      scheduleReconnect();
    }
  };
  socket.onerror = () => {
    connected.value = false;
    connectionState.value = manualClosed ? "disconnected" : "reconnecting";
  };
}

function disconnect() {
  manualClosed = true;
  reconnectAttempts = 0;
  clearHeartbeat();
  if (reconnectTimer) {
    window.clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }
  if (socket) {
    socket.close();
    socket = null;
  }
  connected.value = false;
  connectionState.value = "disconnected";
}

export function useWebSocket() {
  onBeforeUnmount(() => {
    // 不自动断开，保证全局可复用；显式logout时调用disconnect
  });
  return {
    connect,
    disconnect,
    connected: computed(() => connected.value),
    connectionState: computed(() => connectionState.value),
    notifications: computed(() => notifications.value),
    unread: computed(() => unread.value),
    warningBanners: computed(() => warningBanners.value),
    clearUnread,
    closeBanner
  };
}

