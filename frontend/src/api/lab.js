import http from "./http";

export function fetchPendingTests(clinicId = "") {
  return http.get("/lab/pending-tests", {
    params: { clinic_id: clinicId || undefined }
  });
}

export function startLabExam(appointmentId) {
  return http.post(`/lab/start-exam/${appointmentId}`);
}

export function submitLabResult(payload) {
  return http.post("/lab/submit-result", payload);
}

export function fetchLabResults(params = {}) {
  const requestParams = {};
  if (typeof params === "string") {
    requestParams.clinic_id = params || undefined;
  } else {
    Object.assign(requestParams, params || {});
  }
  return http.get("/lab/results", {
    params: requestParams
  });
}

export function fetchLabStats(clinicId = "") {
  return http.get("/lab/stats", {
    params: { clinic_id: clinicId || undefined }
  });
}

