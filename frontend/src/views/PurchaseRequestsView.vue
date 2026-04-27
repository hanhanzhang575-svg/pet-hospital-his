<template>
  <div class="page">
    <el-card class="glass-card">
      <template #header>
        <div class="header-row">
          <span>采购申请（药房）</span>
          <el-space>
            <el-button :loading="loading" @click="loadData">刷新</el-button>
            <el-button type="primary" :loading="creating" @click="createFromLowStock">按低库存生成</el-button>
          </el-space>
        </div>
      </template>
      <el-empty v-if="rows.length === 0" description="库存充足，暂无采购需求" />
      <el-table v-else :data="rows" border :row-class-name="rowClassName">
        <el-table-column prop="id" label="任务ID" width="90" />
        <el-table-column prop="drug_name" label="药品" min-width="160" />
        <el-table-column prop="current_stock" label="当前库存" width="110" />
        <el-table-column prop="safety_stock" label="安全库存" width="110" />
        <el-table-column prop="suggested_qty" label="建议采购量" width="120" />
        <el-table-column prop="status" label="状态" width="120" />
        <el-table-column label="操作" width="220">
          <template #default="{ row }">
            <el-tooltip v-if="row.status === '已撤回'" content="已撤回">
              <el-button size="small" type="info" disabled class="disabled-action">撤回</el-button>
            </el-tooltip>
            <el-button v-else size="small" type="warning" @click="recall(row)" :disabled="row.status !== '待处理'">撤回</el-button>
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
import { onMounted, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { fetchInventoryOverview } from "../api/inventory";
import { fetchPurchaseTasks, updatePurchaseTask } from "../api/tasks";
import { createPharmacyPurchaseOrder } from "../api/pharmacy";
import { getErrorMessage } from "../utils/status";

const loading = ref(false);
const creating = ref(false);
const rows = ref([]);
const lastUpdated = ref("");
const undoBar = ref({ visible: false, title: "", payload: null });
let undoTimer = null;

async function loadData() {
  loading.value = true;
  try {
    const res = await fetchPurchaseTasks();
    rows.value = res.data || [];
    lastUpdated.value = new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "采购任务加载失败"));
  } finally {
    loading.value = false;
  }
}

async function createFromLowStock() {
  creating.value = true;
  try {
    const inv = await fetchInventoryOverview("C001");
    const branch = inv.data?.[0]?.branch_code || "C001";
    const lowCount = (inv.data || []).filter((x) => Number(x.stock_qty) < Number(x.safety_stock)).length;
    if (lowCount === 0) {
      ElMessage.warning("当前无低库存药品");
      return;
    }
    await createPharmacyPurchaseOrder(branch);
    ElMessage.success("已按EOQ规则生成采购申请");
    await loadData();
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "生成采购申请失败"));
  } finally {
    creating.value = false;
  }
}

function showUndo(title, payload) {
  if (undoTimer) window.clearTimeout(undoTimer);
  undoBar.value = { visible: true, title, payload };
  undoTimer = window.setTimeout(() => {
    undoBar.value.visible = false;
  }, 5000);
}

async function recall(row) {
  try {
    await ElMessageBox.confirm(
      "确定撤回该采购申请？撤回后院长将无法审批此单",
      "撤回确认",
      { confirmButtonText: "确认撤回", cancelButtonText: "取消", type: "warning" }
    );
  } catch {
    return;
  }
  try {
    await updatePurchaseTask(row.id, { status: "已撤回" });
    ElMessage.success("采购申请已撤回");
    showUndo("采购申请已撤回，可在5秒内撤销", { id: row.id, status: row.status || "待处理" });
    await loadData();
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "撤回失败"));
  }
}

function rowClassName({ row }) {
  return row.status === "已撤回" ? "withdrawn-row" : "";
}

async function undoAction() {
  const payload = undoBar.value.payload;
  if (!payload) return;
  try {
    await updatePurchaseTask(payload.id, { status: payload.status });
    ElMessage.success("已撤销撤回操作");
    await loadData();
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "撤销失败"));
  } finally {
    undoBar.value.visible = false;
  }
}

onMounted(loadData);
</script>

<style scoped>
.page { padding: 16px; }
.header-row { display: flex; justify-content: space-between; align-items: center; }
.list-meta { margin-top: 10px; color: #909399; font-size: 12px; }
.undo-bar {
  position: fixed;
  left: 50%;
  transform: translateX(-50%);
  bottom: 16px;
  width: 360px;
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
