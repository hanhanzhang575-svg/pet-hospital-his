import http from "./http";

/** 查询处方列表。 */
export function fetchPrescriptions(clinicId = "") {
  return http.get("/prescriptions", {
    params: { clinic_id: clinicId || undefined }
  });
}

/** 催缴提醒。 */
export function urgePrescriptionPayment(prescriptionId) {
  return http.post("/billing/urge-payment", null, {
    params: { prescription_id: prescriptionId }
  });
}

/** 作废处方。 */
export function invalidatePrescription(prescriptionId) {
  return http.post(`/prescriptions/${prescriptionId}/invalidate`);
}

/** 撤销作废处方。 */
export function restorePrescription(prescriptionId) {
  return http.post(`/prescriptions/${prescriptionId}/restore`);
}

