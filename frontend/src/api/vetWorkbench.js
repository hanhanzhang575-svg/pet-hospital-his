import http from "./http";

/** 查询医生待诊队列。 */
export function fetchPendingQueue() {
  return http.get("/vet-workbench/queue");
}

/** 开始接诊。 */
export function startConsultation(appointmentId) {
  return http.post(`/vet-workbench/start/${appointmentId}`);
}

/** 录入病历。 */
export function createMedicalRecord(payload) {
  return http.post("/vet-workbench/medical-record", payload);
}

/** 查询病历记录。 */
export function fetchMedicalRecords(petId) {
  return http.get("/vet-workbench/medical-records", {
    params: { pet_id: petId || undefined }
  });
}

/** 查询宠物全景病历时间轴。 */
export function fetchPetHistoryTimeline(petId) {
  return http.get(`/vet-workbench/pet-history/${petId}`);
}

/** 作废病历记录。 */
export function voidMedicalRecord(recordId, reason) {
  return http.post(`/vet-workbench/medical-record/${recordId}/void`, { reason });
}

