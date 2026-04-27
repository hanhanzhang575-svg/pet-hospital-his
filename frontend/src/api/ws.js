/** 读取当前标签页会话中的用户ID。 */
export function getSessionUserId() {
  return window.sessionStorage.getItem("user_id") || "";
}

/** 构建带 user_id 的 WebSocket 地址，保证按标签页会话隔离。 */
export function buildWsUrl(path) {
  const wsBase = window.sessionStorage.getItem("ws_base_url");
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  const defaultHost = `${window.location.hostname}:8000`;
  const base = wsBase || `${protocol}://${defaultHost}`;
  const userId = getSessionUserId();
  const cleanPath = String(path || "").startsWith("/") ? path : `/${path}`;
  const params = new URLSearchParams();
  if (userId) params.set("user_id", userId);
  return `${base}${cleanPath}${params.toString() ? `?${params.toString()}` : ""}`;
}

