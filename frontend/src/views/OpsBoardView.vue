<template>
  <div class="ops-page">
    <el-row :gutter="16">
      <el-col :xs="24" :sm="12" :md="6" :lg="6">
        <el-card class="kpi-card primary-border" shadow="hover">
          <div class="kpi-content">
            <div class="kpi-label">总门诊量 <span class="tag">今日</span></div>
            <div class="kpi-value">{{ stats.totalOutpatient }}</div>
          </div>
          <div class="kpi-icon icon-blue">👥</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6" :lg="6">
        <el-card class="kpi-card warning-border" shadow="hover">
          <div class="kpi-content">
            <div class="kpi-label">笼舍占用率 <span class="tag">实时</span></div>
            <div class="kpi-value warning">{{ stats.cageRate }}<span class="unit">%</span></div>
          </div>
          <div class="kpi-icon icon-orange">🐾</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6" :lg="6">
        <el-card class="kpi-card danger-border" shadow="hover">
          <div class="kpi-content">
            <div class="kpi-label">低库存药品 <span class="tag">需关注</span></div>
            <div class="kpi-value danger">{{ stats.lowStock }}<span class="unit">项</span></div>
          </div>
          <div class="kpi-icon icon-red">💊</div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6" :lg="6">
        <el-card class="kpi-card success-border" shadow="hover">
          <div class="kpi-content">
            <div class="kpi-label">估算营收 <span class="tag">预估</span></div>
            <div class="kpi-value success"><span class="unit">¥</span>{{ stats.income }}</div>
          </div>
          <div class="kpi-icon icon-green">💰</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :xs="24" :md="14" :lg="15">
        <el-card class="panel-card" shadow="never">
          <template #header>
            <div class="panel-header">
              <span class="panel-title">院区运营趋势</span>
              <span class="panel-subtitle">门诊量 vs 营收</span>
            </div>
          </template>
          <div ref="trendRef" class="chart chart-lg" />
        </el-card>
      </el-col>
      <el-col :xs="24" :md="10" :lg="9">
        <el-card class="panel-card" shadow="never">
          <template #header>
            <div class="panel-header">
              <span class="panel-title">收入结构分析</span>
              <span class="panel-subtitle">3D 分布概览</span>
            </div>
          </template>
          <div ref="income3dRef" class="chart chart-lg" />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :xs="24" :md="12" :lg="8">
        <el-card class="panel-card" shadow="never">
          <template #header><div class="panel-title">复诊率与满意度</div></template>
          <div ref="qualityRef" class="chart chart-mid" />
        </el-card>
      </el-col>
      <el-col :xs="24" :md="12" :lg="8">
        <el-card class="panel-card" shadow="never">
          <template #header><div class="panel-title">科室资源热力</div></template>
          <div ref="heatRef" class="chart chart-mid" />
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="8">
        <el-card class="panel-card advice-card" shadow="never">
          <template #header>
            <div class="panel-header">
              <span class="panel-title">AI 运营建议</span>
              <span class="pulse-dot"></span>
            </div>
          </template>
          <div class="advice-list">
            <div class="advice-item">
              <div class="advice-dot blue"></div>
              <div class="advice-text"><b>沙河口院区：</b>今日门诊集中，建议晚间增加一名全科医生。</div>
            </div>
            <div class="advice-item">
              <div class="advice-dot orange"></div>
              <div class="advice-text"><b>甘井子院区：</b>笼舍周转慢，建议优先完成待出院评估。</div>
            </div>
            <div class="advice-item">
              <div class="advice-dot red"></div>
              <div class="advice-text"><b>高新园区：</b>药耗偏高，需同步采购审批与处方结构复盘。</div>
            </div>
            <div class="advice-item">
              <div class="advice-dot green"></div>
              <div class="advice-text"><b>全局策略：</b>建议本周主推“体检+驱虫”套餐提升中风险用户复诊率。</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import * as echarts from "echarts";
import "echarts-gl";
import { nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import { fetchAppointments } from "../api/appointments";
import { fetchInventoryOverview } from "../api/inventory";
import { fetchInpatientRecords } from "../api/inpatient";

const trendRef = ref(null);
const income3dRef = ref(null);
const qualityRef = ref(null);
const heatRef = ref(null);
let trendChart = null;
let income3dChart = null;
let qualityChart = null;
let heatChart = null;

const stats = ref({ totalOutpatient: 0, cageRate: 0, lowStock: 0, income: 0 });

function ensureCharts() {
  if (trendRef.value && !trendChart) trendChart = echarts.init(trendRef.value);
  if (income3dRef.value && !income3dChart) income3dChart = echarts.init(income3dRef.value);
  if (qualityRef.value && !qualityChart) qualityChart = echarts.init(qualityRef.value);
  if (heatRef.value && !heatChart) heatChart = echarts.init(heatRef.value);
}

// 保持原有的数据处理逻辑不变
async function loadData() {
  const [a1, a2, a3, inv, i1, i2, i3] = await Promise.all([
    fetchAppointments({ clinicId: "C001", limit: 80 }),
    fetchAppointments({ clinicId: "C002", limit: 80 }),
    fetchAppointments({ clinicId: "C003", limit: 80 }),
    fetchInventoryOverview("C001"),
    fetchInpatientRecords("C001"),
    fetchInpatientRecords("C002"),
    fetchInpatientRecords("C003")
  ]);
  const r1 = a1.data || [];
  const r2 = a2.data || [];
  const r3 = a3.data || [];
  const rows = [...r1, ...r2, ...r3];
  
  stats.value.totalOutpatient = rows.length;
  
  const totalBeds = 72;
  const occupied = [...(i1.data || []), ...(i2.data || []), ...(i3.data || [])].filter((x) => x.status !== "已出院").length;
  stats.value.cageRate = Math.round((occupied / totalBeds) * 100);
  
  stats.value.lowStock = (inv.data || []).filter((x) => Number(x.stock_qty) < Number(x.safety_stock)).length;
  stats.value.income = Math.round(rows.reduce((s, x) => s + Number(x.priority_score || 0) * 12, 0));

  await nextTick();
  ensureCharts();

  // 优化：趋势图增加渐变色、平滑曲线、隐藏无用网格线
  trendChart?.setOption({
    tooltip: { trigger: "axis", backgroundColor: 'rgba(255, 255, 255, 0.9)', borderRadius: 8 },
    legend: { data: ["门诊量", "估算营收"], bottom: 0, icon: 'circle' },
    grid: { top: 40, right: 10, bottom: 40, left: 40, containLabel: true },
    xAxis: { type: "category", data: ["沙河口", "甘井子", "高新园区"], axisLine: { lineStyle: { color: '#e2e8f0' } }, axisLabel: { color: '#64748b' } },
    yAxis: [
      { type: "value", name: "门诊量", nameTextStyle: { color: '#94a3b8' }, splitLine: { lineStyle: { type: 'dashed', color: '#f1f5f9' } }, axisLabel: { color: '#64748b' } },
      { type: "value", name: "营收", nameTextStyle: { color: '#94a3b8' }, splitLine: { show: false }, axisLabel: { color: '#64748b' } }
    ],
    series: [
      { 
        name: "门诊量", type: "bar", barWidth: '30%', data: [r1.length, r2.length, r3.length], 
        itemStyle: { 
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: '#60a5fa' }, { offset: 1, color: '#3b82f6' }]),
          borderRadius: [4, 4, 0, 0]
        } 
      },
      { 
        name: "估算营收", type: "line", yAxisIndex: 1, data: [3200 + r1.length * 12, 4100 + r2.length * 10, 3600 + r3.length * 11], 
        smooth: true, symbolSize: 8, 
        itemStyle: { color: "#f59e0b" },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(245, 158, 11, 0.2)' }, { offset: 1, color: 'rgba(245, 158, 11, 0)' }])
        }
      }
    ]
  });

  // 优化：3D柱状图调整视角和色彩主题
  income3dChart?.setOption({
    tooltip: { backgroundColor: 'rgba(255, 255, 255, 0.9)' },
    xAxis3D: { type: "category", data: ["门诊", "住院", "药房"], name: '' },
    yAxis3D: { type: "category", data: ["沙河口", "甘井子", "高新园区"], name: '' },
    zAxis3D: { type: "value", name: "" },
    grid3D: { 
      boxWidth: 140, boxDepth: 80, 
      viewControl: { alpha: 25, beta: 35, distance: 250 },
      axisLine: { lineStyle: { color: '#cbd5e1' } },
      axisPointer: { lineStyle: { color: '#94a3b8' } }
    },
    series: [{
      type: "bar3D",
      data: [
        [0, 0, 1200], [1, 0, 980], [2, 0, 760],
        [0, 1, 1100], [1, 1, 860], [2, 1, 690],
        [0, 2, 1020], [1, 2, 910], [2, 2, 720]
      ],
      shading: "lambert",
      itemStyle: { color: '#10b981', opacity: 0.9 }
    }]
  });

  // 优化：质量图表美化
  qualityChart?.setOption({
    tooltip: { trigger: "axis" },
    legend: { data: ["复诊率", "满意度"], bottom: 0, icon: 'circle' },
    grid: { top: 30, right: 10, bottom: 30, left: 10, containLabel: true },
    xAxis: { type: "category", data: ["沙河口", "甘井子", "高新园区"], axisLine: { lineStyle: { color: '#e2e8f0' } }, axisLabel: { color: '#64748b' } },
    yAxis: { type: "value", max: 100, splitLine: { lineStyle: { type: 'dashed', color: '#f1f5f9' } }, axisLabel: { color: '#64748b' } },
    series: [
      { 
        name: "复诊率", type: "bar", barWidth: '25%', data: [62, 58, 65], 
        itemStyle: { color: '#22c55e', borderRadius: [4, 4, 0, 0] } 
      },
      { 
        name: "满意度", type: "line", data: [91, 89, 93], smooth: true, symbolSize: 8,
        itemStyle: { color: "#8b5cf6" } 
      }
    ]
  });

  // 优化：热力图调色盘和边距
  heatChart?.setOption({
    tooltip: { position: "top", backgroundColor: 'rgba(255, 255, 255, 0.9)' },
    grid: { top: 20, right: 10, bottom: 60, left: 10, containLabel: true },
    xAxis: { type: "category", data: ["内科", "外科", "影像", "检验", "护理", "药房"], axisLine: { show: false }, axisTick: { show: false } },
    yAxis: { type: "category", data: ["沙河口", "甘井子", "高新园区"], axisLine: { show: false }, axisTick: { show: false } },
    visualMap: { 
      min: 0, max: 100, calculable: true, orient: "horizontal", left: "center", bottom: 0,
      inRange: { color: ['#eff6ff', '#bfdbfe', '#60a5fa', '#2563eb'] }
    },
    series: [{
      type: "heatmap",
      data: [
        [0, 0, 82], [1, 0, 65], [2, 0, 58], [3, 0, 74], [4, 0, 90], [5, 0, 68],
        [0, 1, 76], [1, 1, 61], [2, 1, 54], [3, 1, 70], [4, 1, 86], [5, 1, 63],
        [0, 2, 80], [1, 2, 64], [2, 2, 57], [3, 2, 73], [4, 2, 88], [5, 2, 67]
      ],
      itemStyle: { borderColor: '#fff', borderWidth: 2, borderRadius: 4 }
    }]
  });
}

function onResize() {
  trendChart?.resize();
  income3dChart?.resize();
  qualityChart?.resize();
  heatChart?.resize();
}

onMounted(async () => {
  await loadData();
  window.addEventListener("resize", onResize);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", onResize);
  trendChart?.dispose();
  income3dChart?.dispose();
  qualityChart?.dispose();
  heatChart?.dispose();
});
</script>

<style scoped>
.ops-page { 
  padding: 20px; 
  background: #f1f5f9; /* 更现代的中性灰背景 */
  min-height: 100vh;
}

/* 组件间距与基础样式 */
.el-row { margin-bottom: 16px; }
.el-row:last-child { margin-bottom: 0; }
.panel-card, .kpi-card { border-radius: 12px; border: none; }

/* KPI 卡片优化 */
.kpi-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.kpi-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
}
.kpi-card :deep(.el-card__body) {
  display: flex;
  width: 100%;
  justify-content: space-between;
  align-items: center;
}
.primary-border { border-left: 4px solid #3b82f6; }
.warning-border { border-left: 4px solid #f59e0b; }
.danger-border { border-left: 4px solid #ef4444; }
.success-border { border-left: 4px solid #10b981; }

.kpi-label { 
  color: #64748b; 
  font-size: 13px; 
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 6px;
}
.tag {
  font-size: 10px;
  background: #e2e8f0;
  padding: 2px 6px;
  border-radius: 4px;
  color: #475569;
}
.kpi-value { 
  margin-top: 8px; 
  font-size: 28px; 
  font-weight: 800; 
  color: #0f172a; 
}
.kpi-value .unit { font-size: 16px; font-weight: 600; margin-left: 2px; color: #94a3b8; }
.kpi-value.warning { color: #f59e0b; }
.kpi-value.danger { color: #ef4444; }
.kpi-value.success { color: #10b981; }

.kpi-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}
.icon-blue { background: #eff6ff; color: #3b82f6; }
.icon-orange { background: #fffbeb; color: #f59e0b; }
.icon-red { background: #fef2f2; color: #ef4444; }
.icon-green { background: #ecfdf5; color: #10b981; }

/* 面板头部优化 */
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.panel-title { 
  font-weight: 700; 
  color: #1e293b; 
  font-size: 16px;
}
.panel-subtitle {
  font-size: 12px;
  color: #94a3b8;
  font-weight: normal;
}

/* 图表容器 */
.chart { width: 100%; }
.chart-lg { height: 320px; }
.chart-mid { height: 280px; }

/* 运营建议列表优化 */
.advice-card { height: 100%; display: flex; flex-direction: column; }
.pulse-dot {
  width: 8px; height: 8px; background: #10b981; border-radius: 50%;
  box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
  animation: pulse 2s infinite;
}
@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
  70% { box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
  100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
}
.advice-list { display: flex; flex-direction: column; gap: 12px; }
.advice-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  background: #f8fafc;
  padding: 12px;
  border-radius: 8px;
  transition: background 0.2s;
}
.advice-item:hover { background: #f1f5f9; }
.advice-dot { width: 8px; height: 8px; border-radius: 50%; margin-top: 6px; flex-shrink: 0; }
.advice-dot.blue { background: #3b82f6; }
.advice-dot.orange { background: #f59e0b; }
.advice-dot.red { background: #ef4444; }
.advice-dot.green { background: #10b981; }
.advice-text { font-size: 13px; color: #334155; line-height: 1.6; }
.advice-text b { color: #0f172a; }
</style>