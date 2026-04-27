<template>
  <div class="page">
    <el-card v-if="!isLoggedIn" class="login-card">
      <template #header>
        <span>兽医登录</span>
      </template>
      <el-form ref="loginFormRef" :model="loginForm" :rules="loginRules" label-width="90px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="loginForm.username" placeholder="张医生" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="loginForm.password" type="password" show-password placeholder="doc123" />
        </el-form-item>
      </el-form>
      <el-space>
        <el-button class="agile-btn" type="primary" :loading="loginLoading" :disabled="loginLoading" @click="loginAndLoad">登录并加载队列</el-button>
        <el-text type="info">演示账号：张医生 / doc123</el-text>
      </el-space>
    </el-card>

    <el-card class="glass-card">
      <template #header>
        <div class="header-row">
          <span>兽医工作台</span>
          <el-space class="status-strip" :wrap="false">
            <el-tag size="small" :type="aiListening ? 'success' : 'info'">
              {{ aiListening ? "🟢 AI质检·监听中" : "⚪ AI质检·已停止" }}
            </el-tag>
            <el-tooltip
              content="触发条件：仅在诊单状态=就诊中、病历已填写确诊结论、且已上传生化检验结果时，在病历提交环节触发校验。"
              placement="bottom"
            >
              <el-text type="info" class="hint-icon">ℹ️</el-text>
            </el-tooltip>
            <el-tag size="small" type="success">{{ doctorDisplay }}</el-tag>
            <el-button class="agile-btn" @click="logout" :disabled="queueLoading || loginLoading">退出登录</el-button>
            <el-button class="agile-btn" type="primary" :loading="queueLoading" :disabled="queueLoading" @click="loadQueue">刷新待诊队列</el-button>
          </el-space>
        </div>
      </template>
      <el-card class="glass-card ai-entry-banner" shadow="never" @click="router.push('/ai-diagnosis')">
        <div class="ai-entry-title">✨ AI 辅助诊断</div>
        <div class="ai-entry-sub">点击进入 AI 诊断页面，快速完成智能推理与图谱证据链校验</div>
      </el-card>
      <el-breadcrumb separator="/" style="margin-bottom: 10px">
        <el-breadcrumb-item @click="router.push('/home')">首页</el-breadcrumb-item>
        <el-breadcrumb-item>兽医工作台</el-breadcrumb-item>
      </el-breadcrumb>

      <el-skeleton :loading="queueLoading" :rows="5" animated>
        <template #default>
          <el-alert v-if="queueError" type="error" :title="queueError" show-icon :closable="false" style="margin-bottom: 12px">
            <template #default>
              <el-button size="small" @click="loadQueue">重试</el-button>
            </template>
          </el-alert>
            <el-empty v-if="queue.length === 0" description="今日暂无待诊患者">
              <el-button type="primary" @click="router.push('/appointments')">新建挂号</el-button>
            </el-empty>
            <el-table v-else :data="queue" border :row-class-name="queueRowClass">
            <el-table-column prop="record_code" label="诊单编号" min-width="190">
              <template #default="{ row }">
                <div class="code-cell">
                  <el-input :model-value="row.record_code" readonly />
                  <el-button size="small" @click="copyText(row.record_code)">复制</el-button>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="pet_name" label="宠物" min-width="180">
              <template #default="{ row }">
                <el-popover placement="right" :width="240" trigger="hover">
                  <template #reference>
                    <div class="pet-cell">
                      <el-text class="pet-link" @click.stop="openHistoryDialog(row)">{{ row.pet_name || `#${row.pet_id}` }}</el-text>
                      <el-tag
                        v-if="(row.allergy_history || []).length > 0"
                        type="danger"
                        effect="dark"
                        round
                        size="small"
                      >
                        有拉警报: 过敏史
                      </el-tag>
                    </div>
                  </template>
                  <div class="pet-pop">
                    <el-avatar shape="square" :size="56">宠物</el-avatar>
                    <div>
                      <div><strong>{{ row.pet_name || `宠物#${row.pet_id}` }}</strong></div>
                      <div>品种：{{ row.pet_breed || "-" }}</div>
                      <div>年龄：{{ getAgeText(row.pet_birth_date) }}</div>
                      <div>过敏史：{{ (row.allergy_history || []).join("、") || "-" }}</div>
                    </div>
                  </div>
                </el-popover>
              </template>
            </el-table-column>
            <el-table-column prop="urgency_level" label="紧急程度" width="110">
              <template #default="{ row }">
                <el-tag :type="row.urgency_level === '急诊' ? 'danger' : row.urgency_level === '优先' ? 'warning' : ''">
                  {{ row.urgency_level === "急诊" ? "🚨 急诊" : row.urgency_level === "优先" ? "⚡ 优先" : mapStatus(row.urgency_level) }}
                </el-tag>
                <div v-if="row.urgency_level === '急诊'" class="em-warn">⏱️ 等待超过10分钟未接诊将触发二次预警</div>
              </template>
            </el-table-column>
            <el-table-column label="优先级评分" min-width="280">
              <template #default="{ row }">
                <div class="priority-cell">
                  <div class="priority-header">
                    <el-text>{{ row.priority_score }}</el-text>
                    <el-progress :percentage="Math.min(100, Number(row.priority_score) || 0)" :stroke-width="8" />
                  </div>
                  <div class="priority-breakdown">
                    <el-tag size="small" effect="plain">严重度: {{ row.priority_breakdown?.urgency_score ?? "-" }}</el-tag>
                    <el-tag size="small" effect="plain">等待: {{ row.priority_breakdown?.waiting_score ?? "-" }}</el-tag>
                    <el-tag size="small" effect="plain">年龄: {{ row.priority_breakdown?.age_score ?? "-" }}</el-tag>
                  </div>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="110">
              <template #default="{ row }">
                <el-tag :type="getStatusTagType(row.status)">{{ mapStatus(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="320" align="right">
              <template #default="{ row }">
                <div class="action-cell">
                  <el-button
                    v-if="row.status === '待诊'"
                    class="action-btn action-btn-primary"
                    type="success"
                    :loading="startLoadingId === row.id"
                    :disabled="Boolean(startLoadingId)"
                    @click="startVisit(row)"
                  >
                    ▶ 开始接诊
                  </el-button>
                  <template v-else-if="row.status === '就诊中'">
                    <el-button class="action-btn" :disabled="Boolean(startLoadingId)" @click="openRecordDialog(row)">📝 录入/编辑病历</el-button>
                    <el-button class="action-btn" type="primary" :disabled="Boolean(startLoadingId)" @click="openPrescription(row)">💊 开具处方</el-button>
                  </template>
                  <el-button
                    v-else-if="row.status === '已完成'"
                    class="action-btn"
                    type="info"
                    :disabled="Boolean(startLoadingId)"
                    @click="openRecordReadOnly(row)"
                  >
                    👁 查看病历
                  </el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
          <div class="list-meta">
            共{{ queue.length }}条记录，最后更新时间 {{ lastUpdated || "--:--" }}
          </div>
        </template>
      </el-skeleton>
    </el-card>

    <el-dialog v-model="recordDialogVisible" :title="recordReadonly ? '查看病历' : '录入病历'" width="640px">
      <el-form ref="recordFormRef" :model="recordForm" :rules="recordRules" label-width="100px">
        <el-form-item label="预约ID" prop="appointment_id"><el-input v-model="recordForm.appointment_id" disabled /></el-form-item>
        <el-form-item label="宠物姓名"><el-input v-model="recordForm.pet_name" disabled /></el-form-item>
        <el-form-item label="医生姓名"><el-input :model-value="doctorDisplay" disabled /></el-form-item>
        <el-form-item label="主诉" prop="chief_complaint">
          <el-space direction="vertical" style="width:100%">
            <el-dropdown @command="applyChiefTemplate">
              <el-button size="small">加载快捷模板</el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="sterilization">常规绝育手术模板</el-dropdown-item>
                  <el-dropdown-item command="vaccine">基础疫苗接种模板</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
             <el-input v-model="recordForm.chief_complaint" :disabled="recordReadonly" type="textarea" />
          </el-space>
        </el-form-item>
        <el-form-item label="检查记录" prop="exam_notes"><el-input v-model="recordForm.exam_notes" :disabled="recordReadonly" type="textarea" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button :disabled="recordSubmitting" @click="recordDialogVisible = false">取消</el-button>
        <el-button v-if="!recordReadonly" type="primary" :loading="recordSubmitting" :disabled="recordSubmitting" @click="submitRecord">提交</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="historyDialogVisible" title="历史就诊记录时间轴" size="48%">
      <el-skeleton :loading="historyLoading" :rows="4" animated>
        <template #default>
          <el-alert
            v-if="historyPetName"
            :title="`当前宠物：${historyPetName}`"
            type="info"
            :closable="false"
            style="margin-bottom: 12px"
          />
          <el-timeline>
            <el-timeline-item
              v-for="item in medicalTimeline"
              :key="item.key"
              :timestamp="item.time"
              :type="item.type"
              placement="top"
            >
              <el-card>
                <div class="timeline-title">{{ item.title }}</div>
                <div class="timeline-desc">{{ item.description }}</div>
                <el-tag v-if="item.voided" type="info">已作废</el-tag>
              </el-card>
            </el-timeline-item>
          </el-timeline>
          <el-empty v-if="medicalTimeline.length === 0" description="暂无历史就诊记录" />
        </template>
      </el-skeleton>
    </el-drawer>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from "vue";
import { ElMessage } from "element-plus";
import { useRouter } from "vue-router";

import { createMedicalRecord, fetchMedicalRecords, fetchPendingQueue, startConsultation } from "../api/vetWorkbench";
import { loginWithPassword } from "../api/auth";
import { useAuthStore } from "../store";
import { useWebSocket } from "../composables/useWebSocket";
import { getErrorMessage, getStatusTagType } from "../utils/status";
import http from "../api/http";

const authStore = useAuthStore();
const { connect, disconnect } = useWebSocket();
const router = useRouter();
const doctorId = ref(null);
const queue = ref([]);
const lastUpdated = ref("");
const queueLoading = ref(false);
const queueError = ref("");
const loginLoading = ref(false);
const startLoadingId = ref(null);
const recordSubmitting = ref(false);
const recordReadonly = ref(false);
const isLoggedIn = ref(Boolean(authStore.token));
const loginFormRef = ref(null);
const recordFormRef = ref(null);
const loginForm = ref({
  username: "doctor",
  password: "doc123"
});
const aiListening = ref(true);
const flashTop = ref(false);
let timerId = null;
const recordDialogVisible = ref(false);
const historyDialogVisible = ref(false);
const historyLoading = ref(false);
const historyPetName = ref("");
const medicalTimeline = ref([]);
const recordForm = ref({
  appointment_id: 1,
  pet_id: 1,
  pet_name: "",
  vet_id: null,
  chief_complaint: "",
  exam_notes: ""
});

const loginRules = {
  username: [{ required: true, message: "请输入用户名", trigger: "blur" }],
  password: [{ required: true, message: "请输入密码", trigger: "blur" }]
};

const recordRules = {
  appointment_id: [{ required: true, message: "请填写预约ID", trigger: "blur" }],
  chief_complaint: [{ required: true, message: "请填写主诉", trigger: "blur" }]
};

const doctorDisplay = computed(() => {
  const name = authStore.displayName || "张医生";
  return `${name}（内科）`;
});

function logout() {
  if (timerId) {
    window.clearInterval(timerId);
    timerId = null;
  }
  disconnect();
  authStore.logout();
  isLoggedIn.value = false;
  doctorId.value = null;
  queue.value = [];
  ElMessage.success("已退出登录");
}

async function copyText(value) {
  try {
    await navigator.clipboard.writeText(value);
    ElMessage.success("已复制");
  } catch {
    ElMessage.warning("复制失败，请手动复制");
  }
}

async function loadCurrentUser() {
  const result = await http.get("/auth/me");
  doctorId.value = result.data.id;
}

async function loginAndLoad() {
  if (!loginFormRef.value) return;
  await loginFormRef.value.validate();
  loginLoading.value = true;
  try {
    const tokenResult = await loginWithPassword(loginForm.value.username, loginForm.value.password);
    authStore.setToken(tokenResult.access_token);
    await authStore.loadProfile();
    connect();
    isLoggedIn.value = true;
    await loadCurrentUser();
    await loadQueue();
    if (timerId) window.clearInterval(timerId);
    timerId = window.setInterval(async () => {
      await loadQueue();
    }, 30000);
    ElMessage.success("登录成功，已加载待诊队列");
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "登录失败"));
  } finally {
    loginLoading.value = false;
  }
}

async function loadQueue() {
  queueLoading.value = true;
  queueError.value = "";
  try {
    const result = await fetchPendingQueue();
    const baseQueue = enrichQueuePriority(result.data || []);
    queue.value = baseQueue;
    flashTop.value = true;
    window.setTimeout(() => { flashTop.value = false; }, 3000);
    lastUpdated.value = new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
  } catch (error) {
    const message = getErrorMessage(error, "待诊队列加载失败");
    queueError.value = message;
    ElMessage.error(message);
  } finally {
    queueLoading.value = false;
  }
}

function getAgeText(birthDate) {
  if (!birthDate) return "-";
  const birth = new Date(birthDate);
  if (Number.isNaN(birth.getTime())) return "-";
  const years = Math.max(0, Math.floor((Date.now() - birth.getTime()) / 31536000000));
  return `${years}岁`;
}

function mapStatus(status) {
  if (status === "待诊") return "🕐待诊";
  if (status === "就诊中") return "🩺就诊中";
  if (status === "已完成") return "✅已完成";
  if (status === "急诊") return "🚨急诊";
  return status;
}

function enrichQueuePriority(rawQueue) {
  return (rawQueue || []).map((item) => {
    const total = Number(item.priority_score) || 0;
    const urgencyScore = Math.round(total * 0.5);
    const waitingScore = Math.round(total * 0.3);
    const ageScore = Math.round(total * 0.2);
    return {
      ...item,
      priority_breakdown: {
        urgency_score: urgencyScore,
        waiting_score: waitingScore,
        age_score: ageScore
      }
    };
  }).sort((a, b) => {
    if (a.urgency_level === "急诊" && b.urgency_level !== "急诊") return -1;
    if (a.urgency_level !== "急诊" && b.urgency_level === "急诊") return 1;
    return (b.priority_score || 0) - (a.priority_score || 0);
  });
}

async function startVisit(row) {
  startLoadingId.value = row.id;
  try {
    await startConsultation(row.id);
    window.sessionStorage.setItem(
      "consultation_context",
      JSON.stringify({
        appointment_id: row.id,
        pet_id: row.pet_id,
        vet_id: doctorId.value
      })
    );
    ElMessage.success("已开始接诊");
    await router.push("/doctor-consultation");
    await loadQueue();
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "接诊失败"));
  } finally {
    startLoadingId.value = null;
  }
}

function openRecordDialog(row) {
  recordReadonly.value = false;
  recordForm.value = {
    appointment_id: row.id,
    pet_id: row.pet_id,
    pet_name: row.pet_name || `宠物#${row.pet_id}`,
    vet_id: doctorId.value,
    chief_complaint: "",
    exam_notes: ""
  };
  recordDialogVisible.value = true;
}

function openPrescription(row) {
  window.sessionStorage.setItem(
    "consultation_context",
    JSON.stringify({
      appointment_id: row.id,
      pet_id: row.pet_id,
      vet_id: doctorId.value
    })
  );
  router.push("/prescription-create");
}

async function openRecordReadOnly(row) {
  try {
    const result = await fetchMedicalRecords(row.pet_id);
    const latest = (result.data || []).find((x) => x.appointment_id === row.id) || (result.data || [])[0];
    recordReadonly.value = true;
    recordForm.value = {
      appointment_id: row.id,
      pet_id: row.pet_id,
      pet_name: row.pet_name || `宠物#${row.pet_id}`,
      vet_id: doctorId.value,
      chief_complaint: latest?.chief_complaint || "",
      exam_notes: latest?.exam_notes || ""
    };
    recordDialogVisible.value = true;
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "病历加载失败"));
  }
}

function applyChiefTemplate(command) {
  if (command === "sterilization") {
    recordForm.value.chief_complaint = "宠物拟行常规绝育手术，术前评估无明显禁忌。";
    return;
  }
  if (command === "vaccine") {
    recordForm.value.chief_complaint = "宠物进行基础疫苗接种，精神食欲正常，无发热。";
  }
}

async function submitRecord() {
  if (!recordFormRef.value) return;
  await recordFormRef.value.validate();
  recordSubmitting.value = true;
  try {
    const payload = {
      appointment_id: recordForm.value.appointment_id,
      pet_id: recordForm.value.pet_id,
      vet_id: recordForm.value.vet_id,
      chief_complaint: recordForm.value.chief_complaint,
      exam_notes: recordForm.value.exam_notes
    };
    await createMedicalRecord(payload);
    ElMessage.success("病历录入成功");
    recordDialogVisible.value = false;
    await loadQueue();
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "病历录入失败"));
  } finally {
    recordSubmitting.value = false;
  }
}

async function openHistoryDialog(row) {
  historyDialogVisible.value = true;
  historyLoading.value = true;
  historyPetName.value = row.pet_name || `宠物#${row.pet_id}`;
  try {
    const result = await fetchMedicalRecords(row.pet_id);
    const records = result.data || [];
    medicalTimeline.value = records.map((record) => ({
      key: `mr-${record.id}`,
      recordId: record.id,
      type: "primary",
      time: (record.created_at || "").replace("T", " ").slice(0, 19),
      title: `病历 ${record.record_no}`,
      description: `${record.chief_complaint || "无主诉"}；${record.exam_notes || "无检查记录"}`,
      voided: record.is_voided
    }));
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "病历时间轴加载失败"));
    medicalTimeline.value = [];
  } finally {
    historyLoading.value = false;
  }
}

onMounted(async () => {
  isLoggedIn.value = Boolean(authStore.token);
  if (!isLoggedIn.value) return;
  try {
    await loadCurrentUser();
    await loadQueue();
    timerId = window.setInterval(async () => {
      await loadQueue();
    }, 30000);
  } catch (error) {
    authStore.logout();
    isLoggedIn.value = false;
    ElMessage.warning(getErrorMessage(error, "登录已失效，请重新登录"));
  }
});

onUnmounted(() => {
  if (timerId) {
    window.clearInterval(timerId);
  }
});

function queueRowClass({ row, rowIndex }) {
  if (row.urgency_level === "急诊") return "emergency-row";
  if (flashTop.value && rowIndex === 0) return "queue-flash";
  return "";
}
</script>

<style scoped>
.page {
  padding: 16px;
}

.agile-btn {
  border-radius: 100px !important;
}

.ai-entry-banner {
  margin-bottom: 12px;
  border-radius: 20px;
  cursor: pointer;
}

.ai-entry-title {
  font-weight: 700;
}

.ai-entry-sub {
  font-size: 13px;
  color: #64748b;
  margin-top: 4px;
}

.login-card {
  margin-bottom: 16px;
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.status-strip {
  flex-wrap: nowrap;
}
.hint-icon {
  cursor: help;
}
.list-meta { margin-top: 10px; color: #909399; font-size: 12px; }

.code-cell {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 8px;
  align-items: center;
}

.priority-cell {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.priority-header {
  display: grid;
  grid-template-columns: 44px 1fr;
  gap: 8px;
  align-items: center;
}

.priority-breakdown {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.pet-cell {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.pet-link { cursor: pointer; }
.pet-link:hover { color: #3b82f6; text-decoration: underline; }

.pet-pop {
  display: grid;
  grid-template-columns: 56px 1fr;
  gap: 10px;
  align-items: center;
}

.timeline-title {
  font-weight: 600;
  margin-bottom: 6px;
}

.timeline-desc {
  color: #606266;
  margin-bottom: 8px;
}

.action-cell {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  align-items: center;
}

.action-btn {
  width: 132px;
  height: 32px;
}

.action-btn-primary {
  width: 160px;
}

.em-warn {
  margin-top: 4px;
  color: #ef4444;
  font-size: 12px;
}
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
</style>

