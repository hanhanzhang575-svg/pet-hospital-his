<template>
  <div class="lab-page">
    <el-card class="hero-card" shadow="never">
      <div class="hero-row">
        <div>
          <h2>检验员工作台</h2>
          <p>基于紧急度、等待时长和检验复杂度自动排序，提升危急值处理效率。</p>
        </div>
        <el-space>
          <el-button :loading="loading" @click="loadData">刷新</el-button>
        </el-space>
      </div>
    </el-card>

    <el-row :gutter="12" class="kpi-row">
      <el-col :xs="12" :lg="6">
        <el-card class="kpi-card"><div class="kpi-label">待检</div><div class="kpi-value warning">{{ stats.pending || 0 }}</div></el-card>
      </el-col>
      <el-col :xs="12" :lg="6">
        <el-card class="kpi-card"><div class="kpi-label">检验中</div><div class="kpi-value">{{ stats.in_progress || 0 }}</div></el-card>
      </el-col>
      <el-col :xs="12" :lg="6">
        <el-card class="kpi-card"><div class="kpi-label">今日完成</div><div class="kpi-value success">{{ stats.completed_today || 0 }}</div></el-card>
      </el-col>
      <el-col :xs="12" :lg="6">
        <el-card class="kpi-card"><div class="kpi-label">异常率</div><div class="kpi-value warning">{{ abnormalRateText }}</div></el-card>
      </el-col>
      <el-col :xs="12" :lg="24">
        <el-card class="kpi-card"><div class="kpi-label">危急值率</div><div class="kpi-value danger">{{ criticalRateText }}</div></el-card>
      </el-col>
    </el-row>

    <el-row :gutter="12">
      <el-col :xs="24" :lg="12">
        <el-card class="panel-card">
          <template #header><div class="panel-title">检验类型分布</div></template>
          <div ref="typePieRef" class="chart" />
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="12">
        <el-card class="panel-card">
          <template #header><div class="panel-title">近7日检验完成趋势</div></template>
          <div ref="trendRef" class="chart" />
        </el-card>
      </el-col>
    </el-row>

    <el-card class="panel-card">
      <template #header>
        <div class="panel-title">待检队列（按智能分诊排序）</div>
      </template>
      <el-empty v-if="sortedRows.length === 0" description="暂无待检任务" />
      <el-table v-else :data="sortedRows" border stripe :row-class-name="rowClassName" height="420">
        <el-table-column prop="record_code" label="诊单号" width="150" />
        <el-table-column label="宠物" min-width="170">
          <template #default="{ row }">{{ row.pet_name }} ({{ row.pet_species || '-' }})</template>
        </el-table-column>
        <el-table-column prop="requesting_doctor" label="申请医生" width="120" />
        <el-table-column label="项目" min-width="220">
          <template #default="{ row }">
            <el-tag v-for="item in row.exam_items || []" :key="`${row.id}-${item}`" style="margin-right: 4px">{{ item }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="等待时长" width="110">
          <template #default="{ row }">{{ waitMinutes(row) }} 分钟</template>
        </el-table-column>
        <el-table-column label="分诊分数" width="100">
          <template #default="{ row }">{{ triageScore(row) }}</template>
        </el-table-column>
        <el-table-column label="紧急度" width="90">
          <template #default="{ row }">
            <el-tag :type="urgencyTagType(row.urgency_level)">{{ row.urgency_level }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button v-if="String(row.status).includes('待')" size="small" type="success" @click="startExam(row)">开始检验</el-button>
            <el-button v-else size="small" type="primary" @click="openResultDialog(row)">录入结果</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="resultDialogVisible" width="860px" fullscreen destroy-on-close>
      <LabResultsView :embedded="true" :default-order="activeOrder" @submitted="handleSubmitted" />
    </el-dialog>
  </div>
</template>

<script setup>
import * as echarts from "echarts";
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import { fetchLabResults, fetchLabStats, fetchPendingTests, startLabExam } from "../api/lab";
import { useAuthStore } from "../store";
import { getErrorMessage } from "../utils/status";
import LabResultsView from "./LabResultsView.vue";

const authStore = useAuthStore();

const loading = ref(false);
const rows = ref([]);
const stats = ref({ pending: 0, in_progress: 0, completed_today: 0 });
const historyRows = ref([]);
const demoPendingRows = [
  {
    id: "demo-lab-1",
    appointment_id: 18801,
    record_code: "DEMO-LAB-001",
    pet_name: "可乐",
    pet_species: "犬",
    exam_items: ["WBC", "RBC", "ALT"],
    requesting_doctor: "李医生",
    urgency_level: "急诊",
    requested_at: new Date(Date.now() - 26 * 60000).toISOString(),
    status: "待检查"
  },
  {
    id: "demo-lab-2",
    appointment_id: 18802,
    record_code: "DEMO-LAB-002",
    pet_name: "芝士",
    pet_species: "猫",
    exam_items: ["BUN", "Creatinine"],
    requesting_doctor: "张医生",
    urgency_level: "常规",
    requested_at: new Date(Date.now() - 44 * 60000).toISOString(),
    status: "检查中"
  }
];
const demoHistoryRows = [
  { id: "demo-h-1", pet_name: "可乐", exam_type: "biochemistry", abnormal_count: 1, critical_count: 0, completed_at: "2026-04-15T09:20:00" },
  { id: "demo-h-2", pet_name: "芝士", exam_type: "blood_routine", abnormal_count: 2, critical_count: 1, completed_at: "2026-04-15T11:10:00" }
];

const typePieRef = ref(null);
const trendRef = ref(null);
let typePieChart = null;
let trendChart = null;

const resultDialogVisible = ref(false);
const activeOrder = ref(null);

const clinicId = computed(() => authStore.clinicId || "");
const displayRows = computed(() => (rows.value.length ? rows.value : demoPendingRows));
const displayHistoryRows = computed(() => (historyRows.value.length ? historyRows.value : demoHistoryRows));

const abnormalRateText = computed(() => {
  const total = displayHistoryRows.value.length || 1;
  const abnormal = displayHistoryRows.value.filter((x) => Number(x.abnormal_count || 0) > 0).length;
  return `${((abnormal / total) * 100).toFixed(1)}%`;
});

const criticalRateText = computed(() => {
  const total = displayHistoryRows.value.length || 1;
  const critical = displayHistoryRows.value.filter((x) => Number(x.critical_count || 0) > 0).length;
  return `${((critical / total) * 100).toFixed(1)}%`;
});

const sortedRows = computed(() => [...displayRows.value].sort((a, b) => triageScore(b) - triageScore(a)));

function urgencyTagType(level) {
  const t = String(level || "");
  if (t.includes("急")) return "danger";
  if (t.includes("优")) return "warning";
  return "info";
}

function waitMinutes(row) {
  const d = new Date(row.requested_at || "");
  if (Number.isNaN(d.getTime())) return 0;
  return Math.max(0, Math.round((Date.now() - d.getTime()) / 60000));
}

function triageScore(row) {
  const urgency = String(row.urgency_level || "");
  const urgencyScore = urgency.includes("急") ? 60 : urgency.includes("优") ? 30 : 10;
  const waitScore = Math.min(30, Math.round(waitMinutes(row) / 8));
  const complexityScore = Math.min(30, (row.exam_items || []).length * 6);

  const criticalHistory = displayHistoryRows.value.some(
    (h) => String(h.pet_name || "") === String(row.pet_name || "") && Number(h.critical_count || 0) > 0
  );
  const historyScore = criticalHistory ? 12 : 0;

  return urgencyScore + waitScore + complexityScore + historyScore;
}

function rowClassName({ row }) {
  return triageScore(row) >= 80 ? "danger-row" : triageScore(row) >= 55 ? "warn-row" : "";
}

function ensureCharts() {
  if (typePieRef.value && !typePieChart) typePieChart = echarts.init(typePieRef.value);
  if (trendRef.value && !trendChart) trendChart = echarts.init(trendRef.value);
}

function renderTypePie() {
  ensureCharts();
  const map = {};
  displayHistoryRows.value.forEach((row) => {
    const key = row.exam_type || "unknown";
    map[key] = (map[key] || 0) + 1;
  });
  const data = Object.entries(map).map(([name, value]) => ({ name, value }));

  typePieChart?.setOption({
    tooltip: { trigger: "item", formatter: "{b}: {c} ({d}%)" },
    legend: { bottom: 0 },
    series: [
      {
        type: "pie",
        radius: ["36%", "66%"],
        label: { formatter: "{b}: {d}%" },
        data
      }
    ]
  });
}

function renderTrend() {
  ensureCharts();
  const today = new Date();
  const labels = [];
  const map = {};
  displayHistoryRows.value.forEach((row) => {
    const dateKey = String(row.completed_at || "").slice(0, 10);
    map[dateKey] = (map[dateKey] || 0) + 1;
  });
  for (let i = 6; i >= 0; i -= 1) {
    const d = new Date(today);
    d.setDate(today.getDate() - i);
    const key = d.toISOString().slice(0, 10);
    labels.push(key);
  }

  trendChart?.setOption({
    tooltip: { trigger: "axis" },
    xAxis: { type: "category", data: labels.map((x) => x.slice(5)) },
    yAxis: { type: "value", name: "完成数" },
    series: [
      { type: "line", smooth: true, data: labels.map((x) => map[x] || 0), lineStyle: { width: 3, color: "#2563eb" } }
    ],
    grid: { top: 24, right: 18, left: 40, bottom: 24 }
  });
}

function renderCharts() {
  renderTypePie();
  renderTrend();
}

async function loadData() {
  loading.value = true;
  try {
    const [statRes, queueRes, historyRes] = await Promise.all([
      fetchLabStats(clinicId.value),
      fetchPendingTests(clinicId.value),
      fetchLabResults({ clinic_id: clinicId.value })
    ]);
    rows.value = queueRes.data || [];
    historyRows.value = historyRes.data || [];
    const backendStats = statRes.data || {};
    stats.value = {
      pending: Number(backendStats.pending ?? rows.value.filter((x) => String(x.status).includes("待")).length ?? 0),
      in_progress: Number(backendStats.in_progress ?? rows.value.filter((x) => String(x.status).includes("检验中")).length ?? 0),
      completed_today: Number(backendStats.completed_today ?? historyRows.value.length ?? 0),
    };
    if (!rows.value.length && !historyRows.value.length) {
      stats.value = { pending: 1, in_progress: 1, completed_today: 2 };
    }

    await nextTick();
    renderCharts();
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "检验工作台加载失败"));
  } finally {
    loading.value = false;
  }
}

async function startExam(row) {
  if (String(row.id).startsWith("demo-")) {
    ElMessage.info("演示数据不可操作，请先创建真实检验任务");
    return;
  }
  try {
    await startLabExam(row.appointment_id);
    row.status = "检验中";
    ElMessage.success("已开始检验");
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "开始检验失败"));
  }
}

function openResultDialog(row) {
  activeOrder.value = row;
  resultDialogVisible.value = true;
}

async function handleSubmitted() {
  resultDialogVisible.value = false;
  await loadData();
}

function onResize() {
  typePieChart?.resize();
  trendChart?.resize();
}

onMounted(async () => {
  await loadData();
  window.addEventListener("resize", onResize);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", onResize);
  typePieChart?.dispose();
  trendChart?.dispose();
});
</script>

<style scoped>
.lab-page {
  padding: 14px;
  background: linear-gradient(145deg, #f5fbff 0%, #fff8ef 100%);
}
.hero-card,
.kpi-card,
.panel-card {
  border-radius: 14px;
  margin-bottom: 12px;
}
.hero-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}
.hero-row h2 {
  margin: 0;
  font-size: 22px;
  color: #0f172a;
}
.hero-row p {
  margin: 6px 0 0;
  color: #64748b;
  font-size: 13px;
}
.kpi-label {
  font-size: 12px;
  color: #64748b;
}
.kpi-value {
  margin-top: 4px;
  font-size: 24px;
  font-weight: 700;
  color: #0f172a;
}
.kpi-value.success { color: #16a34a; }
.kpi-value.warning { color: #f59e0b; }
.kpi-value.danger { color: #ef4444; }
.panel-title {
  font-weight: 700;
  color: #0f172a;
}
.chart {
  width: 100%;
  height: 250px;
}
:deep(.danger-row > td) {
  background: #fee2e2 !important;
}
:deep(.warn-row > td) {
  background: #fff7ed !important;
}
@media (max-width: 900px) {
  .hero-row {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>

