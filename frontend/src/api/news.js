import http from "./http";

export function fetchNewsPosts(noCacheKey = "") {
  return http.get("/news", {
    params: {
      _: noCacheKey || undefined
    }
  });
}

export function createNewsPost(payload) {
  return http.post("/news", payload);
}

