# 白之助宠物医院信息管理系统 (Shironosuke Pet Hospital IS)

## 项目背景
这是一个面向中型连锁宠物医院的综合信息管理系统，服务于白之助宠物医院
（大连市，3家连锁院区：沙河口、甘井子、高新园区）。
本项目同时作为《信息系统分析与设计》课程大作业的实现载体。

## 技术栈
- 后端：Python + FastAPI + SQLAlchemy + SQLite（WAL模式）
- 前端：Vue 3 + Vite + Element Plus + Axios + Pinia
- AI模块：NetworkX + ChromaDB + DeepSeek API
- 联邦学习：Flower框架（三院区本地模拟节点）

## 组织信息
- 3家院区，共120名员工（兽医28名、护理45名、行政47名）
- 日均门诊65只，住院笼舍72个单元（犬区25、猫区25、VIP区10、ICU8、隔离4）
- 注册会员1.8万人，药品库存约420种，年营收约1800万元

## 系统角色（7类）
1. 院长/系统管理员 - 全局权限
2. 院区主任 - 本院区管理权限
3. 执业兽医师 - 诊断、处方、医嘱
4. 护理人员 - 住院护理、体征录入
5. 前台接诊员 - 挂号、分诊、收费
6. 药房人员 - 处方审核、发药、库存
7. 宠物主人（客户）- 预约、查询

## API接口规范
- 所有接口统一前缀：/api/v1/
- 认证方式：JWT Token，Header携带 Authorization: Bearer {token}
- 响应格式统一：
  {
    "code": 200,
    "message": "success",
    "data": {}
  }
- 错误码规范：
  400 参数错误
  401 未登录
  403 权限不足
  404 资源不存在
  409 冲突（如号源已被占用）
  500 服务器错误

## 核心表关键字段
pets表：
  id, pet_code(宠物ID编码), name, species(犬/猫/兔/鸟/爬行类),
  breed, gender, birth_date, weight, allergy_history(JSON数组),
  owner_id(FK), clinic_id(所属院区), created_at

cage_units表：
  id, cage_code, clinic_id, zone_type(犬区/猫区/VIP/ICU/隔离),
  status(空闲/待入院/住院中/待清洁/维修/临时启用),
  current_pet_id, adjacent_cage_ids(JSON数组，用于互斥校验)

appointments表：
  id, record_code(诊单编号), pet_id, doctor_id, clinic_id,
  scheduled_time, urgency_level(常规/优先/急诊),
  status(待诊/就诊中/已完成/已取消), priority_score(算法计算)

prescriptions表：
  id, prescription_code, medical_record_id, doctor_id,
  status(待缴费/已缴费/已发药/已失效),
  created_at, expire_at(创建时间+2小时), locked_inventory(JSON)

inpatient_records表：
  id, pet_id, cage_id, doctor_id, clinic_id,
  admission_time, discharge_time,
  deposit_amount(押金), consumed_amount(已消费),
  status(待入院/住院观察/术后监护/待出院/已出院)

## 核心模块（MVP开发顺序）
### 阶段一：基础框架 ✓已完成
- FastAPI项目初始化
- SQLite数据库+核心表
- RBAC权限系统
- Vue3项目初始化+登录页

### 阶段二：档案管理（当前阶段）
- 宠物主人档案CRUD
- 宠物档案CRUD（含过敏史JSON字段）
- 宠物ID按编码规范自动生成

### 阶段三：门诊挂号
- 预约挂号（并发防冲突锁）
- 动态优先级排队算法
- 兽医工作台

### 阶段四：住院与药品
- 笼舍三层分配校验（数量→物种隔离→急诊降级）
- 处方库存冻结+2小时超时自动释放
- 住院押金水位每日核算+催缴预警
- EOQ库存模型
- 效期预警定时任务

### 阶段五：AI模块
- KG-RAG知识图谱诊断（被动请求层）
- AI主动监听层（确诊与生化指标相关性校验）
- 人机决策偏差审计日志
- RFM客户流失预警
- Flower联邦学习模拟

## 业务规则（重要）
1. 处方药开具必须校验兽医执业资格
2. 处方提交前自动比对宠物过敏史与配伍禁忌
3. 笼舍分配执行三层校验：
   - 第一层：目标病区空余数量
   - 第二层：邻近笼舍物种互斥校验（犬猫严格隔离）
   - 第三层：急诊触发降级分配（VIP降级→临时笼），禁止跨院转诊
4. 药品库存低于安全阈值时自动冻结开方权限
5. 挂号时间槽并发锁，同一医生同一时段不可重复锁定
6. 急诊宠物强制插队至队列首位，优先级评分系统自动计算
7. 跨院区调阅病历须记录审计日志
8. 处方生成后冻结库存，2小时未缴费自动失效并释放冻结库存
9. 住院押金水位每日核算：
   - 余额<500元：推送催缴通知+护士站预警
   - 余额归零：触发欠费停药预警+通知院区主任
10. AI诊断双层触发：
    - 被动层：医生手动点击AI辅助分析
    - 主动层：确诊结论与生化指标相关性低于阈值时强制弹出警告
11. 人机决策偏差必须录入说明理由，写入审计日志

## 信息编码规则
- 宠物ID：物种码(1位)+院区码(2位)+建档年月(4位)+流水(4位)
  例：C0224050014（犬科/甘井子/2024年5月/第14号）
- 诊单编号：日期(8位)+科室码(2位)+类型码(1位)+流水(3位)
  例：20250616SUA005
- 药品编码：剂型(2位)+药效类别(2位)+规格(3位)+批次流水(5位)
  例：INAB10056789
- 员工编号：职级(2位)+院区(2位)+科室(2位)+工号(4位)
  例：D101IM1045

## 算法模块
1. 动态优先级排队：基于症状严重度+等待时长+年龄加权评分
2. EOQ经济订货批量：动态计算最优补货量和安全库存
3. 笼舍约束满足分配：三层校验+急诊降级的贪心算法
4. RFM客户流失预警：Recency+Frequency+Monetary三维评分

## 注意事项
- SQLite并发写入必须开启WAL模式：PRAGMA journal_mode=WAL
- 笼舍分配和挂号锁定必须用数据库事务，防止并发冲突
- 前端所有时间统一用ISO8601格式传输，显示时转换为本地时间
- 宠物过敏史存储为JSON数组字段
- 跨院区操作必须在日志表写入操作记录
- 处方超时释放用后台定时任务（APScheduler）每15分钟扫描一次

## 目录结构
shironosuke-pet-hospital/
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── models/
│   ├── routers/
│   ├── services/
│   │   ├── queue_priority.py   # 动态优先级排队算法
│   │   ├── cage_allocator.py   # 笼舍三层约束分配算法
│   │   ├── eoq_calculator.py   # EOQ库存模型
│   │   ├── rfm_analyzer.py     # RFM客户预警模型
│   │   ├── prescription_expiry.py  # 处方超时释放定时任务
│   │   ├── deposit_monitor.py  # 押金水位监控定时任务
│   │   └── kg_rag.py           # KG-RAG诊断引擎
│   ├── schemas/
│   └── tests/
├── frontend/
│   └── src/
│       ├── views/
│       ├── components/
│       ├── router/
│       ├── store/
│       └── api/
├── ai_module/
│   ├── knowledge_graph.py
│   ├── vector_store.py
│   ├── llm_client.py
│   └── federated/
│       ├── server.py
│       └── client.py
└── CLAUDE.md

## 代码规范
- 所有函数必须有中文注释说明业务逻辑
- 业务规则校验统一在service层处理，router层只做路由
- 数据库操作统一通过SQLAlchemy ORM，禁止裸SQL
- 前端API调用统一封装在src/api/目录下

## UML图与报告对应关系
- 系统ORM模型 → 第5章类图
- API调用链 → 第6章时序图
- 笼舍状态机代码 → 第6章状态图
- 模块树结构 → 第7章功能结构图
- 运行截图 → 报告各章节配图

## 当前进度
- [x] 阶段一：基础框架 ✓
- [ ] 阶段二：档案管理
- [ ] 阶段三：门诊挂号
- [ ] 阶段四：住院与药品
- [ ] 阶段五：AI模块