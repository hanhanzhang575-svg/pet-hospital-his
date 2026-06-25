<template>
  <div class="app-layout pet-theme">
    <div class="bg-watermark" />
    <!-- 顶部导航栏 -->
    <el-header class="header">
      <div class="header-content">
        <h1 class="logo">🐾 白之助宠物医院 IS</h1>
        <div class="header-center" v-if="authStore.isLoggedIn">
          <el-button text @click="router.push('/home')">工作台</el-button>
            <el-tooltip
              :content="wsState === 'connected' ? '实时推送在线' : '实时推送暂时不可用'"
              placement="bottom"
            >
              <div class="ws-micro-indicator" role="status" aria-live="polite">
                <span v-if="wsState === 'connected'" class="ws-green-icon">🟢</span>
                <span v-else class="ws-cloud">☁️</span>
              </div>
            </el-tooltip>
        </div>
        <el-space>
          <el-popover v-if="authStore.isLoggedIn" placement="bottom-end" :width="340" trigger="click">
            <template #reference>
              <el-badge :value="unreadCount" :hidden="unreadCount === 0">
                <el-button circle><el-icon><Bell /></el-icon></el-button>
              </el-badge>
            </template>
            <el-empty v-if="messages.length === 0" description="暂无消息" />
            <div v-else class="msg-list">
              <div v-for="item in messages" :key="item.id" class="msg-item">
                <div class="msg-title">
                  <span class="msg-level-icon">{{ levelIcon(item.level) }}</span>
                  <span>{{ item.title }}</span>
                </div>
                <div class="msg-content">{{ item.content || "点击查看详情" }}</div>
                <div class="msg-actions">
                  <span class="msg-time">{{ relativeTime(item.createdAt) }}</span>
                  <el-tag size="small" :type="item.read ? 'info' : 'danger'">{{ item.read ? "已读" : "未读" }}</el-tag>
                  <el-button
                    v-if="resolveMessageRoute(item)"
                    link
                    type="primary"
                    size="small"
                    @click="jumpByMessage(item)"
                  >
                    查看并跳转
                  </el-button>
                </div>
              </div>
              <div class="msg-footer">
                <el-button text size="small" @click="markAllRead">标记全部已读</el-button>
              </div>
            </div>
          </el-popover>
          <el-tag v-if="authStore.role">{{ authStore.role }}</el-tag>
          <el-button v-if="authStore.isLoggedIn" size="small" @click="logout">退出</el-button>
        </el-space>
      </div>
    </el-header>

    <!-- 主内容区域 -->
    <div class="body">
      <Sidebar v-if="showSidebar" />
      <el-main class="main-content">
        <!-- 错误消息已改为消息中心集中接收，不再显示全局 banner，保持 UI 整洁 -->
        <router-view />
        <el-button class="manual-fab" type="primary" @click="manualVisible = true">系统手册</el-button>
        <div class="help-fab-wrap">
          <el-popover placement="top-start" :width="320" trigger="click">
            <template #reference>
              <el-button class="help-fab" circle type="info">
                <span style="font-weight:700">?</span>
              </el-button>
            </template>
            <div class="help-box">
              <div class="help-title">{{ help.title }}</div>
              <ol class="help-list">
                <li v-for="(step, idx) in help.steps" :key="idx">{{ step }}</li>
              </ol>
              <el-button size="small" @click="startGuide">重新新手引导</el-button>
            </div>
          </el-popover>
        </div>
      </el-main>
    </div>
    <el-dialog v-model="manualVisible" fullscreen class="manual-dialog" destroy-on-close>
      <template #header>
        <div class="manual-header">
          <h2>白之助系统使用手册与 SQL 数据字典</h2>
        </div>
      </template>
      <el-tabs>
        <el-tab-pane label="现实业务场景与岗位流程">
          <el-alert
            type="info"
            :closable="false"
            show-icon
            title="手册说明：本页同时提供“现实工作语境”与“系统操作路径”，便于培训和课堂汇报复用。"
            style="margin-bottom: 12px"
          />
          <el-collapse accordion>
            <el-collapse-item title="前台接诊员（现实叙事 + 系统流程）" name="receptionist">
              <p>
                <strong>现实场景：</strong>主人抱宠物到院后，前台首先确认既往档案、主诉和紧急程度，决定是否进入急诊通道，再完成挂号与费用预估。
              </p>
              <p>
                <strong>系统流程：</strong>客户档案 → 挂号管理 → 收费结算 → 回访任务。对应状态从“待诊”推进到“就诊中/已结算”。
              </p>
              <p>
                <strong>权限边界：</strong>可创建/更新档案与账单，不可修改医生诊断结论与处方药品明细。
              </p>
            </el-collapse-item>
            <el-collapse-item title="兽医（现实叙事 + 系统流程）" name="doctor">
              <p>
                <strong>现实场景：</strong>医生根据体征、检验结果和影像信息做综合判断，给出诊断与治疗计划；需要时发起住院申请并跟踪病情变化。
              </p>
              <p>
                <strong>系统流程：</strong>接诊工作区 → 电子病历 → AI 辅助诊断 → 处方开具/住院申请。处方提交后触发库存扣减与药房待发药队列。
              </p>
              <p>
                <strong>权限边界：</strong>可写诊断和治疗，不可直接调整财务台账、用户权限和审计日志。
              </p>
            </el-collapse-item>
            <el-collapse-item title="检验员（现实叙事 + 系统流程）" name="lab_tech">
              <p>
                <strong>现实场景：</strong>检验员按优先级接收样本，完成生化/血常规录入，发现危急值时第一时间回传医生并保留复核记录。
              </p>
              <p>
                <strong>系统流程：</strong>待检队列 → 检验工作台 → 报告库。报告提交后自动回写“异常数/危急数”并触发医生端通知。
              </p>
              <p>
                <strong>权限边界：</strong>可录入/修订检验结果，不可发起处方与财务结算。
              </p>
            </el-collapse-item>
            <el-collapse-item title="护理人员（现实叙事 + 系统流程）" name="nurse">
              <p>
                <strong>现实场景：</strong>住院期间按班次记录体温、心率、护理观察；误录数据需在限定窗口内撤回并写明原因，保证医疗追溯。
              </p>
              <p>
                <strong>系统流程：</strong>护理日志 → 体征录入 → 住院管理。体征异常会推送主治医生，体征记录支持 5 分钟内撤回。
              </p>
              <p>
                <strong>权限边界：</strong>可记录护理过程，不可修改他人历史护理记录与处方信息。
              </p>
            </el-collapse-item>
            <el-collapse-item title="管理员/主任（现实叙事 + 系统流程）" name="admin">
              <p>
                <strong>现实场景：</strong>管理员关注系统安全、审计追踪与配置维护；主任关注跨院区运营、人力调度、采购审批和异常事件闭环。
              </p>
              <p>
                <strong>系统流程：</strong>用户管理/权限配置/审计日志 + 运营看板/RFM/采购审批/排班管理/跨院区调度。
              </p>
              <p>
                <strong>权限边界：</strong>可治理流程与权限，不可替代医生篡改病历临床事实。
              </p>
            </el-collapse-item>
          </el-collapse>
        </el-tab-pane>
        <el-tab-pane label="系统流程地图（按状态推进）">
          <el-steps :active="4" align-center>
            <el-step title="接诊建档" description="owners/pets/appointments" />
            <el-step title="诊疗与检验" description="medical_records/lab_test_orders" />
            <el-step title="处方与住院" description="prescriptions/inpatient_records/nursing_logs" />
            <el-step title="结算与回访" description="invoices/followup_tasks/rfm" />
            <el-step title="运营治理" description="tasks/audit_logs/news" />
          </el-steps>
          <el-divider />
          <p>
            <strong>关键状态位：</strong>
            预约（待诊/就诊中/已完成）→ 检验（待检查/检查中/已完成）→ 住院（待入院/住院中/已出院）→ 回访（待处理/进行中/已预约复诊/无效）。
          </p>
        </el-tab-pane>
        <el-tab-pane label="底层数据字典（SQL）">
          <el-table :data="sqlDictRows" border>
            <el-table-column prop="table" label="表名" width="180" />
            <el-table-column prop="pk" label="主键(PK)" width="160" />
            <el-table-column prop="fk" label="外键(FK)" min-width="340" />
            <el-table-column prop="relation" label="关联逻辑" min-width="360" />
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import { Bell } from "@element-plus/icons-vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "./store";
import { useNotificationStore } from "./store/notification";
import Sidebar from "./components/layout/Sidebar.vue";
import { useWebSocket } from "./composables/useWebSocket";
import { useHelpCenter } from "./composables/useHelpCenter";

const router = useRouter();
const authStore = useAuthStore();
const notificationStore = useNotificationStore();
const { help } = useHelpCenter();
const { connect, disconnect, connectionState, clearUnread } = useWebSocket();
const showSidebar = computed(() => authStore.isLoggedIn && !router.currentRoute.value.meta?.public);
const messages = computed(() => notificationStore.recentMessages);
const unreadCount = computed(() => notificationStore.unreadCount);
const wsState = computed(() => connectionState.value || "disconnected");
const manualVisible = ref(false);
const sqlDictRows = [
  { table: "users", pk: "id", fk: "role_id -> roles.id", relation: "用户归属角色，控制路由与接口权限" },
  { table: "owners", pk: "id", fk: "-", relation: "主人主表，连接 pets、invoices、adopters（可选）" },
  { table: "pets", pk: "id", fk: "owner_id -> owners.id", relation: "宠物归属主人，驱动就诊全链路" },
  { table: "appointments", pk: "id", fk: "pet_id -> pets.id, doctor_id -> users.id", relation: "预约连接宠物与医生" },
  { table: "visits", pk: "id", fk: "pet_id -> pets.id", relation: "历史就诊记录可追溯，支持知识图谱证据ID" },
  { table: "medical_records", pk: "id", fk: "appointment_id -> appointments.id", relation: "病历与预约一对一核心关联" },
  { table: "prescriptions", pk: "id", fk: "medical_record_id -> medical_records.id", relation: "处方来源于病历" },
  { table: "inpatient_records", pk: "id", fk: "pet_id -> pets.id, cage_id -> cage_units.id", relation: "住院宠物与笼舍绑定" },
  { table: "nursing_logs", pk: "id", fk: "inpatient_record_id -> inpatient_records.id, nurse_id -> users.id", relation: "体征记录支持撤回窗口与审计追溯" },
  { table: "lab_test_orders", pk: "id", fk: "appointment_id -> appointments.id, doctor_id -> users.id", relation: "检验单关联门诊并回写报告" },
  { table: "followup_tasks", pk: "id", fk: "owner_id -> owners.id", relation: "RFM 触发回访任务并在看板流转" },
  { table: "purchase_tasks", pk: "id", fk: "drug_id -> drugs.id", relation: "库存阈值触发采购审批流程" },
  { table: "referral_records", pk: "id", fk: "pet_id -> pets.id, target_cage_id -> cage_units.id", relation: "跨院区转诊闭环记录" }
];

function formatTime(value) {
  if (!value) return "刚刚";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "刚刚";
  return `${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
}

function relativeTime(value) {
  if (!value) return "刚刚";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "刚刚";
  const diff = Date.now() - date.getTime();
  if (diff < 60000) return "刚刚";
  const minutes = Math.floor(diff / 60000);
  if (minutes < 60) return `${minutes}分钟前`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}小时前`;
  const days = Math.floor(hours / 24);
  return `${days}天前`;
}

function levelIcon(level) {
  if (level === "warning") return "⚠️";
  if (level === "error") return "🚨";
  return "🔔";
}

function markAllRead() {
  notificationStore.markAllRead();
  clearUnread();
}

function resolveMessageRoute(item) {
  const title = String(item?.title || "");
  const mapping = [
    { keys: ["新患者", "排班变动", "体征异常", "AI预警"], route: "/vet-workbench", roles: ["doctor"] },
    { keys: ["新处方"], route: "/pharmacy", roles: ["pharmacist", "pharmacy"] },
    { keys: ["新护理任务"], route: "/inpatient", roles: ["nurse"] },
    { keys: ["欠费预警"], route: "/finance-ledger", roles: ["manager"] },
    { keys: ["库存预警"], route: "/purchase-approvals", roles: ["manager"] },
    { keys: ["库存预警"], route: "/inventory", roles: ["pharmacist", "pharmacy"] },
    { keys: ["处方失效提醒"], route: "/billing-settlement", roles: ["receptionist"] },
    { keys: ["结算完成"], route: "/finance-ledger", roles: ["manager"] }
  ];
  const target = mapping.find((x) => x.keys.some((k) => title.includes(k)) && authStore.hasRole(x.roles));
  if (!target) return "";
  return target.route;
}

function jumpByMessage(item) {
  const route = resolveMessageRoute(item);
  if (!route) return;
  router.push(route);
}

function logout() {
  disconnect();
  authStore.logout();
  ElMessage.success("已退出登录");
  router.push("/login");
}

function startGuide() {
  window.sessionStorage.removeItem("onboarded_role");
  ElMessage.success("已重置引导，下次进入工作台会自动展示");
}

onMounted(async () => {
  if (authStore.token && !authStore.profile) {
    try {
      await authStore.loadProfile();
    } catch {
      authStore.logout();
    }
  }
  if (authStore.isLoggedIn) {
    connect();
    const onboardKey = `onboarded_${authStore.role || "unknown"}`;
    if (!window.sessionStorage.getItem(onboardKey)) {
      ElMessage({
        type: "info",
        message: "欢迎使用！请先查看右下角 ? 操作指引，可随时重新触发。",
        duration: 3000
      });
      window.sessionStorage.setItem(onboardKey, "1");
    }
  }
});
</script>

<style scoped>
.app-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background:
    linear-gradient(180deg, #f8fafc 0%, #eef6f5 46%, #f6f8fb 100%);
  position: relative;
}

.pet-theme {
  --el-color-primary: #42b983;
  --el-color-primary-light-3: #74cea3;
  --el-color-primary-light-5: #96dcc1;
  --el-color-primary-light-7: #b7e9d8;
}

.bg-watermark {
  position: fixed;
  inset: 0;
  background:
    linear-gradient(120deg, rgba(16, 185, 129, 0.06), rgba(59, 130, 246, 0.035) 46%, rgba(245, 158, 11, 0.035)),
    repeating-linear-gradient(135deg, rgba(15, 23, 42, 0.018) 0 1px, transparent 1px 18px);
  pointer-events: none;
  z-index: 0;
}

.header {
  height: 60px;
  background-color: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(16px);
  border-bottom: 1px solid rgba(203, 213, 225, 0.72);
  box-shadow: 0 14px 34px -30px rgba(15, 23, 42, 0.55);
  padding: 0 20px;
  display: flex;
  align-items: center;
  z-index: 8;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.header-center {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
}

.logo {
  margin: 0;
  font-size: 20px;
  line-height: 1;
  font-weight: 800;
  color: #0f766e;
  letter-spacing: 0;
  white-space: nowrap;
}

.body {
  display: flex;
  min-height: calc(100vh - 60px);
  position: relative;
  z-index: 1;
}

.main-content {
  flex: 1;
  padding: 16px;
  min-width: 0;
  max-width: calc(100vw - 236px);
}

.global-error-banner {
  width: 100%;
  margin-bottom: 10px;
}

.ws-micro-indicator {
  margin-left: 10px;
  width: 24px;
  height: 24px;
  border-radius: 999px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.ws-green-icon {
  font-size: 13px;
}

.ws-cloud {
  font-size: 14px;
  color: #94a3b8;
  animation: cloudPulse 1.2s ease-in-out infinite;
}

@keyframes cloudPulse {
  0% {
    opacity: 0.4;
    transform: translateY(0);
  }
  50% {
    opacity: 1;
    transform: translateY(-1px);
  }
  100% {
    opacity: 0.4;
    transform: translateY(0);
  }
}

.msg-list { display: grid; gap: 8px; max-height: 360px; overflow-y: auto; padding-right: 6px; }
.msg-item {
  border: 1px solid #edf2f7;
  background: #fbfdff;
  border-radius: 8px;
  padding: 10px;
}
.msg-title { font-size: 13px; font-weight: 700; color: #1e293b; }
.msg-level-icon { margin-right: 6px; }
.msg-content { font-size: 12px; color: #606266; margin-top: 4px; }
.msg-actions { display: flex; align-items: center; justify-content: space-between; margin-top: 4px; }
.msg-time { font-size: 12px; color: #909399; }
.msg-footer { display: flex; justify-content: flex-end; margin-top: 8px; }
.help-fab-wrap {
  position: fixed;
  right: 24px;
  bottom: 24px;
  z-index: 3100;
}
.manual-fab {
  position: fixed;
  right: 24px;
  bottom: 82px;
  z-index: 3100;
  border-radius: 999px;
  box-shadow: 0 16px 36px -24px rgba(15, 23, 42, 0.58);
}
.manual-header h2 {
  margin: 0;
}
.help-fab {
  box-shadow: 0 16px 36px -24px rgba(15, 23, 42, 0.58);
}
.help-title { font-weight: 700; margin-bottom: 8px; }
.help-list { margin: 0 0 8px 16px; padding: 0; }

.manual-dialog :deep(.el-dialog__body) {
  max-height: calc(100vh - 96px);
  overflow: auto;
}

.manual-dialog :deep(.el-table__body-wrapper) {
  max-height: 420px;
  overflow-y: auto;
}

:deep(.el-card) {
  background: rgba(255, 255, 255, 0.94);
}

@media (max-width: 900px) {
  .body {
    flex-direction: column;
  }

  .main-content {
    max-width: 100vw;
    padding: 12px;
  }

  .manual-fab {
    right: 16px;
    bottom: 76px;
  }

  .help-fab-wrap {
    right: 16px;
    bottom: 18px;
  }
}

@media (max-width: 640px) {
  .header {
    padding: 0 12px;
  }

  .header-content {
    gap: 8px;
  }

  .logo {
    flex: 1 1 auto;
    min-width: 0;
    font-size: 16px;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .header-center {
    display: none;
  }

  .header-content :deep(.el-space) {
    flex: 0 0 auto;
    gap: 6px !important;
  }

  .header-content :deep(.el-tag) {
    max-width: 72px;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .header-content :deep(.el-button) {
    padding: 6px 8px;
  }
}
</style>

