import axios from "axios";
import { getErrorMessage } from "../utils/status";
import { ElMessage } from "element-plus";

const http = axios.create({
  baseURL: "/api/v1",
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
  (response) => response.data,
  (error) => {
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

