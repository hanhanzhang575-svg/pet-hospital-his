import http from "./http";

export function fetchDataCenterTables() {
  return http.get("/data-center/tables");
}

export function fetchTableRows(tableName, page = 1, size = 20) {
  return http.get(`/data-center/table/${tableName}`, { params: { page, size } });
}

export function traceMedicalRecord(recordId) {
  return http.get(`/data-center/trace/medical-record/${recordId}`);
}

