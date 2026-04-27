<template>
  <div class="page">
    <el-card>
      <template #header>
        <div class="header-row">
          <span>采购审批（院长/主任）</span>
          <el-space>
            <el-button type="success" :disabled="processableSelected.length===0" @click="batchApprove">✅ 批量通过</el-button>
            <el-button type="danger" :disabled="processableSelected.length===0" @click="batchReject">❌ 批量驳回</el-button>
            <el-button :loading="loading" @click="loadData">刷新</el-button>
          </el-space>
        </div>
      </template>
      <el-row :gutter="12" style="margin-bottom: 12px">
        <el-col :xs="12" :lg="6"><el-card><div class="kpi-label">待处理</div><div class="kpi-value">{{ pendingCount }}</div></el-card></el-col>
        <el-col :xs="12" :lg="6"><el-card><div class="kpi-label">已通过</div><div class="kpi-value success">{{ approvedCount }}</div></el-card></el-col>
        <el-col :xs="12" :lg="6"><el-card><div class="kpi-label">已驳回</div><div class="kpi-value danger">{{ rejectedCount }}</div></el-card></el-col>
        <el-col :xs="12" :lg="6"><el-card><div class="kpi-label">预计采购金额</div><div class="kpi-value warning">¥{{ estimatedAmount }}</div></el-card></el-col>
      </el-row>
      <el-row :gutter="12" style="margin-bottom: 12px">
        <el-col :xs="24" :lg="12"><div ref="statusChartRef" class="chart" /></el-col>
        <el-col :xs="24" :lg="12"><div ref="qtyChartRef" class="chart" /></el-col>
      </el-row>
      <el-empty v-if="rows.length === 0" description="库存充足，暂无待审批采购申请" />
      <el-table v-else :data="rows" border @selection-change="onSelectionChange" :row-class-name="rowClassName">
        <el-table-column type="selection" width="48" />
        <el-table-column prop="id" label="任务ID" width="90" />
        <el-table-column prop="drug_id" label="药品ID" width="100" />
        <el-table-column prop="current_stock" label="当前库存" width="110" />
        <el-table-column prop="safety_stock" label="安全库存" width="110" />
        <el-table-column prop="suggested_qty" label="建议采购量" width="120" />
        <el-table-column prop="status" label="状态" width="110" />
        <el-table-column label="审批" width="220">
          <template #default="{ row }">
            <el-tooltip v-if="row.status === '已撤回'" content="该申请已被药房撤回，无需审批">
              <el-button size="small" type="success" disabled class="disabled-action">通过</el-button>
            </el-tooltip>
            <el-button v-else size="small" type="success" @click="approve(row)">通过</el-button>
            <el-tooltip v-if="row.status === '已撤回'" content="该申请已被药房撤回，无需审批">
              <el-button size="small" type="danger" disabled class="disabled-action">驳回</el-button>
            </el-tooltip>
            <el-button v-else size="small" type="danger" @click="reject(row)">驳回</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="list-meta">共{{ rows.length }}条记录，最后更新时间 {{ lastUpdated || "--:--" }}</div>
    </el-card>
    <el-alert v-if="undoBar.visible" class="undo-bar" :title="undoBar.title" type="warning" show-icon :closable="false">
      <template #default><el-button size="small" @click="undoAction">撤销</el-button></template>
    </el-alert>
  </div>
</template>

<script setup>
import * as echarts from "echarts";
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { fetchPurchaseTasks, updatePurchaseTask } from "../api/tasks";
import { approvePharmacyPurchaseOrder, rejectPharmacyPurchaseOrder } from "../api/pharmacy";
import { getErrorMessage } from "../utils/status";

const loading = ref(false);
const rows = ref([]);
const lastUpdated = ref("");
const undoBar = ref({ visible: false, title: "", payload: null });
const selected = ref([]);
const processableSelected = computed(() => selected.value.filter((x) => x.status === "待处理"));
let undoTimer = null;
const statusChartRef = ref(null);
const qtyChartRef = ref(null);
let statusChart = null;
let qtyChart = null;
const pendingCount = computed(() => rows.value.filter((x) => String(x.status).includes("待处理")).length);
const approvedCount = computed(() => rows.value.filter((x) => String(x.status).includes("已通过")).length);
const rejectedCount = computed(() => rows.value.filter((x) => String(x.status).includes("已驳回")).length);
const estimatedAmount = computed(() => Math.round(rows.value.reduce((sum, x) => sum + Number(x.suggested_qty || 0) * 10, 0)));

function renderCharts() {
  if (statusChartRef.value && !statusChart) statusChart = echarts.init(statusChartRef.value);
  if (qtyChartRef.value && !qtyChart) qtyChart = echarts.init(qtyChartRef.value);
  statusChart?.setOption({
    tooltip: { trigger: "item" },
    legend: { bottom: 0 },
    series: [{ type: "pie", radius: ["38%", "68%"], data: [
      { name: "待处理", value: pendingCount.value },
      { name: "已通过", value: approvedCount.value },
      { name: "已驳回", value: rejectedCount.value }
    ] }]
  });
  const topRows = [...rows.value].sort((a, b) => Number(b.suggested_qty || 0) - Number(a.suggested_qty || 0)).slice(0, 8);
  qtyChart?.setOption({
    tooltip: { trigger: "axis" },
    xAxis: { type: "value" },
    yAxis: { type: "category", data: topRows.map((x) => String(x.drug_name || x.drug_id)) },
    series: [{ type: "bar", data: topRows.map((x) => Number(x.suggested_qty || 0)), itemStyle: { color: "#3b82f6" } }],
    grid: { left: 110, right: 16, top: 12, bottom: 16 }
  });
}

async function loadData() {
  loading.value = true;
  try {
    const res = await fetchPurchaseTasks();
    rows.value = res.data || [];
    lastUpdated.value = new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
    await nextTick();
    renderCharts();
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "审批数据加载失败"));
  } finally {
    loading.value = false;
  }
}

function onSelectionChange(v) {
  selected.value = v || [];
}

function showUndo(title, payload) {
  if (undoTimer) window.clearTimeout(undoTimer);
  undoBar.value = { visible: true, title, payload };
  undoTimer = window.setTimeout(() => {
    undoBar.value.visible = false;
  }, 5000);
}

async function approve(row) {
  if (row.status === "已撤回") return;
  try {
    const prev = row.status;
    await approvePharmacyPurchaseOrder(row.id);
    ElMessage.success("已通过");
    showUndo(`已通过 [${row.drug_name || row.drug_id}] 的采购申请`, { id: row.id, status: prev || "待处理" });
    await loadData();
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "审批失败"));
  }
}

async function reject(row) {
  if (row.status === "已撤回") return;
  try {
    const prev = row.status;
    await rejectPharmacyPurchaseOrder(row.id);
    ElMessage.success("已驳回");
    showUndo(`已驳回 [${row.drug_name || row.drug_id}] 的采购申请`, { id: row.id, status: prev || "待处理" });
    await loadData();
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "审批失败"));
  }
}

async function undoAction() {
  const payload = undoBar.value.payload;
  if (!payload) return;
  try {
    await updatePurchaseTask(payload.id, { status: payload.status });
    ElMessage.success("已撤销审批操作");
    await loadData();
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "撤销失败"));
  } finally {
    undoBar.value.visible = false;
  }
}

async function batchApprove() {
  const rows = [...processableSelected.value];
  for (const row of rows) {
    await approvePharmacyPurchaseOrder(row.id);
  }
  ElMessage.success(`已批准${rows.length}条采购申请，共涉及药品${new Set(rows.map((x) => x.drug_id)).size}种`);
  selected.value = [];
  await loadData();
}

async function batchReject() {
  let reason = "";
  try {
    reason = await ElMessageBox.prompt("请填写驳回原因", "批量驳回", { confirmButtonText: "确认", cancelButtonText: "取消", inputPlaceholder: "请输入原因" }).then((r) => r.value || "");
  } catch {
    return;
  }
  const rows = [...processableSelected.value];
  for (const row of rows) {
    await updatePurchaseTask(row.id, { status: `已驳回:${reason}` });
  }
  ElMessage.success(`已驳回${rows.length}条采购申请`);
  selected.value = [];
  await loadData();
}

function rowClassName({ row }) {
  return row.status === "已撤回" ? "withdrawn-row" : "";
}

onMounted(loadData);

onBeforeUnmount(() => {
  statusChart?.dispose();
  qtyChart?.dispose();
});
</script>

<style scoped>
.page { padding: 16px; }
.header-row { display: flex; justify-content: space-between; align-items: center; }
.list-meta { margin-top: 10px; color: #909399; font-size: 12px; }
.kpi-label { color: #64748b; font-size: 12px; }
.kpi-value { margin-top: 4px; font-size: 24px; font-weight: 700; color: #0f172a; }
.kpi-value.success { color: #16a34a; }
.kpi-value.warning { color: #f59e0b; }
.kpi-value.danger { color: #ef4444; }
.chart { height: 260px; background: #fff; border-radius: 12px; border: 1px solid #e5e7eb; }
.undo-bar {
  position: fixed;
  right: 20px;
  bottom: 20px;
  width: 380px;
  z-index: 3000;
}
:deep(.withdrawn-row > td) {
  background: #f1f5f9 !important;
  color: #94a3b8 !important;
}
.disabled-action {
  cursor: not-allowed !important;
}
</style>
