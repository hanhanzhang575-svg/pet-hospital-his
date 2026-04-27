<template>
  <el-skeleton :loading="loading" :rows="6" animated>
    <template #default>
      <el-row :gutter="12">
        <el-col :span="6"><el-card class="glass-card"><div class="k">三院区门诊量</div><div class="v">{{ stats.outpatient }}</div></el-card></el-col>
        <el-col :span="6"><el-card class="glass-card"><div class="k">笼舍占用率</div><div class="v warning">{{ stats.cageUsage }}%</div></el-card></el-col>
        <el-col :span="6"><el-card class="glass-card"><div class="k">库存状态</div><div class="v">{{ stats.stockStatus }}</div></el-card></el-col>
        <el-col :span="6"><el-card class="glass-card"><div class="k">今日营收</div><div class="v">¥{{ stats.revenue }}</div></el-card></el-col>
      </el-row>
      <el-row :gutter="12" class="mt12">
        <el-col :span="24">
          <el-card class="glass-card" @click="goInpatient">
            <div class="k">⚠️ 押金预警汇总</div>
            <div class="v warning">当前有{{ depositWarn.count }}位住院宠物押金不足，其中{{ depositWarn.stopped }}位已触发停药，请及时处理</div>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="12" class="mt12">
        <el-col :span="24">
          <el-card class="glass-card">
            <template #header>近7天三院区门诊量对比</template>
            <el-empty v-if="weeklyEmpty" description="暂无统计数据" />
            <div v-else ref="weeklyRef" class="chart" />
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="12" class="mt12">
        <el-col :span="12">
          <el-card class="glass-card">
            <template #header>今日收入结构</template>
            <el-empty v-if="revenueEmpty" description="暂无统计数据" />
            <div v-else ref="revenueRef" class="chart" />
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card class="glass-card">
            <template #header>客户转化漏斗</template>
            <el-empty v-if="funnelEmpty" description="暂无统计数据" />
            <div v-else ref="funnelRef" class="chart" />
          </el-card>
        </el-col>
      </el-row>
    </template>
  </el-skeleton>
</template>

<script setup>
import * as echarts from "echarts";
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import { useRouter } from "vue-router";
import { fetchAppointments } from "../../api/appointments";
import { fetchCages } from "../../api/inpatient";
import { fetchInventoryOverview } from "../../api/inventory";
import { fetchWeeklyVisits, fetchTodayRevenue, fetchConversionFunnel } from "../../api/stats";
import { fetchInpatientRecords } from "../../api/inpatient";
import { getErrorMessage } from "../../utils/status";

const loading = ref(false);
const stats = ref({ outpatient: 0, cageUsage: 0, stockStatus: "良好", revenue: 0 });
const inpatientRows = ref([]);
const router = useRouter();
const depositWarn = computed(() => {
  const low = (inpatientRows.value || []).filter((x) => Number((x.deposit_amount || 0) - (x.consumed_amount || 0)) <= 500);
  return {
    count: low.length,
    stopped: low.filter((x) => Number((x.deposit_amount || 0) - (x.consumed_amount || 0)) <= 0).length,
  };
});

function goInpatient() {
  router.push("/schedule-management");
}

const weeklyRef = ref(null);
const revenueRef = ref(null);
const funnelRef = ref(null);
const weeklyEmpty = ref(false);
const revenueEmpty = ref(false);
const funnelEmpty = ref(false);

let weeklyChart = null;
let revenueChart = null;
let funnelChart = null;
let resizeHandler = null;
let resizeObserver = null;

async function renderWeekly(data) {
  await nextTick();
  if (!weeklyRef.value) return;
  if (!weeklyChart) weeklyChart = echarts.init(weeklyRef.value);
  weeklyChart.setOption({
    tooltip: { trigger: "axis" },
    legend: { top: 0 },
    xAxis: { type: "category", data: data.dates || [] },
    yAxis: { type: "value" },
    series: (data.series || []).map((s, idx) => ({
      name: s.name,
      type: "line",
      smooth: true,
      data: s.data || [],
      lineStyle: { width: 3, color: [ "#3B82F6", "#10B981", "#F59E0B" ][idx] },
    })),
  });
  weeklyChart.resize();
}

async function renderRevenue(data) {
  await nextTick();
  if (!revenueRef.value) return;
  if (!revenueChart) revenueChart = echarts.init(revenueRef.value);
  revenueChart.setOption({
    tooltip: { trigger: "item" },
    legend: { bottom: 0 },
    series: [
      {
        type: "pie",
        radius: ["38%", "68%"],
        data: data || [],
        color: ["#60A5FA", "#34D399", "#FCD34D", "#F9A8D4"],
      },
    ],
  });
  revenueChart.resize();
}

async function renderFunnel(data) {
  await nextTick();
  if (!funnelRef.value) return;
  if (!funnelChart) funnelChart = echarts.init(funnelRef.value);
  funnelChart.setOption({
    tooltip: { trigger: "item" },
    series: [
      {
        type: "funnel",
        left: "10%",
        top: 20,
        bottom: 20,
        width: "80%",
        min: 0,
        max: Math.max(...(data || []).map((x) => Number(x.value || 0)), 1),
        sort: "descending",
        gap: 2,
        label: { show: true, position: "inside" },
        data: data || [],
        color: ["#93C5FD", "#6EE7B7", "#FDE68A", "#FBCFE8"],
      },
    ],
  });
  funnelChart.resize();
}

async function loadData() {
  loading.value = true;
  try {
    const [appt1, appt2, appt3, cages1, inv1, weeklyRes, revenueRes, funnelRes, inpatientRes] = await Promise.all([
      fetchAppointments({ clinicId: "C001" }),
      fetchAppointments({ clinicId: "C002" }),
      fetchAppointments({ clinicId: "C003" }),
      fetchCages("C001"),
      fetchInventoryOverview("C001"),
      fetchWeeklyVisits(),
      fetchTodayRevenue(),
      fetchConversionFunnel(),
      fetchInpatientRecords("C001")
    ]);
    const allAppts = [...(appt1.data || []), ...(appt2.data || []), ...(appt3.data || [])];
    const cageRows = cages1.data || [];
    const busy = cageRows.filter((c) => c.status === "住院中").length;
    const invRows = inv1.data || [];
    const low = invRows.filter((i) => Number(i.stock_qty || 0) < Number(i.safety_stock || 0)).length;
    const revenueTotal = (revenueRes.data || []).reduce((sum, x) => sum + Number(x.value || 0), 0);

    stats.value.outpatient = allAppts.length;
    stats.value.cageUsage = cageRows.length ? Math.round((busy / cageRows.length) * 100) : 0;
    stats.value.stockStatus = low > 5 ? "预警" : "良好";
    stats.value.revenue = revenueTotal.toFixed(0);
    inpatientRows.value = inpatientRes.data || [];

    const weeklyData = weeklyRes.data || {};
    const revenueData = revenueRes.data || [];
    const funnelData = funnelRes.data || [];
    weeklyEmpty.value = !Array.isArray(weeklyData?.dates) || weeklyData.dates.length === 0;
    revenueEmpty.value = !Array.isArray(revenueData) || revenueData.length === 0;
    funnelEmpty.value = !Array.isArray(funnelData) || funnelData.length === 0;

    if (!weeklyEmpty.value) await renderWeekly(weeklyData);
    else if (weeklyChart) weeklyChart.clear();
    if (!revenueEmpty.value) await renderRevenue(revenueData);
    else if (revenueChart) revenueChart.clear();
    if (!funnelEmpty.value) await renderFunnel(funnelData);
    else if (funnelChart) funnelChart.clear();
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "院区主任看板加载失败"));
  } finally {
    loading.value = false;
  }
}

onMounted(async () => {
  resizeHandler = () => {
    weeklyChart?.resize();
    revenueChart?.resize();
    funnelChart?.resize();
  };
  window.addEventListener("resize", resizeHandler);
  resizeObserver = new ResizeObserver(() => {
    weeklyChart?.resize();
    revenueChart?.resize();
    funnelChart?.resize();
  });
  if (weeklyRef.value) resizeObserver.observe(weeklyRef.value);
  if (revenueRef.value) resizeObserver.observe(revenueRef.value);
  if (funnelRef.value) resizeObserver.observe(funnelRef.value);
  await loadData();
});

onBeforeUnmount(() => {
  if (resizeHandler) window.removeEventListener("resize", resizeHandler);
  if (resizeObserver) {
    resizeObserver.disconnect();
    resizeObserver = null;
  }
  weeklyChart?.dispose();
  revenueChart?.dispose();
  funnelChart?.dispose();
  weeklyChart = null;
  revenueChart = null;
  funnelChart = null;
});
</script>

<style scoped>
.k { color: #909399; }
.v { font-size: 30px; font-weight: 700; color: #42b983; }
.v.warning { color: #e6a23c; }
.mt12 { margin-top: 12px; }
.chart { width: 100%; height: 320px; }
</style>

