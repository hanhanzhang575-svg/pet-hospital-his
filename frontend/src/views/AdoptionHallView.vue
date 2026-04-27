<template>
  <div class="adoption-page">
    <el-card class="hero-card" shadow="never">
      <div class="hero-row">
        <div class="hero-content">
          <div class="eyebrow">Adoption Intelligence</div>
          <h2>智能领养匹配中心</h2>
          <p>基于 PACI/MCDA 算法。默认极速返回，后台补算全量结果。所有评分维度均以百分比展示，支持动态监控。</p>
        </div>
        <div class="hero-actions">
          <el-tag :type="statusTagType" effect="dark" round size="large" class="status-badge">
            <el-icon class="is-loading" v-if="statusTagType === 'warning'"><Loading /></el-icon>
            {{ statusBannerText }}
          </el-tag>
        </div>
      </div>
    </el-card>

    <div class="layout-grid">
      <el-card class="pet-card" shadow="never">
        <template #header>
          <div class="panel-header">
            <div class="panel-title">待领养宠物池</div>
            <el-tag size="small" type="info" round>{{ filteredPets.length }} 只</el-tag>
          </div>
        </template>
        <el-empty v-if="pets.length === 0" description="暂无待领养宠物" :image-size="80" />
        <template v-else>
          <el-input 
            v-model="petKeyword" 
            placeholder="搜索名称 / 品种" 
            clearable 
            class="pet-search" 
            :prefix-icon="Search"
          />
          <div class="pet-list compact-scroll">
            <div
              v-for="item in filteredPets"
              :key="item.id"
              :class="['pet-item', selectedPetId === item.id ? 'pet-item--active' : '']"
              @click="!matchingLoading && analyzePet(item)"
            >
              <div class="pet-item-content">
                <div class="pet-name">{{ item.pet_name }}</div>
                <div class="pet-desc">{{ item.species }} <el-divider direction="vertical" /> {{ item.breed || '-' }} <el-divider direction="vertical" /> {{ item.age_months }} 月龄</div>
                <div class="pet-tags">
                  <el-tag size="small" effect="plain" type="info">精力 {{ item.energy_level }}</el-tag>
                  <el-tag size="small" effect="plain" type="danger">医疗 {{ item.medical_need }}</el-tag>
                  <el-tag size="small" effect="plain" type="warning">P{{ item.adoption_priority }}</el-tag>
                </div>
              </div>
              <div class="pet-item-action">
                <el-button
                  size="small"
                  type="primary"
                  :loading="matchingLoading && selectedPetId === item.id"
                  :disabled="matchingLoading && selectedPetId !== item.id"
                  round
                >
                  {{ selectedPetId === item.id && matchingLoading ? '分析中' : '匹配' }}
                </el-button>
              </div>
            </div>
          </div>
        </template>
      </el-card>

      <div class="content-col">
        <el-card class="panel-card" shadow="never">
          <template #header><div class="panel-title">算法引擎与模型状态</div></template>
          <el-empty v-if="!algorithm.model_version" description="算法模型参数加载中" :image-size="60" />
          <template v-else>
            <div class="algorithm-summary">{{ algorithm.summary }}</div>
            <div class="weight-wrap">
              <el-tag v-for="(weight, key) in algorithm.weights || {}" :key="key" type="success" effect="light" round class="weight-tag">
                <span class="weight-key">{{ key }}</span> <span class="weight-val">{{ weight }}</span>
              </el-tag>
            </div>
            <div class="alert-group">
              <el-alert
                type="success"
                :closable="false"
                show-icon
                style="margin-bottom: 8px; border-radius: 8px;"
              >
                <template #title>
                  <span class="font-bold">PACI/MCDA 策略：</span>硬约束先拦截（如新手×烈性犬/物种冲突），再按距离-环境-医疗等维度综合评分。距离采用 Haversine 公式计算。
                </template>
              </el-alert>
              <el-alert
                type="info"
                :closable="false"
                show-icon
                style="border-radius: 8px;"
              >
                <template #title>
                  <span class="font-bold">参考实现：</span>Surprise(协同过滤) | Multi-Criteria-Decision-Making (scikit-criteria)
                </template>
              </el-alert>
            </div>
          </template>
        </el-card>

        <el-row :gutter="16" class="metric-row">
          <el-col :xs="12" :lg="6">
            <el-card class="metric-card stat-blue" shadow="hover">
              <div class="metric-label">候选领养人池</div>
              <div class="metric-value">{{ dashboard.overview?.candidate_count || 0 }} <span class="metric-unit">人</span></div>
            </el-card>
          </el-col>
          <el-col :xs="12" :lg="6">
            <el-card class="metric-card stat-orange" shadow="hover">
              <div class="metric-label">池内平均匹配分</div>
              <div class="metric-value">{{ percentNumber(dashboard.overview?.avg_score || 0) }}</div>
            </el-card>
          </el-col>
          <el-col :xs="12" :lg="6">
            <el-card class="metric-card stat-green" shadow="hover">
              <div class="metric-label">极速领养潜力占比</div>
              <div class="metric-value">{{ percentRatio(dashboard.overview?.fast_ratio || 0) }}</div>
            </el-card>
          </el-col>
          <el-col :xs="12" :lg="6">
            <el-card class="metric-card stat-red" shadow="hover">
              <div class="metric-label">硬约束拦截流失</div>
              <div class="metric-value">{{ percentRatio(dashboard.overview?.hard_blocked_ratio || 0) }}</div>
            </el-card>
          </el-col>
        </el-row>

        <el-row :gutter="16" class="chart-row">
          <el-col :xs="24" :lg="12">
            <el-card class="panel-card" shadow="never">
              <template #header><div class="panel-title">Top 1 领养人维度画像雷达图</div></template>
              <div ref="radarRef" class="chart" />
            </el-card>
          </el-col>
          <el-col :xs="24" :lg="12">
            <el-card class="panel-card" shadow="never">
              <template #header><div class="panel-title">推荐候选人 Top 10 综合分</div></template>
              <div ref="barRef" class="chart" />
            </el-card>
          </el-col>
        </el-row>

        <el-row :gutter="16" class="chart-row">
          <el-col :xs="24" :lg="12">
            <el-card class="panel-card" shadow="never">
              <template #header><div class="panel-title">匹配分 vs 预计领养天数散点</div></template>
              <div ref="scatterRef" class="chart" />
            </el-card>
          </el-col>
          <el-col :xs="24" :lg="12">
            <el-card class="panel-card" shadow="never">
              <template #header><div class="panel-title">预计领养速度评级分布</div></template>
              <div ref="pieRef" class="chart" />
            </el-card>
          </el-col>
        </el-row>

        <el-row :gutter="16" class="chart-row">
          <el-col :xs="24" :lg="8">
            <el-card class="panel-card" shadow="never">
              <template #header><div class="panel-title">候选人养宠经验分布</div></template>
              <div ref="personaBarRef" class="chart chart-short" />
            </el-card>
          </el-col>
          <el-col :xs="24" :lg="8">
            <el-card class="panel-card" shadow="never">
              <template #header><div class="panel-title">候选人住房类型结构</div></template>
              <div ref="personaPieRef" class="chart chart-short" />
            </el-card>
          </el-col>
          <el-col :xs="24" :lg="8">
            <el-card class="panel-card" shadow="never">
              <template #header><div class="panel-title">候选人地理散点映射</div></template>
              <div ref="personaMapRef" class="chart chart-short" />
            </el-card>
          </el-col>
        </el-row>

        <el-row :gutter="16" class="chart-row">
          <el-col :xs="24" :lg="14">
            <el-card class="panel-card table-card" shadow="never">
              <template #header><div class="panel-title">推荐候选人画像摘要</div></template>
              <el-table :data="persona.top_personas || []" class="custom-table" height="240">
                <el-table-column prop="adopter_name" label="领养人" min-width="110" />
                <el-table-column prop="experience_level" label="经验" width="90">
                  <template #default="{ row }">
                    <el-tag size="small" :type="row.experience_level === '新手' ? 'info' : 'success'" effect="plain">{{ row.experience_level }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="housing_type" label="住房" width="90" />
                <el-table-column label="预算" width="90">
                  <template #default="{ row }"><span class="mono-text">¥{{ Number(row.budget || 0).toFixed(0) }}</span></template>
                </el-table-column>
                <el-table-column label="面积" width="80">
                  <template #default="{ row }"><span class="mono-text">{{ Number(row.housing_area || 0).toFixed(0) }}㎡</span></template>
                </el-table-column>
                <el-table-column label="陪伴" width="80">
                  <template #default="{ row }"><span class="mono-text">{{ Number(row.available_hours || 0).toFixed(1) }}h</span></template>
                </el-table-column>
              </el-table>
            </el-card>
          </el-col>
          <el-col :xs="24" :lg="10">
            <el-card class="panel-card" shadow="never">
              <template #header><div class="panel-title">模型维度贡献度 (均值)</div></template>
              <div ref="contribRef" class="chart chart-short" />
            </el-card>
          </el-col>
        </el-row>

        <el-card class="panel-card table-card" shadow="never">
          <template #header><div class="panel-title">全局领养人匹配结果列表</div></template>
          <el-table :data="dashboard.top_matches || []" class="custom-table" height="340">
            <el-table-column prop="adopter_name" label="候选人姓名" min-width="120" />
            <el-table-column label="综合匹配分" width="110">
              <template #default="{ row }">
                <span class="score-high font-bold">{{ percentNumber(row.total_score || 0) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="算法置信度" width="110">
              <template #default="{ row }">
                <el-progress :percentage="Number((row.recommendation_confidence || 0) * 100)" :stroke-width="6" :show-text="false" color="#8b5cf6" />
                <span class="mono-text text-xs text-muted">{{ percentNumber((row.recommendation_confidence || 0) * 100) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="predicted_speed_days" label="预计天数" width="100">
              <template #default="{ row }"><span class="mono-text">{{ row.predicted_speed_days }} 天</span></template>
            </el-table-column>
            <el-table-column prop="speed_level" label="速度评级" width="100">
              <template #default="{ row }">
                <el-tag :type="row.speed_level.includes('极速') ? 'success' : 'warning'" size="small" disable-transitions>{{ row.speed_level }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="子维度快照" min-width="240">
              <template #default="{ row }">
                <el-tooltip effect="light" placement="top" :content="dimensionTip(row)">
                  <span class="dim-tip mono-text">{{ shortDimension(row) }}</span>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column prop="rationale" label="AI 推荐解释" min-width="300" show-overflow-tooltip />
          </el-table>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import * as echarts from "echarts";
import { ElMessage } from "element-plus";
import { Search, Loading } from "@element-plus/icons-vue"; // 引入图标
import {
  fetchAdoptionAlgorithm,
  fetchAdoptionDashboard,
  fetchAdoptionMatchStatus,
  fetchAdoptionPersona,
  fetchAdoptionPets,
  runAdoptionMatch
} from "../api/adoption";
import { getErrorMessage } from "../utils/status";

// === 状态定义与原有逻辑完全保持一致 ===
const pets = ref([]);
const petKeyword = ref("");
const selectedPetId = ref(null);
const algorithm = ref({});
const dashboard = ref({
  overview: { candidate_count: 0, avg_score: 0, fast_ratio: 0, hard_blocked_ratio: 0 },
  meta: { data_freshness: "unknown", is_partial: true, status: { state: "idle" } },
  top_matches: [],
  speed_distribution: [],
  score_breakdown_mean: [],
  scatter: []
});

const latestReason = ref("");
const matchingLoading = ref(false);
const matchStatus = ref({ state: "idle", mode: "fast", processed: 0, total: 0 });

const radarRef = ref(null);
const barRef = ref(null);
const scatterRef = ref(null);
const pieRef = ref(null);
const contribRef = ref(null);
const personaBarRef = ref(null);
const personaPieRef = ref(null);
const personaMapRef = ref(null);

let radarChart = null;
let barChart = null;
let scatterChart = null;
let pieChart = null;
let contribChart = null;
let personaBarChart = null;
let personaPieChart = null;
let personaMapChart = null;
let pollTimer = null;
let currentAbortController = null;
let pollMessageShown = false;

const filteredPets = computed(() => {
  const key = String(petKeyword.value || "").trim().toLowerCase();
  if (!key) return pets.value;
  return pets.value.filter((item) => `${item.pet_name || ""} ${item.species || ""} ${item.breed || ""}`.toLowerCase().includes(key));
});

const persona = ref({
  histograms: { experience: [], housing_type: [] },
  averages: { budget: 0, housing_area: 0, available_hours: 0, activity_level: 0 },
  geo_points: [],
  top_personas: []
});

const statusBannerText = computed(() => {
  const state = matchStatus.value?.state || "idle";
  const mode = matchStatus.value?.mode || "fast";
  if (state === "running" && mode === "full") {
    return `快速结果已就绪，全量结果高并发计算中（${matchStatus.value.processed || 0}/${matchStatus.value.total || 0}）`;
  }
  if (state === "failed") {
    return `全量补算失败：${matchStatus.value.error || "请重试"}，目前展示安全降级结果`;
  }
  if (latestReason.value) return latestReason.value;
  return "选择左侧宠物发起匹配，系统将优先返回极速结果，并自动转入后台执行全量图计算";
});

const statusTagType = computed(() => {
  const state = matchStatus.value?.state;
  if (state === "failed") return "danger";
  if (state === "running") return "warning";
  return "success";
});

function percentNumber(value) {
  return `${Number(value || 0).toFixed(1)}%`;
}

function percentRatio(ratio) {
  return `${(Number(ratio || 0) * 100).toFixed(1)}%`;
}

function dimensionTip(row) {
  return [
    `距离 (D): ${(row.s_dist * 100).toFixed(1)}%`,
    `环境 (E): ${(row.s_env * 100).toFixed(1)}%`,
    `医疗 (M): ${(row.s_med * 100).toFixed(1)}%`,
    `偏好 (P): ${(row.s_pref * 100).toFixed(1)}%`,
    `行为 (B): ${(row.s_behavior * 100).toFixed(1)}%`,
    `成本 (C): ${(row.s_health_cost * 100).toFixed(1)}%`,
    `协同 (Co): ${(row.s_collab * 100).toFixed(1)}%`
  ].join("\n");
}

function shortDimension(row) {
  return `D ${(row.s_dist * 100).toFixed(0)} / E ${(row.s_env * 100).toFixed(0)} / P ${(row.s_pref * 100).toFixed(0)} / M ${(row.s_med * 100).toFixed(0)}`;
}

function ensureCharts() {
  if (radarRef.value && !radarChart) radarChart = echarts.init(radarRef.value);
  if (barRef.value && !barChart) barChart = echarts.init(barRef.value);
  if (scatterRef.value && !scatterChart) scatterChart = echarts.init(scatterRef.value);
  if (pieRef.value && !pieChart) pieChart = echarts.init(pieRef.value);
  if (contribRef.value && !contribChart) contribChart = echarts.init(contribRef.value);
  if (personaBarRef.value && !personaBarChart) personaBarChart = echarts.init(personaBarRef.value);
  if (personaPieRef.value && !personaPieChart) personaPieChart = echarts.init(personaPieRef.value);
  if (personaMapRef.value && !personaMapChart) personaMapChart = echarts.init(personaMapRef.value);
}

// === 可视化 UI 深度调优 ===
function renderCharts() {
  ensureCharts();
  const topRows = dashboard.value.top_matches || [];
  const topOne = topRows[0];
  const dims = topOne
    ? [
        topOne.s_dist * 100, topOne.s_env * 100, topOne.s_med * 100,
        topOne.s_pref * 100, topOne.s_behavior * 100, topOne.s_health_cost * 100, topOne.s_collab * 100
      ]
    : [0, 0, 0, 0, 0, 0, 0];

  radarChart?.setOption({
    tooltip: { trigger: "item", backgroundColor: 'rgba(255, 255, 255, 0.95)' },
    radar: {
      indicator: [
        { name: "距离", max: 100 }, { name: "环境", max: 100 }, { name: "医疗", max: 100 },
        { name: "偏好", max: 100 }, { name: "行为", max: 100 }, { name: "成本", max: 100 }, { name: "协同", max: 100 }
      ],
      axisName: { color: '#64748b', fontWeight: 500 },
      splitArea: { areaStyle: { color: ['rgba(241, 245, 249, 0.4)', 'rgba(248, 250, 252, 0.4)'] } },
      splitLine: { lineStyle: { color: '#e2e8f0' } }
    },
    series: [{
      type: "radar",
      data: [{
        value: dims,
        name: topOne?.adopter_name || "暂无",
        areaStyle: { color: 'rgba(245, 158, 11, 0.2)' }, // 增加半透明填充
        lineStyle: { width: 2, color: '#f59e0b' },
        itemStyle: { color: '#f59e0b' }
      }]
    }]
  });

  const top10 = topRows.slice(0, 10).reverse(); // 翻转数据让最高分在顶部
  barChart?.setOption({
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" }, backgroundColor: 'rgba(255, 255, 255, 0.95)' },
    xAxis: { type: "value", max: 100, axisLabel: { formatter: "{value}%", color: '#94a3b8' }, splitLine: { lineStyle: { type: 'dashed', color: '#f1f5f9' } } },
    yAxis: { type: "category", data: top10.map((x) => x.adopter_name), axisLine: { show: false }, axisTick: { show: false } },
    series: [{
      type: "bar",
      data: top10.map((x) => Number(x.total_score || 0)),
      barMaxWidth: 16,
      label: { show: true, position: "right", formatter: ({ value }) => `${Number(value).toFixed(1)}%`, color: '#1e293b', fontWeight: 600 },
      itemStyle: {
        borderRadius: [0, 4, 4, 0], // 增加条形圆角
        color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [{ offset: 0, color: '#fbbf24' }, { offset: 1, color: '#f59e0b' }])
      }
    }],
    grid: { left: 90, right: 40, top: 10, bottom: 20 }
  });

  scatterChart?.setOption({
    tooltip: {
      trigger: "item", backgroundColor: 'rgba(255, 255, 255, 0.95)',
      formatter: (p) => `<div style="font-weight:bold;margin-bottom:4px;">${p.value[3]}</div>匹配分: <span style="color:#0ea5e9;font-weight:600">${Number(p.value[0]).toFixed(1)}%</span><br/>预计天数: <span style="font-weight:600">${p.value[1]} 天</span><br/>算法置信度: ${(p.value[2] * 100).toFixed(1)}%`
    },
    xAxis: { type: "value", name: "匹配综合分", min: 0, max: 100, axisLabel: { formatter: "{value}%" }, splitLine: { lineStyle: { type: 'dashed', color: '#f1f5f9' } } },
    yAxis: { type: "value", name: "流转周期(天)", min: 0, max: 250, splitLine: { lineStyle: { type: 'dashed', color: '#f1f5f9' } } },
    grid: { left: 40, right: 40, top: 30, bottom: 30, containLabel: true },
    series: [{
      type: "scatter",
      symbolSize: (val) => 10 + val[2] * 20, // 依据置信度控制气泡大小
      data: (dashboard.value.scatter || []).map((x) => [x.score, x.speed_days, x.confidence, x.name]),
      itemStyle: { 
        color: "#0ea5e9", opacity: 0.7,
        shadowBlur: 10, shadowColor: 'rgba(14, 165, 233, 0.3)' // 增加发光阴影提升高级感
      }
    }]
  });

  const pieData = dashboard.value.speed_distribution || [];
  pieChart?.setOption({
    tooltip: { trigger: "item", backgroundColor: 'rgba(255, 255, 255, 0.95)', formatter: (p) => `${p.name}: <span style="font-weight:bold">${p.value}</span> (${p.percent.toFixed(1)}%)` },
    legend: { bottom: 0, icon: 'circle', textStyle: { color: '#64748b' } },
    series: [{ 
      type: "pie", 
      radius: ["45%", "70%"], // 调整为更现代的 Doughnut 样式
      itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 2 },
      label: { formatter: "{b}\n{d}%", color: '#475569' }, 
      data: pieData 
    }]
  });

  const contribution = dashboard.value.score_breakdown_mean || [];
  contribChart?.setOption({
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" }, backgroundColor: 'rgba(255, 255, 255, 0.95)' },
    xAxis: { type: "category", data: contribution.map((x) => x.name), axisTick: { show: false } },
    yAxis: { type: "value", min: 0, max: 100, axisLabel: { formatter: "{value}%" }, splitLine: { lineStyle: { type: 'dashed', color: '#f1f5f9' } } },
    grid: { left: 10, right: 10, top: 20, bottom: 20, containLabel: true },
    series: [{
      type: "bar",
      data: contribution.map((x) => Number(x.value || 0)),
      label: { show: true, position: "top", formatter: ({ value }) => `${Number(value).toFixed(1)}%`, color: '#64748b' },
      itemStyle: { 
        borderRadius: [4, 4, 0, 0],
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: '#8b5cf6' }, { offset: 1, color: '#c4b5fd' }])
      },
      barMaxWidth: 24
    }]
  });

  const expRows = persona.value?.histograms?.experience || [];
  personaBarChart?.setOption({
    tooltip: { trigger: "axis", backgroundColor: 'rgba(255, 255, 255, 0.95)' },
    xAxis: { type: "category", data: expRows.map((x) => x.name), axisTick: { show: false }, axisLabel: { interval: 0 } },
    yAxis: { type: "value", minInterval: 1, splitLine: { lineStyle: { type: 'dashed', color: '#f1f5f9' } } },
    grid: { left: 10, right: 10, top: 20, bottom: 20, containLabel: true },
    series: [{ 
      type: "bar", data: expRows.map((x) => Number(x.value || 0)), 
      itemStyle: { color: "#14b8a6", borderRadius: [4, 4, 0, 0] }, barMaxWidth: 24 
    }]
  });

  const houseRows = persona.value?.histograms?.housing_type || [];
  personaPieChart?.setOption({
    tooltip: { trigger: "item", backgroundColor: 'rgba(255, 255, 255, 0.95)' },
    legend: { bottom: 0, icon: 'circle', textStyle: { color: '#64748b' } },
    series: [{ 
      type: "pie", radius: ["40%", "68%"], 
      itemStyle: { borderRadius: 4, borderColor: '#fff', borderWidth: 2 },
      data: houseRows.map((x) => ({ name: x.name, value: x.value })) 
    }]
  });

  const geoRows = persona.value?.geo_points || [];
  personaMapChart?.setOption({
    tooltip: { trigger: "item", backgroundColor: 'rgba(255, 255, 255, 0.95)', formatter: (p) => `<div style="font-weight:bold">${p.name}</div>适配分: <span style="color:#6366f1">${Number(p.value?.[2] || 0).toFixed(1)}%</span>` },
    xAxis: { type: "value", name: "经度", splitLine: { lineStyle: { color: '#f1f5f9' } } },
    yAxis: { type: "value", name: "纬度", splitLine: { lineStyle: { color: '#f1f5f9' } } },
    grid: { left: 10, right: 30, top: 20, bottom: 20, containLabel: true },
    series: [{ 
      type: "scatter", data: geoRows.map((x) => [x.lng, x.lat, x.score]), 
      symbolSize: (v) => 6 + Number(v[2] || 0) / 10, 
      itemStyle: { color: "#8b5cf6", opacity: 0.7 } 
    }]
  });
}

// === API 调用部分保持不变 ===
async function loadPets() {
  const res = await fetchAdoptionPets();
  pets.value = res.data || [];
}

async function loadAlgorithm() {
  const res = await fetchAdoptionAlgorithm();
  algorithm.value = res.data || {};
}

async function loadDashboard(adoptionPetId) {
  const dashboardRes = await fetchAdoptionDashboard(adoptionPetId, 30);
  dashboard.value = dashboardRes.data || dashboard.value;
  const personaRes = await fetchAdoptionPersona(adoptionPetId);
  persona.value = personaRes.data || persona.value;
  await nextTick();
  renderCharts();
}

async function syncStatus(adoptionPetId) {
  const res = await fetchAdoptionMatchStatus(adoptionPetId);
  matchStatus.value = res.data || matchStatus.value;
}

function stopPolling() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
}

function startPolling(adoptionPetId) {
  stopPolling();
  pollMessageShown = false;
  pollTimer = setInterval(async () => {
    try {
      await syncStatus(adoptionPetId);
      const state = matchStatus.value?.state;
      if (state === "running") {
        if (!pollMessageShown) {
          pollMessageShown = true;
          ElMessage.info("极速图计算模型已命中，全量 MCDA 寻优正在后台异步补算...");
        }
        return;
      }
      if (state === "completed") {
        stopPolling();
        await loadDashboard(adoptionPetId);
        ElMessage.success("全量深度匹配完成，大盘数据已静默刷新。");
        return;
      }
      if (state === "failed") {
        stopPolling();
        ElMessage.warning(`全量补算失败：${matchStatus.value?.error || "服务降级处理"}`);
      }
    } catch { stopPolling(); }
  }, 2500);
}

async function analyzePet(petItem) {
  selectedPetId.value = petItem.id;
  matchingLoading.value = true;
  stopPolling();
  if (currentAbortController) currentAbortController.abort();
  currentAbortController = new AbortController();

  try {
    const matchRes = await runAdoptionMatch(petItem.id, {
      mode: "fast", topN: 200, signal: currentAbortController.signal, timeout: 30000
    });
    const payload = matchRes.data || {};
    const rows = payload.rows || [];
    latestReason.value = rows.length > 0 ? rows[0].rationale || "" : "";
    matchStatus.value = payload.status || matchStatus.value;
    await loadDashboard(petItem.id);
    startPolling(petItem.id);
  } catch (error) {
    if (error?.raw?.name === "CanceledError") return;
    ElMessage.error(getErrorMessage(error, "模型调度异常，已保留历史断点数据"));
  } finally {
    matchingLoading.value = false;
  }
}

function onResize() {
  radarChart?.resize(); barChart?.resize(); scatterChart?.resize(); pieChart?.resize();
  contribChart?.resize(); personaBarChart?.resize(); personaPieChart?.resize(); personaMapChart?.resize();
}

onMounted(async () => {
  try {
    await Promise.all([loadPets(), loadAlgorithm()]);
    if (pets.value.length > 0) {
      selectedPetId.value = pets.value[0].id;
      await loadDashboard(selectedPetId.value);
      await syncStatus(selectedPetId.value);
      if (matchStatus.value?.state === "running") startPolling(selectedPetId.value);
    }
    window.addEventListener("resize", onResize);
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "匹配大厅初始化加载失败"));
  }
});

onBeforeUnmount(() => {
  stopPolling();
  if (currentAbortController) currentAbortController.abort();
  window.removeEventListener("resize", onResize);
  radarChart?.dispose(); barChart?.dispose(); scatterChart?.dispose(); pieChart?.dispose();
  contribChart?.dispose(); personaBarChart?.dispose(); personaPieChart?.dispose(); personaMapChart?.dispose();
});
</script>

<style scoped>
/* 全局页面底色 */
.adoption-page {
  padding: 20px;
  background-color: #f8fafc;
  min-height: 100vh;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}

/* 卡片基础样式统一 */
.hero-card, .pet-card, .panel-card {
  border-radius: 16px;
  border: 1px solid #e2e8f0;
  background: #ffffff;
  margin-bottom: 16px;
  transition: box-shadow 0.3s ease;
}

/* --- Hero 区域 --- */
.hero-card {
  background: linear-gradient(120deg, #ffffff 0%, #f0fdfa 100%);
  border-left: 6px solid #14b8a6;
}
.hero-row {
  display: flex; justify-content: space-between; gap: 20px; align-items: center; padding: 4px;
}
.eyebrow {
  font-size: 13px; color: #14b8a6; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 8px;
}
.hero-row h2 { margin: 0; font-size: 26px; font-weight: 800; color: #0f172a; }
.hero-row p { margin: 8px 0 0; color: #64748b; font-size: 14px; line-height: 1.5; }
.status-badge { padding: 0 16px; font-weight: 500; font-size: 13px; }

/* 页面主体栅格 */
.layout-grid {
  display: grid; grid-template-columns: 360px 1fr; gap: 16px; align-items: start;
}

/* --- 待领养宠物侧边栏 --- */
.pet-card { position: sticky; top: 16px; }
.panel-header { display: flex; justify-content: space-between; align-items: center; }
.panel-card:deep(.el-card__header), .pet-card:deep(.el-card__header) {
  border-bottom: 1px solid #f1f5f9; padding: 16px 20px;
}
.panel-title { font-weight: 700; color: #1e293b; font-size: 15px; }

.pet-search { margin-bottom: 12px; }
.compact-scroll {
  max-height: calc(100vh - 280px); overflow-y: auto; padding-right: 6px;
}
.compact-scroll::-webkit-scrollbar { width: 6px; }
.compact-scroll::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }

.pet-list { display: flex; flex-direction: column; gap: 10px; }
.pet-item {
  display: flex; justify-content: space-between; align-items: center; gap: 12px;
  padding: 14px; border: 1px solid #e2e8f0; border-radius: 12px;
  background: #ffffff; cursor: pointer; transition: all 0.2s ease;
}
.pet-item:hover { background: #f8fafc; border-color: #cbd5e1; }
.pet-item--active {
  border-color: #f97316; background: #fffaf5; 
  box-shadow: 0 4px 12px rgba(249, 115, 22, 0.08);
}
.pet-name { font-weight: 700; color: #0f172a; font-size: 15px; }
.pet-desc { font-size: 12px; color: #64748b; margin: 4px 0 8px; }
.pet-tags { display: flex; gap: 6px; flex-wrap: wrap; }

/* --- 大盘与状态区 --- */
.algorithm-summary { color: #475569; margin-bottom: 12px; font-size: 14px; line-height: 1.5; }
.weight-wrap { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 16px; }
.weight-tag { padding: 0 10px; border: none; background: #f0fdf4; }
.weight-key { font-weight: 600; color: #16a34a; }
.weight-val { color: #15803d; margin-left: 4px; font-family: monospace; }
.alert-group .el-alert { margin-bottom: 8px; }
.font-bold { font-weight: 700; }

/* --- KPI 数据卡片重构 --- */
.metric-row { margin-bottom: 16px; }
.metric-card { 
  border-radius: 16px; border: none; background: #fff; padding: 4px 0;
  transition: transform 0.2s, box-shadow 0.2s;
}
.metric-card:hover {
  transform: translateY(-2px); box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05);
}
.stat-blue { border-bottom: 4px solid #3b82f6; }
.stat-orange { border-bottom: 4px solid #f59e0b; }
.stat-green { border-bottom: 4px solid #10b981; }
.stat-red { border-bottom: 4px solid #ef4444; }

.metric-label { font-size: 13px; color: #64748b; font-weight: 600; }
.metric-value { font-size: 32px; font-weight: 800; color: #1e293b; margin-top: 8px; line-height: 1; }
.metric-unit { font-size: 14px; color: #94a3b8; font-weight: 500; margin-left: 2px; }

/* --- 图表样式 --- */
.chart-row { margin-bottom: 16px; }
.panel-card:deep(.el-card__body) { padding: 16px; }
.chart { width: 100%; height: 320px; }
.chart-short { width: 100%; height: 240px; }

/* --- 表格样式调优 --- */
.table-card:deep(.el-card__body) { padding: 0; }
.custom-table { --el-table-border-color: #f1f5f9; --el-table-header-bg-color: #f8fafc; }
.mono-text { font-family: 'Menlo', 'Monaco', monospace; font-size: 13px; color: #475569; }
.score-high { color: #ea580c; font-size: 15px; }
.dim-tip { color: #64748b; font-size: 12px; cursor: help; }
.text-xs { font-size: 11px; }
.text-muted { color: #94a3b8; margin-left: 6px; }

@media (max-width: 1200px) {
  .layout-grid { grid-template-columns: 1fr; }
  .pet-card { position: static; }
  .pet-list { max-height: 400px; }
  .hero-row { flex-direction: column; align-items: flex-start; }
}
</style>