<template>
  <div class="page layout-bg">
    <el-card class="glass-card">
      <template #header>
        <div class="header-row">
          <span class="page-title">药房EOQ智能补货建议</span>
          <el-space>
            <el-select v-model="branchCode" style="width: 150px" @change="loadData">
              <el-option label="沙河口院区" value="C001" />
              <el-option label="甘井子院区" value="C002" />
              <el-option label="高新园区院区" value="C003" />
            </el-select>
            <el-button class="agile-btn" :loading="loading" @click="loadData">刷新</el-button>
          </el-space>
        </div>
      </template>
      <div class="algo-card glass-card">
        📊 智能补货引擎：基于EOQ经济订货批量模型，综合历史30天消耗数据、采购提前期（5天）、持有成本（单价×20%）及季节消耗系数，自动计算最优订货时机与批量。公式：Q* = √(2DS/H) × 季节系数α，当前季节系数α = {{ seasonalAlpha }}
      </div>
      <div ref="totalTrendRef" class="trend-chart total-trend" />

      <el-empty v-if="rows.length === 0" description="暂无补货建议数据" />
      <el-table v-else :data="rows" border @row-click="openDrawer">
        <el-table-column prop="drug_name" label="药品名称" min-width="180" />
        <el-table-column prop="current_stock" label="当前库存" width="100" />
        <el-table-column prop="daily_demand" label="日均消耗量" width="110" />
        <el-table-column prop="safety_stock" label="安全库存" width="100" />
        <el-table-column label="EOQ建议补货量" width="180">
          <template #default="{ row }">
            <el-space>
              <span>{{ row.eoq_qty }}</span>
              <el-tooltip :content="`D=${row.eoq_formula_params?.D || '-'}单位/年，S=¥${row.eoq_formula_params?.S || '-'}，H=¥${row.eoq_formula_params?.H || '-'}，Q*=${row.eoq_formula_params?.Q || '-'}盒`">
                <span class="hint">ℹ️</span>
              </el-tooltip>
            </el-space>
          </template>
        </el-table-column>
        <el-table-column prop="estimated_depletion_date" label="预计耗尽日期" width="140" />
        <el-table-column label="库存状态" width="120">
          <template #default="{ row }">
            <el-tag :type="stockTagType(row)">{{ stockStatusText(row) }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
      <div class="season-notes">
        <div v-for="item in rows" :key="item.drug_id" class="season-item">{{ item.seasonal_note }}</div>
      </div>

      <div class="footer-row">
        <el-button class="agile-btn" type="primary" :loading="creating" @click="createPurchaseList">
          ⚡一键生成采购清单
        </el-button>
      </div>
    </el-card>

    <el-drawer v-model="drawerVisible" title="近30天消耗趋势" size="500px">
      <template v-if="activeRow">
        <div class="trend-title">{{ activeRow.drug_name }}</div>
        <div ref="trendChartRef" class="trend-chart" />
      </template>
      <el-empty v-else description="暂无统计数据" />
    </el-drawer>
  </div>
</template>

<script setup>
import * as echarts from "echarts";
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { ElMessage } from "element-plus";

import { fetchEoqSuggestions, createPharmacyPurchaseOrder } from "../api/pharmacy";
import { getErrorMessage } from "../utils/status";

const loading = ref(false);
const creating = ref(false);
const branchCode = ref("C001");
const rows = ref([]);
const drawerVisible = ref(false);
const activeRow = ref(null);
const trendChartRef = ref(null);
const totalTrendRef = ref(null);
const seasonalAlpha = ref(1);
let trendChart = null;
let totalTrendChart = null;
let resizeObserver = null;
let onWindowResize = null;

function stockTagType(row) {
  const current = Number(row.current_stock || 0);
  const safety = Number(row.safety_stock || 0);
  if (current > safety * 1.5) return "success";
  if (current >= safety) return "warning";
  return "danger";
}

function stockStatusText(row) {
  const current = Number(row.current_stock || 0);
  const safety = Number(row.safety_stock || 0);
  if (current > safety * 1.5) return "充足";
  if (current >= safety) return "预警";
  return "紧急";
}

async function loadData() {
  loading.value = true;
  try {
    const res = await fetchEoqSuggestions(branchCode.value);
    rows.value = res.data?.rows || [];
    seasonalAlpha.value = Number(res.data?.seasonal_alpha || 1);
    await nextTick();
    if (totalTrendRef.value) {
      if (!totalTrendChart) totalTrendChart = echarts.init(totalTrendRef.value);
      const all = res.data?.aggregate_trend || [];
      const marker = Number(res.data?.reorder_marker_index || 30);
      totalTrendChart.setOption({
        tooltip: { trigger: "axis" },
        xAxis: { type: "category", data: all.map((x) => x.date) },
        yAxis: { type: "value", name: "总消耗量" },
        series: [
          {
            type: "line",
            data: all.map((x) => x.consumed),
            smooth: true,
            lineStyle: { width: 2, color: "#3B82F6" },
            markLine: {
              symbol: "none",
              data: [{ xAxis: all[Math.min(marker, all.length - 1)]?.date || "" }],
              lineStyle: { color: "#EF4444", width: 2 }
            }
          }
        ]
      });
    }
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "EOQ建议加载失败"));
  } finally {
    loading.value = false;
  }
}

async function renderTrend() {
  await nextTick();
  if (!trendChartRef.value || !activeRow.value) return;
  if (!trendChart) trendChart = echarts.init(trendChartRef.value);
  const trend = activeRow.value.trend_30d || [];
  trendChart.setOption({
    tooltip: { trigger: "axis" },
    xAxis: { type: "category", data: trend.map((x) => x.date) },
    yAxis: { type: "value", name: "当日消耗量" },
    series: [
      {
        name: "当日消耗量",
        type: "line",
        smooth: true,
        data: trend.map((x) => Number(x.consumed || 0)),
        lineStyle: { color: "#3B82F6", width: 2 },
      },
      {
        name: "安全库存警戒线",
        type: "line",
        data: trend.map(() => Number(activeRow.value.safety_stock || 0)),
        symbol: "none",
        lineStyle: { color: "#EF4444", type: "dashed", width: 2 },
      },
    ],
  });
  trendChart.resize();
}

async function openDrawer(row) {
  activeRow.value = row;
  drawerVisible.value = true;
  await renderTrend();
}

async function createPurchaseList() {
  creating.value = true;
  try {
    const res = await createPharmacyPurchaseOrder(branchCode.value);
    const count = Number(res?.data?.count || 0);
    ElMessage.success(`已生成采购清单，共${count}种药品，已通知院区主任审批`);
    await loadData();
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "采购清单生成失败"));
  } finally {
    creating.value = false;
  }
}

watch(drawerVisible, async (visible) => {
  if (!visible) return;
  await nextTick();
  trendChart?.resize();
});

onMounted(() => {
  onWindowResize = () => {
    totalTrendChart?.resize();
    trendChart?.resize();
  };
  window.addEventListener("resize", onWindowResize);
  resizeObserver = new ResizeObserver(() => {
    totalTrendChart?.resize();
    trendChart?.resize();
  });
  if (totalTrendRef.value) resizeObserver.observe(totalTrendRef.value);
  if (trendChartRef.value) resizeObserver.observe(trendChartRef.value);
  loadData();
});
onBeforeUnmount(() => {
  if (onWindowResize) {
    window.removeEventListener("resize", onWindowResize);
    onWindowResize = null;
  }
  if (resizeObserver) {
    resizeObserver.disconnect();
    resizeObserver = null;
  }
  if (trendChart) {
    trendChart.dispose();
    trendChart = null;
  }
  if (totalTrendChart) {
    totalTrendChart.dispose();
    totalTrendChart = null;
  }
});
</script>

<style scoped>
.layout-bg {
  background: var(--bg-page);
  padding: 16px;
}
.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.page-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-main);
}
.footer-row {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
.algo-card {
  border-left: 4px solid #3b82f6;
  padding: 12px;
  margin-bottom: 12px;
}
.trend-title {
  font-weight: 700;
  margin-bottom: 8px;
}
.trend-chart {
  width: 100%;
  height: 320px;
}
.total-trend { margin-bottom: 12px; }
.hint { cursor: pointer; }
.season-notes { margin-top: 10px; color: #64748b; font-size: 12px; }
.season-item { margin: 4px 0; }
</style>

