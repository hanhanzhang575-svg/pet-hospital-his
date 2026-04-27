import http from "./http";

/** 查询医生列表。 */
export function fetchDoctors(clinicId = "") {
  return http.get("/users/doctors", {
    params: { clinic_id: clinicId || undefined }
  });
}

/** 查询医技人员列表。 */
export function fetchLabTechs(clinicId = "") {
  return http.get("/users/lab-techs", {
    params: { clinic_id: clinicId || undefined }
  });
}

