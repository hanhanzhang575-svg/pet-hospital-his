import http from "./http";

/** 护理快速体征录入。 */
export function createVitalSigns(payload) {
  return http.post("/nursing/vital-signs", payload);
}

