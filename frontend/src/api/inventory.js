import http from "./http";

/** 查询库存总览。 */
export function fetchInventoryOverview(branchCode = "") {
  return http.get("/inventory/overview", {
    params: { branch_code: branchCode || undefined }
  });
}

/** 查询效期预警药品。 */
export function fetchExpiryWarnings(warningDays = 30) {
  return http.get("/inventory/expiry-warnings", {
    params: { warning_days: warningDays }
  });
}

/** 计算EOQ建议值。 */
export function calculateEoq(payload) {
  return http.post("/inventory/eoq", payload);
}

