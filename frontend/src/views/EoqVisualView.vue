<template>
  <div class="page">
    <el-card>
      <template #header>
        <div class="header-row">
          <span>EOQ补货建议（可视化）</span>
          <el-button :loading="loading" @click="loadData">刷新</el-button>
        </div>
      </template>
      <el-row :gutter="12" class="mb12">
        <el-col :span="6"><el-card><div class="k">低库存药品</div><div class="v warning">{{ lowCount }}</div></el-card></el-col>
        <el-col :span="6"><el-card><div class="k">平均EOQ</div><div class="v">{{ avgEoq }}</div></el-card></el-col>
      </el-row>
      <div ref="chartRef" class="chart"></div>
      <el-table :data="rows" border>
        <el-table-column prop="drug_name" label="药品" min-width="160" />
        <el-table-column prop="stock_qty" label="当前库存" width="110" />
        <el-table-column prop="safety_stock" label="安全库存" width="110" />
        <el-table-column prop="eoq" label="建议补货量" width="120" />
      </el-table>
      <div class="list-meta">共{{ rows.length }}条记录，最后更新时间 {{ lastUpdated || "--:--" }}</div>
    </el-card>
  </div>
</template>

<script setup>
import * as echarts from "echarts";
import { computed, nextTick, onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import { calculateEoq, fetchInventoryOverview } from "../api/inventory";
import { getErrorMessage } from "../utils/status";

const loading = ref(false);
const rows = ref([]);
const lastUpdated = ref("");
const chartRef = ref(null);
let chart = null;
const lowCount = computed(() => rows.value.filter((x) => Number(x.stock_qty) < Number(x.safety_stock)).length);
const avgEoq = computed(() => {
  if (rows.value.length === 0) return 0;
  return Math.round(rows.value.reduce((s, x) => s + Number(x.eoq || 0), 0) / rows.value.length);
});

async function loadData() {
  loading.value = true;
  try {
    const [overview, eoqRes] = await Promise.all([
      fetchInventoryOverview("C001"),
      calculateEoq({ annual_demand: 1095, order_cost: 50, holding_cost: 3, lead_time_days: 5, daily_demand: 3 })
    ]);
    const eoq = Math.round(eoqRes.data.eoq || 0);
    rows.value = (overview.data || []).map((x) => ({
      ...x,
      eoq
    }));
    lastUpdated.value = new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
    await renderChart();
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "EOQ数据加载失败"));
  } finally {
    loading.value = false;
  }
}

async function renderChart() {
  await nextTick();
  if (!chartRef.value) return;
  if (!chart) chart = echarts.init(chartRef.value);
  chart.setOption({
    tooltip: { trigger: "axis" },
    legend: { data: ["当前库存", "安全库存", "EOQ建议"] },
    xAxis: { type: "category", data: rows.value.map((x) => x.drug_name || `药品${x.drug_id}`) },
    yAxis: { type: "value" },
    series: [
      { name: "当前库存", type: "bar", data: rows.value.map((x) => Number(x.stock_qty || 0)) },
      { name: "安全库存", type: "bar", data: rows.value.map((x) => Number(x.safety_stock || 0)) },
      { name: "EOQ建议", type: "line", data: rows.value.map((x) => Number(x.eoq || 0)) }
    ]
  });
}

onMounted(loadData);
</script>

<style scoped>
.page { padding: 16px; }
.header-row { display: flex; justify-content: space-between; align-items: center; }
.mb12 { margin-bottom: 12px; }
.k { color: #909399; }
.v { font-size: 28px; font-weight: 700; color: #42b983; }
.v.warning { color: #e6a23c; }
.chart { width: 100%; height: 360px; margin-bottom: 12px; }
.list-meta { margin-top: 10px; color: #909399; font-size: 12px; }
</style>
