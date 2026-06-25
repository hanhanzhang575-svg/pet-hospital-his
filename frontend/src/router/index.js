import { createRouter, createWebHashHistory, createWebHistory } from "vue-router";
import { useAuthStore } from "../store";
import { getStaticDemoUser, isStaticDemoEnabled } from "../api/staticDemo";

const ArchiveView = () => import("../views/ArchiveView.vue");
const AppointmentsView = () => import("../views/AppointmentsView.vue");
const ForbiddenView = () => import("../views/ForbiddenView.vue");
const InpatientView = () => import("../views/InpatientView.vue");
const InventoryView = () => import("../views/InventoryView.vue");
const LoginView = () => import("../views/LoginView.vue");
const PharmacyView = () => import("../views/PharmacyView.vue");
const RfmBoardView = () => import("../views/RfmBoardView.vue");
const VetWorkbenchView = () => import("../views/VetWorkbenchView.vue");
const BillingSettlementView = () => import("../views/BillingSettlementView.vue");
const FollowupTasksView = () => import("../views/FollowupTasksView.vue");
const PrescriptionCreateView = () => import("../views/PrescriptionCreateView.vue");
const InpatientApplyView = () => import("../views/InpatientApplyView.vue");
const AIDiagnosisView = () => import("../views/AIDiagnosisView.vue");
const DoctorConsultationView = () => import("../views/DoctorConsultationView.vue");
const MedicalRecordDetailView = () => import("../views/MedicalRecordDetailView.vue");
const NursingLogsView = () => import("../views/NursingLogsView.vue");
const VitalsEntryView = () => import("../views/VitalsEntryView.vue");
const ScheduleManagementView = () => import("../views/ScheduleManagementView.vue");
const EoqVisualView = () => import("../views/EoqVisualView.vue");
const CrossClinicRecordsView = () => import("../views/CrossClinicRecordsView.vue");
const CageStatusView = () => import("../views/CageStatusView.vue");
const PurchaseRequestsView = () => import("../views/PurchaseRequestsView.vue");
const OpsBoardView = () => import("../views/OpsBoardView.vue");
const PurchaseApprovalsView = () => import("../views/PurchaseApprovalsView.vue");
const FinanceLedgerView = () => import("../views/FinanceLedgerView.vue");
const CrossClinicDispatchView = () => import("../views/CrossClinicDispatchView.vue");
const UserManagementView = () => import("../views/UserManagementView.vue");
const PermissionConfigView = () => import("../views/PermissionConfigView.vue");
const AuditLogsView = () => import("../views/AuditLogsView.vue");
const FederatedLearning = () => import("../views/FederatedLearning.vue");
const LabDashboardView = () => import("../views/LabDashboardView.vue");
const LabTestsView = () => import("../views/LabTestsView.vue");
const LabResultsView = () => import("../views/LabResultsView.vue");
const DataCenterView = () => import("../views/DataCenterView.vue");
const AdoptionHallView = () => import("../views/AdoptionHallView.vue");
const OwnerCenterView = () => import("../views/OwnerCenterView.vue");

const PROJECT_ENTRY_PATH = "/20231111085-管信2301张默涵";

const routes = [
  { path: "/", redirect: "/login" },
  { path: "/login", name: "login", component: LoginView, meta: { title: "登录", public: true } },
  {
    path: PROJECT_ENTRY_PATH,
    name: "project-entry",
    component: LoginView,
    meta: { title: "宠物医院信息系统 | 管信2301 张默涵", public: true }
  },
  { path: "/403", name: "forbidden", component: ForbiddenView, meta: { title: "无权限", public: true } },
  {
    path: "/home",
    name: "home",
    component: () => import("../views/HomeView.vue"),
    meta: { title: "工作台", roles: ["admin", "manager", "doctor", "receptionist", "nurse", "pharmacy", "pharmacist", "lab_tech"] }
  },
  { path: "/lab-dashboard", name: "lab-dashboard", component: LabDashboardView, meta: { title: "检验工作台", roles: ["lab_tech"] } },
  { path: "/lab-tests", name: "lab-tests", component: LabTestsView, meta: { title: "待检队列", roles: ["lab_tech"] } },
  { path: "/lab-results", name: "lab-results", component: LabResultsView, meta: { title: "报告库", roles: ["lab_tech"] } },

  { path: "/appointments", name: "appointments", component: AppointmentsView, meta: { title: "挂号管理", roles: ["receptionist"] } },
  { path: "/archives", name: "archives", component: ArchiveView, meta: { title: "客户档案", roles: ["receptionist"] } },
  { path: "/billing-settlement", name: "billing-settlement", component: BillingSettlementView, meta: { title: "收费结算", roles: ["receptionist"] } },
  { path: "/followup-tasks", name: "followup-tasks", component: FollowupTasksView, meta: { title: "回访任务", roles: ["receptionist"] } },
  { path: "/owner-center", name: "owner-center", component: OwnerCenterView, meta: { title: "主人运营", roles: ["manager"] } },
  { path: "/adoption-hall", name: "adoption-hall", component: AdoptionHallView, meta: { title: "领养匹配", roles: ["manager"] } },

  { path: "/vet-workbench", name: "vet-workbench", component: VetWorkbenchView, meta: { title: "医生工作台", roles: ["doctor"] } },
  { path: "/medical-records", name: "medical-records", component: CrossClinicRecordsView, meta: { title: "电子病历", roles: ["doctor"] } },
  { path: "/medical-record/:id", name: "medical-record-detail", component: MedicalRecordDetailView, meta: { title: "病历详情", roles: ["doctor"] } },
  { path: "/prescription-create", name: "prescription-create", component: PrescriptionCreateView, meta: { title: "处方开具", roles: ["doctor"] } },
  { path: "/inpatient-apply", name: "inpatient-apply", component: InpatientApplyView, meta: { title: "住院申请", roles: ["doctor"] } },
  { path: "/ai-diagnosis", name: "ai-diagnosis", component: AIDiagnosisView, meta: { title: "AI 辅助诊断", roles: ["doctor"] } },
  { path: "/doctor-consultation", name: "doctor-consultation", component: DoctorConsultationView, meta: { title: "接诊工作区", roles: ["doctor"] } },

  { path: "/inpatient", name: "inpatient", component: InpatientView, meta: { title: "住院管理", roles: ["nurse"] } },
  { path: "/cage-status", name: "cage-status", component: CageStatusView, meta: { title: "笼舍状态", roles: ["nurse"] } },
  { path: "/nursing-logs", name: "nursing-logs", component: NursingLogsView, meta: { title: "护理日志", roles: ["nurse"] } },
  { path: "/vitals-entry", name: "vitals-entry", component: VitalsEntryView, meta: { title: "体征录入", roles: ["nurse"] } },

  { path: "/pharmacy", name: "pharmacy", component: PharmacyView, meta: { title: "药房发药", roles: ["pharmacist", "pharmacy"] } },
  { path: "/inventory", name: "inventory", component: InventoryView, meta: { title: "库存管理", roles: ["pharmacist", "pharmacy"] } },
  { path: "/inventory-eoq", name: "inventory-eoq", component: EoqVisualView, meta: { title: "EOQ 补货建议", roles: ["pharmacist", "pharmacy"] } },
  { path: "/pharmacy-eoq-suggestions", redirect: "/inventory-eoq", meta: { title: "EOQ 补货建议", roles: ["pharmacist", "pharmacy"] } },
  { path: "/purchase-requests", name: "purchase-requests", component: PurchaseRequestsView, meta: { title: "采购申请", roles: ["pharmacist", "pharmacy"] } },

  { path: "/ops-board", name: "ops-board", component: OpsBoardView, meta: { title: "运营看板", roles: ["manager"] } },
  { path: "/rfm-board", name: "rfm-board", component: RfmBoardView, meta: { title: "RFM 看板", roles: ["manager"] } },
  { path: "/purchase-approvals", name: "purchase-approvals", component: PurchaseApprovalsView, meta: { title: "采购审批", roles: ["manager"] } },
  {
    path: "/admin/schedule-manage",
    name: "admin-schedule-manage",
    redirect: "/schedule-management",
    meta: { title: "排班管理", roles: ["manager"] }
  },
  { path: "/schedule-management", name: "schedule-management", component: ScheduleManagementView, meta: { title: "排班管理", roles: ["manager"] } },
  { path: "/finance-ledger", name: "finance-ledger", component: FinanceLedgerView, meta: { title: "财务台账", roles: ["manager"] } },
  { path: "/cross-clinic-dispatch", name: "cross-clinic-dispatch", component: CrossClinicDispatchView, meta: { title: "跨院区调度", roles: ["manager"] } },

  { path: "/user-management", name: "user-management", component: UserManagementView, meta: { title: "用户管理", roles: ["admin"] } },
  { path: "/permission-config", name: "permission-config", component: PermissionConfigView, meta: { title: "权限配置", roles: ["admin"] } },
  { path: "/audit-logs", name: "audit-logs", component: AuditLogsView, meta: { title: "审计日志", roles: ["admin"] } },
  { path: "/federated-status", name: "federated-status", component: FederatedLearning, meta: { title: "联邦学习状态", roles: ["admin"] } },
  { path: "/data-center", name: "data-center", component: DataCenterView, meta: { title: "数据中心", roles: ["admin"] } },
  { path: "/:pathMatch(.*)*", redirect: PROJECT_ENTRY_PATH }
];

const routerBase = import.meta.env.BASE_URL && import.meta.env.BASE_URL !== "./" ? import.meta.env.BASE_URL : "/";
const routerHistory =
  import.meta.env.VITE_ROUTER_MODE === "hash" ? createWebHashHistory(routerBase) : createWebHistory(routerBase);

const router = createRouter({
  history: routerHistory,
  routes
});

router.beforeEach(async (to, _from, next) => {
  const authStore = useAuthStore();
  if (isStaticDemoEnabled() && to.path === "/403") {
    next(PROJECT_ENTRY_PATH);
    return;
  }

  if (to.meta?.public) {
    next();
    return;
  }

  const requiredRoles = to.meta?.roles || [];
  if (isStaticDemoEnabled() && requiredRoles.length > 0) {
    const preferredRole = normalizeDemoRole(requiredRoles[0]);
    if (!authStore.isLoggedIn || !authStore.hasRole(requiredRoles)) {
      activateStaticDemoRole(authStore, preferredRole);
    }
    next();
    return;
  }

  if (authStore.token && !authStore.profile) {
    try {
      await authStore.loadProfile();
    } catch {
      authStore.logout();
    }
  }

  if (requiredRoles.length === 0) {
    next();
    return;
  }

  if (!authStore.isLoggedIn) {
    next("/login");
    return;
  }

  if (!authStore.hasRole(requiredRoles)) {
    next("/403");
    return;
  }

  next();
});

export default router;

function normalizeDemoRole(role) {
  return role === "pharmacy" ? "pharmacist" : role || "doctor";
}

function activateStaticDemoRole(authStore, role) {
  const user = getStaticDemoUser(normalizeDemoRole(role));
  window.sessionStorage.setItem("static_demo", "1");
  window.sessionStorage.setItem("static_demo_role", user.role);
  authStore.setToken(`static-demo-token-${user.role}`);
  authStore.setDemoRole(user.role);
  authStore.setProfile(user);
}
