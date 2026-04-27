<template>
  <div class="page layout-bg">
    <el-card class="glass-card main-card">
      <template #header>
        <div class="header-row">
          <span class="page-title">🏥 门诊挂号中心</span>
          <el-space>
            <el-select v-model="filters.clinic_id" placeholder="📍 院区筛选" clearable class="agile-select" style="width: 160px">
              <el-option label="C001 沙河口" value="C001" />
              <el-option label="C002 甘井子" value="C002" />
              <el-option label="C003 高新园区" value="C003" />
            </el-select>
            <el-button class="agile-btn btn-ghost" :loading="tableLoading" :disabled="tableLoading" @click="loadAppointments">
              <span class="btn-text">🔄 刷新</span>
            </el-button>
            <el-button class="agile-btn btn-primary" :disabled="tableLoading" @click="openCreateDialog">
              <span class="btn-text">✨ 新建预约</span>
            </el-button>
          </el-space>
        </div>
      </template>

      <el-alert type="success" :closable="false" show-icon class="mb16">
        ⚡ 动态排队引擎运行中，每分钟实时更新优先级
      </el-alert>
      <el-skeleton :loading="tableLoading" :rows="6" animated class="cute-skeleton">
        <template #default>
          <transition name="slide-fade">
            <el-alert
              v-if="loadError"
              type="error"
              :title="loadError"
              show-icon
              :closable="false"
              class="agile-alert mb16"
            >
              <template #default>
                <el-button size="small" class="agile-btn-small" @click="loadAppointments">重试</el-button>
              </template>
            </el-alert>
          </transition>
          
          <el-table :data="visibleAppointments" class="cute-table" :row-class-name="queueRowClass" :header-cell-style="{ background: '#F8FAFC', color: '#475569', fontWeight: '800' }">
            <el-table-column prop="record_code" label="诊单编号" min-width="210">
              <template #default="{ row }">
                <div class="code-cell">
                  <el-input :model-value="row.record_code" readonly class="code-input" />
                  <el-button size="small" class="agile-btn-small btn-copy" @click="copyText(row.record_code)">复制</el-button>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="pet_name" label="宠物" min-width="150">
               <template #default="{ row }"><span class="fw-bold">{{ row.pet_name || `#${row.pet_id}` }}</span></template>
            </el-table-column>
            <el-table-column prop="doctor_name" label="医生" min-width="140">
               <template #default="{ row }"><span class="fw-bold text-primary">{{ row.doctor_name || `#${row.doctor_id}` }}</span></template>
            </el-table-column>
            <el-table-column prop="clinic_name" label="院区" min-width="120">
               <template #default="{ row }">
                 <el-tag effect="light" type="info" round class="clinic-tag">{{ row.clinic_name || row.clinic_id }}</el-tag>
               </template>
            </el-table-column>
            <el-table-column prop="scheduled_time" label="就诊时间" min-width="170">
              <template #default="{ row }">
                 <span class="time-text">🕒 {{ row.scheduled_time?.replace('T', ' ') || '-' }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="urgency_level" label="紧急程度" width="110">
              <template #default="{ row }">
                <el-tag round :class="['urgency-tag', `urgency-${row.urgency_level === '急诊' ? 'danger' : row.urgency_level === '优先' ? 'warning' : 'normal'}`]">
                  {{ row.urgency_level }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="dynamic_priority_score" label="评分" width="120">
              <template #default="{ row }">
                <span class="score-text">{{ row.dynamic_priority_score }}</span>
                <el-tooltip
                  placement="top"
                  :content="`症状严重度(40%)×${row.priority_detail?.urgency_ratio || '0'} + 等待时长(40%)×${row.priority_detail?.waiting_ratio || '0'} + 年龄(20%)×${row.priority_detail?.age_ratio || '0'}`"
                >
                  <el-text class="score-info">ℹ️</el-text>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="110">
              <template #default="{ row }">
                <el-tag round effect="dark" :type="getStatusTagType(row.status)" class="status-tag">{{ mapStatus(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120" fixed="right">
              <template #default="{ row }">
                <el-button
                  size="small"
                  class="agile-btn-small btn-danger"
                  :loading="cancelingId === row.id"
                  :disabled="tableLoading || row.status === '已取消'"
                  @click="cancelOne(row)"
                >
                  取消挂号
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          <div class="list-meta">
            共 <span class="meta-highlight">{{ appointments.length }}</span> 条记录，最后更新于 {{ lastUpdated || "--:--" }}
          </div>
        </template>
      </el-skeleton>
    </el-card>

    <el-dialog v-model="dialogVisible" title="🎈 新建预约挂号" width="680px" class="glass-dialog" @close="resetDirty">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px" label-position="left" class="modern-form" :class="{ 'emergency-pulse': form.urgency_level === '急诊' }">
        <el-steps :active="appointmentStep" finish-status="success" align-center class="cute-steps mb24">
          <el-step title="选择宠物" icon="Guide" />
          <el-step title="科室排班" icon="Calendar" />
          <el-step title="确认缴费" icon="Wallet" />
        </el-steps>
        
        <transition name="fade-slide" mode="out-in">
          <div v-show="appointmentStep === 0" class="step-container">
            <el-form-item label="📍 院区" prop="clinic_id">
              <el-select v-model="form.clinic_id" placeholder="请选择就诊院区" class="agile-input fluid-select" @change="loadDoctors">
                <el-option label="C001 沙河口院区" value="C001" />
                <el-option label="C002 甘井子院区" value="C002" />
                <el-option label="C003 高新园区" value="C003" />
              </el-select>
            </el-form-item>
            <el-form-item label="🐾 宠物" prop="pet_id">
              <el-select v-model="form.pet_id" filterable placeholder="搜索或选择宠物" class="agile-input fluid-select">
                <el-option v-for="pet in petOptions" :key="pet.id" :label="`${pet.name} (#${pet.id})`" :value="pet.id" />
              </el-select>
            </el-form-item>
          </div>
        </transition>

        <transition name="fade-slide" mode="out-in">
          <div v-show="appointmentStep === 1" class="step-container">
            <el-form-item label="👨‍⚕️ 医生" prop="doctor_id">
              <el-select v-model="form.doctor_id" filterable placeholder="请选择排班医生" class="agile-input fluid-select">
                <el-option
                  v-for="doctor in doctorOptions"
                  :key="doctor.id"
                  :label="`${doctor.full_name} (${doctor.department || '综合门诊'})`"
                  :value="doctor.id"
                  :disabled="doctor.disabled"
                >
                  <el-tooltip v-if="doctor.disabledReason" :content="doctor.disabledReason" placement="right">
                    <span class="doctor-option doctor-option-disabled">{{ doctor.full_name }} <span class="doc-id">({{ doctor.department || "综合门诊" }})</span></span>
                  </el-tooltip>
                  <span v-else class="doctor-option">{{ doctor.full_name }} <span class="doc-id">({{ doctor.department || "综合门诊" }})</span></span>
                </el-option>
              </el-select>
              <transition name="fade">
                <div v-if="unavailableDoctorsText" class="doc-warning-text">⚠️ {{ unavailableDoctorsText }}</div>
              </transition>
            </el-form-item>
            
            <el-form-item label="🕒 时间" prop="scheduled_time">
              <el-date-picker
                v-model="form.scheduled_time"
                type="datetime"
                value-format="YYYY-MM-DDTHH:mm:ss"
                placeholder="点击选择精确时间"
                class="agile-input fluid-select"
                :editable="false"
              />
            </el-form-item>

            <el-form-item v-if="slotMatrixRows.length > 0">
              <template #label>
                <div class="label-help">
                  排班视图
                  <el-tooltip content="粉色=已满；薄荷绿=可约。点击方块可快速锁定时间和医生哦！" placement="top">
                    <span class="help-icon">?</span>
                  </el-tooltip>
                </div>
              </template>
              <div class="slot-matrix-card">
                <div class="slot-matrix">
                  <div class="slot-header time-header">时间轴</div>
                  <div v-for="doctor in doctorOptions" :key="`header-${doctor.id}`" class="slot-header doc-header">
                    {{ doctor.full_name }}<span class="doc-id">({{ doctor.department || "综合门诊" }})</span>
                  </div>
                  <template v-for="row in slotMatrixRows" :key="row.timeLabel">
                    <div class="slot-time">{{ row.timeLabel }}</div>
                    <div
                      v-for="cell in row.cells"
                      :key="`${row.timeLabel}-${cell.doctorId}`"
                      class="slot-cell"
                      :class="{ occupied: cell.occupied, selected: isCellSelected(cell) }"
                      @click="chooseSlot(cell)"
                      :title="cell.occupied ? '呜呜，此时段已被预约' : '点击抢占此时段！'"
                    >
                      <span v-if="isCellSelected(cell)">✔️</span>
                      <span v-else>{{ cell.occupied ? "已满" : "可约" }}</span>
                    </div>
                  </template>
                </div>
              </div>
            </el-form-item>
            
            <transition name="bounce">
              <el-form-item v-if="bestAvailableCell">
                <div class="recommend-box">
                  <span class="rec-text">💡 推荐最快时段：<strong>{{ bestAvailableCell.timeLabel }}</strong> (医生 #{{ bestAvailableCell.doctorId }})</span>
                  <el-button class="agile-btn-small btn-primary" @click="applyRecommendedSlot">一键填入</el-button>
                </div>
              </el-form-item>
            </transition>
          </div>
        </transition>

        <transition name="fade-slide" mode="out-in">
          <div v-show="appointmentStep === 2" class="step-container">
            <el-form-item prop="urgency_level">
              <template #label>
                <div class="label-help">
                  🚨 紧急程度
                  <el-tooltip content="急诊将获得最高优先级，并触发警报色" placement="top">
                    <span class="help-icon">?</span>
                  </el-tooltip>
                </div>
              </template>
              <el-radio-group v-model="form.urgency_level" class="cute-radio-group">
                <el-radio label="常规" border>常规</el-radio>
                <el-radio label="优先" border>优先</el-radio>
                <el-radio label="急诊" border class="urgent-radio">急诊</el-radio>
              </el-radio-group>
            </el-form-item>
            
            <div class="confirm-ticket">
              <div class="ticket-header">就诊凭证预览</div>
              <div class="ticket-body">
                <div class="ticket-row"><span>🐾 宠物编号：</span><strong>#{{ form.pet_id || "未选" }}</strong></div>
                <div class="ticket-row"><span>👨‍⚕️ 负责医生：</span><strong>#{{ form.doctor_id || "未选" }}</strong></div>
                <div class="ticket-row"><span>🕒 预约时间：</span><strong>{{ form.scheduled_time ? form.scheduled_time.replace('T', ' ') : "未选" }}</strong></div>
              </div>
            </div>
          </div>
        </transition>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button class="agile-btn btn-ghost" :disabled="submitLoading" @click="dialogVisible = false">取消</el-button>
          <el-button class="agile-btn btn-ghost" v-if="appointmentStep > 0" :disabled="submitLoading" @click="appointmentStep -= 1">上一步</el-button>
          <el-button class="agile-btn btn-primary" v-if="appointmentStep < 2" :disabled="submitLoading" @click="nextStep">下一步</el-button>
          <el-button class="agile-btn btn-success" v-else :loading="submitLoading" :disabled="submitLoading" @click="submit">🚀 确认并缴费</el-button>
        </div>
      </template>
    </el-dialog>

    <transition name="slide-up">
      <el-alert v-if="undoBar.visible" class="agile-alert undo-bar" :title="undoBar.title" type="warning" show-icon :closable="false">
        <template #default>
          <el-button class="agile-btn-small" style="margin-left: 16px" @click="undoAction">↩️ 立即撤销</el-button>
        </template>
      </el-alert>
    </transition>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { onBeforeRouteLeave } from "vue-router";

import { cancelAppointment, createAppointment, fetchAppointments } from "../api/appointments";
import { fetchPets } from "../api/pets";
import { fetchDoctors } from "../api/users";
import { getErrorMessage, getStatusTagType } from "../utils/status";

const appointments = ref([]);
const petOptions = ref([]);
const doctorOptions = ref([]);
const dialogVisible = ref(false);
const appointmentStep = ref(0);
const tableLoading = ref(false);
const submitLoading = ref(false);
const cancelingId = ref(null);
const loadError = ref("");
const dirty = ref(false);
const lastUpdated = ref("");
const formRef = ref(null);
const filters = ref({ clinic_id: "" });
const clinicAppointments = ref([]);
const URGENCY_RANK = { "急诊": 3, "优先": 2, "常规": 1 };
const STORAGE_FILTER_KEY = "appointment_filters_v1";
const STORAGE_FORM_KEY = "appointment_form_draft_v1";
const undoBar = ref({ visible: false, title: "", payload: null });
const flashingId = ref(0);
const virtualLimit = ref(50);
let undoTimer = null;
let scoreTimer = null;
const form = ref({
  pet_id: null,
  doctor_id: null,
  clinic_id: "C001",
  scheduled_time: "",
  urgency_level: "常规"
});

const rules = {
  pet_id: [{ required: true, message: "请选择宠物", trigger: "change" }],
  doctor_id: [{ required: true, message: "请选择医生", trigger: "change" }],
  clinic_id: [{ required: true, message: "请选择院区", trigger: "change" }],
  scheduled_time: [{ required: true, message: "请选择就诊时间", trigger: "change" }]
};

const unavailableDoctorsText = computed(() => {
  const unavailable = doctorOptions.value.filter((item) => item.disabled);
  if (unavailable.length === 0) return "";
  const names = unavailable.map((item) => item.full_name).join("、");
  return `已置灰医生：${names}（该时段已满）`;
});

const slotMatrixRows = computed(() => {
  if (!dialogVisible.value || doctorOptions.value.length === 0 || !form.value.clinic_id) return [];
  const baseDate = form.value.scheduled_time
    ? new Date(form.value.scheduled_time)
    : new Date();
  baseDate.setSeconds(0, 0);
  const start = new Date(baseDate);
  start.setHours(9, 0, 0, 0);
  const end = new Date(baseDate);
  end.setHours(17, 0, 0, 0);
  const rows = [];
  for (let t = new Date(start); t <= end; t = new Date(t.getTime() + 30 * 60 * 1000)) {
    const iso = toIsoLocal(t);
    const key = iso.slice(0, 16);
    rows.push({
      timeLabel: key.slice(11, 16),
      iso,
      cells: doctorOptions.value.map((doctor) => ({
        doctorId: doctor.id,
        scheduledTime: iso,
        occupied: clinicAppointments.value.some(
          (item) =>
            item.doctor_id === doctor.id &&
            (item.scheduled_time || "").slice(0, 16) === key &&
            item.status !== "已取消"
        )
      }))
    });
  }
  return rows;
});
const visibleAppointments = computed(() => (appointments.value || []).slice(0, virtualLimit.value));

const bestAvailableCell = computed(() => {
  for (const row of slotMatrixRows.value) {
    const found = row.cells.find((cell) => !cell.occupied);
    if (found) return { ...found, timeLabel: row.timeLabel };
  }
  return null;
});

function mapStatus(status) {
  if (status === "待诊") return "🕐待诊";
  if (status === "就诊中") return "🩺就诊中";
  if (status === "已完成") return "✅已完成";
  if (status === "急诊") return "🚨急诊";
  return status;
}

function toIsoLocal(date) {
  const d = new Date(date);
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  const h = String(d.getHours()).padStart(2, "0");
  const min = String(d.getMinutes()).padStart(2, "0");
  const s = String(d.getSeconds()).padStart(2, "0");
  return `${y}-${m}-${day}T${h}:${min}:${s}`;
}

watch(() => ({ ...form.value }), () => { if (dialogVisible.value) dirty.value = true; }, { deep: true });
watch(() => [form.value.clinic_id, form.value.scheduled_time], async () => { if (dialogVisible.value) await loadDoctors(); });
watch(() => filters.value.clinic_id, () => { window.localStorage.setItem(STORAGE_FILTER_KEY, JSON.stringify(filters.value)); });
watch(() => ({ ...form.value }), () => { if (dialogVisible.value) { window.localStorage.setItem(STORAGE_FORM_KEY, JSON.stringify(form.value)); } }, { deep: true });

function resetDirty() { dirty.value = false; appointmentStep.value = 0; }

function nextStep() {
  if (appointmentStep.value === 0 && (!form.value.clinic_id || !form.value.pet_id)) { ElMessage.warning("请先选择院区和宠物"); return; }
  if (appointmentStep.value === 1 && (!form.value.doctor_id || !form.value.scheduled_time)) { ElMessage.warning("请先选择医生和就诊时间"); return; }
  appointmentStep.value += 1;
}

async function copyText(value) {
  try { await navigator.clipboard.writeText(value); ElMessage.success("已复制"); } catch { ElMessage.warning("复制失败，请手动复制"); }
}

async function loadAppointments() {
  tableLoading.value = true;
  loadError.value = "";
  try {
    const result = await fetchAppointments({ clinicId: filters.value.clinic_id, limit: 60, offset: 0 });
    const decoratedRows = (result.data || []).map((item) => ({ ...item }));
    appointments.value = recomputePriorityRuntime(decoratedRows);
    if (filters.value.clinic_id) clinicAppointments.value = appointments.value;
    lastUpdated.value = new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
  } catch (error) {
    const message = getErrorMessage(error, "预约列表加载失败");
    loadError.value = message;
    ElMessage.error(message);
  } finally { tableLoading.value = false; }
}

function computePriorityDetail(item) {
  const urgencyRatioMap = { 急诊: 0.95, 优先: 0.75, 常规: 0.55 };
  const urgencyRatio = urgencyRatioMap[item.urgency_level] || 0.55;
  const urgencyScore = Math.round(40 * urgencyRatio);
  const scheduled = new Date(item.scheduled_time || Date.now());
  const waitedMinutes = Math.max(0, Math.floor((Date.now() - scheduled.getTime()) / 60000));
  const waitingRatio = Math.min(1, waitedMinutes / 75);
  const waitingScore = Math.round(40 * waitingRatio);
  const ageYears = Number(item.pet_age_years || 5);
  const ageRatio = Math.min(1, Math.max(0.25, ageYears / 12));
  const ageScore = Math.round(20 * ageRatio);
  const total = urgencyScore + waitingScore + ageScore;
  return {
    urgency_ratio: urgencyRatio.toFixed(2),
    waiting_ratio: waitingRatio.toFixed(2),
    age_ratio: ageRatio.toFixed(2),
    urgency_score: urgencyScore,
    waiting_score: waitingScore,
    age_score: ageScore,
    total
  };
}

function sortRowsByPriority(rows) {
  return [...rows].sort((a, b) => {
    const scoreDiff = Number(b.dynamic_priority_score || b.priority_score || 0) - Number(a.dynamic_priority_score || a.priority_score || 0);
    if (scoreDiff !== 0) return scoreDiff;
    const urgencyDiff = (URGENCY_RANK[b.urgency_level] || 0) - (URGENCY_RANK[a.urgency_level] || 0);
    if (urgencyDiff !== 0) return urgencyDiff;
    return String(a.scheduled_time || "").localeCompare(String(b.scheduled_time || ""));
  });
}

function recomputePriorityRuntime(sourceRows) {
  const enriched = (sourceRows || []).map((item) => {
    const detail = computePriorityDetail(item);
    return { ...item, dynamic_priority_score: detail.total, priority_detail: detail };
  });
  return sortRowsByPriority(enriched).map((item, idx) => ({
    ...item,
    priority_detail: {
      ...item.priority_detail,
      queue_hint: idx === 0 ? "已插队至第1位" : `当前第${idx + 1}位`
    }
  }));
}

async function cancelOne(row) {
  try {
    await ElMessageBox.confirm(`确定要取消[${row.pet_name || row.pet_id}]的挂号吗？此操作不可恢复`, "危险操作确认", { type: "warning", confirmButtonText: "确认取消", cancelButtonText: "取消" });
  } catch { return; }
  cancelingId.value = row.id;
  try {
    await cancelAppointment(row.id);
    ElMessage.success("取消挂号成功");
    showUndo("已取消挂号，可在5秒内撤销", { type: "appointment_cancel", row });
    await loadAppointments();
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "取消挂号失败"));
  } finally { cancelingId.value = null; }
}

function showUndo(title, payload) {
  if (undoTimer) window.clearTimeout(undoTimer);
  undoBar.value = { visible: true, title, payload };
  undoTimer = window.setTimeout(() => { undoBar.value.visible = false; }, 5000);
}

async function undoAction() {
  const payload = undoBar.value.payload;
  if (!payload) return;
  if (payload.type === "appointment_cancel") {
    try {
      await createAppointment({ pet_id: payload.row.pet_id, doctor_id: payload.row.doctor_id, clinic_id: payload.row.clinic_id, scheduled_time: payload.row.scheduled_time, urgency_level: payload.row.urgency_level });
      ElMessage.success("撤销成功，挂号已恢复");
      await loadAppointments();
    } catch (error) { ElMessage.error(getErrorMessage(error, "撤销失败")); }
  }
  undoBar.value.visible = false;
}

async function loadPets() {
  try { const result = await fetchPets(); petOptions.value = result.data || []; } catch (error) { ElMessage.error(getErrorMessage(error, "宠物列表加载失败")); }
}

async function loadDoctors() {
  try {
    const [doctorResult, appointmentResult] = await Promise.all([
      fetchDoctors(form.value.clinic_id),
      fetchAppointments({ clinicId: form.value.clinic_id, limit: 60, offset: 0 })
    ]);
    clinicAppointments.value = appointmentResult.data || [];
    const slotKey = (form.value.scheduled_time || "").slice(0, 16);
    const occupiedDoctorIds = new Set(
      (appointmentResult.data || [])
        .filter((item) => (item.scheduled_time || "").slice(0, 16) === slotKey)
        .filter((item) => item.status !== "已取消" && item.status !== "排班" && !item.is_leave)
        .map((item) => item.doctor_id)
    );
    const doctorLoadMap = new Map();
    (appointmentResult.data || []).forEach((item) => {
      if (!["待诊", "就诊中"].includes(item.status)) return;
      doctorLoadMap.set(item.doctor_id, (doctorLoadMap.get(item.doctor_id) || 0) + 1);
    });
    doctorOptions.value = (doctorResult.data || []).map((item) => {
      const loadCount = doctorLoadMap.get(item.id) || 0;
      const disabled = Boolean(slotKey) && occupiedDoctorIds.has(item.id);
      return { ...item, loadCount, disabled, disabledReason: disabled ? "该时段已满" : "" };
    }).sort((a, b) => a.loadCount - b.loadCount || a.id - b.id);
    if (form.value.doctor_id && doctorOptions.value.some((item) => item.id === form.value.doctor_id && item.disabled)) {
      form.value.doctor_id = null;
      ElMessage.warning("已选择医生在该时段不可用，请重新选择");
    }
  } catch (error) { ElMessage.error(getErrorMessage(error, "医生列表加载失败")); }
}

function isCellSelected(cell) { return form.value.doctor_id === cell.doctorId && (form.value.scheduled_time || "").slice(0, 19) === cell.scheduledTime; }

function chooseSlot(cell) {
  if (cell.occupied) { ElMessage.warning("该时段已满，请选择其他时段"); return; }
  form.value.doctor_id = cell.doctorId;
  form.value.scheduled_time = cell.scheduledTime;
}

function applyRecommendedSlot() {
  if (!bestAvailableCell.value) { ElMessage.warning("暂无可预约时段"); return; }
  chooseSlot(bestAvailableCell.value);
  ElMessage.success("已自动填入推荐时段");
}

async function openCreateDialog() {
  let draft = null;
  try { const saved = window.localStorage.getItem(STORAGE_FORM_KEY); if (saved) { draft = JSON.parse(saved); } } catch { draft = null; }
  form.value = draft || { pet_id: null, doctor_id: null, clinic_id: "C001", scheduled_time: "", urgency_level: "常规" };
  await Promise.all([loadPets(), loadDoctors()]);
  appointmentStep.value = 0;
  dialogVisible.value = true;
}

async function submit() {
  if (!formRef.value) return;
  await formRef.value.validate();
  submitLoading.value = true;
  try {
    await createAppointment(form.value);
    if (form.value.urgency_level === "急诊" || Number(form.value.priority_score || 0) > Number(appointments.value?.[0]?.priority_score || 0)) {
      flashingId.value = -1;
      window.setTimeout(() => { flashingId.value = 0; }, 3000);
    }
    ElMessage.success("预约挂号创建成功");
    dialogVisible.value = false;
    resetDirty();
    window.localStorage.removeItem(STORAGE_FORM_KEY);
    await loadAppointments();
  } catch (error) { ElMessage.error(getErrorMessage(error, "预约挂号创建失败")); } finally { submitLoading.value = false; }
}

window.addEventListener("beforeunload", (event) => { if (dirty.value) { event.preventDefault(); event.returnValue = ""; }});
onBeforeRouteLeave(async (_to, _from, next) => {
  if (!dirty.value) { next(); return; }
  try { await ElMessageBox.confirm("当前有未保存内容，确定离开吗？", "离开确认", { type: "warning", confirmButtonText: "离开", cancelButtonText: "取消" }); next(); } catch { next(false); }
});
onMounted(async () => {
  try { const savedFilters = window.localStorage.getItem(STORAGE_FILTER_KEY); if (savedFilters) { filters.value = { ...filters.value, ...JSON.parse(savedFilters) }; } } catch {}
  await loadAppointments();
  scoreTimer = window.setInterval(() => {
    appointments.value = recomputePriorityRuntime(appointments.value);
  }, 60000);
});
onUnmounted(() => {
  if (scoreTimer) window.clearInterval(scoreTimer);
});
defineExpose({ getStatusTagType });

function queueRowClass({ row }) {
  if (row.urgency_level === "急诊") return "emergency-row";
  if (flashingId.value === -1 && row === appointments.value[0]) return "queue-flash";
  return "";
}
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
  --danger: #EF4444;
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
   玻璃态主卡片
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
.page-title { font-size: 22px; font-weight: 800; color: var(--text-main); letter-spacing: 0.5px; }

/* ====================================================
   按钮状态覆盖机制 (防御 disabled 导致光学隐形)
   ==================================================== */
.agile-btn {
  border-radius: 100px !important;
  height: 40px !important;
  font-weight: 800 !important;
  padding: 0 20px !important;
  transition: all 0.3s var(--spring) !important;
  border: none !important;
}

/* Primary 按钮逻辑强制阻断 */
.btn-primary {
  background-color: #3B82F6 !important; 
  color: #FFFFFF !important;
  box-shadow: 0 4px 10px rgba(59, 130, 246, 0.3) !important;
}
.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px) scale(1.02) !important;
  box-shadow: 0 6px 14px rgba(59, 130, 246, 0.4) !important;
  background-color: #2563EB !important;
}
.btn-primary:disabled {
  background-color: #E2E8F0 !important;
  color: #94A3B8 !important;
  box-shadow: none !important;
  cursor: not-allowed !important;
}

/* Success 按钮逻辑强制阻断 */
.btn-success { 
  background-color: #10B981 !important; 
  color: #FFFFFF !important; 
  box-shadow: 0 4px 10px rgba(16, 185, 129, 0.3) !important; 
}
.btn-success:hover:not(:disabled) { 
  transform: translateY(-2px) scale(1.02) !important; 
  background-color: #059669 !important;
}
.btn-success:disabled {
  background-color: #E2E8F0 !important;
  color: #94A3B8 !important;
  box-shadow: none !important;
  cursor: not-allowed !important;
}

/* Ghost 按钮逻辑强制阻断 */
.btn-ghost {
  background-color: #FFFFFF !important; 
  color: #64748B !important;
  border: 2px solid #E2E8F0 !important; 
  box-shadow: 0 2px 4px rgba(0,0,0,0.02) !important;
}
.btn-ghost:hover:not(:disabled) {
  border-color: #CBD5E1 !important; 
  color: #1E293B !important; 
  transform: translateY(-2px) !important;
}
.btn-ghost:disabled {
  background-color: #F8FAFC !important;
  color: #CBD5E1 !important;
  border-color: #F1F5F9 !important;
  box-shadow: none !important;
  cursor: not-allowed !important;
}

.agile-btn-small { border-radius: 8px !important; font-weight: 700 !important; transition: all 0.2s var(--spring) !important; }
.btn-copy { background-color: #F1F5F9 !important; color: #475569 !important; border: none !important; }
.btn-copy:hover { background-color: #E2E8F0 !important; transform: scale(1.05) !important; }
.btn-danger { background-color: #FEF2F2 !important; color: #DC2626 !important; border: none !important; }
.btn-danger:hover:not(:disabled) { background-color: #DC2626 !important; color: #FFF !important; transform: scale(1.05) !important; }

/* ====================================================
   深度定制下拉与输入框
   ==================================================== */
:deep(.agile-input .el-input__wrapper), :deep(.agile-select .el-input__wrapper) {
  border-radius: 12px !important; background-color: #F8FAFC; box-shadow: 0 0 0 1px #E2E8F0 inset !important; transition: all 0.3s var(--spring) !important;
}
:deep(.agile-input .el-input__wrapper.is-focus), :deep(.agile-select .el-input__wrapper.is-focus) {
  background-color: #FFFFFF; box-shadow: 0 0 0 2px var(--primary) inset, 0 4px 12px rgba(59, 130, 246, 0.1) !important;
}
.fluid-select { width: 100%; }

/* ====================================================
   数据表格
   ==================================================== */
:deep(.cute-table) {
  border-radius: 16px; overflow: hidden; border: 1px solid #F1F5F9;
  --el-table-border-color: #F1F5F9;
}
:deep(.cute-table .el-table__row) { transition: background-color 0.3s var(--smooth); }
:deep(.cute-table .el-table__row:hover > td) { background-color: #F8FAFC !important; }
:deep(.el-table .emergency-row > td) {
  background: linear-gradient(90deg, rgba(239,68,68,.18), rgba(239,68,68,.08)) !important;
  font-weight: 800;
}
:deep(.el-table .queue-flash > td) {
  animation: queueFlash 0.7s ease-in-out 4;
}
@keyframes queueFlash {
  0% { background-color: rgba(239,68,68,.05); }
  50% { background-color: rgba(239,68,68,.3); }
  100% { background-color: rgba(239,68,68,.05); }
}

.code-cell { display: grid; grid-template-columns: 1fr auto; gap: 8px; align-items: center; }
:deep(.code-input .el-input__wrapper) { border-radius: 8px !important; box-shadow: none !important; background: transparent; padding: 0; }
:deep(.code-input .el-input__inner) { font-family: monospace; font-size: 13px; color: #64748B; }

.clinic-tag { font-weight: 800; }
.time-text { font-weight: 600; color: #475569; }
.score-text { font-weight: 800; color: #8B5CF6; background: #F5F3FF; padding: 2px 8px; border-radius: 8px; }
.score-info { margin-left: 6px; cursor: help; color: #64748B; }

.urgency-tag { font-weight: 800; border: none !important; padding: 0 12px; }
.urgency-danger { background-color: #FEF2F2 !important; color: #DC2626 !important; }
.urgency-warning { background-color: #FFFBEB !important; color: #D97706 !important; }
.urgency-normal { background-color: #F1F5F9 !important; color: #475569 !important; }
.status-tag { font-weight: 700; padding: 0 12px; }

.list-meta { margin-top: 16px; color: #94A3B8; font-size: 13px; font-weight: 600; text-align: right; }
.meta-highlight { color: var(--primary); font-weight: 800; font-size: 15px; }

/* ====================================================
   弹窗与排班矩阵交互
   ==================================================== */
:deep(.glass-dialog) { border-radius: 24px; overflow: hidden; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25); }
:deep(.glass-dialog .el-dialog__header) { background-color: #F8FAFC; margin-right: 0; padding: 20px 24px; border-bottom: 1px solid #F1F5F9; font-weight: 800; }
:deep(.glass-dialog .el-dialog__title) { font-weight: 800; font-size: 18px; color: var(--text-main); }
.dialog-footer { display: flex; justify-content: flex-end; gap: 12px; padding: 10px 0; }

.modern-form { padding: 10px 0; }
:deep(.el-form-item__label) { font-weight: 800; color: var(--text-main); }

.label-help { display: inline-flex; align-items: center; gap: 6px; }
.help-icon { width: 16px; height: 16px; border-radius: 50%; background-color: #CBD5E1; color: #fff; display: inline-flex; align-items: center; justify-content: center; font-size: 12px; cursor: pointer; transition: background 0.2s; }
.help-icon:hover { background-color: var(--primary); }

.doctor-option { display: inline-block; width: 100%; font-weight: 700; }
.doc-id { color: #94A3B8; font-size: 12px; margin-left: 4px; }
.doctor-option-disabled { color: #CBD5E1; }
.doc-warning-text { font-size: 12px; color: #F59E0B; margin-top: 6px; font-weight: 700; }

/* 排班矩阵 */
.slot-matrix-card { background-color: #F8FAFC; border-radius: 16px; padding: 16px; border: 1px solid #E2E8F0; }
.slot-matrix { width: 100%; display: grid; grid-template-columns: 80px repeat(auto-fit, minmax(90px, 1fr)); gap: 8px; align-items: center; }
.slot-header { font-weight: 800; font-size: 13px; text-align: center; color: #475569; padding-bottom: 8px; }
.time-header { color: #94A3B8; }
.slot-time { text-align: center; color: #64748B; font-size: 13px; font-weight: 700; }

.slot-cell {
  text-align: center; border-radius: 10px; font-size: 13px; font-weight: 800; line-height: 32px; height: 32px;
  cursor: pointer; transition: all 0.3s var(--spring);
  background-color: #ECFDF5; color: #10B981; border: 2px solid transparent;
}
.slot-cell:not(.occupied):hover { transform: scale(1.08) translateY(-2px); box-shadow: 0 4px 10px rgba(16, 185, 129, 0.2); border-color: #34D399; }
.slot-cell.occupied { background-color: #FEF2F2; color: #FCA5A5; cursor: not-allowed; }
.slot-cell.selected { background-color: var(--primary); color: #FFF; transform: scale(1.05); box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4); }

.recommend-box { display: flex; justify-content: space-between; align-items: center; background-color: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 12px; padding: 12px 16px; width: 100%; }
.rec-text { color: #1E40AF; font-size: 13px; }

/* 步骤条 */
:deep(.cute-steps .el-step__head.is-success) { color: var(--primary); border-color: var(--primary); }
:deep(.cute-steps .el-step__title.is-success) { color: var(--primary); font-weight: 800; }
:deep(.cute-steps .el-step__title.is-process) { font-weight: 800; color: var(--text-main); }

/* 单选框与急诊呼吸特效 */
:deep(.cute-radio-group .el-radio.is-bordered) { border-radius: 10px; transition: all 0.2s var(--smooth); }
:deep(.cute-radio-group .el-radio.is-bordered.is-checked) { border-color: var(--primary); background-color: #EFF6FF; }
:deep(.cute-radio-group .el-radio__input.is-checked .el-radio__inner) { background-color: var(--primary); border-color: var(--primary); }

.urgent-radio :deep(.el-radio__label) { color: #EF4444; font-weight: 800; }
@keyframes pulse-border {
  0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); border-color: #EF4444; }
  70% { box-shadow: 0 0 0 8px rgba(239, 68, 68, 0); border-color: #FCA5A5; }
  100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); border-color: #EF4444; }
}
.emergency-pulse { background-color: #FEF2F2; padding: 16px; border-radius: 16px; animation: pulse-border 2s infinite; border: 2px solid #EF4444; margin: -16px; width: calc(100% + 32px); }

/* 缴费凭证预览 */
.confirm-ticket { background-color: #FFFBEB; border: 2px dashed #FCD34D; border-radius: 16px; padding: 20px; position: relative; overflow: hidden; margin-top: 10px; }
.confirm-ticket::before, .confirm-ticket::after { content: ''; position: absolute; top: 50%; width: 20px; height: 20px; background-color: var(--surface); border-radius: 50%; transform: translateY(-50%); border: 2px solid #FCD34D; }
.confirm-ticket::before { left: -12px; border-left-color: transparent; border-top-color: transparent; border-bottom-color: transparent; }
.confirm-ticket::after { right: -12px; border-right-color: transparent; border-top-color: transparent; border-bottom-color: transparent; }
.ticket-header { text-align: center; font-size: 16px; font-weight: 800; color: #D97706; margin-bottom: 16px; border-bottom: 2px dashed #FDE68A; padding-bottom: 12px; }
.ticket-row { display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 14px; color: #92400E; }
.ticket-row span { color: #B45309; }

/* 动画与撤销条 */
.undo-bar { position: fixed; left: 50%; transform: translateX(-50%); bottom: 24px; width: auto; min-width: 400px; z-index: 3000; border-radius: 16px !important; box-shadow: 0 10px 25px rgba(245, 158, 11, 0.3) !important; font-weight: 800 !important; }

.fade-slide-enter-active, .fade-slide-leave-active { transition: all 0.3s var(--spring); }
.fade-slide-enter-from { opacity: 0; transform: translateX(20px); }
.fade-slide-leave-to { opacity: 0; transform: translateX(-20px); }
.slide-up-enter-active, .slide-up-leave-active { transition: all 0.4s var(--spring); }
.slide-up-enter-from, .slide-up-leave-to { opacity: 0; transform: translate(-50%, 40px); }
.bounce-enter-active { animation: bounce-in 0.5s var(--spring); }
@keyframes bounce-in { 0% { transform: scale(0.8); opacity: 0; } 100% { transform: scale(1); opacity: 1; } }
.slide-fade-enter-active { transition: all 0.3s ease-out; }
.slide-fade-enter-from { transform: translateY(-10px); opacity: 0; }
</style>
