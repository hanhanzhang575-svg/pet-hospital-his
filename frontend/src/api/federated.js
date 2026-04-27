import http from "./http";

export function fetchFederatedStatus() {
  return http.get("/federated/status");
}

