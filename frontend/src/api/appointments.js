import http from "./http";

/** 创建预约挂号。 */
export function createAppointment(payload) {
  return http.post("/appointments", payload);
}

/** 查询预约列表。 */
export function fetchAppointments({
  clinicId = "",
  doctorId = undefined,
  petId = undefined,
  status = undefined,
  limit = 120,
  offset = 0
} = {}) {
  return http.get("/appointments", {
    params: {
      clinic_id: clinicId || undefined,
      doctor_id: doctorId,
      pet_id: petId,
      status,
      limit,
      offset
    }
  });
}

/** 取消预约挂号。 */
export function cancelAppointment(appointmentId) {
  return http.post(`/appointments/${appointmentId}/cancel`);
}

/** 更新预约（排班调整）。 */
export function updateAppointment(appointmentId, payload) {
  return http.put(`/appointments/${appointmentId}`, payload);
}

/** 查询排班周视图。 */
export function fetchScheduleWeek({ clinicId = "C001", weekStart = "" } = {}) {
  return http.get("/appointments/schedule/week", {
    params: { clinic_id: clinicId, week_start: weekStart || undefined }
  });
}

/** 新增排班。 */
export function createSchedule(payload) {
  return http.post("/appointments/schedule/create", payload);
}

/** 标记请假（含自动转移/短信退号）。 */
export function resolveScheduleLeave(appointmentId, payload) {
  return http.post(`/appointments/schedule/${appointmentId}/leave`, payload || {});
}

/** 删除排班。 */
export function deleteSchedule(appointmentId) {
  return http.delete(`/appointments/schedule/${appointmentId}`);
}

/** 批量复制上周排班。 */
export function copyScheduleFromLastWeek({ clinicId = "C001", weekStart = "" } = {}) {
  return http.post("/appointments/schedule/copy-last-week", null, {
    params: { clinic_id: clinicId, week_start: weekStart || undefined }
  });
}

/** 查询某排班时段预约患者。 */
export function fetchSchedulePatients(appointmentId) {
  return http.get(`/appointments/schedule/${appointmentId}/patients`);
}

/** 查询排班高峰预测。 */
export function fetchSchedulePeakPrediction({ clinicId = "C001", weekStart = "" } = {}) {
  return http.get("/appointments/schedule/peak-prediction", {
    params: { clinic_id: clinicId, week_start: weekStart || undefined }
  });
}

/** 查询排班优化建议。 */
export function fetchScheduleRecommendations({ clinicId = "C001", weekStart = "" } = {}) {
  return http.get("/appointments/schedule/recommendations", {
    params: { clinic_id: clinicId, week_start: weekStart || undefined }
  });
}

