<template>
  <div class="rfm-page">
    <el-card class="hero-card" shadow="never">
      <div class="hero-row">
        <div class="hero-content">
          <div class="eyebrow">Retention Intelligence</div>
          <h2>RFM 客户运营看板</h2>
          <p>此页面专供院区运营使用，用于精准识别风险人群、分配触达动作并追踪回访转化结果。</p>
        </div>
        <div class="hero-actions">
          <el-button :loading="loading" @click="refreshAll" class="action-btn" round>
            <el-icon class="el-icon--left"><Refresh /></el-icon> 刷新数据
          </el-button>
          <el-button 
            type="primary" 
            :disabled="highRiskRows.length === 0" 
            @click="batchCreateTasks" 
            class="action-btn"
            round
          >
            批量生成高风险任务
          </el-button>
        </div>
      </div>
    </el-card>

    <el-row :gutter="16" class="kpi-row">
      <el-col v-for="item in kpiCards" :key="item.label" :xs="12" :lg="6">
        <el-card class="kpi-card" :class="item.tone" shadow="hover">
          <div class="kpi-header">
            <span class="kpi-label">{{ item.label }}</span>
            <div class="kpi-indicator"></div>
          </div>
          <div class="kpi-value">{{ item.value }}</div>
          <div class="kpi-note">{{ item.note }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="panel-row">
      <el-col :xs="24" :lg="11">
        <el-card class="panel-card kanban-panel" shadow="never">
          <template #header>
            <div class="panel-title">运营任务流 <span class="kanban-subtitle">(拖拽更改状态)</span></div>
          </template>
          <div class="kanban-grid">
            <div 
              v-for="col in columns" 
              :key="col.key" 
              class="kanban-col" 
              @dragover.prevent 
              @drop="onDrop(col.key)"
            >
              <div class="kanban-title">
                {{ col.title }} 
                <span class="kanban-count">{{ kanban[col.key].length }}</span>
              </div>
              <div class="kanban-list">
                <div
                  v-for="task in kanban[col.key]"
                  :key="task.id"
                  class="kanban-card"
                  draggable="true"
                  @dragstart="onDrag(task, col.key)"
                >
                  <div class="card-header">
                    <span class="card-name">{{ task.owner_name }}</span>
                    <el-tag size="small" :type="task.risk_score > 80 ? 'danger' : 'warning'" effect="dark" round>
                      {{ Number(task.risk_score || 0).toFixed(0) }}分
                    </el-tag>
                  </div>
                  <div class="card-meta">
                    <el-icon><Calendar /></el-icon> 未到院 {{ task.recency_days }} 天
                  </div>
                </div>
                <div v-if="kanban[col.key].length === 0" class="kanban-empty">拖拽至此</div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="13">
        <el-card class="panel-card" shadow="never">
          <template #header>
            <div class="panel-title">三维客户分布分析 ( R / F / M )</div>
          </template>
          <div ref="scatterRef" class="chart chart-lg" />
        </el-card>
      </el-col>
      
      <el-col :xs="24" :lg="24">
        <el-card class="panel-card" shadow="never">
          <template #header>
            <div class="panel-title">风险分布占比</div>
          </template>
          <div ref="pieRef" class="chart chart-mid" />
          <div class="segment-list">
            <div v-for="item in segmentTips" :key="item.title" class="segment-card">
              <div class="segment-title">{{ item.title }}</div>
              <div class="segment-desc">{{ item.desc }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="panel-row">
      <el-col :xs="24" :lg="24">
        <el-card class="panel-card" shadow="never">
          <template #header>
            <div class="panel-title">高风险客户清单</div>
          </template>
          <el-table :data="pagedHighRiskRows" style="width: 100%" class="custom-table" height="360">
            <el-table-column prop="owner_name" label="主人姓名" min-width="100">
              <template #default="{ row }">
                <span class="font-bold">{{ row.owner_name }}</span>
              </template>
            </el-table-column>
            <el-table-column label="最近到院" width="100">
              <template #default="{ row }">
                <el-tag :type="row.recency_days > 90 ? 'danger' : 'warning'" size="small" disable-transitions>
                  {{ row.recency_days }} 天前
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="frequency" label="频次" width="70" align="center" />
            <el-table-column label="消费额" width="100">
              <template #default="{ row }">
                <span class="monetary-text">¥{{ Number(row.monetary || 0).toFixed(0) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="建议策略" min-width="200">
              <template #default="{ row }">
                <div class="strategy-text">{{ suggestionFor(row) }}</div>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100" align="center" fixed="right">
              <template #default="{ row }">
                <el-button 
                  size="small" 
                  :type="createdOwnerIds.has(row.owner_id) ? 'info' : 'primary'" 
                  :plain="!createdOwnerIds.has(row.owner_id)"
                  :disabled="createdOwnerIds.has(row.owner_id)" 
                  @click="createSingleTask(row)"
                  round
                >
                  {{ createdOwnerIds.has(row.owner_id) ? "已生成" : "建任务" }}
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <div class="pagination-wrapper">
            <el-pagination
              v-if="highRiskRows.length > pageSize"
              background
              layout="prev, pager, next, total"
              :page-size="pageSize"
              :total="highRiskRows.length"
              :current-page="highRiskPage"
              @current-change="(p) => (highRiskPage = p)"
            />
          </div>
        </el-card>
      </el-col>

    </el-row>
  </div>
</template>

<script setup>
import * as echarts from "echarts";
import "echarts-gl";
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import { Refresh, Calendar } from "@element-plus/icons-vue"; // 引入图标
import { fetchRfmWarnings } from "../api/ai";
import { createRfmFollowupTasks, fetchFollowupTasks, updateFollowupTask } from "../api/tasks";
import { getErrorMessage } from "../utils/status";

// === 原有业务逻辑保持不变 ===
const loading = ref(false);
const rows = ref([]);
const createdOwnerIds = ref(new Set());
const highRiskPage = ref(1);
const pageSize = 8;
const MAX_UI_ROWS = 40;

const columns = [
  { key: "todo", title: "待处理" },
  { key: "ongoing", title: "跟进中" },
  { key: "booked", title: "已预约" },
  { key: "closed", title: "无效" }
];

const kanban = ref({ todo: [], ongoing: [], booked: [], closed: [] });
const dragging = ref(null);
const draggingFrom = ref("");

const scatterRef = ref(null);
const pieRef = ref(null);

let scatterChart = null;
let pieChart = null;

const highRiskRows = computed(() => rows.value.filter((item) => normalizeRisk(item.risk_level) === "high"));
const mediumRiskRows = computed(() => rows.value.filter((item) => normalizeRisk(item.risk_level) === "medium"));
const lowRiskRows = computed(() => rows.value.filter((item) => normalizeRisk(item.risk_level) === "low"));
const pagedHighRiskRows = computed(() => {
  const start = (highRiskPage.value - 1) * pageSize;
  return highRiskRows.value.slice(start, start + pageSize);
});

const conversionRate = computed(() => {
  const total = Object.values(kanban.value).reduce((sum, list) => sum + list.length, 0);
  if (!total) return 0;
  return Number(((kanban.value.booked.length / total) * 100).toFixed(1));
});

const kpiCards = computed(() => [
  { label: "高风险客户", value: highRiskRows.value.length, note: "需要尽快建联的流失人群", tone: "danger" },
  { label: "中风险客户", value: mediumRiskRows.value.length, note: "适合短信+电话分层触达", tone: "warning" },
  { label: "健康客户", value: lowRiskRows.value.length, note: "建议保持常规服务频次", tone: "success" },
  { label: "复诊转化率", value: `${conversionRate.value}%`, note: "以已预约任务占比估算", tone: "primary" }
]);

const segmentTips = computed(() => [
  { title: "高 R / 低 F / 低 M", desc: "长期未到院且消费有限，优先用优惠券或复诊提醒唤醒。" },
  { title: "中 R / 高 F / 高 M", desc: "属于高价值老客户，建议提供专属客服与快速预约通道。" },
  { title: "低 R / 中 F / 中 M", desc: "关系健康，可用疫苗、体检、洗护等日常活动维持粘性。" }
]);

function normalizeRisk(value) {
  const text = String(value || "").toLowerCase();
  if (text.includes("high") || text.includes("高")) return "high";
  if (text.includes("medium") || text.includes("中")) return "medium";
  return "low";
}

function statusGroup(status) {
  const text = String(status || "");
  if (text.includes("预约")) return "booked";
  if (text.includes("无效") || text.includes("拒")) return "closed";
  if (text.includes("进行") || text.includes("跟进")) return "ongoing";
  return "todo";
}

function toBackendStatus(key) {
  if (key === "booked") return "已预约复诊";
  if (key === "closed") return "无效拒接";
  if (key === "ongoing") return "进行中";
  return "待处理";
}

function suggestionFor(row) {
  if (Number(row.recency_days || 0) >= 120) return "沉默客户：电话外呼 + 限时体检券";
  if (Number(row.monetary || 0) >= 3200) return "高价值客户：专属客服 + 快速复诊通道";
  if (Number(row.frequency || 0) <= 1) return "低频客户：疫苗/驱虫提醒 + 二次触达";
  return "短信提醒 + 72 小时内电话补触达";
}

function percentileScale(values, target) {
  const sorted = [...values].sort((a, b) => a - b);
  if (!sorted.length) return 0;
  const index = sorted.findIndex((item) => item >= target);
  const rank = index === -1 ? sorted.length - 1 : index;
  return Number(((rank / Math.max(sorted.length - 1, 1)) * 100).toFixed(2));
}

function buildScatterPoints() {
  const recencyValues = rows.value.map((item) => Number(item.recency_days || 0));
  const frequencyValues = rows.value.map((item) => Number(item.frequency || 0));
  const monetaryValues = rows.value.map((item) => Number(item.monetary || 0));

  return rows.value.map((row, index) => {
    const angle = (Number(row.owner_id || index + 1) * 137.5 * Math.PI) / 180;
    const radius = 1.4 + ((index % 7) * 0.28);
    const jitterX = Math.cos(angle) * radius;
    const jitterY = Math.sin(angle) * radius;
    const jitterZ = Math.cos(angle / 2) * 1.15;

    const r = percentileScale(recencyValues, Number(row.recency_days || 0)) + jitterX;
    const f = percentileScale(frequencyValues, Number(row.frequency || 0)) + jitterY;
    const m = percentileScale(monetaryValues, Number(row.monetary || 0)) + jitterZ;

    return {
      name: row.owner_name,
      value: [Number(r.toFixed(2)), Number(f.toFixed(2)), Number(m.toFixed(2)), Number(row.rfm_score || 0)],
      raw: row,
      risk: normalizeRisk(row.risk_level)
    };
  });
}

async function loadRfmWarnings() {
  const res = await fetchRfmWarnings();
  const raw = res.data || [];
  rows.value = raw.slice(0, MAX_UI_ROWS);
}

async function loadKanban() {
  const res = await fetchFollowupTasks("");
  const tasks = res.data || [];
  kanban.value = { todo: [], ongoing: [], booked: [], closed: [] };
  createdOwnerIds.value = new Set();
  tasks.forEach((item) => {
    const key = statusGroup(item.status);
    kanban.value[key].push(item);
    createdOwnerIds.value.add(item.owner_id);
  });
}

function ensureCharts() {
  if (scatterRef.value && !scatterChart) scatterChart = echarts.init(scatterRef.value);
  if (pieRef.value && !pieChart) pieChart = echarts.init(pieRef.value);
}

// === 优化图表视觉配置 ===
function renderScatter() {
  ensureCharts();
  const data = buildScatterPoints();

  scatterChart?.setOption({
    tooltip: {
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e2e8f0',
      textStyle: { color: '#1e293b' },
      formatter: (params) => {
        const row = params.data.raw;
        return [
          `<div style="font-weight: 700; margin-bottom: 6px; border-bottom: 1px solid #f1f5f9; padding-bottom: 4px;">${row.owner_name}</div>`,
          `<span style="color: #64748b">最近到院:</span> <span style="font-weight: 500">${row.recency_days} 天前</span>`,
          `<span style="color: #64748b">到院频次:</span> <span style="font-weight: 500">${row.frequency} 次</span>`,
          `<span style="color: #64748b">历史消费:</span> <span style="font-weight: 500">¥${Number(row.monetary || 0).toFixed(0)}</span>`,
          `<span style="color: #64748b">RFM 风险分:</span> <span style="font-weight: 700; color: #ef4444">${Number(row.rfm_score || 0).toFixed(1)}</span>`
        ].join("<br/>");
      }
    },
    visualMap: {
      max: 100, min: 0, dimension: 3, calculable: true,
      orient: "horizontal", left: "center", bottom: 0,
      itemWidth: 15, itemHeight: 200,
      textStyle: { color: '#64748b' },
      inRange: {
        color: ["#10b981", "#f59e0b", "#ef4444"] // 绿黄红语义化色板
      }
    },
    xAxis3D: { name: "Recency", type: "value", min: 0, max: 100, nameTextStyle: { color: '#64748b' } },
    yAxis3D: { name: "Frequency", type: "value", min: 0, max: 100, nameTextStyle: { color: '#64748b' } },
    zAxis3D: { name: "Monetary", type: "value", min: 0, max: 100, nameTextStyle: { color: '#64748b' } },
    grid3D: {
      boxWidth: 110, boxDepth: 90,
      viewControl: {
        projection: "perspective",
        autoRotate: true,          // 增加缓慢自转，提升 3D 高级感
        autoRotateSpeed: 4,
        alpha: 20, beta: 30
      },
      light: {
        main: { intensity: 1.5, shadow: true, alpha: 30 },
        ambient: { intensity: 0.6 }
      }
    },
    series: [{
      type: "scatter3D",
      data,
      symbolSize: (value) => Math.max(12, Math.min(26, 10 + Number(value[3] || 0) / 7)),
      itemStyle: { opacity: 0.85, borderWidth: 1, borderColor: '#fff' }
    }]
  });
}

function renderPie() {
  ensureCharts();
  const total = rows.value.length || 1;
  const pieData = [
    { name: "高风险", value: highRiskRows.value.length, itemStyle: { color: '#ef4444' } },
    { name: "中风险", value: mediumRiskRows.value.length, itemStyle: { color: '#f59e0b' } },
    { name: "低风险", value: lowRiskRows.value.length, itemStyle: { color: '#10b981' } }
  ];

  pieChart?.setOption({
    tooltip: { 
      trigger: "item", 
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      formatter: (item) => `<span style="display:inline-block;margin-right:4px;border-radius:10px;width:10px;height:10px;background-color:${item.color};"></span>${item.name}: <b>${item.value}</b> (${((item.value / total) * 100).toFixed(1)}%)` 
    },
    legend: {
      bottom: 0, icon: 'circle', textStyle: { color: '#475569' },
      formatter: (name) => {
        const row = pieData.find((item) => item.name === name);
        if (!row) return name;
        return `${name} | ${row.value} 人`;
      }
    },
    series: [{
      type: "pie",
      radius: ["50%", "75%"],  // 改为更现代的环形图
      center: ['50%', '45%'],
      itemStyle: { 
        borderRadius: 8,      // 增加圆角
        borderColor: '#fff', 
        borderWidth: 2 
      },
      label: { 
        formatter: "{b}\n{d}%",
        color: '#475569',
        lineHeight: 18
      },
      data: pieData
    }]
  });
}

function renderAll() {
  renderScatter();
  renderPie();
}

async function refreshAll() {
  loading.value = true;
  try {
    await Promise.all([loadRfmWarnings(), loadKanban()]);
    await nextTick();
    renderAll();
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "RFM 看板加载失败"));
  } finally {
    loading.value = false;
  }
}

async function batchCreateTasks() {
  try {
    const res = await createRfmFollowupTasks();
    const count = Number(res?.data?.count || 0);
    ElMessage.success(`已生成 ${count} 条高风险跟进任务`);
    await loadKanban();
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "批量建任务失败"));
  }
}

async function createSingleTask(row) {
  try {
    const res = await createRfmFollowupTasks({ owner_ids: [row.owner_id] });
    const count = Number(res?.data?.count || 0);
    if (count > 0) {
      createdOwnerIds.value.add(row.owner_id);
      ElMessage.success("任务已创建");
      await loadKanban();
    } else {
      ElMessage.info("该客户已有进行中的任务");
    }
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "创建任务失败"));
  }
}

function onDrag(task, fromKey) {
  dragging.value = task;
  draggingFrom.value = fromKey;
}

async function onDrop(targetKey) {
  if (!dragging.value) return;
  const task = dragging.value;
  const fromKey = draggingFrom.value;
  if (!fromKey || fromKey === targetKey) {
    dragging.value = null;
    return;
  }

  kanban.value[fromKey] = kanban.value[fromKey].filter((item) => item.id !== task.id);
  kanban.value[targetKey].push(task);
  dragging.value = null;

  try {
    await updateFollowupTask(task.id, { status: toBackendStatus(targetKey) });
    ElMessage.success("任务状态已更新");
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "任务状态更新失败"));
    await loadKanban();
  }
}

function onResize() {
  scatterChart?.resize();
  pieChart?.resize();
}

onMounted(async () => {
  await refreshAll();
  window.addEventListener("resize", onResize);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", onResize);
  scatterChart?.dispose();
  pieChart?.dispose();
});
</script>

<style scoped>
/* 全局页面底色优化 */
.rfm-page {
  padding: 20px;
  background-color: #f8fafc;
  min-height: 100vh;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}

/* 卡片基础样式统一 */
.hero-card, .kpi-card, .panel-card {
  border-radius: 16px;
  border: 1px solid #e2e8f0;
  background: #ffffff;
  margin-bottom: 16px;
  transition: box-shadow 0.3s ease;
}

/* --- Hero 区域 --- */
.hero-card {
  background: linear-gradient(120deg, #ffffff 0%, #f0f9ff 100%);
  border-left: 6px solid #0284c7;
}

.hero-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  padding: 4px;
}

.eyebrow {
  font-size: 13px;
  color: #0284c7;
  font-weight: 700;
  letter-spacing: 1px;
  text-transform: uppercase;
  margin-bottom: 8px;
}

.hero-content h2 {
  margin: 0;
  font-size: 26px;
  font-weight: 800;
  color: #0f172a;
}

.hero-content p {
  margin: 8px 0 0;
  color: #64748b;
  font-size: 14px;
  line-height: 1.5;
}

.hero-actions {
  display: flex;
  gap: 12px;
}
.action-btn {
  font-weight: 600;
}

/* --- KPI 卡片区域 --- */
.kpi-row {
  margin-bottom: 4px;
}

.kpi-card {
  padding: 4px 0;
  position: relative;
  overflow: hidden;
}

.kpi-card:hover {
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.01);
}

.kpi-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.kpi-label {
  color: #64748b;
  font-size: 13px;
  font-weight: 600;
}

.kpi-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.kpi-value {
  margin-top: 10px;
  font-size: 32px;
  font-weight: 800;
  color: #1e293b;
}

.kpi-note {
  margin-top: 8px;
  color: #94a3b8;
  font-size: 12px;
}

/* 颜色语义化 */
.kpi-card.danger .kpi-indicator { background: #ef4444; box-shadow: 0 0 8px rgba(239, 68, 68, 0.4); }
.kpi-card.danger .kpi-value { color: #ef4444; }

.kpi-card.warning .kpi-indicator { background: #f59e0b; box-shadow: 0 0 8px rgba(245, 158, 11, 0.4); }
.kpi-card.warning .kpi-value { color: #f59e0b; }

.kpi-card.success .kpi-indicator { background: #10b981; box-shadow: 0 0 8px rgba(16, 185, 129, 0.4); }
.kpi-card.success .kpi-value { color: #10b981; }

.kpi-card.primary .kpi-indicator { background: #3b82f6; box-shadow: 0 0 8px rgba(59, 130, 246, 0.4); }
.kpi-card.primary .kpi-value { color: #3b82f6; }

/* --- 图表与内容面板 --- */
.panel-card {
  height: calc(100% - 16px);
}
.panel-title {
  font-size: 16px;
  font-weight: 700;
  color: #1e293b;
}

.chart { width: 100%; }
.chart-lg { height: 440px; }
.chart-mid { height: 260px; }

.panel-row {
  align-items: stretch;
}

/* 右侧风险提示卡片 */
.segment-list {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-top: 16px;
  padding: 0;
}

.segment-card {
  padding: 12px 16px;
  background: #f8fafc;
  border-left: 4px solid #cbd5e1;
  border-radius: 8px;
  transition: all 0.2s;
}

.segment-card:hover {
  background: #f1f5f9;
}

.segment-title {
  font-size: 13px;
  font-weight: 700;
  color: #334155;
}

.segment-desc {
  margin-top: 6px;
  font-size: 12px;
  color: #64748b;
  line-height: 1.5;
}

/* 第一个高风险卡片特殊高亮 */
.segment-list .segment-card:nth-child(1) { border-left-color: #ef4444; background: #fef2f2; }
.segment-list .segment-card:nth-child(2) { border-left-color: #f59e0b; background: #fffbeb; }

/* --- 表格样式优化 --- */
.custom-table {
  --el-table-border-color: #f1f5f9;
  --el-table-header-bg-color: #f8fafc;
  --el-table-header-text-color: #475569;
}

.font-bold { font-weight: 600; color: #1e293b; }
.monetary-text { font-family: monospace; font-size: 14px; font-weight: 600; color: #0f172a; }
.strategy-text { font-size: 13px; color: #475569; line-height: 1.4; }

.pagination-wrapper {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

/* --- 看板 (Kanban) 样式优化 --- */
.kanban-panel .el-card__body {
  padding: 16px;
}

.kanban-subtitle {
  font-size: 12px;
  color: #94a3b8;
  font-weight: 400;
  margin-left: 8px;
}

.kanban-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.kanban-col {
  background: #f1f5f9;
  border-radius: 12px;
  padding: 14px;
  min-height: 240px;
  display: flex;
  flex-direction: column;
}

.kanban-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 700;
  font-size: 14px;
  color: #475569;
  margin-bottom: 12px;
  padding: 0 4px;
}

.kanban-count {
  background: #e2e8f0;
  color: #64748b;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.kanban-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.kanban-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 12px;
  cursor: grab;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  transition: transform 0.15s, box-shadow 0.15s;
}

.kanban-card:active {
  cursor: grabbing;
  transform: scale(0.98);
}

.kanban-card:hover {
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  transform: translateY(-2px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.card-name {
  font-size: 14px;
  font-weight: 700;
  color: #1e293b;
}

.card-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #64748b;
}

.kanban-empty {
  text-align: center;
  padding: 20px 0;
  color: #94a3b8;
  font-size: 13px;
  border: 2px dashed #cbd5e1;
  border-radius: 8px;
  margin-top: auto;
  margin-bottom: auto;
}

/* 响应式调整 */
@media (max-width: 992px) {
  .hero-row { flex-direction: column; align-items: flex-start; }
  .hero-actions { margin-top: 16px; width: 100%; }
  .action-btn { flex: 1; }
  .segment-list { grid-template-columns: 1fr; }
  .kanban-grid { grid-template-columns: 1fr; }
}
</style>
