import http from "./http";

/** 护理录入异常体征并触发医生告警。 */
export function notifyNursingAbnormal(doctorId, petName, temperature) {
  return http.post("/notifications/nursing-abnormal", null, {
    params: { doctor_id: doctorId, pet_name: petName, temperature }
  });
}

/** 院区主任修改排班后触发医生通知。 */
export function notifyScheduleUpdated(doctorId, scheduleText) {
  return http.post("/notifications/schedule-updated", null, {
    params: { doctor_id: doctorId, schedule_text: scheduleText }
  });
}

/** 收费结算完成通知院区主任。 */
export function notifySettlementComplete(settledCount, totalIncome) {
  return http.post("/billing/settlement-complete", null, {
    params: { settled_count: settledCount, total_income: totalIncome }
  });
}

/** 触发场景一：猫纯文本验证（禁忌药检查）。 */
export function runAiScenarioText() {
  return http.post("/ai/multimodal-diagnosis", {
    symptoms_text: "反复呕吐三天，食欲废绝，腹部触诊疼痛",
    image_files: [],
    pet_info: { species: "猫", breed: "英短", age: 3, weight: 4.8, allergy_history: [] }
  });
}

/** 触发场景二：犬图文验证（影像字段检查）。 */
export function runAiScenarioMultimodal(mockImageBase64 = "dGVzdC1pbWFnZQ==") {
  return http.post("/ai/multimodal-diagnosis", {
    symptoms_text: "跛行，右后肢不敢负重",
    image_files: [mockImageBase64],
    pet_info: { species: "犬", breed: "拉布拉多", age: 4, weight: 25.0, allergy_history: [] }
  });
}

