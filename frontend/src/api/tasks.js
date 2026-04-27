import http from "./http";

/** 创建采购任务。 */
export function createPurchaseTasks(payload) {
  return http.post("/tasks/purchase", payload);
}

/** 查询采购任务。 */
export function fetchPurchaseTasks(status = "") {
  return http.get("/tasks/purchase", {
    params: { status: status || undefined }
  });
}

/** 更新采购任务状态。 */
export function updatePurchaseTask(taskId, payload) {
  return http.put(`/tasks/purchase/${taskId}`, payload);
}

/** 创建回访任务。 */
export function createFollowupTasks(payload) {
  return http.post("/tasks/followup", payload);
}

/** 查询回访任务。 */
export function fetchFollowupTasks(status = "") {
  return http.get("/tasks/followup", {
    params: { status: status || undefined }
  });
}

/** 更新回访任务状态。 */
export function updateFollowupTask(taskId, payload) {
  return http.put(`/tasks/followup/${taskId}`, payload);
}

/** 按RFM高危客户批量创建回访工单。 */
export function createRfmFollowupTasks(payload = {}) {
  return http.post("/rfm/create-followup-tasks", payload);
}

