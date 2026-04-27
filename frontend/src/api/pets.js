import http from "./http";

/** 查询宠物列表。 */
export function fetchPets() {
  return http.get("/pets");
}

/** 查询宠物详情。 */
export function fetchPetById(id) {
  return http.get(`/pets/${id}`);
}

/** 新建宠物。 */
export function createPet(payload) {
  return http.post("/pets", payload);
}

/** 更新宠物。 */
export function updatePet(id, payload) {
  return http.put(`/pets/${id}`, payload);
}

/** 删除宠物。 */
export function deletePet(id) {
  return http.delete(`/pets/${id}`);
}

