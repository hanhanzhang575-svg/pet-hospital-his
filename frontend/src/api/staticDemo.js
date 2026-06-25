const today = new Date().toISOString().slice(0, 10);

const appointments = [
  {
    id: 1,
    record_code: "BZH-OP-260625-001",
    pet_name: "奶糖",
    pet_id: 1,
    doctor_id: 2,
    clinic_id: "C001",
    scheduled_time: `${today}T09:20:00`,
    urgency_level: "急诊",
    status: "待诊",
    priority_score: 86
  },
  {
    id: 2,
    record_code: "BZH-OP-260625-002",
    pet_name: "可乐",
    pet_id: 2,
    doctor_id: 2,
    clinic_id: "C001",
    scheduled_time: `${today}T10:10:00`,
    urgency_level: "优先",
    status: "待诊",
    priority_score: 64
  },
  {
    id: 3,
    record_code: "BZH-OP-260625-003",
    pet_name: "团子",
    pet_id: 3,
    doctor_id: 3,
    clinic_id: "C002",
    scheduled_time: `${today}T11:40:00`,
    urgency_level: "常规",
    status: "待诊",
    priority_score: 28
  },
  {
    id: 4,
    record_code: "BZH-OP-260625-004",
    pet_name: "栗子",
    pet_id: 4,
    doctor_id: 4,
    clinic_id: "C003",
    scheduled_time: `${today}T14:30:00`,
    urgency_level: "常规",
    status: "已完成",
    priority_score: 18
  }
];

const cages = Array.from({ length: 36 }, (_, idx) => ({
  id: idx + 1,
  code: `C001-${String(idx + 1).padStart(2, "0")}`,
  clinic_id: "C001",
  status: idx % 5 === 0 ? "清洁中" : idx % 3 === 0 ? "住院中" : "空闲",
  zone_type: idx % 2 === 0 ? "犬区" : "猫区"
}));

const inpatientRecords = [
  { id: 1, pet_id: 1, doctor_id: 2, pet_name: "奶糖", status: "住院中", deposit_amount: 1800, consumed_amount: 1420 },
  { id: 2, pet_id: 2, doctor_id: 2, pet_name: "可乐", status: "待入院", deposit_amount: 1200, consumed_amount: 320 },
  { id: 3, pet_id: 5, doctor_id: 3, pet_name: "芝士", status: "住院中", deposit_amount: 900, consumed_amount: 960 }
];

const inventoryRows = [
  { id: 1, name: "阿莫西林克拉维酸钾", stock_qty: 42, safety_stock: 30, branch_code: "C001" },
  { id: 2, name: "犬猫复合维生素", stock_qty: 12, safety_stock: 24, branch_code: "C001" },
  { id: 3, name: "伊曲康唑胶囊", stock_qty: 8, safety_stock: 16, branch_code: "C001" },
  { id: 4, name: "泌尿道处方粮", stock_qty: 28, safety_stock: 18, branch_code: "C001" }
];

const prescriptions = [
  { id: 1, prescription_code: "RX-260625-001", pet_name: "奶糖", status: "已缴费", clinic_id: "C001" },
  { id: 2, prescription_code: "RX-260625-002", pet_name: "可乐", status: "已缴费", clinic_id: "C001" },
  { id: 3, prescription_code: "RX-260625-003", pet_name: "团子", status: "待缴费", clinic_id: "C001" }
];

const followupTasks = [
  { id: 1, owner_name: "张女士", status: "待处理", topic: "术后 48 小时回访" },
  { id: 2, owner_name: "陈先生", status: "待处理", topic: "疫苗后反应确认" }
];

const weeklyVisits = {
  dates: ["06-19", "06-20", "06-21", "06-22", "06-23", "06-24", "06-25"],
  series: [
    { name: "沙河院区", data: [42, 48, 51, 39, 58, 62, 55] },
    { name: "甘井子院区", data: [31, 34, 38, 36, 41, 45, 40] },
    { name: "高新园区", data: [22, 28, 24, 27, 31, 33, 36] }
  ]
};

const todayRevenue = [
  { name: "诊疗", value: 12680 },
  { name: "药品", value: 8420 },
  { name: "检验", value: 5360 },
  { name: "住院", value: 3880 }
];

const conversionFunnel = [
  { name: "到院咨询", value: 168 },
  { name: "完成挂号", value: 124 },
  { name: "完成诊疗", value: 106 },
  { name: "复诊预约", value: 54 }
];

const users = {
  receptionist: { id: 101, username: "receptionist1", role: "receptionist", full_name: "张悦", clinic_id: "C001" },
  doctor: { id: 201, username: "doctor1", role: "doctor", full_name: "张医生", clinic_id: "C001" },
  nurse: { id: 301, username: "nurse1", role: "nurse", full_name: "王佳", clinic_id: "C001" },
  pharmacist: { id: 401, username: "pharmacist1", role: "pharmacist", full_name: "赵雪", clinic_id: "C001" },
  pharmacy: { id: 401, username: "pharmacist1", role: "pharmacist", full_name: "赵雪", clinic_id: "C001" },
  lab_tech: { id: 501, username: "labtech1", role: "lab_tech", full_name: "孙超", clinic_id: "C001" },
  manager: { id: 601, username: "manager1", role: "manager", full_name: "周院长", clinic_id: "C001" },
  admin: { id: 701, username: "admin", role: "admin", full_name: "系统管理员", clinic_id: "C001" }
};

const ownerRows = [
  { id: 1, name: "张女士", phone: "13800000001", level: "VIP", address: "沙河口区", created_at: `${today}T08:30:00` },
  { id: 2, name: "陈先生", phone: "13800000002", level: "普通", address: "甘井子区", created_at: `${today}T09:10:00` },
  { id: 3, name: "林同学", phone: "13800000003", level: "复诊", address: "高新园区", created_at: `${today}T10:20:00` }
];

const petRows = [
  { id: 1, owner_id: 1, owner_name: "张女士", name: "奶糖", species: "猫", breed: "英短", gender: "雌", age: 3, weight: 4.2 },
  { id: 2, owner_id: 2, owner_name: "陈先生", name: "可乐", species: "犬", breed: "柯基", gender: "雄", age: 4, weight: 12.5 },
  { id: 3, owner_id: 3, owner_name: "林同学", name: "团子", species: "猫", breed: "布偶", gender: "雄", age: 2, weight: 5.1 },
  { id: 4, owner_id: 1, owner_name: "张女士", name: "栗子", species: "犬", breed: "柴犬", gender: "雌", age: 5, weight: 9.4 },
  { id: 5, owner_id: 2, owner_name: "陈先生", name: "芝士", species: "猫", breed: "橘猫", gender: "雄", age: 6, weight: 6.3 }
];

const medicalRecords = [
  {
    id: 1,
    appointment_id: 1,
    pet_id: 1,
    pet_name: "奶糖",
    doctor_id: 201,
    doctor_name: "张医生",
    chief_complaint: "食欲下降，轻微呕吐",
    diagnosis: "疑似急性胃肠炎",
    treatment_plan: "补液、止吐、少量多餐观察 48 小时",
    status: "已完成",
    created_at: `${today}T10:10:00`
  },
  {
    id: 2,
    appointment_id: 2,
    pet_id: 2,
    pet_name: "可乐",
    doctor_id: 201,
    doctor_name: "张医生",
    chief_complaint: "皮肤瘙痒，局部脱毛",
    diagnosis: "过敏性皮炎",
    treatment_plan: "抗炎止痒，复查皮肤镜",
    status: "就诊中",
    created_at: `${today}T11:00:00`
  }
];

const labOrders = [
  { id: 1, appointment_id: 1, pet_name: "奶糖", test_type: "血常规", status: "待检", priority: "急诊", created_at: `${today}T09:40:00` },
  { id: 2, appointment_id: 2, pet_name: "可乐", test_type: "皮肤刮片", status: "检查中", priority: "优先", created_at: `${today}T10:30:00` },
  { id: 3, appointment_id: 3, pet_name: "团子", test_type: "生化检查", status: "已完成", priority: "常规", created_at: `${today}T11:30:00` }
];

const labResults = [
  { id: 1, order_id: 3, pet_name: "团子", test_type: "生化检查", result_summary: "轻度脱水指标", status: "已出报告", abnormal_count: 1, created_at: `${today}T12:10:00` }
];

const nursingLogs = [
  { id: 1, inpatient_record_id: 1, pet_name: "奶糖", temperature: 38.6, heart_rate: 128, respiration: 28, status: "正常", created_at: `${today}T12:30:00` },
  { id: 2, inpatient_record_id: 3, pet_name: "芝士", temperature: 39.4, heart_rate: 142, respiration: 34, status: "异常", created_at: `${today}T13:10:00` }
];

const purchaseTasks = [
  { id: 1, drug_name: "犬猫复合维生素", quantity: 30, status: "待审批", priority: "高", created_at: `${today}T09:00:00` },
  { id: 2, drug_name: "伊曲康唑胶囊", quantity: 20, status: "已通过", priority: "中", created_at: `${today}T09:30:00` }
];

const rfmWarnings = [
  { owner_id: 1, owner_name: "张女士", level: "高价值待回访", score: 92, suggestion: "建议安排术后复诊提醒" },
  { owner_id: 2, owner_name: "陈先生", level: "疫苗提醒", score: 76, suggestion: "建议推送免疫加强通知" }
];

const scheduleStaff = Object.values(users).map((user) => ({
  id: user.id,
  name: user.full_name,
  role: user.role,
  clinic_id: user.clinic_id
}));

const scheduleAssignments = [
  { id: 1, staff_id: 201, staff_name: "张医生", date: today, shift: "早班", room: "诊室 A" },
  { id: 2, staff_id: 301, staff_name: "王佳", date: today, shift: "白班", room: "住院部" },
  { id: 3, staff_id: 401, staff_name: "赵雪", date: today, shift: "白班", room: "药房" }
];

const adoptionPets = [
  { id: 1, name: "豆包", species: "猫", age: 1, status: "待领养", match_score: 94 },
  { id: 2, name: "小七", species: "犬", age: 2, status: "待领养", match_score: 88 }
];

const billingLedger = [
  { id: 1, type: "诊疗", amount: 286, status: "已结算", pet_name: "奶糖", created_at: `${today}T10:50:00` },
  { id: 2, type: "药品", amount: 168, status: "待缴费", pet_name: "可乐", created_at: `${today}T11:15:00` }
];

const newsRows = [
  { id: 1, title: "白之助春季义诊周开放预约（疫苗+体检）", category: "院内通知", summary: "前台可直接创建义诊预约。", source_name: "白之助运营中心", published_at: "2026-04-10" },
  { id: 2, title: "猫咪应激期 72 小时观察法", category: "养宠妙招", summary: "固定喂食、隐藏处和猫砂位置可降低应激。", source_name: "白之助猫科门诊", published_at: "2026-04-08" }
];

function success(data) {
  return { code: 200, message: "success", data };
}

function getCurrentDemoRole() {
  return window.sessionStorage.getItem("ui_role") || window.sessionStorage.getItem("static_demo_role") || "doctor";
}

function getPath(config) {
  const url = String(config?.url || "");
  try {
    return new URL(url, "http://demo.local").pathname.replace(/^\/api\/v1/, "");
  } catch {
    return url.replace(/^\/api\/v1/, "");
  }
}

export function isStaticDemoEnabled() {
  return import.meta.env.VITE_STATIC_DEMO === "1" || window.sessionStorage.getItem("static_demo") === "1";
}

export function getStaticDemoUser(role = getCurrentDemoRole()) {
  return users[role] || users.doctor;
}

export function getStaticDemoResponse(config) {
  const method = String(config?.method || "get").toLowerCase();
  const path = getPath(config);

  if (!["get", "post", "put", "delete", "patch"].includes(method)) return success({ ok: true, static_demo: true });

  if (path === "/auth/me") return success(getStaticDemoUser());
  if (path === "/vet-workbench/queue") return success(appointments.filter((item) => item.status === "待诊"));
  if (path === "/vet-workbench/medical-records") return success(medicalRecords);
  if (path.startsWith("/vet-workbench/medical-record/")) return success(findById(medicalRecords, path) || medicalRecords[0]);
  if (path.startsWith("/vet-workbench/pet-history/")) return success(medicalRecords);
  if (path.startsWith("/vet-workbench/start/")) return success({ status: "就诊中", appointment: appointments[0] });
  if (path === "/appointments") return success(appointments);
  if (path === "/appointments/schedule/week") return success(scheduleAssignments);
  if (path === "/appointments/schedule/peak-prediction") return success({ peak_hours: ["09:00", "10:00", "15:00"], risk: "中" });
  if (path === "/appointments/schedule/recommendations") return success(scheduleAssignments);
  if (path.includes("/appointments/schedule/") && path.endsWith("/patients")) return success(appointments);
  if (path === "/tasks/followup") return success(followupTasks);
  if (path === "/tasks/purchase") return success(purchaseTasks);
  if (path === "/tasks/coordination/overview") return success({ referrals: 3, support_requests: 2, available_cages: 18 });
  if (path === "/tasks/coordination/referrals") return success([{ id: 1, pet_name: "奶糖", from_clinic: "沙河院区", to_clinic: "高新园区", status: "协调中" }]);
  if (path === "/tasks/coordination/available-cages") return success(cages.filter((item) => item.status === "空闲").slice(0, 8));
  if (path === "/inpatient-records") return success(inpatientRecords);
  if (path.startsWith("/inpatient-records/") && path.endsWith("/nursing-logs")) return success(nursingLogs);
  if (path.startsWith("/inpatient-records/")) return success(findById(inpatientRecords, path) || inpatientRecords[0]);
  if (path === "/cages") return success(cages);
  if (path === "/prescriptions") return success(prescriptions);
  if (path.startsWith("/prescriptions/")) return success(findById(prescriptions, path) || prescriptions[0]);
  if (path === "/inventory/overview") return success(inventoryRows);
  if (path === "/inventory/expiry-warnings") return success([{ id: 1, name: "伊曲康唑胶囊", days_left: 18 }]);
  if (path === "/inventory/eoq") return success(inventoryRows.map((item) => ({ ...item, recommended_qty: Math.max(0, item.safety_stock - item.stock_qty + 20) })));
  if (path === "/pharmacy/eoq-suggestions") return success(inventoryRows.map((item) => ({ ...item, recommended_qty: Math.max(0, item.safety_stock - item.stock_qty + 20) })));
  if (path.startsWith("/pharmacy/purchase-order")) return success({ ok: true, status: "已提交", static_demo: true });
  if (path === "/stats/weekly-visits") return success(weeklyVisits);
  if (path === "/stats/today-revenue") return success(todayRevenue);
  if (path === "/stats/conversion-funnel") return success(conversionFunnel);
  if (path === "/stats/billing-ledger") return success(billingLedger);
  if (path === "/owners") return success(ownerRows);
  if (path.startsWith("/owners/")) return success(findById(ownerRows, path) || ownerRows[0]);
  if (path === "/pets") return success(petRows);
  if (path.startsWith("/pets/")) return success(findById(petRows, path) || petRows[0]);
  if (path === "/users") return success(Object.values(users));
  if (path === "/users/doctors") return success([users.doctor, { id: 202, username: "doctor2", role: "doctor", full_name: "李医生", clinic_id: "C001" }]);
  if (path === "/users/lab-techs") return success([users.lab_tech]);
  if (path === "/lab/pending-tests") return success(labOrders.filter((item) => item.status !== "已完成"));
  if (path === "/lab/results") return success(labResults);
  if (path === "/lab/stats") return success({ pending: 2, processing: 1, completed: 8, abnormal: 1 });
  if (path.startsWith("/lab/start-exam/")) return success({ status: "检查中", static_demo: true });
  if (path === "/nursing/vital-signs") return success({ ok: true, status: "已记录", static_demo: true });
  if (path === "/ai/rfm-warning") return success(rfmWarnings);
  if (path === "/ai/active-listener") return success({ active: true, status: "监听中" });
  if (path === "/ai/knowledge/retrieve") return success([{ title: "犬猫胃肠炎处置建议", score: 0.92, source: "静态知识库" }]);
  if (path === "/ai/full-diagnosis" || path === "/ai/multimodal-diagnosis") {
    return success({ diagnosis: "静态演示诊断：建议结合体征与检验结果复核", confidence: 0.88, risk_level: "中" });
  }
  if (path === "/ai/graph/viz") return success({ nodes: [{ id: "pet", label: "宠物" }, { id: "symptom", label: "症状" }], edges: [{ source: "pet", target: "symptom" }] });
  if (path === "/ai/graph/reasoning") return success({ conclusion: "静态演示推理完成", evidence: ["病史", "体征", "检验"] });
  if (path === "/federated/status") return success({ status: "running", clients: 3, accuracy: 0.91, rounds: 12 });
  if (path === "/scheduling/staff") return success(scheduleStaff);
  if (path === "/scheduling/assignments") return success(scheduleAssignments);
  if (path === "/scheduling/generate") return success(scheduleAssignments);
  if (path === "/owner-center/1" || path.startsWith("/owner-center/")) {
    return success({ owner: ownerRows[0], pets: petRows.filter((item) => item.owner_id === 1), visits: medicalRecords, rfm: rfmWarnings[0] });
  }
  if (path === "/adoption/pets") return success(adoptionPets);
  if (path.startsWith("/adoption/match/")) return success({ matches: ownerRows, top_score: 94, status: "已匹配" });
  if (path.startsWith("/adoption/dashboard/")) return success({ pet: adoptionPets[0], candidates: ownerRows, score: 94 });
  if (path === "/adoption/algorithm") return success({ model: "静态匹配模型", status: "ready", precision: 0.89 });
  if (path.startsWith("/adoption/match-status/")) return success({ status: "completed", progress: 100 });
  if (path.startsWith("/adoption/persona/")) return success({ persona: "亲人、安静、适合家庭陪伴" });
  if (path === "/data-center/tables") return success([{ name: "appointments", rows: appointments.length }, { name: "medical_records", rows: medicalRecords.length }]);
  if (path.startsWith("/data-center/table/")) return success({ rows: appointments, total: appointments.length });
  if (path.startsWith("/data-center/trace/medical-record/")) return success({ record: medicalRecords[0], pet: petRows[0], owner: ownerRows[0], timeline: medicalRecords });
  if (path === "/news") return success(newsRows);
  if (path.startsWith("/notifications/") || path === "/billing/settlement-complete") return success({ ok: true, static_demo: true });

  if (method !== "get") return success({ ok: true, static_demo: true, status: "success" });
  return success(getFallbackData(path));
}

function findById(items, path) {
  const id = Number(String(path).match(/\/(\d+)(?:\/[^/]*)?$/)?.[1] || 0);
  return items.find((item) => Number(item.id) === id);
}

function getFallbackData(path) {
  if (path.includes("stats") || path.includes("status") || path.includes("overview") || path.includes("dashboard")) {
    return { static_demo: true, status: "ready" };
  }
  if (/\/\d+(?:\/)?$/.test(path) || path.includes("/trace/")) {
    return { id: 1, static_demo: true, title: "静态演示记录", status: "正常" };
  }
  return [];
}
