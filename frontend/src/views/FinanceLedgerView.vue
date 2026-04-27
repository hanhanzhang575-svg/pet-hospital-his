<template>
  <div class="finance-page">
    <el-card class="hero-card" shadow="never">
      <div class="hero-row">
        <div>
          <h2>财务台账与结算看板</h2>
          <p>展示收费状态、收入结构和漏费风险，支持收款、退费和对账导出。</p>
        </div>
        <el-space>
          <el-select v-model="clinicId" style="width: 160px" @change="loadData">
            <el-option label="C001 沙河口" value="C001" />
            <el-option label="C002 甘井子" value="C002" />
            <el-option label="C003 高新区" value="C003" />
          </el-select>
          <el-button :loading="loading" @click="loadData">刷新</el-button>
          <el-button type="primary" :loading="exporting" @click="exportExcel">导出对账单</el-button>
        </el-space>
      </div>
    </el-card>

    <el-alert v-if="leakWarnings.length" type="warning" show-icon :closable="false" class="mb12">
      <template #default>
        检测到 {{ leakWarnings.length }} 笔疑似漏费记录（手术单未包含麻醉/耗材费用），已建议人工复核。
      </template>
    </el-alert>

    <el-row :gutter="12" class="kpi-row">
      <el-col :xs="12" :lg="6">
        <el-card class="kpi-card">
          <div class="kpi-label">已收费笔数</div>
          <div class="kpi-value success">{{ paidCount }}</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :lg="6">
        <el-card class="kpi-card">
          <div class="kpi-label">待收费笔数</div>
          <div class="kpi-value warning">{{ unpaidCount }}</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :lg="6">
        <el-card class="kpi-card">
          <div class="kpi-label">已收金额</div>
          <div class="kpi-value">￥{{ totalPaid.toFixed(0) }}</div>
        </el-card>
      </el-col>
      <el-col :xs="12" :lg="6">
        <el-card class="kpi-card">
          <div class="kpi-label">待收金额</div>
          <div class="kpi-value danger">￥{{ totalUnpaid.toFixed(0) }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="12">
      <el-col :xs="24" :lg="8">
        <el-card class="panel-card">
          <template #header>
            <div class="panel-title">收入结构占比</div>
          </template>
          <div ref="revenuePieRef" class="chart chart-short" />
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="8">
        <el-card class="panel-card">
          <template #header>
            <div class="panel-title">账单状态占比</div>
          </template>
          <div ref="statusPieRef" class="chart chart-short" />
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="8">
        <el-card class="panel-card">
          <template #header>
            <div class="panel-title">日内收款趋势（按小时）</div>
          </template>
          <div ref="hourLineRef" class="chart chart-short" />
        </el-card>
      </el-col>
    </el-row>

    <el-card class="panel-card">
      <template #header>
        <div class="panel-title">账单明细</div>
      </template>
      <el-table :data="rows" border stripe height="420">
        <el-table-column prop="record_code" label="诊单号" min-width="160" />
        <el-table-column prop="pet_name" label="宠物" width="110" />
        <el-table-column label="总金额" width="120">
          <template #default="{ row }">￥{{ Number(row.amount || 0).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="payment_method" label="支付方式" width="120" />
        <el-table-column prop="operator_name" label="经手人" width="100" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="收入构成" min-width="260">
          <template #default="{ row }">
            诊疗 {{ Number(row.diagnosis_fee || 0).toFixed(0) }} / 药费 {{ Number(row.drug_fee || 0).toFixed(0) }} / 检验 {{ Number(row.test_fee || 0).toFixed(0) }} / 住院 {{ Number(row.inpatient_fee || 0).toFixed(0) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <template v-if="String(row.status).includes('待')">
              <el-select v-model="row.payment_method" size="small" style="width: 95px">
                <el-option label="微信" value="微信支付" />
                <el-option label="支付宝" value="支付宝" />
                <el-option label="银联" value="银联" />
                <el-option label="现金" value="现金" />
              </el-select>
              <el-button size="small" type="primary" @click="settle(row)">确认收款</el-button>
            </template>
            <el-button v-else-if="String(row.status).includes('已收')" size="small" type="danger" @click="refund(row)">退费</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="payVisible" title="模拟支付" width="420px">
      <div class="pay-box">
        <div>应付金额：￥{{ Number(payContext.amount || 0).toFixed(2) }}</div>
        <div>支付方式：{{ payContext.payment_method }}</div>
        <img :src="qrUrl" alt="qrcode" class="qr" />
        <div class="waiting"><span class="dot" /> 等待扫码支付...</div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import * as echarts from "echarts";
import * as XLSX from "xlsx";
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { fetchBillingLedger } from "../api/stats";
import { getErrorMessage } from "../utils/status";

const clinicId = ref("C001");
const loading = ref(false);
const exporting = ref(false);
const rows = ref([]);

const payVisible = ref(false);
const payContext = ref({ id: 0, amount: 0, payment_method: "微信支付" });
const qrUrl = "https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=shironosuke-pay";

const revenuePieRef = ref(null);
const statusPieRef = ref(null);
const hourLineRef = ref(null);

let revenuePieChart = null;
let statusPieChart = null;
let hourLineChart = null;

const paidCount = computed(() => rows.value.filter((x) => String(x.status).includes("已收")).length);
const unpaidCount = computed(() => rows.value.filter((x) => String(x.status).includes("待")).length);
const totalPaid = computed(() => rows.value.filter((x) => String(x.status).includes("已收")).reduce((s, x) => s + Number(x.amount || 0), 0));
const totalUnpaid = computed(() => rows.value.filter((x) => String(x.status).includes("待")).reduce((s, x) => s + Number(x.amount || 0), 0));

const leakWarnings = computed(() => rows.value.filter((x) => x.has_surgery && (!x.has_anesthesia_fee || !x.has_consumable_fee)));

function statusTagType(status) {
  const text = String(status || "");
  if (text.includes("已收")) return "success";
  if (text.includes("退")) return "danger";
  return "warning";
}

function ensureCharts() {
  if (revenuePieRef.value && !revenuePieChart) revenuePieChart = echarts.init(revenuePieRef.value);
  if (statusPieRef.value && !statusPieChart) statusPieChart = echarts.init(statusPieRef.value);
  if (hourLineRef.value && !hourLineChart) hourLineChart = echarts.init(hourLineRef.value);
}

function renderRevenuePie() {
  ensureCharts();
  const totals = rows.value.reduce(
    (acc, row) => {
      acc.diagnosis += Number(row.diagnosis_fee || 0);
      acc.drug += Number(row.drug_fee || 0);
      acc.inpatient += Number(row.inpatient_fee || 0);
      acc.test += Number(row.test_fee || 0);
      return acc;
    },
    { diagnosis: 0, drug: 0, inpatient: 0, test: 0 }
  );

  revenuePieChart?.setOption({
    tooltip: { trigger: "item", formatter: (p) => `${p.name}: ￥${Number(p.value).toFixed(0)} (${p.percent.toFixed(1)}%)` },
    legend: { bottom: 0 },
    series: [
      {
        type: "pie",
        radius: ["38%", "66%"],
        label: { formatter: "{b}: {d}%" },
        data: [
          { name: "诊疗费", value: totals.diagnosis },
          { name: "药品费", value: totals.drug },
          { name: "住院费", value: totals.inpatient },
          { name: "检验费", value: totals.test }
        ]
      }
    ]
  });
}

function renderStatusPie() {
  ensureCharts();
  const data = [
    { name: "已收费", value: paidCount.value },
    { name: "待收费", value: unpaidCount.value },
    { name: "已退费", value: rows.value.filter((x) => String(x.status).includes("退")).length }
  ];
  statusPieChart?.setOption({
    tooltip: { trigger: "item", formatter: (p) => `${p.name}: ${p.value} (${p.percent.toFixed(1)}%)` },
    legend: { bottom: 0 },
    series: [
      { type: "pie", radius: ["38%", "66%"], label: { formatter: "{b}: {d}%" }, data }
    ]
  });
}

function renderHourLine() {
  ensureCharts();
  const bucket = Array.from({ length: 24 }, () => 0);
  rows.value.forEach((row) => {
    if (!String(row.status).includes("已收")) return;
    const d = new Date(row.created_at || "");
    if (Number.isNaN(d.getTime())) return;
    bucket[d.getHours()] += Number(row.amount || 0);
  });

  hourLineChart?.setOption({
    tooltip: { trigger: "axis" },
    xAxis: { type: "category", data: Array.from({ length: 24 }, (_, i) => `${i}:00`) },
    yAxis: { type: "value", name: "收款" },
    series: [
      { type: "line", smooth: true, data: bucket.map((x) => Number(x.toFixed(1))), lineStyle: { width: 3, color: "#2563eb" } }
    ],
    grid: { top: 20, right: 20, left: 48, bottom: 28 }
  });
}

function renderCharts() {
  renderRevenuePie();
  renderStatusPie();
  renderHourLine();
}

async function loadData() {
  loading.value = true;
  try {
    const res = await fetchBillingLedger(clinicId.value);
    rows.value = res.data || [];
    await nextTick();
    renderCharts();
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "财务台账加载失败"));
  } finally {
    loading.value = false;
  }
}

function settle(row) {
  if (row.has_surgery && (!row.has_anesthesia_fee || !row.has_consumable_fee)) {
    ElMessage.error("存在漏费风险，当前账单已拦截结算");
    return;
  }
  if (["微信支付", "支付宝"].includes(row.payment_method)) {
    payContext.value = row;
    payVisible.value = true;
    window.setTimeout(() => {
      row.status = "已收费";
      payVisible.value = false;
      renderCharts();
      ElMessage.success("支付成功，账单已结算");
    }, 5000);
    return;
  }
  row.status = "已收费";
  renderCharts();
  ElMessage.success("账单已结算");
}

async function refund(row) {
  try {
    await ElMessageBox.prompt("请输入退费原因", "退费确认", {
      confirmButtonText: "确认",
      cancelButtonText: "取消",
      inputPattern: /^.{2,}$/,
      inputErrorMessage: "退费原因不少于2个字",
      type: "warning"
    });
    row.status = "已退费";
    renderCharts();
    ElMessage.success("退费成功");
  } catch (error) {
    if (error !== "cancel" && error !== "close") {
      ElMessage.error(getErrorMessage(error, "退费失败"));
    }
  }
}

async function exportExcel() {
  exporting.value = true;
  try {
    const data = rows.value.map((r) => ({
      日期: (r.created_at || "").replace("T", " ").slice(0, 19),
      诊单号: r.record_code,
      宠物: r.pet_name,
      金额: r.amount,
      支付方式: r.payment_method,
      经手人: r.operator_name,
      状态: r.status
    }));

    const ws = XLSX.utils.json_to_sheet(data);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "财务台账");
    const d = new Date();
    const stamp = `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, "0")}${String(d.getDate()).padStart(2, "0")}`;
    XLSX.writeFile(wb, `财务台账_${clinicId.value}_${stamp}.xlsx`);
    ElMessage.success(`导出成功，共 ${data.length} 条记录`);
  } finally {
    exporting.value = false;
  }
}

function onResize() {
  revenuePieChart?.resize();
  statusPieChart?.resize();
  hourLineChart?.resize();
}

onMounted(async () => {
  await loadData();
  window.addEventListener("resize", onResize);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", onResize);
  revenuePieChart?.dispose();
  statusPieChart?.dispose();
  hourLineChart?.dispose();
});
</script>

<style scoped>
.finance-page {
  padding: 14px;
  background: linear-gradient(145deg, #f5fbff 0%, #fff7ef 100%);
}
.hero-card,
.kpi-card,
.panel-card {
  border-radius: 14px;
  margin-bottom: 12px;
}
.mb12 { margin-bottom: 12px; }
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
  height: 260px;
}
.chart-short {
  height: 240px;
}
.pay-box {
  text-align: center;
}
.qr {
  width: 180px;
  height: 180px;
  margin: 12px auto;
  display: block;
}
.waiting {
  color: #16a34a;
  font-weight: 700;
}
.dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #16a34a;
  margin-right: 6px;
  animation: pulse 1.2s infinite;
}
@keyframes pulse {
  0% { opacity: 0.3; }
  50% { opacity: 1; }
  100% { opacity: 0.3; }
}
@media (max-width: 900px) {
  .hero-row {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>

