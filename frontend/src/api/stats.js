import http from "./http";

/** 近7天三院区门诊量。 */
export function fetchWeeklyVisits() {
  return http.get("/stats/weekly-visits");
}

/** 今日收入结构。 */
export function fetchTodayRevenue() {
  return http.get("/stats/today-revenue");
}

/** 客户转化漏斗。 */
export function fetchConversionFunnel() {
  return http.get("/stats/conversion-funnel");
}

/** HIS财务台账。 */
export function fetchBillingLedger(clinicId = "C001") {
  return http.get("/stats/billing-ledger", { params: { clinic_id: clinicId } });
}

