<template>
  <div class="page layout-bg">
    <el-card class="glass-card main-card stagger-in-1">
      <template #header>
        <div class="header-row">
          <div class="title-wrap">
            <div class="page-title">🏥 笼舍可视化总览</div>
            <div class="meta-subtitle">
              共 <span class="meta-highlight">{{ cages.length }}</span> 个微型舱位，最后更新于 {{ lastUpdated || "--:--" }}
            </div>
          </div>
          <el-space class="action-space">
            <el-select v-model="clinicId" class="agile-select" style="width: 170px" @change="loadData">
              <el-option label="📍 C001 沙河口" value="C001" />
              <el-option label="📍 C002 甘井子" value="C002" />
              <el-option label="📍 C003 高新园区" value="C003" />
            </el-select>
            <el-select v-model="zoneFilter" class="agile-select" style="width: 140px" @change="loadData">
              <el-option label="🔍 全部分区" value="" />
              <el-option label="🐶 犬区" value="犬区" />
              <el-option label="🐱 猫区" value="猫区" />
              <el-option label="⭐ VIP" value="VIP" />
              <el-option label="🚑 ICU" value="ICU" />
              <el-option label="🧪 隔离" value="隔离" />
            </el-select>
            <el-button class="agile-btn btn-ghost" :loading="loading" @click="loadData">
              <span class="btn-text">🔄 刷新矩阵</span>
            </el-button>
          </el-space>
        </div>
      </template>

      <div class="legend-bar stagger-in-2">
        <span class="legend-item"><div class="dot-jelly free-bg" /> 呼吸空闲</span>
        <span class="legend-item"><div class="dot-jelly busy-bg" /> 深度住院</span>
        <span class="legend-item"><div class="dot-jelly pending-bg" /> 准备入院</span>
        <span class="legend-item"><div class="dot-jelly clean-bg" /> 消毒待清</span>
        <span class="legend-item"><div class="dot-jelly repair-bg" /> 维护封锁</span>
      </div>

      <el-row :gutter="20" class="stagger-in-3">
        <el-col v-for="zone in zoneBoards" :key="zone.zoneType" :xs="24" :sm="24" :md="12" :lg="12" :xl="8">
          <el-card class="zone-glass-card" shadow="never">
            <template #header>
              <div class="zone-header">
                <span class="zone-title">{{ zoneIcon(zone.zoneType) }} {{ zone.zoneType }}</span>
                <el-tag round effect="light" class="zone-tag">{{ zone.cages.length }} 个舱位</el-tag>
              </div>
            </template>

            <div class="zone-grid" :class="zoneGridClass(zone.zoneType)">
              
              <el-tooltip 
                v-for="cage in zone.cages" 
                :key="cage.id"
                placement="top" 
                effect="light"
                popper-class="jelly-tooltip"
                :show-after="200"
              >
                <template #content>
                  <div class="tooltip-content">
                    <div class="tt-header">
                      <span class="tt-code">{{ cage.cage_code }}</span>
                      <el-tag size="small" :type="getStatusTagType(cage.status)" effect="dark" round>{{ cage.status }}</el-tag>
                    </div>
                    <div v-if="cage.status === '住院中'" class="tt-body">
                      <div class="tt-row"><span>🐾 宠物：</span><strong>{{ cage.petSpeciesIcon }} {{ cage.petName }} ({{ cage.petSpeciesText }})</strong></div>
                      <div class="tt-row"><span>👤 主人：</span><strong>{{ cage.ownerName }}</strong></div>
                      <div class="tt-row"><span>🕒 入院：</span><strong>{{ cage.admissionTime || "--" }}</strong></div>
                      <div class="tt-row"><span>💰 消费：</span><strong class="text-danger">{{ cage.consumedAmountText }}</strong></div>
                      <div class="tt-row"><span>💳 余额：</span><strong class="text-success">{{ cage.depositBalanceText }}</strong></div>
                    </div>
                    <div v-else class="tt-body-empty">
                      当前舱位状态：{{ cage.status }}
                    </div>
                  </div>
                </template>

                <div
                  class="cage-cell"
                  :class="statusClass(cage.status)"
                  @click="selectCage(cage)"
                >
                  <div class="cell-top">
                    <span class="code-font">{{ cage.cage_code.split('-').pop() }}</span>
                  </div>
                  <div class="cell-center">
                    <span v-if="cage.status === '住院中'" class="pet-emoji">{{ cage.petSpeciesIcon }}</span>
                    <span v-else-if="cage.status === '空闲'" class="empty-icon">🍃</span>
                    <span v-else-if="cage.status === '待清洁'" class="clean-icon">✨</span>
                    <span v-else-if="cage.status === '维修/其他'" class="repair-icon">🔧</span>
                  </div>
                  <div class="cell-bottom">
                    <span v-if="cage.status === '住院中'" class="pet-name-mini">{{ cage.petName }}</span>
                    <span v-else class="status-mini">{{ cage.status }}</span>
                  </div>
                </div>
              </el-tooltip>
              
            </div>
          </el-card>
        </el-col>
      </el-row>
    </el-card>

    <el-drawer v-model="drawerVisible" title="🐾 舱位全息档案" size="430px" class="glass-drawer">
      <template v-if="activeCage">
        <el-descriptions :column="1" border class="cute-descriptions">
          <el-descriptions-item label="舱位编号"><span class="code-font-lg">{{ activeCage.cage_code }}</span></el-descriptions-item>
          <el-descriptions-item label="所属分区">
            <el-tag effect="light" type="info" round class="fw-bold">{{ activeCage.zone_type }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="当前状态">
            <el-tag :type="getStatusTagType(activeCage.status)" effect="dark" round class="fw-bold">{{ activeCage.status }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="入住宠物">
            <span class="fw-bold text-primary">{{ activeCage.petSpeciesIcon }} {{ activeCage.petName || "未入住" }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="物种档案">{{ activeCage.petSpeciesText }}</el-descriptions-item>
          <el-descriptions-item label="联系主人"><span class="fw-bold">{{ activeCage.ownerName || "--" }}</span></el-descriptions-item>
          <el-descriptions-item label="住院状态">{{ activeCage.inpatientStatus || "--" }}</el-descriptions-item>
          <el-descriptions-item label="入院时间">{{ activeCage.admissionTime || "--" }}</el-descriptions-item>
          <el-descriptions-item label="当前消费"><span class="fw-bold text-danger">{{ activeCage.consumedAmountText }}</span></el-descriptions-item>
          <el-descriptions-item label="押金余额"><span class="fw-bold text-success">{{ activeCage.depositBalanceText }}</span></el-descriptions-item>
          <el-descriptions-item label="相邻节点">
            <span class="code-font-sm">{{ (activeCage.adjacent_cage_ids || []).length ? activeCage.adjacent_cage_ids.join(", ") : "独立隔离" }}</span>
          </el-descriptions-item>
        </el-descriptions>
        <el-divider>体征录入</el-divider>
        <el-form :model="vitalsForm" label-width="96px">
          <el-form-item :label="`体温(℃)`">
            <el-input v-model.number="vitalsForm.temperature" type="number" :step="0.1" />
            <el-text type="info" style="margin-left:8px">{{ vitalsRangeText }}</el-text>
          </el-form-item>
          <el-form-item label="心率(bpm)">
            <el-input v-model.number="vitalsForm.heart_rate" type="number" />
          </el-form-item>
          <el-form-item label="备注">
            <el-input v-model="vitalsForm.notes" type="textarea" :rows="2" />
          </el-form-item>
          <el-button class="agile-btn" type="primary" :loading="vitalsSubmitting" @click="submitVitals">
            提交体征
          </el-button>
        </el-form>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
// ==========================================
// 逻辑代码层 (完全保持不变)
// ==========================================
import { computed, onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import { createNursingLog, fetchCages, fetchInpatientRecords } from "../api/inpatient";
import { fetchPets } from "../api/pets";
import { fetchOwners } from "../api/owners";
import { getErrorMessage } from "../utils/status";

const clinicId = ref("C001");
const zoneFilter = ref("");
const cages = ref([]);
const inpatientRecords = ref([]);
const pets = ref([]);
const owners = ref([]);
const loading = ref(false);
const lastUpdated = ref("");
const drawerVisible = ref(false);
const activeCage = ref(null);
const vitalsSubmitting = ref(false);
const vitalsForm = ref({
  temperature: 38.5,
  heart_rate: 120,
  notes: ""
});

const ownerMap = computed(() => { const map = new Map(); for (const owner of owners.value) map.set(owner.id, owner); return map; });
const petMap = computed(() => { const map = new Map(); for (const pet of pets.value) map.set(pet.id, pet); return map; });

const inpatientByCageId = computed(() => {
  const map = new Map();
  for (const item of inpatientRecords.value) {
    if (!item?.cage_id) continue;
    if (!map.has(item.cage_id)) map.set(item.cage_id, item);
  }
  return map;
});

const decoratedCages = computed(() =>
  cages.value.map((cage) => {
    const inpatient = inpatientByCageId.value.get(cage.id);
    const pet = petMap.value.get(cage.current_pet_id || inpatient?.pet_id);
    const owner = ownerMap.value.get(pet?.owner_id);
    const species = String(pet?.species || "");
    const petSpeciesIcon = species.includes("犬") ? "🐶" : species.includes("猫") ? "🐱" : species.includes("兔") ? "🐰" : species.includes("鸟") ? "🦜" : "🐾";
    const petSpeciesText = species || "未知";
    const deposit = Number(inpatient?.deposit_amount || 0);
    const consumed = Number(inpatient?.consumed_amount || 0);
    return {
      ...cage,
      petName: pet?.name || "",
      ownerName: owner?.name || "",
      petSpeciesIcon,
      petSpeciesText,
      inpatientStatus: inpatient?.status || "",
      admissionTime: formatDateTime(inpatient?.admission_time),
      consumedAmountText: consumed ? `¥${consumed.toFixed(2)}` : "--",
      depositBalanceText: deposit ? `¥${(deposit - consumed).toFixed(2)}` : "--"
    };
  })
);

const zoneBoards = computed(() => {
  const groups = {};
  for (const cage of decoratedCages.value) {
    const zone = cage.zone_type || "未分区";
    if (!groups[zone]) groups[zone] = [];
    groups[zone].push(cage);
  }
  const order = ["犬区", "猫区", "VIP", "ICU", "隔离", "临时笼", "未分区"];
  return order.filter((z) => groups[z]).map((z) => ({
    zoneType: z,
    cages: groups[z].sort((a, b) => String(a.cage_code).localeCompare(String(b.cage_code)))
  }));
});

function zoneIcon(zoneType) {
  if (zoneType === "犬区") return "🐶";
  if (zoneType === "猫区") return "🐱";
  if (zoneType === "VIP") return "⭐";
  if (zoneType === "ICU") return "🚑";
  if (zoneType === "隔离") return "🧪";
  return "📦";
}

function zoneGridClass(zoneType) {
  if (zoneType === "犬区" || zoneType === "猫区") return "grid-5";
  if (zoneType === "VIP" || zoneType === "ICU") return "grid-4";
  if (zoneType === "隔离" || zoneType === "临时笼") return "grid-2";
  return "grid-3";
}

function statusClass(status) {
  if (status === "空闲") return "free";
  if (status === "住院中") return "busy";
  if (status === "待入院") return "pending";
  if (status === "待清洁") return "clean";
  return "repair";
}

function getStatusTagType(status) {
  if (status === "空闲") return "success";
  if (status === "住院中") return "primary";
  if (status === "待入院") return "warning";
  if (status === "待清洁") return "info";
  return "danger";
}

function selectCage(cage) { activeCage.value = cage; drawerVisible.value = true; }

const vitalsRangeText = computed(() => {
  const species = String(activeCage.value?.petSpeciesText || "");
  if (species.includes("犬")) return "犬 38.0-39.5℃";
  if (species.includes("猫")) return "猫 38.1-39.2℃";
  return "其他 38.0-40.0℃";
});

async function submitVitals() {
  if (!activeCage.value?.id) {
    ElMessage.warning("当前笼位暂无住院记录");
    return;
  }
  const inpatient = inpatientByCageId.value.get(activeCage.value.id);
  if (!inpatient) {
    ElMessage.warning("该笼位暂无住院记录");
    return;
  }
  vitalsSubmitting.value = true;
  try {
    await createNursingLog(inpatient.id, {
      temperature: Number(vitalsForm.value.temperature || 0),
      heart_rate: Number(vitalsForm.value.heart_rate || 0),
      notes: vitalsForm.value.notes || ""
    });
    ElMessage.success("体征录入成功");
    vitalsForm.value.notes = "";
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "体征录入失败"));
  } finally {
    vitalsSubmitting.value = false;
  }
}

function formatDateTime(value) {
  if (!value) return "";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "";
  const hh = String(d.getHours()).padStart(2, "0");
  const mm = String(d.getMinutes()).padStart(2, "0");
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")} ${hh}:${mm}`;
}

function updateLastUpdated() {
  const now = new Date();
  lastUpdated.value = `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`;
}

async function loadData() {
  loading.value = true;
  try {
    const [cageRes, inpatientRes, petRes, ownerRes] = await Promise.all([
      fetchCages(clinicId.value, zoneFilter.value),
      fetchInpatientRecords(clinicId.value),
      fetchPets(),
      fetchOwners()
    ]);
    cages.value = cageRes.data || [];
    inpatientRecords.value = inpatientRes.data || [];
    pets.value = petRes.data || [];
    owners.value = ownerRes.data || [];
    updateLastUpdated();
  } catch (error) { ElMessage.error(getErrorMessage(error, "笼舍状态加载失败")); } 
  finally { loading.value = false; }
}

onMounted(loadData);
</script>

<style scoped>
/* ====================================================
   全局变量与基础设定 (Spring 物理曲线)
   ==================================================== */
:root {
  --primary: #3B82F6;
  --success: #10B981;
  --danger: #EF4444;
  --warning: #F59E0B;
  --bg-page: #F8FAFC;
  --surface: #FFFFFF;
  --text-main: #1E293B;
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
.text-danger { color: var(--danger); }
.text-success { color: var(--success); }

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
.header-row { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;}
.title-wrap { display: flex; flex-direction: column; gap: 4px; }
.page-title { font-size: 22px; font-weight: 800; color: var(--text-main); letter-spacing: 0.5px; }
.meta-subtitle { font-size: 13px; color: #64748B; font-weight: 600;}
.meta-highlight { color: var(--primary); font-weight: 800; font-size: 15px; }

/* 控件区 */
.action-space { display: flex; gap: 12px; }
:deep(.agile-select .el-input__wrapper) { border-radius: 12px !important; background-color: #F8FAFC; box-shadow: 0 0 0 1px #E2E8F0 inset !important; transition: all 0.3s var(--spring) !important; }
:deep(.agile-select .el-input__wrapper.is-focus) { background-color: #FFFFFF; box-shadow: 0 0 0 2px var(--primary) inset, 0 4px 12px rgba(59, 130, 246, 0.1) !important; }

.agile-btn { border-radius: 100px !important; height: 36px !important; font-weight: 800 !important; padding: 0 20px !important; transition: all 0.3s var(--spring) !important; border: none !important; }
.btn-ghost { background-color: #FFFFFF !important; color: #64748B !important; border: 2px solid #E2E8F0 !important; box-shadow: 0 2px 4px rgba(0,0,0,0.02) !important; }
.btn-ghost:hover { border-color: #CBD5E1 !important; color: #1E293B !important; transform: translateY(-2px) !important; }

/* ====================================================
   治愈系图例 (Legend)
   ==================================================== */
.legend-bar { display: flex; gap: 20px; margin-bottom: 24px; padding: 12px 20px; background: #FFFFFF; border-radius: 16px; border: 1px dashed #E2E8F0; flex-wrap: wrap; }
.legend-item { display: flex; align-items: center; gap: 8px; font-size: 14px; font-weight: 700; color: #475569; }
.dot-jelly { width: 14px; height: 14px; border-radius: 50%; box-shadow: inset 0 -2px 4px rgba(0,0,0,0.1); }

/* 色彩定义 */
.free-bg { background: #10B981; }
.busy-bg { background: #3B82F6; }
.pending-bg { background: #F59E0B; }
.clean-bg { background: #8B5CF6; }
.repair-bg { background: #94A3B8; }

/* ====================================================
   分区卡片与舱位矩阵 (Zone & Grid)
   ==================================================== */
.zone-glass-card { margin-bottom: 20px; border-radius: 16px !important; border: 1px solid #E2E8F0 !important; background: #FAFAFA !important;}
:deep(.zone-glass-card .el-card__header) { padding: 12px 20px; background: #F1F5F9; border-bottom: 1px solid #E2E8F0; }
.zone-header { display: flex; justify-content: space-between; align-items: center; }
.zone-title { font-size: 16px; font-weight: 800; color: #1E293B; }
.zone-tag { font-weight: 800; border: none; background: #FFFFFF;}

.zone-grid { display: grid; gap: 12px; padding: 4px; }
.grid-5 { grid-template-columns: repeat(auto-fill, minmax(60px, 1fr)); }
.grid-4 { grid-template-columns: repeat(auto-fill, minmax(70px, 1fr)); }
.grid-3 { grid-template-columns: repeat(auto-fill, minmax(80px, 1fr)); }
.grid-2 { grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)); }

/* 微型舱位卡片设计 */
.cage-cell {
  position: relative;
  border-radius: 14px;
  padding: 8px;
  cursor: pointer;
  transition: all 0.3s var(--spring);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  align-items: center;
  aspect-ratio: 1 / 1.1; /* 保持微缩比例 */
  border: 2px solid transparent;
}

.cage-cell:hover {
  transform: translateY(-4px) scale(1.05);
  box-shadow: 0 10px 20px -5px rgba(0,0,0,0.15);
  z-index: 10;
}

.cell-top { width: 100%; text-align: left; }
.code-font { font-family: 'JetBrains Mono', monospace; font-size: 13px; font-weight: 800; color: #475569; opacity: 0.7;}

.cell-center { flex-grow: 1; display: flex; align-items: center; justify-content: center; }
.pet-emoji { font-size: 28px; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2)); }
.empty-icon { font-size: 24px; opacity: 0.4; }
.clean-icon { font-size: 24px; filter: hue-rotate(240deg); opacity: 0.8;}
.repair-icon { font-size: 24px; opacity: 0.5; filter: grayscale(1); }

.cell-bottom { width: 100%; text-align: center; }
.pet-name-mini { font-size: 12px; font-weight: 800; color: #1E293B; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: block;}
.status-mini { font-size: 11px; font-weight: 800; opacity: 0.6; }

/* 状态专属配色与边框发光 */
.free { background: #ECFDF5; border-color: #A7F3D0; color: #059669; }
.free:hover { border-color: #10B981; box-shadow: 0 8px 16px rgba(16, 185, 129, 0.2); }

.busy { background: #EFF6FF; border-color: #BFDBFE; color: #1D4ED8; }
.busy:hover { border-color: #3B82F6; box-shadow: 0 8px 16px rgba(59, 130, 246, 0.2); }
.busy .code-font { color: #1D4ED8; opacity: 1;}

.pending { background: #FFFBEB; border-color: #FDE68A; color: #D97706; }
.pending:hover { border-color: #F59E0B; box-shadow: 0 8px 16px rgba(245, 158, 11, 0.2); }

.clean { background: #F5F3FF; border-color: #DDD6FE; color: #6D28D9; }
.clean:hover { border-color: #8B5CF6; box-shadow: 0 8px 16px rgba(139, 92, 246, 0.2); }

.repair { background: #F8FAFC; border-color: #E2E8F0; color: #475569; }
.repair:hover { border-color: #94A3B8; }

/* ====================================================
   悬停信息卡 (Tooltip Popover)
   ==================================================== */
:deep(.jelly-tooltip) {
  background: rgba(255, 255, 255, 0.95) !important;
  backdrop-filter: blur(10px) !important;
  border: 1px solid #E2E8F0 !important;
  box-shadow: 0 20px 40px -10px rgba(0, 0, 0, 0.15) !important;
  border-radius: 16px !important;
  padding: 16px !important;
  color: #1E293B !important;
  font-family: 'Nunito', ui-rounded, 'Hiragino Maru Gothic ProN', sans-serif !important;
}
:deep(.jelly-tooltip .el-popper__arrow::before) {
  background: #FFFFFF !important;
  border: 1px solid #E2E8F0 !important;
}

.tooltip-content { min-width: 200px; display: flex; flex-direction: column; gap: 12px;}
.tt-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px dashed #E2E8F0; padding-bottom: 8px;}
.tt-code { font-family: 'JetBrains Mono', monospace; font-weight: 800; font-size: 16px; color: #0F172A;}
.tt-body { display: flex; flex-direction: column; gap: 8px; font-size: 13px;}
.tt-row { display: flex; justify-content: space-between; align-items: center; }
.tt-row span { color: #64748B; font-weight: 600;}
.tt-body-empty { font-size: 13px; font-weight: 700; color: #94A3B8; text-align: center; padding: 10px 0;}

/* ====================================================
   侧边详情抽屉
   ==================================================== */
:deep(.glass-drawer .el-drawer__header) { font-weight: 800; color: var(--text-main); border-bottom: 1px solid #F1F5F9; padding-bottom: 16px; margin-bottom: 0;}
:deep(.cute-descriptions) { border-radius: 12px; overflow: hidden; border: 1px solid #F1F5F9; margin-top: 16px;}
:deep(.cute-descriptions .el-descriptions__label) { background-color: #F8FAFC !important; font-weight: 800; color: #475569; width: 100px; }
:deep(.cute-descriptions .el-descriptions__content) { color: #1E293B; }
.code-font-lg { font-family: 'JetBrains Mono', monospace; font-size: 18px; font-weight: 800; color: var(--primary); }
.code-font-sm { font-family: 'JetBrains Mono', monospace; font-size: 14px; font-weight: 700; color: #475569; }

/* 动画 */
@keyframes fadeInUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
[class*="stagger-in-"] { animation: fadeInUp 0.6s var(--spring) both; }
.stagger-in-1 { animation-delay: 0.1s; } .stagger-in-2 { animation-delay: 0.2s; } .stagger-in-3 { animation-delay: 0.3s; }
</style>
