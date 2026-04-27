import http from "./http";

export function fetchAdoptionPets() {
  return http.get("/adoption/pets");
}

export function runAdoptionMatch(adoptionPetId, { mode = "fast", topN = 200, signal, timeout = 20000 } = {}) {
  return http.post(`/adoption/match/${adoptionPetId}`, null, {
    params: { mode, top_n: topN },
    signal,
    timeout
  });
}

export function fetchAdoptionMatch(adoptionPetId) {
  return http.get(`/adoption/match/${adoptionPetId}`);
}

export function fetchAdoptionDashboard(adoptionPetId, topN = 20) {
  return http.get(`/adoption/dashboard/${adoptionPetId}`, { params: { top_n: topN } });
}

export function fetchAdoptionAlgorithm() {
  return http.get("/adoption/algorithm");
}

export function fetchAdoptionMatchStatus(adoptionPetId) {
  return http.get(`/adoption/match-status/${adoptionPetId}`);
}

export function fetchAdoptionPersona(adoptionPetId) {
  return http.get(`/adoption/persona/${adoptionPetId}`);
}

