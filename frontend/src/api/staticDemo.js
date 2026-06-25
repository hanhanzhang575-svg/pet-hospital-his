const today = new Date().toISOString().slice(0, 10);
const DAY_MS = 24 * 60 * 60 * 1000;
const seed = Number(today.replace(/-/g, "")) || 20260625;
const random = mulberry32(seed);

const clinics = [
  { id: "C001", name: "沙河口院区", short: "沙河口" },
  { id: "C002", name: "甘井子院区", short: "甘井子" },
  { id: "C003", name: "高新园区", short: "高新园区" }
];

const doctors = [
  { id: 201, username: "doctor_zhang", role: "doctor", full_name: "张亦辰", doctor_name: "张亦辰", department: "综合门诊", clinic_id: "C001", avatar: "张" },
  { id: 202, username: "doctor_li", role: "doctor", full_name: "李明澈", doctor_name: "李明澈", department: "皮肤科", clinic_id: "C001", avatar: "李" },
  { id: 203, username: "doctor_wang", role: "doctor", full_name: "王嘉宁", doctor_name: "王嘉宁", department: "外科", clinic_id: "C002", avatar: "王" },
  { id: 204, username: "doctor_zhao", role: "doctor", full_name: "赵予安", doctor_name: "赵予安", department: "牙科", clinic_id: "C002", avatar: "赵" },
  { id: 205, username: "doctor_chen", role: "doctor", full_name: "陈若溪", doctor_name: "陈若溪", department: "眼科", clinic_id: "C003", avatar: "陈" },
  { id: 206, username: "doctor_sun", role: "doctor", full_name: "孙承宇", doctor_name: "孙承宇", department: "内科", clinic_id: "C003", avatar: "孙" }
];

const nurses = [
  { id: 301, username: "nurse_wang", role: "nurse", full_name: "王佳", clinic_id: "C001" },
  { id: 302, username: "nurse_liu", role: "nurse", full_name: "刘思雨", clinic_id: "C001" },
  { id: 303, username: "nurse_lin", role: "nurse", full_name: "林悦", clinic_id: "C002" },
  { id: 304, username: "nurse_xu", role: "nurse", full_name: "徐梓涵", clinic_id: "C002" },
  { id: 305, username: "nurse_zhou", role: "nurse", full_name: "周可心", clinic_id: "C003" }
];

const pharmacists = [
  { id: 401, username: "pharmacist_zhao", role: "pharmacist", full_name: "赵雪", clinic_id: "C001" },
  { id: 402, username: "pharmacist_gao", role: "pharmacist", full_name: "高芷晴", clinic_id: "C002" }
];

const labTechs = [
  { id: 501, username: "labtech_sun", role: "lab_tech", full_name: "孙超", clinic_id: "C001" },
  { id: 502, username: "labtech_he", role: "lab_tech", full_name: "何沐阳", clinic_id: "C003" }
];

const managers = [
  { id: 601, username: "manager_zhou", role: "manager", full_name: "周院长", clinic_id: "C001" },
  { id: 602, username: "manager_yang", role: "manager", full_name: "杨主任", clinic_id: "C002" }
];

const users = {
  receptionist: { id: 101, username: "receptionist1", role: "receptionist", full_name: "张悦", clinic_id: "C001" },
  doctor: doctors[0],
  nurse: nurses[0],
  pharmacist: pharmacists[0],
  pharmacy: pharmacists[0],
  lab_tech: labTechs[0],
  manager: managers[0],
  admin: { id: 701, username: "admin", role: "admin", full_name: "系统管理员", clinic_id: "C001" }
};

const allUsers = [users.receptionist, ...doctors, ...nurses, ...pharmacists, ...labTechs, ...managers, users.admin];

const ownerNames = [
  "张予安", "李明熙", "王可然", "赵梓涵", "陈景行", "刘诗雨", "孙若溪", "周嘉宁",
  "吴一诺", "郑沐辰", "冯思远", "蒋亦菲", "沈星河", "韩知夏", "杨乐言", "朱芷晴",
  "秦子墨", "许清越", "何念初", "吕承宇", "林书瑶", "高云深", "郭向晚", "马若白",
  "罗南枝", "梁言蹊", "宋安禾", "谢屿白", "唐清欢", "邓星眠", "胡景澄", "叶温言"
];

const ownerRows = ownerNames.map((name, index) => ({
  id: index + 1,
  name,
  phone: `13${8 + (index % 2)}${String(26000000 + index * 1739).slice(0, 8)}`,
  level: pickByIndex(["普通", "银卡", "金卡", "VIP", "复诊重点"], index),
  address: `${pickByIndex(["沙河口区", "甘井子区", "高新园区", "中山区", "西岗区"], index)} ${pickByIndex(["海桐街", "春柳路", "软件园路", "星海路", "黄河街"], index + 2)} ${18 + index} 号`,
  source_channel: pickByIndex(["自然到店", "老客转介绍", "小红书咨询", "社区活动", "领养合作"], index + 1),
  created_at: dateTime(-index - 5, 9 + (index % 8), (index * 7) % 60)
}));

const petNames = [
  "奶糖", "可乐", "团子", "栗子", "芝士", "布丁", "元宝", "年糕", "豆包", "小七",
  "摩卡", "花卷", "乌龙", "雪球", "桃桃", "米粒", "泡芙", "黑豆", "橘子", "可颂",
  "旺财", "糯米", "皮蛋", "十一", "小满", "椰椰", "豆乳", "阿福", "小鱼", "露娜",
  "拿铁", "小熊", "乐乐", "丸子", "芋圆", "多多", "麦兜", "米修", "闪电", "奥利奥",
  "灰灰", "木木", "贝贝", "饭团", "松子", "小鹿", "七喜", "白桃", "小八", "云朵"
];

const petRows = petNames.map((name, index) => {
  const species = pickByIndex(["猫", "犬", "猫", "犬", "兔"], index);
  const breed = species === "猫"
    ? pickByIndex(["英短", "布偶", "橘猫", "暹罗", "美短", "银渐层", "狸花"], index)
    : species === "犬"
      ? pickByIndex(["柯基", "柴犬", "泰迪", "金毛", "边牧", "比熊", "法斗"], index)
      : "垂耳兔";
  const owner = ownerRows[(index * 5) % ownerRows.length];
  const age = 1 + ((index * 3) % 12);
  return {
    id: index + 1,
    owner_id: owner.id,
    owner_name: owner.name,
    name,
    pet_name: name,
    species,
    breed,
    gender: index % 2 === 0 ? "雌" : "雄",
    age,
    pet_age_years: age,
    age_months: age * 12 + ((index * 2) % 11),
    weight: Number((species === "犬" ? 5 + randomBetween(1, 22) : species === "猫" ? 2.4 + randomBetween(0, 5) : 1.5 + randomBetween(0, 2)).toFixed(1)),
    sterilized: index % 3 !== 0,
    allergy_history: pickByIndex(["无", "青霉素慎用", "海鲜蛋白敏感", "疫苗后低热"], index + 3)
  };
});

const appointments = Array.from({ length: 72 }, (_, index) => {
  const pet = petRows[index % petRows.length];
  const clinic = clinics[index % clinics.length];
  const availableDoctors = doctors.filter((item) => item.clinic_id === clinic.id);
  const doctor = availableDoctors[index % availableDoctors.length] || doctors[index % doctors.length];
  const urgency = pickByIndex(["急诊", "优先", "常规", "常规", "复诊"], index);
  const status = pickByIndex(["待诊", "就诊中", "已完成", "待诊", "已取消", "已完成"], index + 1);
  return {
    id: index + 1,
    record_code: `BZH-OP-${today.replace(/-/g, "").slice(2)}-${String(index + 1).padStart(3, "0")}`,
    pet_id: pet.id,
    pet_name: pet.name,
    owner_id: pet.owner_id,
    owner_name: pet.owner_name,
    doctor_id: doctor.id,
    doctor_name: doctor.full_name,
    clinic_id: clinic.id,
    clinic_name: clinic.name,
    scheduled_time: dateTime((index % 9) - 3, 8 + (index % 10), (index * 13) % 60),
    urgency_level: urgency,
    status,
    department: doctor.department,
    pet_age_years: pet.age,
    priority_score: Math.min(98, 28 + (urgency === "急诊" ? 45 : urgency === "优先" ? 28 : 10) + ((index * 11) % 22))
  };
});

const cageStatusMix = ["空闲", "住院中", "空闲", "待清洁", "空闲", "待入院", "住院中", "维修"];
const cages = clinics.flatMap((clinic, clinicIndex) =>
  Array.from({ length: 48 }, (_, index) => {
    const id = clinicIndex * 100 + index + 1;
    const zone = pickByIndex(["犬区", "猫区", "VIP", "ICU", "隔离"], index + clinicIndex);
    const status = pickByIndex(cageStatusMix, index + clinicIndex * 3);
    const pet = petRows[(id * 7) % petRows.length];
    const cageCode = `${clinic.id}-${zone === "犬区" ? "D" : zone === "猫区" ? "C" : zone === "VIP" ? "V" : zone === "ICU" ? "I" : "Q"}${String(index + 1).padStart(2, "0")}`;
    return {
      id,
      code: cageCode,
      cage_code: cageCode,
      clinic_id: clinic.id,
      clinic_name: clinic.name,
      status,
      zone_type: zone,
      current_pet_id: ["住院中", "待入院"].includes(status) ? pet.id : null,
      adjacent_cage_ids: [id - 1, id + 1].filter((item) => item >= clinicIndex * 100 + 1 && item <= clinicIndex * 100 + 48)
    };
  })
);

const inpatientCages = cages.filter((item) => ["住院中", "待入院"].includes(item.status)).slice(0, 42);
const inpatientRecords = inpatientCages.map((cage, index) => {
  const pet = petRows.find((item) => item.id === cage.current_pet_id) || petRows[index % petRows.length];
  const doctor = doctors[index % doctors.length];
  const consumed = 180 + ((index * 137) % 2600);
  const deposit = consumed + pickByIndex([160, 420, 880, 1300, -120], index);
  return {
    id: index + 1,
    pet_id: pet.id,
    pet_name: pet.name,
    pet_species: pet.species,
    cage_id: cage.id,
    cage_code: cage.cage_code,
    clinic_id: cage.clinic_id,
    doctor_id: doctor.id,
    doctor_name: doctor.full_name,
    status: pickByIndex(["住院观察", "术后监护", "待入院", "住院中", "已出院"], index),
    admission_time: dateTime(-((index % 11) + 1), 9 + (index % 8), (index * 9) % 60),
    deposit_amount: Math.max(300, deposit),
    consumed_amount: consumed,
    deposit_balance: Math.max(-220, deposit - consumed),
    nursing_level: pickByIndex(["一级护理", "二级护理", "术后观察", "隔离观察"], index)
  };
});

const symptoms = [
  ["食欲下降", "轻微呕吐", "急性胃肠炎"],
  ["皮肤瘙痒", "局部脱毛", "过敏性皮炎"],
  ["精神沉郁", "体温升高", "上呼吸道感染"],
  ["跛行", "触诊疼痛", "软组织挫伤"],
  ["频繁排尿", "尿色偏深", "泌尿道炎症"],
  ["咳嗽", "运动后喘", "支气管炎"],
  ["牙龈红肿", "口臭明显", "牙周炎"],
  ["眼部分泌物", "畏光", "结膜炎"]
];

const medicalRecords = Array.from({ length: 58 }, (_, index) => {
  const appointment = appointments[index % appointments.length];
  const symptom = symptoms[index % symptoms.length];
  const doctor = doctors.find((item) => item.id === appointment.doctor_id) || doctors[index % doctors.length];
  return {
    id: index + 1,
    record_no: `MR-${today.replace(/-/g, "")}-${String(index + 1).padStart(4, "0")}`,
    appointment_id: appointment.id,
    pet_id: appointment.pet_id,
    pet_name: appointment.pet_name,
    owner_name: appointment.owner_name,
    vet_id: doctor.id,
    doctor_id: doctor.id,
    doctor_name: doctor.full_name,
    clinic_id: appointment.clinic_id,
    chief_complaint: `${symptom[0]}，伴随${symptom[1]}`,
    exam_notes: `体格检查：${symptom[1]}，精神状态${index % 4 === 0 ? "一般" : "尚可"}，建议结合检验复核。`,
    diagnosis: symptom[2],
    treatment_plan: pickByIndex(["补液观察 48 小时", "口服用药 5 天后复诊", "局部清创并限制活动", "完成检验后调整处方", "住院观察并监测体征"], index),
    status: pickByIndex(["已完成", "就诊中", "已归档", "已完成"], index),
    is_voided: index % 19 === 0,
    created_at: dateTime(-((index % 18) + 1), 9 + (index % 9), (index * 5) % 60)
  };
});

const testTypes = ["血常规", "生化检查", "皮肤刮片", "粪便检查", "尿液分析", "X光影像", "CRP炎症指标", "耳道镜检"];
const labOrders = Array.from({ length: 36 }, (_, index) => {
  const appointment = appointments[index % appointments.length];
  return {
    id: index + 1,
    appointment_id: appointment.id,
    pet_id: appointment.pet_id,
    pet_name: appointment.pet_name,
    owner_name: appointment.owner_name,
    clinic_id: appointment.clinic_id,
    test_type: pickByIndex(testTypes, index),
    status: pickByIndex(["待检", "检查中", "已完成", "待检"], index),
    priority: pickByIndex(["急诊", "优先", "常规"], index + 2),
    created_at: dateTime(-(index % 5), 8 + (index % 10), (index * 11) % 60)
  };
});

const labResults = labOrders
  .filter((item, index) => item.status === "已完成" || index % 3 === 0)
  .slice(0, 26)
  .map((item, index) => ({
    id: index + 1,
    order_id: item.id,
    appointment_id: item.appointment_id,
    pet_id: item.pet_id,
    pet_name: item.pet_name,
    clinic_id: item.clinic_id,
    test_type: item.test_type,
    result_summary: pickByIndex(["指标基本正常", "白细胞轻度升高", "提示轻度脱水", "皮肤样本见少量真菌孢子", "建议复查肝肾指标"], index),
    status: "已出报告",
    abnormal_count: index % 4,
    created_at: dateTime(-(index % 5), 10 + (index % 7), (index * 17) % 60)
  }));

const inventoryNames = [
  "阿莫西林克拉维酸钾", "犬猫复合维生素", "伊曲康唑胶囊", "泌尿道处方粮", "速诺片", "拜有利注射液",
  "宠物益生菌", "止吐宁", "眼康滴眼液", "耳肤灵", "驱虫滴剂", "关节营养膏", "术后敷料包", "留置针",
  "生理盐水", "乳酸林格液", "皮肤修复喷剂", "猫三联疫苗", "犬四联疫苗", "免疫球蛋白", "止痛针剂", "处方罐头",
  "血糖试纸", "一次性采血管", "麻醉耗材包", "牙科洁治套装", "消毒湿巾", "营养恢复粉"
];

const inventoryRows = inventoryNames.map((name, index) => {
  const safety = 18 + ((index * 7) % 36);
  const stock = Math.max(2, safety + pickByIndex([-16, -8, -2, 7, 18, 31], index));
  return {
    id: index + 1,
    drug_id: index + 1,
    name,
    drug_name: name,
    stock_qty: stock,
    safety_stock: safety,
    branch_code: clinics[index % clinics.length].id,
    unit: pickByIndex(["盒", "瓶", "袋", "支", "套"], index),
    supplier: pickByIndex(["瑞宠医药", "海恒供应链", "康牧生物", "北湾器械"], index),
    expire_date: dateOnly(20 + index * 9),
    daily_demand: 2 + (index % 8),
    price: Number((18 + randomBetween(3, 180)).toFixed(2))
  };
});

const prescriptions = Array.from({ length: 46 }, (_, index) => {
  const record = medicalRecords[index % medicalRecords.length];
  const items = [inventoryRows[index % inventoryRows.length], inventoryRows[(index + 5) % inventoryRows.length]];
  const amount = Number((items.reduce((sum, item) => sum + item.price, 0) + 36 + (index % 7) * 18).toFixed(2));
  return {
    id: index + 1,
    prescription_code: `RX-${today.replace(/-/g, "").slice(2)}-${String(index + 1).padStart(3, "0")}`,
    medical_record_id: record.id,
    pet_id: record.pet_id,
    pet_name: record.pet_name,
    owner_name: record.owner_name,
    doctor_name: record.doctor_name,
    clinic_id: record.clinic_id,
    status: pickByIndex(["已缴费", "待缴费", "已发药", "已缴费", "待缴费", "已失效"], index),
    amount,
    total_amount: amount,
    items: items.map((item) => ({ drug_id: item.drug_id, drug_name: item.drug_name, quantity: 1 + (index % 3), unit_price: item.price })),
    created_at: dateTime(-(index % 9), 10 + (index % 8), (index * 7) % 60),
    expire_at: dateTime(index % 6 === 0 ? -1 : 1 + (index % 3), 18, (index * 13) % 60)
  };
});

const purchaseTasks = inventoryRows
  .filter((item) => item.stock_qty <= item.safety_stock + 8)
  .slice(0, 18)
  .map((item, index) => ({
    id: index + 1,
    drug_id: item.drug_id,
    drug_name: item.drug_name,
    branch_code: item.branch_code,
    quantity: Math.max(12, item.safety_stock * 2 - item.stock_qty),
    status: pickByIndex(["待审批", "已通过", "采购中", "已驳回", "待审批"], index),
    priority: item.stock_qty < item.safety_stock ? "高" : "中",
    requester: pickByIndex(["赵雪", "高芷晴", "系统自动EOQ"], index),
    created_at: dateTime(-(index % 6), 9 + (index % 7), (index * 8) % 60)
  }));

const rfmWarnings = ownerRows.slice(0, 26).map((owner, index) => {
  const recency = 3 + ((index * 9) % 110);
  const frequency = 1 + ((index * 4) % 12);
  const monetary = 260 + ((index * 431) % 9200);
  const risk = recency > 75 ? "high" : recency > 35 ? "medium" : "low";
  return {
    owner_id: owner.id,
    owner_name: owner.name,
    phone: owner.phone,
    risk_level: risk,
    level: risk === "high" ? "高流失风险" : risk === "medium" ? "需主动关怀" : "健康活跃",
    segment_label: pickByIndex(["高价值沉睡客", "术后复诊提醒", "疫苗周期客户", "新客培育", "高频稳定客"], index),
    rfm_score: Math.max(18, 98 - recency * 0.42 + frequency * 1.6),
    score: Math.max(18, 98 - recency * 0.42 + frequency * 1.6),
    r_score: Math.max(1, 5 - Math.floor(recency / 25)),
    f_score: Math.min(5, 1 + Math.floor(frequency / 3)),
    m_score: Math.min(5, 1 + Math.floor(monetary / 1800)),
    recency_days: recency,
    frequency,
    monetary,
    last_invoice_at: dateTime(-recency, 14, (index * 4) % 60),
    suggestion: pickByIndex(["安排复诊提醒", "推送疫苗加强通知", "发送术后护理问候", "推荐年度体检套餐", "邀请参加领养公益日"], index)
  };
});

const followupTasks = rfmWarnings.slice(0, 24).map((item, index) => ({
  id: index + 1,
  owner_id: item.owner_id,
  owner_name: item.owner_name,
  phone: item.phone,
  status: pickByIndex(["待处理", "跟进中", "已预约", "已完成", "待处理"], index),
  topic: item.suggestion,
  risk_score: Number(item.rfm_score.toFixed(1)),
  risk_level: item.risk_level,
  recency_days: item.recency_days,
  frequency: item.frequency,
  monetary: item.monetary,
  due_at: dateTime(index % 4, 10 + (index % 7), 0),
  script_text: `您好${item.owner_name}，这里是白之助宠物医院，${item.suggestion}会更稳妥。`
}));

const scheduleDoctors = doctors.map((doctor) => ({ ...doctor }));
const scheduleStaff = {
  doctor: {
    count: scheduleDoctors.length,
    items: scheduleDoctors.map((doctor) => ({
      employee_id: doctor.id,
      employee_name: doctor.full_name,
      role_name: "doctor",
      clinic_id: doctor.clinic_id
    }))
  },
  nurse: {
    count: nurses.length,
    items: nurses.map((nurse) => ({
      employee_id: nurse.id,
      employee_name: nurse.full_name,
      role_name: "nurse",
      clinic_id: nurse.clinic_id
    }))
  }
};

const weekStart = getWeekStart(new Date(today));
const scheduleSlots = Array.from({ length: 7 }).flatMap((_, dayIndex) => {
  const date = dateFromBase(weekStart, dayIndex);
  return scheduleDoctors.flatMap((doctor, doctorIndex) =>
    ["morning", "afternoon"].map((period, periodIndex) => {
      const capacity = 9 + ((doctorIndex + periodIndex) % 5);
      const booked = Math.min(capacity, 3 + ((dayIndex * 3 + doctorIndex * 2 + periodIndex) % capacity));
      return {
        appointment_id: 9000 + dayIndex * 20 + doctorIndex * 2 + periodIndex,
        doctor_id: doctor.id,
        date,
        period,
        booked_count: booked,
        max_capacity: capacity,
        utilization_rate: Number(((booked / capacity) * 100).toFixed(1)),
        is_peak: booked / capacity > 0.78
      };
    })
  );
});

const shiftOrder = ["早班", "中班", "晚班"];
const scheduleAssignments = Array.from({ length: 7 }).flatMap((_, dayIndex) => {
  const date = dateFromBase(weekStart, dayIndex);
  return shiftOrder.flatMap((shift, shiftIndex) => [
    {
      assignment_id: 1 + dayIndex * 6 + shiftIndex * 2,
      employee_id: scheduleDoctors[(dayIndex + shiftIndex) % scheduleDoctors.length].id,
      employee_name: scheduleDoctors[(dayIndex + shiftIndex) % scheduleDoctors.length].full_name,
      role_name: "doctor",
      date,
      shift_id: shift,
      clinic_id: clinics[(dayIndex + shiftIndex) % clinics.length].id
    },
    {
      assignment_id: 2 + dayIndex * 6 + shiftIndex * 2,
      employee_id: nurses[(dayIndex + shiftIndex) % nurses.length].id,
      employee_name: nurses[(dayIndex + shiftIndex) % nurses.length].full_name,
      role_name: "nurse",
      date,
      shift_id: shift,
      clinic_id: clinics[(dayIndex + shiftIndex + 1) % clinics.length].id
    }
  ]);
});

const coordinationOverview = clinics.map((clinic, index) => ({
  clinic_id: clinic.id,
  clinic_name: clinic.name,
  doctor_load: pickByIndex(["高", "中", "低"], index),
  cage_idle: cages.filter((item) => item.clinic_id === clinic.id && item.status === "空闲").length,
  daily_completed_visits: appointments.filter((item) => item.clinic_id === clinic.id && item.status === "已完成").length + 28 + index * 7,
  daily_surgeries: 1 + index,
  inventory_risk: pickByIndex(["中", "低", "高"], index)
}));

const coordinationReferrals = Array.from({ length: 9 }, (_, index) => {
  const pet = petRows[(index * 4) % petRows.length];
  const from = clinics[index % clinics.length];
  const to = clinics[(index + 1) % clinics.length];
  const target = cages.find((item) => item.clinic_id === to.id && item.status === "空闲") || cages[index];
  return {
    id: index + 1,
    pet_name: pet.name,
    from_clinic_name: from.name,
    to_clinic_name: to.name,
    target_cage_code: target.cage_code,
    reason: pickByIndex(["术后观察床位调剂", "专家门诊转诊", "隔离笼舍需求", "影像设备排期更快"], index),
    eta_time: dateTime(0, 13 + (index % 6), (index * 10) % 60),
    status: pickByIndex(["待接收", "已接收", "已完成"], index)
  };
});

const adoptionPets = Array.from({ length: 14 }, (_, index) => {
  const species = pickByIndex(["猫", "犬"], index);
  return {
    id: index + 1,
    pet_name: pickByIndex(["豆包", "小七", "橙子", "山竹", "贝果", "芝麻", "小葵", "云吞", "琥珀", "小满", "蓝莓", "雪糕", "花生", "白露"], index),
    name: pickByIndex(["豆包", "小七", "橙子", "山竹", "贝果", "芝麻", "小葵", "云吞", "琥珀", "小满", "蓝莓", "雪糕", "花生", "白露"], index),
    species,
    breed: species === "猫" ? pickByIndex(["橘猫", "狸花", "英短", "三花"], index) : pickByIndex(["田园犬", "柯基", "比熊", "边牧"], index),
    age_months: 4 + ((index * 5) % 48),
    energy_level: pickByIndex(["低", "中", "高"], index),
    medical_need: pickByIndex(["低", "中", "低", "高"], index),
    adoption_priority: 1 + (index % 5),
    status: "待领养",
    match_score: 72 + ((index * 7) % 25)
  };
});

const billingLedger = Array.from({ length: 36 }, (_, index) => {
  const appointment = appointments[index % appointments.length];
  const hasSurgery = index % 8 === 0;
  return {
    id: index + 1,
    record_code: appointment.record_code,
    pet_name: appointment.pet_name,
    owner_name: appointment.owner_name,
    clinic_id: appointment.clinic_id,
    item_type: pickByIndex(["诊疗", "药品", "检验", "住院", "手术"], index),
    type: pickByIndex(["诊疗", "药品", "检验", "住院", "手术"], index),
    amount: 90 + ((index * 73) % 1800),
    payment_method: pickByIndex(["微信支付", "支付宝", "现金", "会员卡"], index),
    status: pickByIndex(["已收费", "待收费", "已退费", "已收费"], index),
    has_surgery: hasSurgery,
    has_anesthesia_fee: !hasSurgery || index % 3 !== 0,
    has_consumable_fee: !hasSurgery || index % 4 !== 0,
    created_at: dateTime(-(index % 12), 9 + (index % 9), (index * 6) % 60)
  };
});

const weeklyVisits = {
  dates: Array.from({ length: 7 }, (_, index) => dateFromBase(weekStart, index).slice(5)),
  series: clinics.map((clinic, clinicIndex) => ({
    name: clinic.name,
    data: Array.from({ length: 7 }, (_, dayIndex) => 34 + clinicIndex * 9 + ((dayIndex * 7 + clinicIndex * 5) % 24))
  }))
};

const todayRevenue = [
  { name: "诊疗", value: sumBy(billingLedger.filter((item) => item.item_type === "诊疗"), "amount") || 12680 },
  { name: "药品", value: sumBy(billingLedger.filter((item) => item.item_type === "药品"), "amount") || 8420 },
  { name: "检验", value: sumBy(billingLedger.filter((item) => item.item_type === "检验"), "amount") || 5360 },
  { name: "住院", value: sumBy(billingLedger.filter((item) => item.item_type === "住院"), "amount") || 3880 },
  { name: "手术", value: sumBy(billingLedger.filter((item) => item.item_type === "手术"), "amount") || 6680 }
];

const conversionFunnel = [
  { name: "到院咨询", value: 286 },
  { name: "完成挂号", value: 218 },
  { name: "完成诊疗", value: 176 },
  { name: "处方结算", value: 142 },
  { name: "复诊预约", value: 84 }
];

const newsRows = [
  { id: 1, title: "白之助春季义诊周开放预约（疫苗+体检）", category: "院内通知", summary: "前台可直接创建义诊预约，三院区共享名额。", source_name: "白之助运营中心", published_at: "2026-04-10" },
  { id: 2, title: "猫咪应激期 72 小时观察法", category: "养宠妙招", summary: "固定喂食、隐藏处和猫砂位置可降低应激。", source_name: "白之助猫科门诊", published_at: "2026-04-08" },
  { id: 3, title: "夏季犬只皮肤病高发提醒", category: "健康科普", summary: "洗澡频率、驱虫周期和皮肤检查建议同步更新。", source_name: "皮肤科小组", published_at: "2026-04-06" },
  { id: 4, title: "术后住院押金预警规则升级", category: "运营公告", summary: "低余额账单将自动提醒前台回访和补缴。", source_name: "系统管理员", published_at: "2026-04-03" }
];

export function isStaticDemoEnabled() {
  return import.meta.env.VITE_STATIC_DEMO === "1" || window.sessionStorage.getItem("static_demo") === "1";
}

export function getStaticDemoUser(role = getCurrentDemoRole()) {
  return users[role] || users.doctor;
}

export function getStaticDemoResponse(config) {
  const method = String(config?.method || "get").toLowerCase();
  const path = getPath(config);
  const params = getParams(config);

  if (!["get", "post", "put", "delete", "patch"].includes(method)) return success({ ok: true, static_demo: true });

  if (path === "/auth/me") return success(getStaticDemoUser());
  if (path === "/vet-workbench/queue") return success(filterByClinic(appointments, params).filter((item) => ["待诊", "就诊中"].includes(item.status)).slice(0, 24));
  if (path === "/vet-workbench/medical-record" && method !== "get") return success({ ...medicalRecords[0], id: medicalRecords.length + 1, status: "已保存" });
  if (path === "/vet-workbench/medical-records") {
    const rows = filterMedicalRecords(params);
    const pageRows = paginate(rows, params);
    return { ...success(pageRows), total: rows.length };
  }
  if (path.startsWith("/vet-workbench/medical-record/") && path.endsWith("/void")) return success({ ok: true, status: "已作废" });
  if (path.startsWith("/vet-workbench/medical-record/")) return success(findById(medicalRecords, path) || medicalRecords[0]);
  if (path.startsWith("/vet-workbench/pet-history/")) return success(buildPetHistory(path));
  if (path.startsWith("/vet-workbench/start/")) return success({ status: "就诊中", appointment: appointments[0] });

  if (path === "/appointments") {
    if (method !== "get") return success({ ...appointments[0], id: appointments.length + 1, status: "待诊" });
    return success(paginate(filterAppointments(params), params));
  }
  if (path === "/appointments/schedule/week") return success({ doctors: scheduleDoctors, slots: scheduleSlots });
  if (path === "/appointments/schedule/peak-prediction") return success(scheduleSlots.filter((item) => item.is_peak).map((item) => ({ appointment_id: item.appointment_id })));
  if (path === "/appointments/schedule/recommendations") {
    return success({
      recommendations: [
        { priority: "high", doctor_name: "李明澈", message: "沙河口上午高峰明显，建议开放下午加号并提前分诊。" },
        { priority: "medium", doctor_name: "王嘉宁", message: "甘井子院区外科住院笼舍紧张，可将慢病复诊分流至高新园区。" },
        { priority: "low", doctor_name: "赵予安", message: "牙科下午仍有 3 个空余号源，可推送洁牙活动提醒。" }
      ]
    });
  }
  if (path.includes("/appointments/schedule/") && path.endsWith("/patients")) return success(appointments.slice(0, 8));
  if (path.startsWith("/appointments/schedule/") || path === "/appointments/schedule/create" || path === "/appointments/schedule/copy-last-week") return success({ ok: true, count: 8 });

  if (path === "/tasks/followup") return method === "get" ? success(filterByStatus(followupTasks, params).slice(0, 80)) : success({ count: 5, ok: true });
  if (path === "/tasks/purchase") return method === "get" ? success(filterByStatus(purchaseTasks, params).slice(0, 80)) : success({ count: 6, ok: true });
  if (path.startsWith("/tasks/purchase/") || path.startsWith("/tasks/followup/")) return success({ ok: true, status: "已更新" });
  if (path === "/tasks/coordination/overview") return success(coordinationOverview);
  if (path === "/tasks/coordination/referrals") return success(coordinationReferrals);
  if (path === "/tasks/coordination/available-cages") return success(filterCages({ ...params, status: "空闲" }).slice(0, 16));
  if (path.startsWith("/tasks/coordination/")) return success({ ok: true, status: "已提交" });

  if (path === "/inpatient-records/allocate-cage") return success(filterCages({ ...params, status: "空闲" })[0] || cages.find((item) => item.status === "空闲"));
  if (path === "/inpatient-records") return method === "get" ? success(filterInpatientRecords(params)) : success({ ...inpatientRecords[0], id: inpatientRecords.length + 1 });
  if (path.startsWith("/inpatient-records/") && path.endsWith("/nursing-logs")) return success(nursingLogsForRecord(path));
  if (path.startsWith("/inpatient-records/")) return success(findById(inpatientRecords, path) || inpatientRecords[0]);
  if (path === "/cages") return success(filterCages(params));

  if (path === "/prescriptions") return success(filterPrescriptions(params));
  if (path.startsWith("/prescriptions/")) return success(findById(prescriptions, path) || prescriptions[0]);
  if (path === "/billing/urge-payment" || path === "/billing/settlement-complete") return success({ ok: true, static_demo: true });

  if (path === "/inventory/overview") return success(filterInventory(params));
  if (path === "/inventory/expiry-warnings") return success(inventoryRows.filter((item) => daysUntil(item.expire_date) <= Number(params.warning_days || 30)).slice(0, 12));
  if (path === "/inventory/eoq") {
    if (method !== "get") return success({ eoq: 86, reorder_point: 25, safety_stock: 18 });
    return success(eoqRows());
  }
  if (path === "/pharmacy/eoq-suggestions") {
    return success({
      rows: eoqRows(),
      seasonal_alpha: 1.18,
      aggregate_trend: Array.from({ length: 60 }, (_, index) => 22 + Math.round(Math.sin(index / 5) * 6 + (index % 7))),
      reorder_marker_index: 38
    });
  }
  if (path.startsWith("/pharmacy/purchase-order")) return success({ ok: true, count: purchaseTasks.length, status: "已提交", static_demo: true });

  if (path === "/stats/weekly-visits") return success(weeklyVisits);
  if (path === "/stats/today-revenue") return success(todayRevenue);
  if (path === "/stats/conversion-funnel") return success(conversionFunnel);
  if (path === "/stats/billing-ledger") return success(filterByClinic(billingLedger, params));

  if (path === "/owners") return success(ownerRows);
  if (path.startsWith("/owners/")) return success(findById(ownerRows, path) || ownerRows[0]);
  if (path === "/pets") return success(filterPets(params));
  if (path.startsWith("/pets/")) return success(findById(petRows, path) || petRows[0]);

  if (path === "/users") return success(allUsers);
  if (path === "/users/doctors") return success(filterByClinic(doctors, params));
  if (path === "/users/lab-techs") return success(filterByClinic(labTechs, params));

  if (path === "/lab/pending-tests") return success(filterByClinic(labOrders, params).filter((item) => item.status !== "已完成"));
  if (path === "/lab/results") return success(filterByClinic(labResults, params));
  if (path === "/lab/stats") {
    const clinicOrders = filterByClinic(labOrders, params);
    const clinicResults = filterByClinic(labResults, params);
    return success({
      pending: clinicOrders.filter((item) => item.status === "待检").length,
      in_progress: clinicOrders.filter((item) => item.status === "检查中").length,
      processing: clinicOrders.filter((item) => item.status === "检查中").length,
      completed: clinicResults.length,
      completed_today: clinicResults.length,
      abnormal: clinicResults.filter((item) => item.abnormal_count > 0).length
    });
  }
  if (path.startsWith("/lab/start-exam/")) return success({ status: "检查中", static_demo: true });
  if (path === "/lab/submit-result") return success({ ok: true, status: "已出报告" });
  if (path === "/nursing/vital-signs") return success({ ok: true, status: "已记录", static_demo: true });

  if (path === "/ai/rfm-warning") return success(rfmWarnings);
  if (path === "/rfm/create-followup-tasks") return success({ count: 8, ok: true });
  if (path === "/ai/active-listener") return success({ active: true, status: "监听中", transcript_count: 18 });
  if (path === "/ai/knowledge/retrieve") return success([
    { title: "犬猫胃肠炎处置建议", score: 0.92, source: "静态知识库" },
    { title: "术后住院体征监测路径", score: 0.88, source: "护理SOP" },
    { title: "皮肤瘙痒鉴别诊断流程", score: 0.84, source: "皮肤科指南" }
  ]);
  if (path === "/ai/full-diagnosis" || path === "/ai/multimodal-diagnosis") {
    return success({ diagnosis: "静态演示诊断：疑似胃肠炎合并轻度脱水，建议结合体征与检验结果复核", confidence: 0.88, risk_level: "中" });
  }
  if (path === "/ai/graph/viz") return success(buildKnowledgeGraph());
  if (path === "/ai/graph/reasoning") return success({ conclusion: "推理完成：症状、病史与检验结果支持当前诊断路径", evidence: ["病史", "体征", "检验", "用药记录"] });
  if (path === "/federated/status") return success(buildFederatedStatus());

  if (path === "/scheduling/staff") return success(scheduleStaff);
  if (path === "/scheduling/assignments") return { ...success(scheduleAssignments), meta: { staff: scheduleStaff } };
  if (path === "/scheduling/generate") return { ...success({ assignments: scheduleAssignments, staff: scheduleStaff }), message: "静态演示排班已生成" };

  if (path.startsWith("/owner-center/")) return success(buildOwnerCenter(path));
  if (path === "/adoption/pets") return success(adoptionPets);
  if (path.startsWith("/adoption/match/")) return success(buildAdoptionMatch(path));
  if (path.startsWith("/adoption/dashboard/")) return success(buildAdoptionDashboard(path));
  if (path === "/adoption/algorithm") return success({
    model_version: "PACI-MCDA v2.6-demo",
    summary: "融合距离、住房、经验、陪伴时间、预算与医疗照护能力的多准则领养匹配模型。",
    weights: { 距离: "18%", 经验: "22%", 住房: "16%", 医疗: "18%", 陪伴: "14%", 预算: "12%" }
  });
  if (path.startsWith("/adoption/match-status/")) return success({ state: "completed", mode: "full", processed: 200, total: 200, progress: 100 });
  if (path.startsWith("/adoption/persona/")) return success(buildAdoptionPersona());

  if (path === "/data-center/tables") return success(["owners", "pets", "appointments", "medical_records", "inpatient_records", "prescriptions", "inventory"]);
  if (path.startsWith("/data-center/table/")) return success(buildDataCenterTable(path, params));
  if (path.startsWith("/data-center/trace/medical-record/")) return success(buildTrace(path));
  if (path === "/news") return success(newsRows);
  if (path.startsWith("/notifications/")) return success({ ok: true, static_demo: true });

  if (method !== "get") return success({ ok: true, static_demo: true, status: "success", count: 1 });
  return success(getFallbackData(path));
}

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
    return url.replace(/^\/api\/v1/, "").split("?")[0];
  }
}

function getParams(config) {
  const params = { ...(config?.params || {}) };
  try {
    const url = new URL(String(config?.url || ""), "http://demo.local");
    url.searchParams.forEach((value, key) => {
      if (params[key] === undefined) params[key] = value;
    });
  } catch {
    // Ignore malformed demo URLs.
  }
  return params;
}

function filterByClinic(rows, params = {}) {
  const clinicId = params.clinic_id || params.branch_code;
  if (!clinicId) return rows;
  return rows.filter((item) => !item.clinic_id || item.clinic_id === clinicId || item.branch_code === clinicId);
}

function filterByStatus(rows, params = {}) {
  const status = params.status;
  if (!status) return rows;
  return rows.filter((item) => item.status === status);
}

function filterAppointments(params = {}) {
  return paginateSource(
    filterByStatus(filterByClinic(appointments, params), params)
      .filter((item) => !params.pet_id || Number(item.pet_id) === Number(params.pet_id))
      .filter((item) => !params.doctor_id || Number(item.doctor_id) === Number(params.doctor_id))
      .sort((a, b) => String(b.scheduled_time).localeCompare(String(a.scheduled_time))),
    params
  );
}

function filterMedicalRecords(params = {}) {
  return medicalRecords
    .filter((item) => !params.pet_id || Number(item.pet_id) === Number(params.pet_id))
    .filter((item) => !params.vet_id || Number(item.vet_id || item.doctor_id) === Number(params.vet_id))
    .sort((a, b) => String(b.created_at).localeCompare(String(a.created_at)));
}

function filterCages(params = {}) {
  return filterByClinic(cages, params)
    .filter((item) => !params.zone_type || item.zone_type === params.zone_type)
    .filter((item) => !params.status || item.status === params.status);
}

function filterInpatientRecords(params = {}) {
  return filterByClinic(inpatientRecords, params)
    .filter((item) => !params.medical_record_id || Number(item.medical_record_id) === Number(params.medical_record_id));
}

function filterInventory(params = {}) {
  return filterByClinic(inventoryRows, params);
}

function filterPrescriptions(params = {}) {
  return filterByClinic(prescriptions, params)
    .filter((item) => !params.medical_record_id || Number(item.medical_record_id) === Number(params.medical_record_id));
}

function filterPets(params = {}) {
  return petRows.filter((item) => !params.owner_id || Number(item.owner_id) === Number(params.owner_id));
}

function paginateSource(rows, params = {}) {
  const offset = Number(params.offset || 0);
  const limit = Number(params.limit || 0);
  if (!limit) return rows;
  return rows.slice(offset, offset + limit);
}

function paginate(rows, params = {}) {
  const page = Number(params.page || 0);
  const size = Number(params.size || 0);
  if (page && size) return rows.slice((page - 1) * size, page * size);
  return paginateSource(rows, params);
}

function findById(items, path) {
  const id = Number(String(path).match(/\/(\d+)(?:\/[^/]*)?$/)?.[1] || 0);
  return items.find((item) => Number(item.id) === id);
}

function buildPetHistory(path) {
  const petId = Number(String(path).match(/\/(\d+)$/)?.[1] || 1);
  const pet = petRows.find((item) => item.id === petId) || petRows[0];
  const owner = ownerRows.find((item) => item.id === pet.owner_id) || ownerRows[0];
  const timeline = medicalRecords.filter((item) => item.pet_id === pet.id).slice(0, 8);
  return {
    pet_profile: { ...pet, owner_name: owner.name, owner_phone: owner.phone },
    timeline: timeline.length ? timeline : medicalRecords.slice(0, 5)
  };
}

function nursingLogsForRecord(path) {
  const id = Number(String(path).match(/inpatient-records\/(\d+)/)?.[1] || 1);
  const record = inpatientRecords.find((item) => item.id === id) || inpatientRecords[0];
  return Array.from({ length: 5 }, (_, index) => ({
    id: id * 10 + index,
    inpatient_record_id: id,
    pet_name: record.pet_name,
    temperature: Number((38.2 + (index % 4) * 0.25).toFixed(1)),
    heart_rate: 98 + index * 8,
    respiration: 22 + index * 2,
    status: index % 4 === 3 ? "异常" : "正常",
    notes: pickByIndex(["精神尚可，少量进食", "术口干燥，继续观察", "补液后状态改善", "夜间轻微躁动"], index),
    created_at: dateTime(-index, 8 + index, 20)
  }));
}

function eoqRows() {
  return inventoryRows.map((item, index) => ({
    ...item,
    recommended_qty: Math.max(0, item.safety_stock * 2 - item.stock_qty + 12),
    eoq: 60 + ((index * 9) % 45),
    reorder_point: item.safety_stock + 8,
    annual_demand: item.daily_demand * 365
  }));
}

function buildOwnerCenter(path) {
  const ownerId = Number(String(path).match(/\/(\d+)$/)?.[1] || 1);
  const owner = ownerRows.find((item) => item.id === ownerId) || ownerRows[0];
  const pets = petRows.filter((item) => item.owner_id === owner.id);
  const bills = billingLedger.filter((item, index) => index % ownerRows.length === (owner.id - 1) % ownerRows.length).slice(0, 8);
  const rfm = rfmWarnings.find((item) => item.owner_id === owner.id) || rfmWarnings[0];
  return {
    owner,
    my_pets: pets,
    medical_bills: bills,
    billing_trend: Array.from({ length: 8 }, (_, index) => ({ month: `${index + 1}月`, amount: 260 + ((owner.id * 71 + index * 123) % 1800) })),
    adoption_top_recommendations: adoptionPets.slice(owner.id % 5, owner.id % 5 + 5).map((pet, index) => ({ ...pet, score: 96 - index * 4 })),
    owner_kpis: {
      total_spend: sumBy(bills, "amount"),
      visit_count: appointments.filter((item) => item.owner_id === owner.id).length,
      pet_count: pets.length,
      last_visit_days: rfm.recency_days
    },
    rfm_profile: rfm
  };
}

function buildAdoptionMatch(path) {
  const petId = Number(String(path).match(/\/(\d+)$/)?.[1] || 1);
  const rows = ownerRows.slice(0, 30).map((owner, index) => ({
    adopter_id: owner.id,
    adopter_name: owner.name,
    total_score: Number((96 - index * 1.7 + (petId % 5)).toFixed(1)),
    recommendation_confidence: Number((0.92 - index * 0.008).toFixed(2)),
    predicted_speed_days: 2 + (index % 18),
    speed_level: index < 6 ? "极速领养" : index < 18 ? "稳妥跟进" : "长期培育",
    rationale: `${owner.name} 的住房、陪伴时间和预算与当前宠物画像匹配度较高。`
  }));
  return {
    rows,
    status: { state: "completed", mode: "fast", processed: 200, total: 200 }
  };
}

function buildAdoptionDashboard(path) {
  const match = buildAdoptionMatch(path).rows;
  const top = match.slice(0, 10);
  return {
    overview: { candidate_count: ownerRows.length, avg_score: 84.6, fast_ratio: 0.31, hard_blocked_ratio: 0.08 },
    top_matches: top,
    radar: [
      { name: "距离", value: 88 },
      { name: "经验", value: 92 },
      { name: "住房", value: 84 },
      { name: "医疗", value: 78 },
      { name: "陪伴", value: 90 },
      { name: "预算", value: 86 }
    ],
    scatter: match.slice(0, 24).map((item) => ({ name: item.adopter_name, score: item.total_score, speed_days: item.predicted_speed_days, confidence: item.recommendation_confidence })),
    speed_distribution: [
      { name: "极速领养", value: 9 },
      { name: "稳妥跟进", value: 14 },
      { name: "长期培育", value: 7 }
    ],
    score_breakdown_mean: [
      { name: "距离", value: 18 },
      { name: "经验", value: 22 },
      { name: "住房", value: 16 },
      { name: "医疗", value: 18 },
      { name: "陪伴", value: 14 },
      { name: "预算", value: 12 }
    ]
  };
}

function buildAdoptionPersona() {
  return {
    top_personas: ownerRows.slice(0, 12).map((owner, index) => ({
      adopter_name: owner.name,
      experience_level: pickByIndex(["新手", "有经验", "资深"], index),
      housing_type: pickByIndex(["公寓", "住宅", "别墅"], index),
      budget: 600 + ((index * 230) % 4200),
      housing_area: 58 + ((index * 13) % 120),
      available_hours: Number((2.5 + (index % 7) * 0.8).toFixed(1))
    })),
    histograms: {
      experience: [{ name: "新手", value: 9 }, { name: "有经验", value: 15 }, { name: "资深", value: 8 }],
      housing_type: [{ name: "公寓", value: 16 }, { name: "住宅", value: 12 }, { name: "别墅", value: 4 }]
    },
    geo_points: ownerRows.slice(0, 20).map((owner, index) => ({ name: owner.name, lng: 121.52 + index * 0.012, lat: 38.86 + (index % 7) * 0.018, score: 72 + (index % 20) }))
  };
}

function buildDataCenterTable(path, params) {
  const tableName = decodeURIComponent(String(path).split("/").pop() || "appointments");
  const sourceMap = {
    owners: ownerRows,
    pets: petRows,
    appointments,
    medical_records: medicalRecords,
    inpatient_records: inpatientRecords,
    prescriptions,
    inventory: inventoryRows
  };
  const rows = sourceMap[tableName] || appointments;
  const pageRows = paginate(rows, params);
  const columns = Object.keys(rows[0] || {}).filter((key) => !Array.isArray(rows[0]?.[key]) && typeof rows[0]?.[key] !== "object");
  return {
    columns,
    pk_columns: ["id"],
    fk_columns: columns.filter((col) => col.endsWith("_id")),
    rows: pageRows,
    total: rows.length
  };
}

function buildTrace(path) {
  const record = findById(medicalRecords, path) || medicalRecords[0];
  const pet = petRows.find((item) => item.id === record.pet_id) || petRows[0];
  const owner = ownerRows.find((item) => item.id === pet.owner_id) || ownerRows[0];
  return {
    record_id: record.id,
    pet_id: pet.id,
    pet_name: pet.name,
    pet_species: pet.species,
    owner_id: owner.id,
    owner_name: owner.name
  };
}

function buildKnowledgeGraph() {
  return {
    nodes: [
      { id: "pet", label: "宠物" },
      { id: "symptom", label: "症状" },
      { id: "test", label: "检验" },
      { id: "diagnosis", label: "诊断" },
      { id: "rx", label: "处方" },
      { id: "followup", label: "复诊" }
    ],
    edges: [
      { source: "pet", target: "symptom" },
      { source: "symptom", target: "test" },
      { source: "test", target: "diagnosis" },
      { source: "diagnosis", target: "rx" },
      { source: "rx", target: "followup" }
    ]
  };
}

function buildFederatedStatus() {
  return {
    status: "running",
    clients: clinics.length,
    accuracy: 0.914,
    rounds: 18,
    clinics: clinics.map((clinic, index) => ({
      id: clinic.id,
      name: clinic.name,
      samples: 320 + index * 148,
      auc: Number((0.89 + index * 0.017).toFixed(3))
    }))
  };
}

function getFallbackData(path) {
  if (path.includes("stats") || path.includes("status") || path.includes("overview") || path.includes("dashboard")) {
    return { static_demo: true, status: "ready", count: 12 };
  }
  if (/\/\d+(?:\/)?$/.test(path) || path.includes("/trace/")) {
    return { id: 1, static_demo: true, title: "静态演示记录", status: "正常" };
  }
  return Array.from({ length: 12 }, (_, index) => ({ id: index + 1, name: `演示数据 ${index + 1}`, status: "正常" }));
}

function mulberry32(value) {
  return function next() {
    let t = (value += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function randomBetween(min, max) {
  return min + random() * (max - min);
}

function pickByIndex(items, index) {
  return items[Math.abs(index) % items.length];
}

function dateTime(dayOffset = 0, hour = 9, minute = 0) {
  const date = new Date(new Date(today).getTime() + dayOffset * DAY_MS);
  date.setHours(hour, minute, 0, 0);
  return `${dateOnlyFromDate(date)}T${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}:00`;
}

function dateOnly(dayOffset = 0) {
  return dateOnlyFromDate(new Date(new Date(today).getTime() + dayOffset * DAY_MS));
}

function dateOnlyFromDate(date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}

function dateFromBase(baseDate, dayOffset = 0) {
  return dateOnlyFromDate(new Date(baseDate.getTime() + dayOffset * DAY_MS));
}

function getWeekStart(date) {
  const current = new Date(date);
  const day = current.getDay() || 7;
  current.setDate(current.getDate() - day + 1);
  current.setHours(0, 0, 0, 0);
  return current;
}

function daysUntil(dateValue) {
  return Math.ceil((new Date(dateValue).getTime() - new Date(today).getTime()) / DAY_MS);
}

function sumBy(rows, key) {
  return rows.reduce((sum, item) => sum + Number(item[key] || 0), 0);
}
