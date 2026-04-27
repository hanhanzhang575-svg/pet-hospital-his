import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "../store";

import ArchiveView from "../views/ArchiveView.vue";
import AppointmentsView from "../views/AppointmentsView.vue";
import ForbiddenView from "../views/ForbiddenView.vue";
import InpatientView from "../views/InpatientView.vue";
import InventoryView from "../views/InventoryView.vue";
import LoginView from "../views/LoginView.vue";
import PharmacyView from "../views/PharmacyView.vue";
import RfmBoardView from "../views/RfmBoardView.vue";
import VetWorkbenchView from "../views/VetWorkbenchView.vue";
import BillingSettlementView from "../views/BillingSettlementView.vue";
import FollowupTasksView from "../views/FollowupTasksView.vue";
import PrescriptionCreateView from "../views/PrescriptionCreateView.vue";
import InpatientApplyView from "../views/InpatientApplyView.vue";
import AIDiagnosisView from "../views/AIDiagnosisView.vue";
import DoctorConsultationView from "../views/DoctorConsultationView.vue";
import MedicalRecordDetailView from "../views/MedicalRecordDetailView.vue";
import NursingLogsView from "../views/NursingLogsView.vue";
import VitalsEntryView from "../views/VitalsEntryView.vue";
import ScheduleManagementView from "../views/ScheduleManagementView.vue";
import EoqVisualView from "../views/EoqVisualView.vue";
import EoqSuggestionView from "../views/EoqSuggestion.vue";
import CrossClinicRecordsView from "../views/CrossClinicRecordsView.vue";
import CageStatusView from "../views/CageStatusView.vue";
import PurchaseRequestsView from "../views/PurchaseRequestsView.vue";
import OpsBoardView from "../views/OpsBoardView.vue";
import PurchaseApprovalsView from "../views/PurchaseApprovalsView.vue";
import FinanceLedgerView from "../views/FinanceLedgerView.vue";
import CrossClinicDispatchView from "../views/CrossClinicDispatchView.vue";
import UserManagementView from "../views/UserManagementView.vue";
import PermissionConfigView from "../views/PermissionConfigView.vue";
import AuditLogsView from "../views/AuditLogsView.vue";
import FederatedLearning from "../views/FederatedLearning.vue";
import LabDashboardView from "../views/LabDashboardView.vue";
import LabTestsView from "../views/LabTestsView.vue";
import LabResultsView from "../views/LabResultsView.vue";
import DataCenterView from "../views/DataCenterView.vue";
import AdoptionHallView from "../views/AdoptionHallView.vue";
import OwnerCenterView from "../views/OwnerCenterView.vue";

const routes = [
  { path: "/", redirect: "/login" },
  { path: "/login", name: "login", component: LoginView, meta: { title: "登录", public: true } },
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

  { path: "/appointments", name: "appointments", component: AppointmentsView, meta: { title: "挂号管理", roles: ["receptionist", "doctor"] } },
  { path: "/archives", name: "archives", component: ArchiveView, meta: { title: "客户档案", roles: ["receptionist", "doctor"] } },
  { path: "/billing-settlement", name: "billing-settlement", component: BillingSettlementView, meta: { title: "收费结算", roles: ["receptionist"] } },
  { path: "/followup-tasks", name: "followup-tasks", component: FollowupTasksView, meta: { title: "回访任务", roles: ["receptionist"] } },
  { path: "/owner-center", name: "owner-center", component: OwnerCenterView, meta: { title: "主人运营", roles: ["receptionist", "manager"] } },
  { path: "/adoption-hall", name: "adoption-hall", component: AdoptionHallView, meta: { title: "领养匹配", roles: ["receptionist", "manager"] } },

  { path: "/vet-workbench", name: "vet-workbench", component: VetWorkbenchView, meta: { title: "医生工作台", roles: ["doctor"] } },
  { path: "/medical-records", name: "medical-records", component: CrossClinicRecordsView, meta: { title: "电子病历", roles: ["doctor"] } },
  { path: "/medical-record/:id", name: "medical-record-detail", component: MedicalRecordDetailView, meta: { title: "病历详情", roles: ["doctor"] } },
  { path: "/prescription-create", name: "prescription-create", component: PrescriptionCreateView, meta: { title: "处方开具", roles: ["doctor"] } },
  { path: "/inpatient-apply", name: "inpatient-apply", component: InpatientApplyView, meta: { title: "住院申请", roles: ["doctor"] } },
  { path: "/ai-diagnosis", name: "ai-diagnosis", component: AIDiagnosisView, meta: { title: "AI 辅助诊断", roles: ["doctor"] } },
  { path: "/doctor-consultation", name: "doctor-consultation", component: DoctorConsultationView, meta: { title: "接诊工作区", roles: ["doctor"] } },

  { path: "/inpatient", name: "inpatient", component: InpatientView, meta: { title: "住院管理", roles: ["nurse", "doctor"] } },
  { path: "/cage-status", name: "cage-status", component: CageStatusView, meta: { title: "笼舍状态", roles: ["nurse", "manager"] } },
  { path: "/nursing-logs", name: "nursing-logs", component: NursingLogsView, meta: { title: "护理日志", roles: ["nurse"] } },
  { path: "/vitals-entry", name: "vitals-entry", component: VitalsEntryView, meta: { title: "体征录入", roles: ["nurse"] } },

  { path: "/pharmacy", name: "pharmacy", component: PharmacyView, meta: { title: "药房发药", roles: ["pharmacist", "pharmacy"] } },
  { path: "/inventory", name: "inventory", component: InventoryView, meta: { title: "库存管理", roles: ["pharmacist", "pharmacy", "manager"] } },
  { path: "/inventory-eoq", name: "inventory-eoq", component: EoqVisualView, meta: { title: "EOQ 补货建议", roles: ["pharmacist", "pharmacy", "manager"] } },
  { path: "/pharmacy-eoq-suggestions", name: "pharmacy-eoq-suggestions", component: EoqSuggestionView, meta: { title: "药房 EOQ 策略", roles: ["pharmacist", "pharmacy", "manager"] } },
  { path: "/purchase-requests", name: "purchase-requests", component: PurchaseRequestsView, meta: { title: "采购申请", roles: ["pharmacist", "pharmacy"] } },

  { path: "/ops-board", name: "ops-board", component: OpsBoardView, meta: { title: "运营看板", roles: ["manager"] } },
  { path: "/rfm-board", name: "rfm-board", component: RfmBoardView, meta: { title: "RFM 看板", roles: ["manager"] } },
  { path: "/purchase-approvals", name: "purchase-approvals", component: PurchaseApprovalsView, meta: { title: "采购审批", roles: ["manager"] } },
  {
    path: "/admin/schedule-manage",
    name: "admin-schedule-manage",
    component: () => import("../views/admin/ScheduleManage.vue"),
    meta: { title: "医生护士排班", roles: ["admin", "manager"] }
  },
  { path: "/schedule-management", name: "schedule-management", component: ScheduleManagementView, meta: { title: "排班管理", roles: ["manager"] } },
  { path: "/finance-ledger", name: "finance-ledger", component: FinanceLedgerView, meta: { title: "财务台账", roles: ["manager"] } },
  { path: "/cross-clinic-dispatch", name: "cross-clinic-dispatch", component: CrossClinicDispatchView, meta: { title: "跨院区调度", roles: ["manager"] } },

  { path: "/user-management", name: "user-management", component: UserManagementView, meta: { title: "用户管理", roles: ["admin"] } },
  { path: "/permission-config", name: "permission-config", component: PermissionConfigView, meta: { title: "权限配置", roles: ["admin"] } },
  { path: "/audit-logs", name: "audit-logs", component: AuditLogsView, meta: { title: "审计日志", roles: ["admin"] } },
  { path: "/federated-status", name: "federated-status", component: FederatedLearning, meta: { title: "联邦学习状态", roles: ["admin"] } },
  { path: "/data-center", name: "data-center", component: DataCenterView, meta: { title: "数据中心", roles: ["admin"] } }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

router.beforeEach(async (to, _from, next) => {
  const authStore = useAuthStore();
  if (to.meta?.public) {
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

  const requiredRoles = to.meta?.roles || [];
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
