<template>
  <div class="owner-page">
    <el-card class="hero-card" shadow="never">
      <div class="hero-row">
        <div class="hero-content">
          <div class="eyebrow">Owner Operations</div>
          <h2>主人运营中心</h2>
          <p>聚合账单、宠物、RFM 风险与领养推荐，支持精准分层运营与复诊触达。</p>
        </div>
        <div class="hero-actions">
          <el-space>
            <el-select 
              v-model="ownerId" 
              filterable 
              clearable 
              placeholder="搜索或选择主人" 
              class="owner-select"
              @change="loadData"
            >
              <template #prefix><el-icon><Search /></el-icon></template>
              <el-option 
                v-for="item in ownerOptions" 
                :key="item.id" 
                :label="`${item.name} (${item.phone || '-'})`" 
                :value="item.id" 
              />
            </el-select>
            <el-button type="primary" :loading="loading" @click="loadData" round class="action-btn">
              <el-icon class="el-icon--left"><Refresh /></el-icon>刷新数据
            </el-button>
          </el-space>
        </div>
      </div>
    </el-card>

    <el-row :gutter="16" class="kpi-row">
      <el-col :xs="12" :lg="6">
        <el-card class="kpi-card stat-blue" shadow="hover">
          <div class="kpi-content">
            <div class="kpi-info">
              <div class="kpi-label">累计消费</div>
              <div class="kpi-value"><span class="currency">￥</span>{{ Number(kpis.total_amount || 0).toFixed(0) }}</div>
            </div>
            <div class="kpi-icon-wrapper"><el-icon><Wallet /></el-icon></div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :lg="6">
        <el-card class="kpi-card stat-warning" shadow="hover">
          <div class="kpi-content">
            <div class="kpi-info">
              <div class="kpi-label">待收金额</div>
              <div class="kpi-value warning"><span class="currency">￥</span>{{ Number(kpis.unpaid_amount || 0).toFixed(0) }}</div>
            </div>
            <div class="kpi-icon-wrapper"><el-icon><Money /></el-icon></div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :lg="6">
        <el-card class="kpi-card stat-info" shadow="hover">
          <div class="kpi-content">
            <div class="kpi-info">
              <div class="kpi-label">宠物数量</div>
              <div class="kpi-value">{{ kpis.pet_count || 0 }} <span class="kpi-unit">只</span></div>
            </div>
            <div class="kpi-icon-wrapper"><el-icon><Guide /></el-icon></div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :lg="6">
        <el-card class="kpi-card stat-danger" shadow="hover">
          <div class="kpi-content">
            <div class="kpi-info">
              <div class="kpi-label">RFM 风险分</div>
              <div class="kpi-value danger">{{ Number(rfmProfile.rfm_score || 0).toFixed(1) }}</div>
            </div>
            <div class="kpi-icon-wrapper"><el-icon><Warning /></el-icon></div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="panel-row">
      <el-col :xs="24" :lg="14">
        <el-card class="panel-card" shadow="never">
          <template #header>
            <div class="panel-header">
              <div class="panel-title">账单趋势 <span class="panel-subtitle">近 6 个月</span></div>
            </div>
          </template>
          <div ref="trendRef" class="chart" />
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="10">
        <el-card class="panel-card" shadow="never">
          <template #header>
            <div class="panel-header">
              <div class="panel-title">领养推荐得分 <span class="panel-subtitle">Top 10</span></div>
            </div>
          </template>
          <div ref="matchRef" class="chart" />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="panel-row">
      <el-col :xs="24" :lg="7">
        <el-card class="panel-card" shadow="never">
          <template #header><div class="panel-title">主人画像</div></template>
          <el-descriptions border :column="1" size="default" class="custom-desc">
            <el-descriptions-item label="主人姓名">
              <span class="font-bold">{{ owner.name || '-' }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="联系方式">{{ owner.phone || '-' }}</el-descriptions-item>
            <el-descriptions-item label="风险等级">
              <el-tag :type="riskTagType" effect="light" round>{{ riskLevelText }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="最近就诊">
              <el-tag size="small" type="info" disable-transitions>{{ rfmProfile.recency_days || 0 }} 天前</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="历史频次">共 {{ rfmProfile.frequency || 0 }} 次</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="9">
        <el-card class="panel-card" shadow="never">
          <template #header><div class="panel-title">关联宠物</div></template>
          <el-empty v-if="pets.length === 0" description="暂无关联宠物" :image-size="80" />
          <div v-else class="pet-list compact-scroll">
            <div v-for="p in pets" :key="p.id" class="pet-item">
              <div class="pet-avatar">
                <el-icon><Box /></el-icon>
              </div>
              <div class="pet-info">
                <div class="pet-name">{{ p.name }}</div>
                <div class="pet-meta">
                  <span>{{ p.species }}</span><el-divider direction="vertical" />
                  <span>{{ p.breed || '-' }}</span><el-divider direction="vertical" />
                  <span>{{ Number(p.weight || 0).toFixed(1) }} kg</span>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="8">
        <el-card class="panel-card advice-card" shadow="never">
          <template #header><div class="panel-title">智能运营建议</div></template>
          <div class="advice-list compact-scroll">
            <div class="advice-item warning" v-if="Number(kpis.unpaid_amount || 0) > 0">
              <div class="advice-dot"></div>
              <div class="advice-text">建议先触达结算提醒，再推送体检套餐。</div>
            </div>
            <div class="advice-item danger" v-if="String(rfmProfile.risk_level || '').includes('high')">
              <div class="advice-dot"></div>
              <div class="advice-text">建议 48 小时内进行电话回访，优先预约复诊。</div>
            </div>
            <div class="advice-item primary" v-if="(adoptionTop || []).length > 0">
              <div class="advice-dot"></div>
              <div class="advice-text">可推送领养匹配 Top3，提高用户参与度。</div>
            </div>
            <div class="advice-item success" v-if="adviceList.length === 0">
              <div class="advice-dot"></div>
              <div class="advice-text">客户状态稳定，建议维持月度关怀提醒。</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="panel-card table-card" shadow="never">
      <template #header>
        <div class="panel-title">历史账单明细</div>
      </template>
      <el-table :data="bills" class="custom-table" height="280">
        <el-table-column prop="invoice_no" label="账单流水号" min-width="180">
          <template #default="{ row }">
            <span class="mono-text">{{ row.invoice_no }}</span>
          </template>
        </el-table-column>
        <el-table-column label="总金额" width="140">
          <template #default="{ row }">
            <span class="font-bold">￥{{ Number(row.total_amount || 0).toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="已支付" width="140">
          <template #default="{ row }">
            <span class="text-success">￥{{ Number(row.paid_amount || 0).toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="row.status === '已结清' ? 'success' : 'warning'" size="small">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="生成时间" min-width="170" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import * as echarts from "echarts";
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
// 引入需要用到的新图标
import { Search, Refresh, Wallet, Money, Guide, Warning, Box } from "@element-plus/icons-vue"; 
import { fetchOwnerCenter } from "../api/ownerCenter";
import { fetchOwners } from "../api/owners";
import { getErrorMessage } from "../utils/status";

const ownerId = ref(null);
const ownerOptions = ref([]);
const loading = ref(false);

const owner = ref({});
const pets = ref([]);
const bills = ref([]);
const trendRows = ref([]);
const adoptionTop = ref([]);
const kpis = ref({});
const rfmProfile = ref({});

const trendRef = ref(null);
const matchRef = ref(null);
let trendChart = null;
let matchChart = null;

const riskLevelText = computed(() => {
  const level = String(rfmProfile.value.risk_level || "").toLowerCase();
  if (level.includes("high")) return "高风险";
  if (level.includes("medium")) return "中风险";
  return "健康";
});

const riskTagType = computed(() => {
  const level = String(rfmProfile.value.risk_level || "").toLowerCase();
  if (level.includes("high")) return "danger";
  if (level.includes("medium")) return "warning";
  return "success";
});

const adviceList = computed(() => {
  const list = [];
  if (Number(kpis.value.unpaid_amount || 0) > 0) list.push("unpaid");
  if (String(rfmProfile.value.risk_level || "").toLowerCase().includes("high")) list.push("high-risk");
  if ((adoptionTop.value || []).length > 0) list.push("adoption");
  return list;
});

function ensureCharts() {
  if (trendRef.value && !trendChart) trendChart = echarts.init(trendRef.value);
  if (matchRef.value && !matchChart) matchChart = echarts.init(matchRef.value);
}

// --- 1. 账单趋势图优化 (面积渐变 + 平滑阴影) ---
function renderTrendChart() {
  ensureCharts();
  trendChart?.setOption({
    tooltip: { 
      trigger: "axis",
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e2e8f0',
      textStyle: { color: '#1e293b' }
    },
    legend: { data: ["应收金额", "已收金额"], bottom: 0, icon: 'circle' },
    xAxis: { 
      type: "category", 
      data: trendRows.value.map((x) => x.month),
      axisLine: { lineStyle: { color: "#cbd5e1" } },
      axisLabel: { color: "#475569" }
    },
    yAxis: { 
      type: "value", name: "金额 (元)",
      nameTextStyle: { color: "#64748b", padding: [0, 0, 0, 10] },
      splitLine: { lineStyle: { type: "dashed", color: "#f1f5f9" } }
    },
    grid: { top: 40, right: 20, left: 20, bottom: 30, containLabel: true },
    series: [
      { 
        name: "应收金额", type: "line", smooth: true, symbolSize: 6,
        data: trendRows.value.map((x) => Number(x.amount || 0)), 
        lineStyle: { width: 3, color: "#3b82f6", shadowColor: 'rgba(59, 130, 246, 0.3)', shadowBlur: 8, shadowOffsetY: 4 },
        itemStyle: { color: "#3b82f6" },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(59, 130, 246, 0.2)' },
            { offset: 1, color: 'rgba(59, 130, 246, 0)' }
          ])
        }
      },
      { 
        name: "已收金额", type: "line", smooth: true, symbolSize: 6,
        data: trendRows.value.map((x) => Number(x.paid || 0)), 
        lineStyle: { width: 3, color: "#10b981", shadowColor: 'rgba(16, 185, 129, 0.3)', shadowBlur: 8, shadowOffsetY: 4 },
        itemStyle: { color: "#10b981" },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(16, 185, 129, 0.2)' },
            { offset: 1, color: 'rgba(16, 185, 129, 0)' }
          ])
        }
      }
    ]
  });
}

// --- 2. 匹配得分图优化 (横向渐变色 + 圆角) ---
function renderMatchChart() {
  ensureCharts();
  const rows = (adoptionTop.value || []).slice(0, 10).reverse(); // 翻转以让分数高的在最上方
  matchChart?.setOption({
    tooltip: { 
      trigger: "axis", axisPointer: { type: "shadow" },
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
    },
    xAxis: { 
      type: "value", min: 0, max: 100, 
      axisLabel: { formatter: "{value}%", color: "#64748b" },
      splitLine: { lineStyle: { type: "dashed", color: "#f1f5f9" } }
    },
    yAxis: { 
      type: "category", 
      data: rows.map((x) => x.match_id || x.adopter_name || `#${x.match_id}`),
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: "#475569", fontWeight: 500 }
    },
    grid: { top: 20, right: 40, left: 10, bottom: 20, containLabel: true },
    series: [
      {
        type: "bar",
        data: rows.map((x) => Number(x.total_score || 0)),
        label: { 
          show: true, position: "right", 
          formatter: ({ value }) => `${Number(value).toFixed(1)}%`,
          color: '#1e293b', fontWeight: 600
        },
        barMaxWidth: 16,
        itemStyle: { 
          borderRadius: [0, 8, 8, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#fcd34d' },
            { offset: 1, color: '#f59e0b' }
          ])
        }
      }
    ]
  });
}

function renderCharts() {
  renderTrendChart();
  renderMatchChart();
}

async function loadData() {
  if (!ownerId.value) {
    owner.value = {};
    pets.value = [];
    bills.value = [];
    trendRows.value = [];
    adoptionTop.value = [];
    kpis.value = {};
    rfmProfile.value = {};
    return;
  }
  loading.value = true;
  try {
    const res = await fetchOwnerCenter(ownerId.value);
    const data = res?.data || {};
    owner.value = data.owner || {};
    pets.value = data.my_pets || [];
    bills.value = data.medical_bills || [];
    trendRows.value = data.billing_trend || [];
    adoptionTop.value = data.adoption_top_recommendations || [];
    kpis.value = data.owner_kpis || {};
    rfmProfile.value = data.rfm_profile || {};

    await nextTick();
    renderCharts();
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "主人运营数据加载失败"));
  } finally {
    loading.value = false;
  }
}

async function loadOwnersOptions() {
  try {
    const res = await fetchOwners();
    ownerOptions.value = res.data || [];
    if (!ownerId.value && ownerOptions.value.length) {
      ownerId.value = ownerOptions.value[0].id;
    }
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "主人列表加载失败"));
  }
}

function onResize() {
  trendChart?.resize();
  matchChart?.resize();
}

onMounted(async () => {
  await loadOwnersOptions();
  await loadData();
  window.addEventListener("resize", onResize);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", onResize);
  trendChart?.dispose();
  matchChart?.dispose();
});
</script>

<style scoped>
/* 全局背景优化 */
.owner-page {
  padding: 20px;
  background-color: #f8fafc;
  min-height: 100vh;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}

/* 卡片统一的基础样式 */
.hero-card, .kpi-card, .panel-card {
  border-radius: 16px;
  border: 1px solid #e2e8f0;
  background: #ffffff;
  margin-bottom: 16px;
}

/* --- Hero 区域 --- */
.hero-card {
  background: linear-gradient(135deg, #ffffff 0%, #f0f9ff 100%);
  border-left: 6px solid #0ea5e9;
}
.hero-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  padding: 4px;
}
.eyebrow {
  font-size: 12px;
  color: #0ea5e9;
  font-weight: 700;
  letter-spacing: 1px;
  text-transform: uppercase;
  margin-bottom: 6px;
}
.hero-content h2 { margin: 0; font-size: 24px; font-weight: 800; color: #0f172a; }
.hero-content p { margin: 8px 0 0; color: #64748b; font-size: 14px; line-height: 1.5; }
.owner-select { width: 280px; }

/* --- KPI 卡片区域 --- */
.kpi-row { margin-bottom: 8px; }
.kpi-card { transition: transform 0.2s, box-shadow 0.2s; border: none; }
.kpi-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.01);
}
.kpi-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px;
}
.kpi-label { color: #64748b; font-size: 13px; font-weight: 600; margin-bottom: 8px; }
.kpi-value { font-size: 28px; font-weight: 800; color: #1e293b; line-height: 1; }
.kpi-unit { font-size: 13px; color: #94a3b8; font-weight: 500; margin-left: 2px; }
.currency { font-size: 18px; margin-right: 2px; font-weight: 600; }

.kpi-value.warning { color: #f59e0b; }
.kpi-value.danger { color: #ef4444; }

.kpi-icon-wrapper {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 24px;
}
.stat-blue .kpi-icon-wrapper { background: #eff6ff; color: #3b82f6; }
.stat-warning .kpi-icon-wrapper { background: #fffbeb; color: #f59e0b; }
.stat-info .kpi-icon-wrapper { background: #f0fdf4; color: #10b981; }
.stat-danger .kpi-icon-wrapper { background: #fef2f2; color: #ef4444; }

/* --- 图表与面板内容 --- */
.panel-card:deep(.el-card__header) {
  border-bottom: 1px solid #f1f5f9;
  padding: 16px 20px;
}
.panel-card:deep(.el-card__body) { padding: 20px; }
.panel-title { font-weight: 700; color: #1e293b; font-size: 15px; }
.panel-subtitle { font-size: 12px; color: #94a3b8; font-weight: 400; margin-left: 6px; }

.chart { width: 100%; height: 280px; }

/* --- 描述列表优化 --- */
.custom-desc { --el-descriptions-border-color: #f1f5f9; }
.font-bold { font-weight: 600; color: #0f172a; }

/* --- 宠物列表设计 (名片化) --- */
.compact-scroll { max-height: 240px; overflow-y: auto; padding-right: 6px; }
.compact-scroll::-webkit-scrollbar { width: 6px; }
.compact-scroll::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }

.pet-list { display: flex; flex-direction: column; gap: 10px; }
.pet-item {
  display: flex;
  align-items: center;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 12px;
  background: #f8fafc;
  transition: background 0.2s;
}
.pet-item:hover { background: #f1f5f9; }
.pet-avatar {
  width: 40px; height: 40px;
  border-radius: 50%; background: #e0f2fe; color: #0284c7;
  display: flex; justify-content: center; align-items: center;
  font-size: 20px; margin-right: 12px; flex-shrink: 0;
}
.pet-name { font-weight: 700; color: #1e293b; font-size: 14px; }
.pet-meta { color: #64748b; font-size: 12px; margin-top: 4px; display: flex; align-items: center; }

/* --- 运营建议列表重构 --- */
.advice-card { display: flex; flex-direction: column; }
.advice-list { display: flex; flex-direction: column; gap: 10px; }
.advice-item {
  display: flex; align-items: flex-start;
  padding: 12px; border-radius: 8px; background: #f8fafc;
  position: relative; transition: background 0.2s;
}
.advice-item:hover { background: #f1f5f9; }
.advice-dot { width: 8px; height: 8px; border-radius: 50%; margin-top: 5px; margin-right: 12px; flex-shrink: 0; }
.advice-text { font-size: 13px; color: #334155; line-height: 1.5; }

.advice-item.warning .advice-dot { background: #f59e0b; box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.2); }
.advice-item.danger .advice-dot { background: #ef4444; box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.2); }
.advice-item.primary .advice-dot { background: #3b82f6; box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2); }
.advice-item.success .advice-dot { background: #10b981; box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.2); }

/* --- 账单表格优化 --- */
.table-card:deep(.el-card__body) { padding: 0; }
.custom-table { --el-table-border-color: #f1f5f9; --el-table-header-bg-color: #f8fafc; }
.mono-text { font-family: monospace; font-size: 13px; color: #475569; }
.text-success { color: #10b981; font-weight: 600; }

@media (max-width: 900px) {
  .hero-row { flex-direction: column; align-items: flex-start; }
  .hero-actions { width: 100%; margin-top: 12px; }
  .owner-select { width: 100%; }
}
</style>