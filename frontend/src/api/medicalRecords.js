import http from "./http";

export async function getMedicalRecords(params) {
  const res = await http.get("/vet-workbench/medical-records", { params });
  return res;
}

export async function getMedicalRecord(recordId) {
  const res = await http.get(`/vet-workbench/medical-record/${recordId}`);
  return res;
}

export async function createMedicalRecord(payload) {
  const res = await http.post("/vet-workbench/medical-record", payload);
  return res;
}

export async function updateMedicalRecord(recordId, payload) {
  const res = await http.put(`/vet-workbench/medical-record/${recordId}`, payload);
  return res;
}

export async function voidMedicalRecord(recordId, reason) {
  const res = await http.post(`/vet-workbench/medical-record/${recordId}/void`, { reason });
  return res;
}
