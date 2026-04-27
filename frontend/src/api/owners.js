import http from "./http";

/** 查询主人列表。 */
export function fetchOwners() {
  return http.get("/owners");
}

/** 新建主人。 */
export function createOwner(payload) {
  return http.post("/owners", payload);
}

/** 更新主人。 */
export function updateOwner(id, payload) {
  return http.put(`/owners/${id}`, payload);
}

/** 删除主人。 */
export function deleteOwner(id) {
  return http.delete(`/owners/${id}`);
}

