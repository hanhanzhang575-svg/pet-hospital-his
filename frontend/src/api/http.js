import axios from "axios";
import { getErrorMessage } from "../utils/status";
import { ElMessage } from "element-plus";
import { getStaticDemoResponse, isStaticDemoEnabled } from "./staticDemo";

const rawBackendUrl = String(import.meta.env.VITE_BACKEND_URL || "").trim();
const backendUrl = rawBackendUrl.replace(/\/+$/, "");
const apiBaseUrl = backendUrl ? `${backendUrl}/api/v1` : "/api/v1";

const http = axios.create({
  baseURL: apiBaseUrl,
  timeout: 10000
});

http.interceptors.request.use((config) => {
  /** 为每个请求自动附加JWT令牌。 */
  const token = window.sessionStorage.getItem("access_token");
  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

http.interceptors.response.use(
  (response) => {
    const payload = response.data;
    if (isStaticDemoEnabled()) {
      const demoResponse = getStaticDemoResponse(response.config);
      if (demoResponse) {
        return demoResponse;
      }
    }

    const appCode = Number(payload?.code || 0);
    if (appCode >= 400) {
      const wrapped = new Error(payload?.message || "请求失败");
      wrapped.status = response.status;
      wrapped.appCode = appCode;
      wrapped.response = response;
      wrapped.raw = response;
      return Promise.reject(wrapped);
    }
    return payload;
  },
  (error) => {
    if (isStaticDemoEnabled()) {
      const demoResponse = getStaticDemoResponse(error?.config);
      if (demoResponse) {
        return Promise.resolve(demoResponse);
      }
    }

    const suppressAuthErrorToast = Boolean(error?.config?.suppressAuthErrorToast);
    const status = Number(error?.response?.status || 0);
    const appCode = Number(error?.response?.data?.code || 0);
    const message = getErrorMessage(
      {
        ...error,
        status,
        appCode
      },
      "请求失败"
    );
    if ((status === 401 || appCode === 401) && !suppressAuthErrorToast) {
      window.sessionStorage.clear();
      ElMessage.error(message);
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    const wrapped = new Error(message);
    wrapped.status = status;
    wrapped.appCode = appCode;
    wrapped.raw = error;
    return Promise.reject(wrapped);
  }
);

export default http;

