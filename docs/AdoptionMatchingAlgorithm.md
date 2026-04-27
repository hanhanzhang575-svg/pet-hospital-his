# 领养匹配算法设计（Hybrid v2.1）

## 1. 目标
- 解决“领养匹配页面空白、无算法、无可视化”问题。
- 用现有 SQL 表 + 扩展字段，实现可解释的混合推荐：
  - 内容匹配（Content-based）
  - 协同信号（Collaborative）
  - 领养速度预测（Speed Prediction）

## 2. 模块树（用于后续 UML）
```text
Adoption Matching Module
├─ Data Layer (SQL)
│  ├─ adoption_pets
│  ├─ adopters
│  ├─ match_results
│  ├─ pets (基础宠物资料)
│  └─ owners (地理坐标/画像来源)
├─ Service Layer
│  └─ paci_service.py
│     ├─ Hard Constraints
│     ├─ Multi-dimensional Scoring
│     ├─ Collaborative Signal
│     ├─ Adoption Speed Prediction
│     └─ Explainability Builder
├─ API Layer
│  └─ routers/adoption.py
│     ├─ GET /adoption/algorithm
│     ├─ GET /adoption/pets
│     ├─ POST /adoption/match/{pet_id}
│     ├─ GET /adoption/match/{pet_id}
│     └─ GET /adoption/dashboard/{pet_id}
└─ Visualization Layer (Vue + ECharts)
   └─ AdoptionHallView.vue
      ├─ 算法说明区
      ├─ 指标卡
      ├─ 雷达图
      ├─ Top10 条形图
      ├─ 分数-天数散点图
      ├─ 速度分布图
      └─ Top候选表格
```

## 3. 评分公式
### 3.1 硬约束过滤
任何一条命中即 `hard_blocked = true` 且 `total_score = 0`：
- 新手 + 危险犬
- 家庭有儿童 + 宠物攻击性过高
- 家庭不兼容物种冲突
- 可陪伴时长低于最低阈值

### 3.2 七维软评分（0~1）
- `s_dist` 距离可达（Haversine）
- `s_env` 居住环境匹配（面积/陪伴时长/居住类型/是否有院子）
- `s_med` 医疗可达与健康负担（附近医疗点 + 预算 + 免疫绝育 + 医疗需求）
- `s_pref` 偏好匹配（物种偏好 + 年龄区间 + 家庭结构）
- `s_behavior` 行为契合（活跃度/耐心/训练性/社交友好）
- `s_health_cost` 健康经济承受能力（预算/时间/信用/历史成功）
- `s_collab` 协同信号（个人历史 + 同类宠物历史 + 相似领养人邻域）

### 3.3 综合分
\[
Score = 100 \times (0.16s_{dist}+0.18s_{env}+0.16s_{med}+0.18s_{pref}+0.14s_{behavior}+0.10s_{health\_cost}+0.08s_{collab})
\]

## 4. 领养速度预测
输出 `predicted_speed_days` 与 `speed_level`（`fast/medium/slow/very_slow`）。

核心思想参考竞赛型速度预测：  
将综合分与年龄、医疗、行为压力、优先级、偏好命中、协同热度联合映射到预计领养天数。

## 5. SQL 字段利用（关键）
### adoption_pets（新增）
- `age_months`, `vaccinated`, `neutered`
- `body_condition_score`
- `friendliness_human`, `friendliness_pet`
- `shelter_stress`, `adoption_priority`

### adopters（新增）
- `preferred_species`, `preferred_age_min`, `preferred_age_max`
- `has_children`, `has_elderly`, `has_allergy_family`
- `work_from_home_days`, `activity_level`, `patience_level`
- `housing_type`, `has_yard`
- `credit_score`, `historical_adoption_success`

### match_results（新增）
- `s_pref`, `s_behavior`, `s_health_cost`, `s_collab`
- `predicted_speed_days`, `speed_level`
- `recommendation_confidence`, `model_version`
- `adopted`, `feedback_score`

## 6. 随机数据生成
新增脚本：`generate_adoption_data.py`
- 不清空现有数据，增量生成大规模样本。
- 自动保证关键唯一性（owner_code/pet_code/匹配对）。
- 会生成历史匹配反馈，供协同信号学习使用。

## 7. 当前可视化
- 模型说明 + 权重标签
- 匹配核心指标卡
- Top1 多维雷达
- Top10 匹配总分条形图
- 匹配分 vs 预计天数散点图
- 速度分级占比饼图
- 候选领养人 Top 表格（带解释文本）
