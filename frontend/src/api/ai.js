import http from "./http";

/** RFM流失预警。 */
export function fetchRfmWarnings() {
  return http.get("/ai/rfm-warning");
}

/** 主动监听校验。 */
export function checkActiveListener(payload) {
  return http.post("/ai/active-listener", payload);
}

/** 症状实时检索知识条目。 */
export function retrieveKnowledge(payload) {
  return http.post("/ai/knowledge/retrieve", payload);
}

/** 多模态联合诊断（有图/无图统一入口）。 */
export function runMultimodalDiagnosis(payload) {
  return http.post("/ai/multimodal-diagnosis", payload);
}

/** 完整诊断流水线：检索 + 图谱 + LLM。 */
export function runFullDiagnosis(payload) {
  return http.post("/ai/full-diagnosis", payload);
}

/** 获取图谱可视化结构。 */
export function fetchKnowledgeGraph(payload) {
  return http.post("/ai/graph/viz", payload);
}

/** 执行图谱多跳推理。 */
export function runGraphReasoning(payload) {
  return http.post("/ai/graph/reasoning", payload);
}

/** 写入AI审计日志。 */
export function createAiAuditLog(payload) {
  return http.post("/ai/audit-log", payload);
}

