import http from "./http";

/** 获取EOQ智能补货建议。 */
export function fetchEoqSuggestions(branchCode = "C001") {
  return http.get("/pharmacy/eoq-suggestions", {
    params: { branch_code: branchCode || undefined }
  });
}

/** 一键生成采购清单。 */
export function createPharmacyPurchaseOrder(branchCode = "C001") {
  return http.post("/pharmacy/purchase-order", null, {
    params: { branch_code: branchCode || undefined }
  });
}

/** 采购审批通过。 */
export function approvePharmacyPurchaseOrder(taskId) {
  return http.put(`/pharmacy/purchase-order/${taskId}/approve`);
}

/** 采购审批驳回。 */
export function rejectPharmacyPurchaseOrder(taskId) {
  return http.put(`/pharmacy/purchase-order/${taskId}/reject`);
}

