import http from "./http";

/**
 * 生成医生与护士排班（OR-Tools）。
 * @param {object} payload
 */
export function generateSchedule(payload) {
  return http.post("/scheduling/generate", payload);
}

/**
 * 查询参与排班的医生与护士员工池。
 * @param {object} params
 */
export function fetchSchedulingStaff(params = {}) {
  return http.get("/scheduling/staff", { params });
}

/**
 * 查询排班列表。
 * @param {object} params
 */
export function fetchSchedulingAssignments(params = {}) {
  return http.get("/scheduling/assignments", { params });
}

/**
 * 拖拽后同步单条排班。
 * @param {object} payload
 */
export function upsertSchedulingAssignment(payload) {
  return http.put("/scheduling/assignment", payload);
}

