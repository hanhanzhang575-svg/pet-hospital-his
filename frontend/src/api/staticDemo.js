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

  if (method !== "get" && method !== "post") return null;

  if (path === "/auth/me") return success(getStaticDemoUser());
  if (path === "/vet-workbench/queue") return success(appointments.filter((item) => item.status === "待诊"));
  if (path === "/appointments") return success(appointments);
  if (path === "/tasks/followup") return success(followupTasks);
  if (path === "/inpatient-records") return success(inpatientRecords);
  if (path === "/cages") return success(cages);
  if (path === "/prescriptions") return success(prescriptions);
  if (path === "/inventory/overview") return success(inventoryRows);
  if (path === "/inventory/expiry-warnings") return success([{ id: 1, name: "伊曲康唑胶囊", days_left: 18 }]);
  if (path === "/stats/weekly-visits") return success(weeklyVisits);
  if (path === "/stats/today-revenue") return success(todayRevenue);
  if (path === "/stats/conversion-funnel") return success(conversionFunnel);

  if (method === "post") return success({ ok: true, static_demo: true });
  return null;
}
