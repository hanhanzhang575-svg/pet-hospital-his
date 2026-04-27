import http from "./http";

/** 查询住院记录。 */
export function fetchInpatientRecords(clinicId = "") {
  return http.get("/inpatient-records", {
    params: { clinic_id: clinicId || undefined }
  });
}

/** 创建住院记录。 */
export function createInpatientRecord(payload) {
  return http.post("/inpatient-records", payload);
}

/** 更新住院记录。 */
export function updateInpatientRecord(recordId, payload) {
  return http.put(`/inpatient-records/${recordId}`, payload);
}

/** 查询笼舍列表。 */
export function fetchCages(clinicId, zoneType = "") {
  return http.get("/cages", {
    params: {
      clinic_id: clinicId,
      zone_type: zoneType || undefined
    }
  });
}

/** 自动分配笼舍（住院三层约束）。 */
export function allocateCage(payload) {
  return http.post("/inpatient-records/allocate-cage", payload);
}

/** 查询护理日志。 */
export function fetchNursingLogs(recordId) {
  return http.get(`/inpatient-records/${recordId}/nursing-logs`);
}

/** 提交体征/护理日志。 */
export function createNursingLog(recordId, payload) {
  return http.post(`/inpatient-records/${recordId}/nursing-logs`, payload);
}

/** 撤回护理日志（5分钟窗口）。 */
export function voidNursingLog(recordId, logId, reason = "") {
  return http.delete(`/inpatient-records/${recordId}/nursing-logs/${logId}`, {
    data: { reason }
  });
}

