<template>
  <div class="page layout-bg">
    <el-card class="glass-card main-card stagger-in-1">
      <template #header>
        <div class="header-row">
          <span class="page-title">💰 门诊收费中心 <span class="sub-badge">前台专用</span></span>
          <el-space>
            <el-button class="agile-btn btn-ghost" :loading="exporting" @click="exportStatement">
              <span class="btn-text">📥 导出对账单</span>
            </el-button>
            <el-button class="agile-btn btn-settle" :loading="settling" @click="settleToday">
              <span class="btn-text">🚀 完成今日结算并上报</span>
            </el-button>
          </el-space>
        </div>
      </template>
      
      <el-breadcrumb separator="/" class="cute-breadcrumb mb16">
        <el-breadcrumb-item @click="router.push('/home')">🏠 首页</el-breadcrumb-item>
        <el-breadcrumb-item>收费结算</el-breadcrumb-item>
      </el-breadcrumb>

      <el-row :gutter="16" class="mb24 stat-row">
        <el-col :span="8" class="stagger-in-2">
          <div class="stat-card stat-warning">
            <div class="stat-icon">🕐</div>
            <div class="stat-content">
              <div class="k">待收费 (单)</div>
              <div class="v">{{ pendingCount }}</div>
            </div>
          </div>
        </el-col>
        <el-col :span="8" class="stagger-in-3">
          <div class="stat-card stat-success">
            <div class="stat-icon">✅</div>
            <div class="stat-content">
              <div class="k">已收费 (单)</div>
              <div class="v">{{ paidCount }}</div>
            </div>
          </div>
        </el-col>
        <el-col :span="8" class="stagger-in-4">
          <div class="stat-card stat-primary">
            <div class="stat-icon">💸</div>
            <div class="stat-content">
              <div class="k">今日总收入 (元)</div>
              <div class="v"><span class="currency">¥</span> {{ totalIncome.toFixed(2) }}</div>
            </div>
          </div>
        </el-col>
      </el-row>

      <div class="stagger-in-5">
        <div class="pending-rx-panel">
          <div class="pending-rx-title">待缴费处方（倒计时）</div>
          <el-empty v-if="pendingPrescriptions.length === 0" description="暂无待缴费处方" />
          <el-table v-else :data="pendingPrescriptions" class="cute-table pending-rx-table" :header-cell-style="{ background: '#F8FAFC', color: '#475569', fontWeight: '800' }">
            <el-table-column prop="prescription_code" label="处方编号" min-width="180" />
            <el-table-column prop="pet_name" label="宠物" min-width="140" />
            <el-table-column label="倒计时" width="150">
              <template #default="{ row }">
                <el-text :type="row.expired ? 'info' : 'danger'">{{ row.countdown }}</el-text>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="120" />
          </el-table>
        </div>
        <el-table :data="rows" class="cute-table" :header-cell-style="{ background: '#F8FAFC', color: '#475569', fontWeight: '800' }">
          <el-table-column prop="record_code" label="诊单号" min-width="190">
            <template #default="{ row }">
              <span class="code-font">{{ row.record_code }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="pet_name" label="宠物" min-width="120">
            <template #default="{ row }">
              <span class="fw-bold text-primary">{{ row.pet_name }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="140">
            <template #default="{ row }">
              <el-tag 
                round 
                effect="light" 
                :type="row.status === '待收费' ? 'warning' : 'success'" 
                class="status-tag"
              >
                {{ row.status === "待收费" ? "🕐 待收费" : "✅ 已收费" }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="应收金额" width="140" align="right">
            <template #default="{ row }">
              <span class="amount-text" :class="{ 'is-pending': row.status === '待收费' }">
                ¥ {{ row.amount.toFixed(2) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="支付方式" width="150">
            <template #default="{ row }">
              <el-select v-model="row.paymentMethod" size="small" style="width: 120px">
                <el-option label="微信支付" value="微信支付" />
                <el-option label="支付宝" value="支付宝" />
                <el-option label="银联" value="银联" />
                <el-option label="现金" value="现金" />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="收费" width="120">
            <template #default="{ row }">
              <el-button size="small" type="success" :disabled="row.status !== '待收费'" @click="chargeRow(row)">收费</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div class="list-meta">
          共 <span class="meta-highlight">{{ rows.length }}</span> 条记录，最后更新于 {{ lastUpdated || "--:--" }}
        </div>
      </div>
    </el-card>
    <el-dialog v-model="payDialogVisible" title="模拟支付" width="420px" :close-on-click-modal="false">
      <div class="pay-box">
        <div>应付金额：¥ {{ payAmount.toFixed(2) }}</div>
        <div>支付方式：{{ payMethod }}</div>
        <img v-if="showQr" class="qr" src="https://api.qrserver.com/v1/create-qr-code/?size=220x220&data=shironosuke-demo-pay" alt="qr" />
        <div class="wait-tip"><span class="breath-dot"></span> 等待扫码支付...</div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
// ==========================================
// 逻辑代码层 (完全保持不变)
// ==========================================
import { computed, onMounted, onUnmounted, ref } from "vue";
import { ElMessage } from "element-plus";
import { useRouter } from "vue-router";
import * as XLSX from "xlsx";
import { fetchAppointments } from "../api/appointments";
import { fetchPrescriptions } from "../api/prescriptions";
import { notifySettlementComplete } from "../api/notifications";
import { getErrorMessage } from "../utils/status";

const rows = ref([]);
const router = useRouter();
const settling = ref(false);
const exporting = ref(false);
const lastUpdated = ref("");
const pendingPrescriptions = ref([]);
const payDialogVisible = ref(false);
const payAmount = ref(0);
const payMethod = ref("");
const showQr = ref(false);
let rxTimer = null;

const pendingCount = computed(() => rows.value.filter((x) => x.status === "待收费").length); 
const paidCount = computed(() => rows.value.filter((x) => x.status === "已收费").length);
const totalIncome = computed(() => rows.value.filter((x) => x.status === "已收费").reduce((s, x) => s + x.amount, 0));

async function loadData() {
  try {
    const [result, prescriptionRes] = await Promise.all([
      fetchAppointments({ clinicId: "C001" }),
      fetchPrescriptions("C001")
    ]);
    rows.value = (result.data || []).slice(0, 12).map((x, i) => ({
      record_code: x.record_code,
      pet_name: x.pet_name || `宠物#${x.pet_id}`,
      status: i % 3 === 0 ? "待收费" : "已收费",
      amount: 120 + (Number(x.priority_score || 0) * 2),
      paymentMethod: "微信支付"
    }));
    pendingPrescriptions.value = (prescriptionRes.data || [])
      .filter((x) => x.status === "待缴费")
      .map((x) => {
        const remainingMs = new Date(x.expire_at).getTime() - Date.now();
        const expired = remainingMs <= 0;
        const safeMs = Math.max(0, remainingMs);
        const h = String(Math.floor(safeMs / 3600000)).padStart(2, "0");
        const m = String(Math.floor((safeMs % 3600000) / 60000)).padStart(2, "0");
        const s = String(Math.floor((safeMs % 60000) / 1000)).padStart(2, "0");
        return {
          ...x,
          countdown: `${h}:${m}:${s}`,
          status: expired ? "已失效" : "待缴费",
          expired
        };
      });
    lastUpdated.value = new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "结算数据加载失败"));
  }
}

async function settleToday() {
  settling.value = true;
  try {
    await notifySettlementComplete(paidCount.value, totalIncome.value);
    ElMessage.success("已完成结算并推送院区主任");
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "上报结算失败"));
  } finally {
    settling.value = false;
  }
}

async function exportStatement() {
  exporting.value = true;
  try {
    const dateText = new Date().toISOString().slice(0, 10);
    const data = rows.value.map((row) => ({
      日期: dateText,
      诊单编号: row.record_code,
      宠物名称: row.pet_name,
      服务项目: "门诊诊疗",
      金额: Number(row.amount || 0),
      支付方式: row.status === "已收费" ? "微信/支付宝" : "待支付",
      经手人: "前台接诊员",
    }));
    const ws = XLSX.utils.json_to_sheet(data);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "日结对账单");
    const fileName = `白之助宠物医院_日结对账单_${dateText}.xlsx`;
    XLSX.writeFile(wb, fileName);
    ElMessage.success(`导出成功，共${data.length}条记录`);
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "导出失败"));
  } finally {
    exporting.value = false;
  }
}

function chargeRow(row) {
  payAmount.value = Number(row.amount || 0);
  payMethod.value = row.paymentMethod || "微信支付";
  if (payMethod.value === "微信支付" || payMethod.value === "支付宝") {
    showQr.value = true;
    payDialogVisible.value = true;
    window.setTimeout(() => {
      row.status = "已收费";
      payDialogVisible.value = false;
      ElMessage.success("支付成功，账单已结算");
    }, 30000);
  } else {
    row.status = "已收费";
    ElMessage.success("已完成收费结算");
  }
}

onMounted(async () => {
  await loadData();
  rxTimer = window.setInterval(async () => {
    await loadData();
  }, 30000);
});

onUnmounted(() => {
  if (rxTimer) window.clearInterval(rxTimer);
});
</script>

<style scoped>
/* ====================================================
   全局变量与基础设定
   ==================================================== */
:root {
  --primary: #3B82F6;
  --primary-hover: #2563EB;
  --success: #10B981;
  --warning: #F59E0B;
  --bg-page: #F8FAFC;
  --surface: #FFFFFF;
  --text-main: #1E293B;
  --text-sub: #64748B;
  --spring: cubic-bezier(0.34, 1.56, 0.64, 1);
  --smooth: cubic-bezier(0.4, 0, 0.2, 1);
}

.layout-bg {
  background-color: var(--bg-page);
  min-height: 100vh;
  padding: 24px;
  font-family: 'Nunito', ui-rounded, 'Hiragino Maru Gothic ProN', 'PingFang SC', sans-serif;
}

.fw-bold { font-weight: 800; }
.text-primary { color: var(--primary); }
.mb16 { margin-bottom: 16px; }
.mb24 { margin-bottom: 24px; }

/* ====================================================
   玻璃态主卡片 & 标题栏
   ==================================================== */
:deep(.glass-card) {
  border-radius: 20px !important; 
  border: 1px solid rgba(226, 232, 240, 0.8) !important;
  box-shadow: 0 20px 40px -10px rgba(15, 23, 42, 0.05), 0 10px 15px -5px rgba(15, 23, 42, 0.02) !important;
  background: var(--surface); 
  overflow: visible;
}
:deep(.glass-card > .el-card__header) {
  background: linear-gradient(to right, #FFFFFF, #F8FAFC); 
  border-bottom: 1px solid #F1F5F9;
  padding: 20px 24px; 
  border-radius: 20px 20px 0 0;
}
.header-row { display: flex; justify-content: space-between; align-items: center; }
.page-title { font-size: 22px; font-weight: 800; color: var(--text-main); letter-spacing: 0.5px; display: flex; align-items: center; gap: 8px;}
.sub-badge { font-size: 12px; background: #E0E7FF; color: #4F46E5; padding: 4px 10px; border-radius: 20px; font-weight: 800; }
.cute-breadcrumb { font-weight: 700; padding: 0 4px; }

/* ====================================================
   核心按钮防隐身样式 (The Bulletproof Button)
   ==================================================== */
.agile-btn {
  border-radius: 100px !important; 
  height: 44px !important; 
  font-weight: 800 !important; 
  padding: 0 24px !important;
  transition: all 0.3s var(--spring) !important; 
  border: none !important;
  font-size: 15px !important;
}

/* 正常状态：亮眼渐变 + 强力文字阴影 */
.btn-settle {
  background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%) !important;
  color: #FFFFFF !important;
  text-shadow: 0px 1px 2px rgba(0, 0, 0, 0.3) !important; /* 文字阴影防止隐身 */
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3) !important;
}
/* 悬停状态：上浮 */
.btn-settle:hover:not(:disabled):not(.is-loading) {
  transform: translateY(-2px) scale(1.02) !important;
  box-shadow: 0 6px 16px rgba(59, 130, 246, 0.4) !important;
  background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
}
/* 禁用/加载状态：强制浅灰底 + 深灰字 */
.btn-settle:disabled,
.btn-settle.is-loading {
  background: #F1F5F9 !important;
  color: #475569 !important; 
  text-shadow: none !important;
  border: 1px solid #CBD5E1 !important;
  box-shadow: none !important;
}
/* 强制穿透修改 Loading 图标颜色 */
:deep(.btn-settle.is-loading .el-icon) {
  color: #475569 !important;
}

/* ====================================================
   灵动统计看板 (Dashboard Widgets)
   ==================================================== */
.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 24px;
  border-radius: 20px;
  transition: all 0.4s var(--spring);
  border: 1px solid transparent;
}
.stat-card:hover {
  transform: translateY(-4px) scale(1.01);
}
.stat-icon {
  font-size: 40px;
  filter: drop-shadow(0 4px 6px rgba(0,0,0,0.1));
}
.stat-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.k { 
  color: #64748B; 
  font-size: 14px; 
  font-weight: 800; 
}
.v { 
  font-size: 32px; 
  font-weight: 900; 
  font-family: 'Nunito', ui-rounded, 'Hiragino Maru Gothic ProN', sans-serif;
  letter-spacing: -0.5px;
  line-height: 1.1;
}
.currency {
  font-size: 20px;
  margin-right: 2px;
}

/* 各状态专属配色 */
.stat-warning { 
  background: linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%); 
  border-color: #FDE68A;
}
.stat-warning .v { color: #D97706; }
.stat-warning:hover { box-shadow: 0 10px 25px rgba(217, 119, 6, 0.15); border-color: #FCD34D; }

.stat-success { 
  background: linear-gradient(135deg, #ECFDF5 0%, #D1FAE5 100%); 
  border-color: #A7F3D0;
}
.stat-success .v { color: #059669; }
.stat-success:hover { box-shadow: 0 10px 25px rgba(5, 150, 105, 0.15); border-color: #6EE7B7; }

.stat-primary { 
  background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%); 
  border-color: #BFDBFE;
}
.stat-primary .v { color: #1D4ED8; }
.stat-primary:hover { box-shadow: 0 10px 25px rgba(29, 78, 216, 0.15); border-color: #93C5FD; }

/* ====================================================
   可爱的数据表格
   ==================================================== */
:deep(.cute-table) {
  border-radius: 16px; 
  overflow: hidden; 
  border: 1px solid #F1F5F9;
  --el-table-border-color: #F1F5F9;
}
:deep(.cute-table .el-table__row) { transition: background-color 0.3s var(--smooth); }
:deep(.cute-table .el-table__row:hover > td) { background-color: #F8FAFC !important; }

.code-font {
  font-family: 'JetBrains Mono', monospace; 
  font-size: 14px; 
  color: #475569;
  background: #F1F5F9;
  padding: 4px 8px;
  border-radius: 8px;
}

.status-tag { font-weight: 800; padding: 0 12px; border: none !important;}
.amount-text {
  font-size: 16px;
  font-weight: 800;
  color: #059669; 
  font-family: 'JetBrains Mono', monospace;
}
.amount-text.is-pending {
  color: #D97706; 
}

/* 底部元信息 */
.list-meta { margin-top: 16px; color: #94A3B8; font-size: 13px; font-weight: 600; text-align: right; }
.meta-highlight { color: var(--primary); font-weight: 800; font-size: 15px; }
.pending-rx-panel {
  margin-bottom: 16px;
}
.pending-rx-title {
  font-size: 14px;
  font-weight: 800;
  color: #1e293b;
  margin-bottom: 8px;
}
.pay-box { display: grid; gap: 8px; justify-items: center; }
.qr { width: 220px; height: 220px; border-radius: 8px; }
.wait-tip { color: #16a34a; font-weight: 700; }
.breath-dot {
  display: inline-block; width: 8px; height: 8px; border-radius: 50%;
  background: #16a34a; margin-right: 6px; animation: breathing 1.2s ease-in-out infinite;
}
@keyframes breathing { 0% { opacity: .3 } 50% { opacity: 1 } 100% { opacity: .3 } }

/* ====================================================
   阶梯入场动效 (Staggered Animation)
   ==================================================== */
@keyframes fadeInUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
[class*="stagger-in-"] { animation: fadeInUp 0.6s var(--spring) both; }
.stagger-in-1 { animation-delay: 0.1s; }
.stagger-in-2 { animation-delay: 0.2s; }
.stagger-in-3 { animation-delay: 0.3s; }
.stagger-in-4 { animation-delay: 0.4s; }
.stagger-in-5 { animation-delay: 0.5s; }
</style>
