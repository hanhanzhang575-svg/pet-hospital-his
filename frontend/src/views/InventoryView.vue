<template>
  <div class="page">
    <el-card>
      <template #header>
        <div class="header-row">
          <span>药品库存与EOQ智能补货</span>
          <el-space>
            <el-button :loading="loading" :disabled="loading" @click="loadData">刷新</el-button>
            <el-button type="primary" :disabled="loading || lowStockRows.length === 0" @click="exportCsv">
              一键生成采购清单
            </el-button>
            <el-button type="primary" :disabled="loading || lowStockRows.length === 0" @click="createPurchase">
              生成采购任务
            </el-button>
          </el-space>
        </div>
      </template>

      <el-skeleton :loading="loading" :rows="6" animated>
        <template #default>
          <el-alert v-if="loadError" type="error" :title="loadError" show-icon :closable="false" style="margin-bottom: 12px">
            <template #default>
              <el-button size="small" @click="loadData">重试</el-button>
            </template>
          </el-alert>
          <el-table :data="tableRows" border @expand-change="onExpand">
            <el-table-column type="expand">
              <template #default="{ row }">
                <div class="trend-wrap">
                  <div class="trend-title">近30天消耗趋势（模拟）- {{ row.drug_name || `药品ID ${row.drug_id}` }}</div>
                  <div :id="`trend-${row.drug_id}`" class="trend-chart" />
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="drug_id" label="药品ID" width="90" />
            <el-table-column prop="drug_name" label="药品名称" min-width="140" />
            <el-table-column prop="stock_qty" label="当前库存" width="100" />
            <el-table-column prop="safety_stock" width="150">
              <template #header>
                <div class="label-help">
                  EOQ安全阈值
                  <el-tooltip content="EOQ安全阈值：保证采购周期内不断货的最小库存线。低于该值建议立即补货。" placement="top">
                    <span class="help-icon">?</span>
                  </el-tooltip>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="eoq" label="EOQ建议补货量" width="140" />
            <el-table-column prop="estimated_depletion_days" label="预计耗尽天数" width="130" />
            <el-table-column label="库存状态" width="160">
              <template #default="{ row }">
                <el-tag :type="stockTagType(row)">{{ stockStatusText(row) }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </template>
      </el-skeleton>
    </el-card>
  </div>
</template>

<script setup>
import * as echarts from "echarts";
import { computed, nextTick, onMounted, ref } from "vue";
import { ElMessage, ElNotification } from "element-plus";

import { calculateEoq, fetchInventoryOverview } from "../api/inventory";
import { createPharmacyPurchaseOrder } from "../api/pharmacy";
import { getErrorMessage } from "../utils/status";

const loading = ref(false);
const loadError = ref("");
const tableRows = ref([]);

const lowStockRows = computed(() =>
  tableRows.value.filter((item) => Number(item.stock_qty || 0) < Number(item.safety_stock || 0))
);

function stockTagType(row) {
  const stock = Number(row.stock_qty || 0);
  const safety = Number(row.safety_stock || 0);
  if (stock < safety) return "danger";
  if (stock < safety * 1.2) return "warning";
  return "success";
}

function stockStatusText(row) {
  const stock = Number(row.stock_qty || 0);
  const safety = Number(row.safety_stock || 0);
  if (stock < safety) return "低于安全库存（已冻结）";
  if (stock < safety * 1.2) return "接近阈值";
  return "库存充足";
}

function estimateDepletionDays(stockQty) {
  const daily = 3;
  return Math.max(1, Math.floor(Number(stockQty || 0) / daily));
}

async function loadData() {
  loading.value = true;
  loadError.value = "";
  try {
    const overview = await fetchInventoryOverview("C001");
    const rows = (overview.data || []).map((item, idx) => ({
      drug_id: item.drug_id,
      drug_name: item.drug_name,
      stock_qty: Number(item.stock_qty || 0),
      safety_stock: Number(item.safety_stock || 0),
      eoq: 0,
      estimated_depletion_days: estimateDepletionDays(item.stock_qty),
      trend: Array.from({ length: 30 }, (_x, i) => Math.max(1, Math.round(5 + Math.sin(i / 4) * 2 + (idx % 3))))
    }));
    const eoqResult = await calculateEoq({
      annual_demand: 365 * 3,
      order_cost: 50,
      holding_cost: 3,
      lead_time_days: 5,
      daily_demand: 3
    });
    const eoqValue = Math.round(eoqResult.data.eoq || 0);
    rows.forEach((row) => {
      row.eoq = eoqValue;
    });
    tableRows.value = rows;
    const lowCount = rows.filter((row) => Number(row.stock_qty) < Number(row.safety_stock)).length;
    if (lowCount > 0) {
      ElNotification({
        title: "库存低于安全阈值",
        message: `当前有 ${lowCount} 种药品低于安全库存，请尽快补货。`,
        type: "warning",
        duration: 5000,
        position: "bottom-right"
      });
    }
  } catch (error) {
    loadError.value = getErrorMessage(error, "库存数据加载失败");
    ElMessage.error(loadError.value);
  } finally {
    loading.value = false;
  }
}

async function onExpand(row, expandedRows) {
  if (!expandedRows.find((item) => item.drug_id === row.drug_id)) return;
  await nextTick();
  const container = document.getElementById(`trend-${row.drug_id}`);
  if (!container) return;
  const chart = echarts.init(container);
  chart.setOption({
    xAxis: { type: "category", data: Array.from({ length: 30 }, (_x, i) => `${i + 1}`) },
    yAxis: { type: "value" },
    series: [{ type: "line", smooth: true, data: row.trend }]
  });
}

function exportCsv() {
  const headers = ["drug_id", "drug_name", "stock_qty", "safety_stock", "eoq", "estimated_depletion_days"];
  const lines = [headers.join(",")];
  for (const row of lowStockRows.value) {
    lines.push([row.drug_id, row.drug_name, row.stock_qty, row.safety_stock, row.eoq, row.estimated_depletion_days].join(","));
  }
  const blob = new Blob([`\ufeff${lines.join("\n")}`], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "采购清单.csv";
  a.click();
  URL.revokeObjectURL(url);
  ElMessage.success("采购清单已导出");
}

async function createPurchase() {
  try {
    const result = await createPharmacyPurchaseOrder("C001");
    ElMessage.success(`已创建 ${Number(result?.data?.count || 0)} 条采购任务`);
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "采购任务创建失败"));
  }
}

onMounted(async () => {
  await loadData();
});
</script>

<style scoped>
.page {
  padding: 16px;
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.trend-wrap {
  padding: 8px;
}

.trend-title {
  margin-bottom: 8px;
  font-size: 13px;
  color: #606266;
}

.trend-chart {
  width: 100%;
  height: 220px;
}

.label-help {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.help-icon {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #909399;
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
}
</style>

