/** 统一状态Tag颜色规范。 */
export function getStatusTagType(status) {
  const okSet = new Set(["正常", "已完成", "就诊中", "住院观察", "术后监护", "已缴费", "已发药", "空闲"]);
  const warnSet = new Set(["待诊", "待处理", "待入院", "待出院", "待缴费", "待清洁", "预警"]);
  const dangerSet = new Set(["急诊", "异常", "告警", "欠费停药", "维修"]);
  const neutralSet = new Set(["已取消", "已失效", "已出院"]);
  if (okSet.has(status)) return "success";
  if (warnSet.has(status)) return "warning";
  if (dangerSet.has(status)) return "danger";
  if (neutralSet.has(status)) return "info";
  return "";
}

/** 将axios错误对象转换为用户可读信息。 */
export function getErrorMessage(error, fallback = "请求失败") {
  const appCode = Number(error?.appCode || error?.response?.data?.code || 0);
  const httpStatus = Number(error?.status || error?.response?.status || 0);
  if (appCode === 401 || httpStatus === 401) return "登录已过期，请重新登录";
  if (appCode === 403 || httpStatus === 403) return "您没有执行此操作的权限，如有疑问请联系系统管理员";
  if (appCode === 404 || httpStatus === 404) return "未找到相关记录，可能已被删除或编号有误";
  if (appCode === 409 || httpStatus === 409) return "操作冲突：该时间段已被占用，请选择其他时间";
  if (appCode === 500 || httpStatus === 500) return "系统内部错误，请稍后重试。如持续出现请联系信息技术部（内线：XXX）";
  if (error?.code === "ECONNABORTED") return "网络连接超时，请检查网络后点击重试";
  if (error?.code === "ERR_NETWORK") return "网络错误：无法连接服务器，请确认后端服务已启动";
  if (String(error?.message || "").toLowerCase().includes("network error")) {
    return "网络错误：无法连接服务器，请确认后端服务已启动";
  }
  const data = error?.response?.data;
  if (appCode === 422 || httpStatus === 422) {
    if (Array.isArray(data?.detail) && data.detail.length > 0) {
      const first = data.detail[0];
      const field = Array.isArray(first?.loc) ? first.loc[first.loc.length - 1] : "字段";
      const detailText = typeof first?.msg === "string" ? first.msg : JSON.stringify(first);
      return `${field}：${detailText}`;
    }
    return "输入参数不正确，请检查后重试";
  }
  if (typeof data?.message === "string" && data.message.trim()) {
    return data.message;
  }
  if (Array.isArray(data?.detail) && data.detail.length > 0) {
    const first = data.detail[0];
    const field = Array.isArray(first?.loc) ? first.loc[first.loc.length - 1] : "字段";
    const detailText = typeof first?.msg === "string" ? first.msg : JSON.stringify(first);
    return `${field}：${detailText}`;
  }
  if (typeof data?.detail === "string" && data.detail.trim()) {
    return data.detail;
  }
  if (data && typeof data === "object") {
    return JSON.stringify(data);
  }
  if (typeof error?.message === "string" && error.message.trim()) {
    return error.message;
  }
  if (error && typeof error === "object") {
    return JSON.stringify(error);
  }
  return String(error || fallback);
}

