# 白之助宠物医院系统 - 数据库SQL文档

## 一、数据库概览

- **数据库类型**: SQLite 3
- **数据库名**: shironosuke.db
- **存储模式**: WAL（Write-Ahead Logging）模式
- **外键约束**: 启用（PRAGMA foreign_keys=ON）
- **表数量**: 23张核心业务表

---

## 二、核心数据表及主外键设计

### 1. 角色表 (roles)
```sql
CREATE TABLE roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) UNIQUE NOT NULL,
    description VARCHAR(255) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
-- 主键: id
-- 唯一索引: name
-- 业务说明: 定义系统角色，如医生、护士、出纳、管理员、主人等
```

### 2. 用户表 (users)
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_code VARCHAR(20) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role_id INTEGER NOT NULL,
    branch_code VARCHAR(10) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    is_licensed_vet BOOLEAN NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id)
);
-- 主键: id
-- 外键: role_id → roles.id
-- 唯一索引: employee_code, username
-- 业务说明: 系统操作员，包括医生、护士、管理员等
-- 关键字段: is_licensed_vet表示是否持证兽医，影响诊疗权限
```

### 3. 宠物主人表 (owners)
```sql
CREATE TABLE owners (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    telephone VARCHAR(20) NULL,
    id_card VARCHAR(30) NULL,
    address VARCHAR(255) NULL,
    member_level VARCHAR(20) NOT NULL DEFAULT 'normal',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
-- 主键: id
-- 唯一索引: owner_code
-- 业务说明: 宠物的所有者，一对多关系（一个主人可拥有多个宠物）
-- 关键字段: member_level用于区分会员等级，影响费用折扣和优先级
```

### 4. 宠物档案表 (pets)
```sql
CREATE TABLE pets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pet_code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    species VARCHAR(20) NOT NULL,
    breed VARCHAR(50) NULL,
    gender VARCHAR(10) NULL,
    birth_date DATE NULL,
    color VARCHAR(100) NULL,
    type_id INTEGER NULL,
    weight FLOAT NULL,
    allergy_history JSON NOT NULL DEFAULT '[]',
    owner_id INTEGER NOT NULL,
    clinic_id VARCHAR(10) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES owners(id)
);
-- 主键: id
-- 外键: owner_id → owners.id
-- 唯一索引: pet_code
-- 业务说明: 宠物患者基础档案，每只宠物一条记录
-- 关键字段: allergy_history为JSON数组，记录已知过敏信息
```

### 5. 预约挂号表 (appointments)
```sql
CREATE TABLE appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_code VARCHAR(30) UNIQUE NOT NULL,
    pet_id INTEGER NOT NULL,
    doctor_id INTEGER NOT NULL,
    clinic_id VARCHAR(10) NOT NULL,
    scheduled_time DATETIME NOT NULL,
    urgency_level VARCHAR(20) NOT NULL DEFAULT '常规',
    status VARCHAR(20) NOT NULL DEFAULT '待诊',
    priority_score FLOAT NOT NULL DEFAULT 0,
    max_capacity INTEGER NOT NULL DEFAULT 10,
    is_leave BOOLEAN NOT NULL DEFAULT 0,
    schedule_note VARCHAR(255) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pet_id) REFERENCES pets(id),
    FOREIGN KEY (doctor_id) REFERENCES users(id),
    UNIQUE (doctor_id, scheduled_time)
);
-- 主键: id
-- 外键: pet_id → pets.id, doctor_id → users.id
-- 唯一约束: (doctor_id, scheduled_time) 保证医生同一时段只有一个预约
-- 业务说明: 门诊预约，绑定宠物、医生、时间
-- 关键字段: 
--   - urgency_level: 常规、加急、急诊
--   - priority_score: 动态计算的优先级
--   - status: 待诊、就诊中、已完成、已取消
```

### 6. 就诊记录表 (visits)
```sql
CREATE TABLE visits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pet_id INTEGER NOT NULL,
    visit_date DATE NULL,
    description VARCHAR(255) NULL,
    kg_evidence_id VARCHAR(100) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pet_id) REFERENCES pets(id)
);
-- 主键: id
-- 外键: pet_id → pets.id
-- 业务说明: 简化的就诊记录（兼容Spring PetClinic数据模型）
-- 关键字段: kg_evidence_id用于关联知识图谱中的诊断依据
```

### 7. 病历主表 (medical_records)
```sql
CREATE TABLE medical_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_no VARCHAR(30) UNIQUE NOT NULL,
    appointment_id INTEGER NOT NULL,
    pet_id INTEGER NOT NULL,
    vet_id INTEGER NOT NULL,
    chief_complaint TEXT NULL,
    exam_notes TEXT NULL,
    diagnosis VARCHAR(100) NULL,
    treatment_plan TEXT NULL,
    is_voided BOOLEAN NOT NULL DEFAULT 0,
    void_reason TEXT NULL,
    voided_at DATETIME NULL,
    kg_evidence_id VARCHAR(100) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (appointment_id) REFERENCES appointments(id),
    FOREIGN KEY (pet_id) REFERENCES pets(id),
    FOREIGN KEY (vet_id) REFERENCES users(id)
);
-- 主键: id
-- 外键: appointment_id → appointments.id, pet_id → pets.id, vet_id → users.id
-- 唯一索引: record_no
-- 业务说明: 详细病历记录，不可追溯修改，修改需要审计
-- 关键字段:
--   - is_voided: 是否作废（作废后不可恢复）
--   - kg_evidence_id: 关联知识图谱中的诊断推理路径
```

### 8. 诊断结果表 (diagnoses)
```sql
CREATE TABLE diagnoses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    medical_record_id INTEGER NOT NULL,
    diagnosis_code VARCHAR(20) NOT NULL,
    diagnosis_name VARCHAR(100) NOT NULL,
    severity_level INTEGER NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (medical_record_id) REFERENCES medical_records(id)
);
-- 主键: id
-- 外键: medical_record_id → medical_records.id
-- 业务说明: 一份病历可有多个诊断结果
-- 关键字段: severity_level表示严重程度（1-5级）
```

### 9. 药品主数据表 (drugs)
```sql
CREATE TABLE drugs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    drug_code VARCHAR(30) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    dosage_form VARCHAR(20) NOT NULL,
    category VARCHAR(50) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    unit_price FLOAT NOT NULL DEFAULT 10.0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
-- 主键: id
-- 唯一索引: drug_code
-- 业务说明: 药品库的主文件，由管理员维护
-- 关键字段:
--   - dosage_form: 片剂、注射液、粉剂等
--   - category: 抗生素、止痛药、消炎药等
--   - unit: 片、支、克等
```

### 10. 药品库存表 (drug_inventory)
```sql
CREATE TABLE drug_inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    drug_id INTEGER NOT NULL,
    branch_code VARCHAR(10) NOT NULL,
    stock_qty FLOAT NOT NULL DEFAULT 0,
    safety_stock FLOAT NOT NULL DEFAULT 0,
    frozen_for_prescription BOOLEAN NOT NULL DEFAULT 0,
    expiry_date DATETIME NULL,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (drug_id) REFERENCES drugs(id),
    UNIQUE (drug_id, branch_code)
);
-- 主键: id
-- 外键: drug_id → drugs.id
-- 唯一约束: (drug_id, branch_code) 保证同一药品在同一分院只有一条库存记录
-- 业务说明: 按分院维护药品库存，支持多个分院
-- 关键字段:
--   - frozen_for_prescription: 处方冻结标记
--   - safety_stock: 安全库存，低于此数量时告警
```

### 11. 处方主表 (prescriptions)
```sql
CREATE TABLE prescriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prescription_code VARCHAR(30) UNIQUE NOT NULL,
    medical_record_id INTEGER NOT NULL,
    doctor_id INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT '待缴费',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expire_at DATETIME NOT NULL,
    locked_inventory JSON NOT NULL DEFAULT '{}',
    FOREIGN KEY (medical_record_id) REFERENCES medical_records(id),
    FOREIGN KEY (doctor_id) REFERENCES users(id)
);
-- 主键: id
-- 外键: medical_record_id → medical_records.id, doctor_id → users.id
-- 唯一索引: prescription_code
-- 业务说明: 处方主记录，关联病历和医生
-- 关键字段:
--   - status: 待缴费、已缴费、已调配、已取药、已逾期
--   - expire_at: 处方有效期（默认2小时），超时自动作废
--   - locked_inventory: JSON字典，记录冻结的药品数量 {"drug_id": qty}
```

### 12. 处方明细表 (prescription_items)
```sql
CREATE TABLE prescription_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prescription_id INTEGER NOT NULL,
    drug_id INTEGER NOT NULL,
    dosage VARCHAR(50) NOT NULL,
    frequency VARCHAR(50) NOT NULL,
    duration_days INTEGER NOT NULL,
    quantity FLOAT NOT NULL,
    FOREIGN KEY (prescription_id) REFERENCES prescriptions(id),
    FOREIGN KEY (drug_id) REFERENCES drugs(id)
);
-- 主键: id
-- 外键: prescription_id → prescriptions.id, drug_id → drugs.id
-- 业务说明: 处方中的单个药物配置
-- 关键字段:
--   - dosage: "5mg每次"、"10ml每次"
--   - frequency: "每天2次"、"每8小时1次"
--   - duration_days: 疗程天数
--   - quantity: 所需总数量（自动计算）
```

### 13. 笑舍单元表 (cage_units)
```sql
CREATE TABLE cage_units (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cage_code VARCHAR(20) UNIQUE NOT NULL,
    clinic_id VARCHAR(10) NOT NULL,
    zone_type VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT '空闲',
    current_pet_id INTEGER NULL,
    adjacent_cage_ids JSON NOT NULL DEFAULT '[]',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (current_pet_id) REFERENCES pets(id)
);
-- 主键: id
-- 外键: current_pet_id → pets.id
-- 唯一索引: cage_code
-- 业务说明: 住院笑舍单元
-- 关键字段:
--   - zone_type: 隔离笑舍、普通笑舍、重症笑舍等
--   - status: 空闲、使用中、维护中
--   - adjacent_cage_ids: JSON数组，记录相邻笑舍ID，用于隔离检查
```

### 14. 住院记录表 (inpatient_records)
```sql
CREATE TABLE inpatient_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pet_id INTEGER NOT NULL,
    cage_id INTEGER NOT NULL,
    doctor_id INTEGER NOT NULL,
    clinic_id VARCHAR(10) NOT NULL,
    admission_time DATETIME NOT NULL,
    discharge_time DATETIME NULL,
    deposit_amount FLOAT NOT NULL DEFAULT 0,
    consumed_amount FLOAT NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT '待入院',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pet_id) REFERENCES pets(id),
    FOREIGN KEY (cage_id) REFERENCES cage_units(id),
    FOREIGN KEY (doctor_id) REFERENCES users(id)
);
-- 主键: id
-- 外键: pet_id → pets.id, cage_id → cage_units.id, doctor_id → users.id
-- 业务说明: 住院记录，追踪住院期间的宠物状态和费用
-- 关键字段:
--   - status: 待入院、住院中、已出院
--   - deposit_amount: 预存金额
--   - consumed_amount: 实际消费金额
```

### 15. 护理日志表 (nursing_logs)
```sql
CREATE TABLE nursing_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inpatient_record_id INTEGER NOT NULL,
    nurse_id INTEGER NOT NULL,
    temperature FLOAT NULL,
    heart_rate INTEGER NULL,
    notes TEXT NULL,
    logged_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (inpatient_record_id) REFERENCES inpatient_records(id),
    FOREIGN KEY (nurse_id) REFERENCES users(id)
);
-- 主键: id
-- 外键: inpatient_record_id → inpatient_records.id, nurse_id → users.id
-- 业务说明: 住院期间的护理记录，护士定时记录
-- 关键字段:
--   - temperature: 体温（摄氏度）
--   - heart_rate: 心率（次/分钟）
--   - notes: 护理备注（进食、排尿、特殊情况等）
```

### 16. 收费发票表 (invoices)
```sql
CREATE TABLE invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_no VARCHAR(30) UNIQUE NOT NULL,
    owner_id INTEGER NOT NULL,
    appointment_id INTEGER NULL,
    total_amount FLOAT NOT NULL DEFAULT 0,
    paid_amount FLOAT NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'unpaid',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES owners(id),
    FOREIGN KEY (appointment_id) REFERENCES appointments(id)
);
-- 主键: id
-- 外键: owner_id → owners.id, appointment_id → appointments.id
-- 唯一索引: invoice_no
-- 业务说明: 收费发票，聚合同一宠物主人的多个收费项目
-- 关键字段:
--   - status: unpaid(未支付)、paid(已支付)、partial(部分支付)、refunded(已退款)
--   - paid_amount: 已支付金额，可能小于total_amount
```

### 17. 收费明细表 (invoice_items)
```sql
CREATE TABLE invoice_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id INTEGER NOT NULL,
    item_type VARCHAR(20) NOT NULL,
    item_name VARCHAR(100) NOT NULL,
    amount FLOAT NOT NULL,
    FOREIGN KEY (invoice_id) REFERENCES invoices(id)
);
-- 主键: id
-- 外键: invoice_id → invoices.id
-- 业务说明: 发票中的单个收费项目
-- 关键字段:
--   - item_type: 诊疗费、药品费、住院费、其他
--   - item_name: 具体项目名称（如"血常规检验"、"青霉素针注"）
```

### 18. AI决策审计表 (ai_decision_audit_logs)
```sql
CREATE TABLE ai_decision_audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    medical_record_id INTEGER NOT NULL,
    doctor_id INTEGER NOT NULL,
    ai_suggestion TEXT NOT NULL,
    doctor_decision TEXT NOT NULL,
    deviation_reason TEXT NOT NULL,
    correlation_score FLOAT NOT NULL DEFAULT 0,
    warning_triggered BOOLEAN NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (medical_record_id) REFERENCES medical_records(id),
    FOREIGN KEY (doctor_id) REFERENCES users(id)
);
-- 主键: id
-- 外键: medical_record_id → medical_records.id, doctor_id → users.id
-- 业务说明: 人机决策偏差审计，追踪医生对AI建议的采纳情况
-- 关键字段:
--   - correlation_score: AI建议与医生决策的相关度（0-1）
--   - warning_triggered: 是否触发异常告警
```

---

## 三、表间主外键关系总览

| 表1 | 字段 | 表2 | 字段 | 关系说明 |
|-----|------|-----|------|---------|
| users | role_id | roles | id | 用户属于某角色（多对一） |
| pets | owner_id | owners | id | 宠物属于某主人（多对一） |
| appointments | pet_id | pets | id | 预约关联某宠物（多对一） |
| appointments | doctor_id | users | id | 预约分配给某医生（多对一） |
| medical_records | appointment_id | appointments | id | 病历关联某预约（一对一） |
| medical_records | pet_id | pets | id | 病历记录某宠物（多对一） |
| medical_records | vet_id | users | id | 病历由某兽医创建（多对一） |
| diagnoses | medical_record_id | medical_records | id | 诊断属于某病历（多对一） |
| prescriptions | medical_record_id | medical_records | id | 处方关联某病历（多对一） |
| prescriptions | doctor_id | users | id | 处方由某医生开具（多对一） |
| prescription_items | prescription_id | prescriptions | id | 明细属于某处方（多对一） |
| prescription_items | drug_id | drugs | id | 明细指定某药品（多对一） |
| drug_inventory | drug_id | drugs | id | 库存记录某药品（多对一） |
| cage_units | current_pet_id | pets | id | 笑舍当前住宿某宠物（多对一） |
| inpatient_records | pet_id | pets | id | 住院记录某宠物（多对一） |
| inpatient_records | cage_id | cage_units | id | 住院使用某笑舍（多对一） |
| inpatient_records | doctor_id | users | id | 住院由某医生主治（多对一） |
| nursing_logs | inpatient_record_id | inpatient_records | id | 护理日志属于某住院（多对一） |
| nursing_logs | nurse_id | users | id | 护理日志由某护士创建（多对一） |
| invoices | owner_id | owners | id | 发票属于某主人（多对一） |
| invoices | appointment_id | appointments | id | 发票关联某预约（多对一） |
| invoice_items | invoice_id | invoices | id | 明细属于某发票（多对一） |
| visits | pet_id | pets | id | 就诊记录某宠物（多对一） |
| ai_decision_audit_logs | medical_record_id | medical_records | id | 审计关联某病历（多对一） |
| ai_decision_audit_logs | doctor_id | users | id | 审计记录某医生决策（多对一） |

---

## 四、关键业务流程中的数据流

### 4.1 预约挂号流程
```
owners → pets → appointments → users(doctor)
         ↓            ↓
      建档    预约分配与优先级
```

### 4.2 就诊与诊疗流程
```
appointments → medical_records → diagnoses
                    ↓
              vet_id(users)
                    ↓
              treatment_plan
```

### 4.3 处方调配流程
```
medical_records → prescriptions → prescription_items → drugs
                       ↓              ↓
                    doctor_id      drug_id
                       ↓              ↓
                     users      drug_inventory
                       ↓              ↓
                   locked_inventory   stock_qty
```

### 4.4 住院管理流程
```
appointments → medical_records → inpatient_records → cage_units
                    ↓                ↓                    ↓
              vet_id(users)    doctor_id(users)    current_pet_id
                                     ↓
                            nursing_logs ← nurse_id(users)
```

### 4.5 收费结算流程
```
appointments → invoices ← owner_id(owners)
     ↓             ↓
pet_id         invoice_items
              (诊疗费、药品费、住院费)
```

---

## 五、SQL常用查询示例

### 查询某医生今日待诊患者
```sql
SELECT 
    a.record_code,
    p.name AS pet_name,
    o.name AS owner_name,
    o.phone,
    a.urgency_level,
    a.priority_score
FROM appointments a
JOIN pets p ON a.pet_id = p.id
JOIN owners o ON p.owner_id = o.id
WHERE a.doctor_id = ? 
  AND DATE(a.scheduled_time) = DATE('now')
  AND a.status = '待诊'
ORDER BY a.priority_score DESC;
```

### 查询某宠物的完整诊疗历史
```sql
SELECT 
    mr.record_no,
    mr.created_at,
    mr.chief_complaint,
    mr.diagnosis,
    d.diagnosis_name,
    GROUP_CONCAT(pi.frequency, '; ') AS medications
FROM medical_records mr
LEFT JOIN diagnoses d ON mr.id = d.medical_record_id
LEFT JOIN prescriptions p ON mr.id = p.medical_record_id
LEFT JOIN prescription_items pi ON p.id = pi.prescription_id
WHERE mr.pet_id = ?
  AND mr.is_voided = 0
GROUP BY mr.id
ORDER BY mr.created_at DESC;
```

### 检查药品库存预警
```sql
SELECT 
    d.name,
    d.drug_code,
    di.stock_qty,
    di.safety_stock,
    CASE 
        WHEN di.stock_qty <= di.safety_stock THEN '低于安全库存'
        ELSE '正常'
    END AS status
FROM drug_inventory di
JOIN drugs d ON di.drug_id = d.id
WHERE di.branch_code = ?
  AND di.stock_qty <= di.safety_stock * 1.2
ORDER BY di.stock_qty ASC;
```

### 查询逾期未支付处方
```sql
SELECT 
    p.prescription_code,
    p.created_at,
    p.expire_at,
    SUM(pi.quantity * d.unit_price) AS total_amount,
    o.name AS owner_name,
    o.phone
FROM prescriptions p
JOIN prescription_items pi ON p.id = pi.prescription_id
JOIN drugs d ON pi.drug_id = d.id
JOIN medical_records mr ON p.medical_record_id = mr.id
JOIN pets pt ON mr.pet_id = pt.id
JOIN owners o ON pt.owner_id = o.id
WHERE p.status = '待缴费'
  AND DATETIME('now') > p.expire_at
GROUP BY p.id;
```

### 查询住院患者及笑舍使用情况
```sql
SELECT 
    p.name AS pet_name,
    o.name AS owner_name,
    ir.admission_time,
    c.cage_code,
    c.zone_type,
    ir.consumed_amount,
    ir.deposit_amount,
    ir.status
FROM inpatient_records ir
JOIN pets p ON ir.pet_id = p.id
JOIN owners o ON p.owner_id = o.id
JOIN cage_units c ON ir.cage_id = c.id
WHERE ir.status IN ('住院中', '待出院')
  AND ir.clinic_id = ?
ORDER BY ir.admission_time DESC;
```

---

## 六、数据完整性约束

### 唯一约束（UNIQUE）
- `roles.name` - 角色名称全局唯一
- `users.employee_code` - 员工编号全局唯一
- `users.username` - 用户名全局唯一
- `owners.owner_code` - 客户编号全局唯一
- `pets.pet_code` - 宠物编号全局唯一
- `appointments.record_code` - 预约号全局唯一
- `appointments.(doctor_id, scheduled_time)` - 医生同一时段唯一
- `medical_records.record_no` - 病历号全局唯一
- `drugs.drug_code` - 药品编号全局唯一
- `drug_inventory.(drug_id, branch_code)` - 分院药品库存唯一
- `prescriptions.prescription_code` - 处方号全局唯一
- `cage_units.cage_code` - 笑舍编号全局唯一
- `invoices.invoice_no` - 发票号全局唯一

### 外键约束（FOREIGN KEY）
- 所有外键均设置 `ON DELETE RESTRICT` 或 `ON DELETE CASCADE`
- 需要保护的关键数据（如医生、用户）使用 `RESTRICT`
- 业务无关的关联可使用 `CASCADE`

### 非空约束（NOT NULL）
- 所有业务关键字段均设置 NOT NULL
- 允许为空的字段仅为非必需的补充信息

---

## 七、性能优化建议

### 推荐的索引
```sql
-- 按预约医生和时间查询
CREATE INDEX idx_appointments_doctor_time ON appointments(doctor_id, scheduled_time);

-- 按宠物查询病历
CREATE INDEX idx_medical_records_pet ON medical_records(pet_id, created_at DESC);

-- 按状态查询处方
CREATE INDEX idx_prescriptions_status ON prescriptions(status, expire_at);

-- 按库存查询药品
CREATE INDEX idx_drug_inventory_stock ON drug_inventory(stock_qty, branch_code);

-- 按住院状态查询
CREATE INDEX idx_inpatient_records_status ON inpatient_records(status, clinic_id);
```

### WAL模式优势
- 提高并发读写性能
- 支持多个读者同时访问数据库
- 写操作不阻塞读操作

---

**文档版本**: 1.0  
**最后更新**: 2024年4月  
**维护责任**: 信息系统开发组
