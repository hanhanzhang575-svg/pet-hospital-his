import http from "./http";

export function fetchOwnerCenter(ownerId) {
  return http.get(`/owner-center/${ownerId}`);
}

