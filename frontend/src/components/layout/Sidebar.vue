<template>
  <aside class="sidebar">
    <div class="brand" @click="goHome">
      <div class="brand-mark">PH</div>
      <div>
        <div class="brand-title">宠物医院信息系统</div>
        <div class="brand-subtitle">{{ roleLabel }}</div>
      </div>
    </div>

    <el-scrollbar class="menu-scroll">
      <el-menu :default-active="activePath" class="menu" router>
        <el-menu-item v-for="item in currentMenus" :key="item.path" :index="item.path">
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.title }}</span>
        </el-menu-item>
      </el-menu>
    </el-scrollbar>
  </aside>
</template>

<script setup>
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  Avatar,
  Box,
  Calendar,
  Checked,
  Connection,
  DataAnalysis,
  DataLine,
  Document,
  EditPen,
  Folder,
  Grid,
  House,
  List,
  Lock,
  MagicStick,
  Money,
  Notebook,
  Phone,
  PieChart,
  PictureFilled,
  Share,
  ShoppingCart,
  Stamp,
  TrendCharts,
  User
} from "@element-plus/icons-vue";
import { useAuthStore } from "../../store";

const authStore = useAuthStore();
const route = useRoute();
const router = useRouter();

const menuMap = {
  receptionist: [
    { title: "挂号管理", path: "/appointments", icon: Calendar },
    { title: "客户档案", path: "/archives", icon: Folder },
    { title: "主人运营", path: "/owner-center", icon: Avatar },
    { title: "收费结算", path: "/billing-settlement", icon: Money },
    { title: "回访任务", path: "/followup-tasks", icon: Phone },
    { title: "领养匹配", path: "/adoption-hall", icon: PictureFilled }
  ],
  doctor: [
    { title: "医生工作台", path: "/vet-workbench", icon: User },
    { title: "电子病历", path: "/medical-records", icon: Document },
    { title: "接诊工作区", path: "/doctor-consultation", icon: EditPen },
    { title: "处方开具", path: "/prescription-create", icon: Checked },
    { title: "住院申请", path: "/inpatient-apply", icon: House },
    { title: "AI 辅助诊断", path: "/ai-diagnosis", icon: MagicStick }
  ],
  lab_tech: [
    { title: "待检队列", path: "/lab-tests", icon: Calendar },
    { title: "检验工作台", path: "/lab-dashboard", icon: EditPen },
    { title: "报告库", path: "/lab-results", icon: Folder }
  ],
  nurse: [
    { title: "住院管理", path: "/inpatient", icon: House },
    { title: "笼舍状态", path: "/cage-status", icon: Grid },
    { title: "护理日志", path: "/nursing-logs", icon: Notebook },
    { title: "体征录入", path: "/vitals-entry", icon: DataLine }
  ],
  pharmacist: [
    { title: "药房发药", path: "/pharmacy", icon: Checked },
    { title: "库存管理", path: "/inventory", icon: Box },
    { title: "EOQ 建议", path: "/inventory-eoq", icon: TrendCharts },
    { title: "采购申请", path: "/purchase-requests", icon: ShoppingCart }
  ],
  manager: [
    { title: "运营看板", path: "/ops-board", icon: DataAnalysis },
    { title: "主人运营", path: "/owner-center", icon: Avatar },
    { title: "领养匹配", path: "/adoption-hall", icon: PictureFilled },
    { title: "RFM 看板", path: "/rfm-board", icon: TrendCharts },
    { title: "采购审批", path: "/purchase-approvals", icon: Stamp },
    { title: "排班管理", path: "/schedule-management", icon: Calendar },
    { title: "财务台账", path: "/finance-ledger", icon: PieChart },
    { title: "跨院区调度", path: "/cross-clinic-dispatch", icon: Share }
  ],
  admin: [
    { title: "用户管理", path: "/user-management", icon: Avatar },
    { title: "权限配置", path: "/permission-config", icon: Lock },
    { title: "审计日志", path: "/audit-logs", icon: List },
    { title: "联邦学习", path: "/federated-status", icon: Connection },
    { title: "数据中心", path: "/data-center", icon: DataAnalysis }
  ]
};

const roleNameMap = {
  receptionist: "前台接诊",
  doctor: "医生",
  nurse: "护理",
  pharmacist: "药房",
  pharmacy: "药房",
  manager: "院区运营",
  admin: "系统管理",
  lab_tech: "检验"
};

const normalizedRole = computed(() => {
  if (authStore.role === "pharmacy") return "pharmacist";
  return authStore.role;
});

const currentMenus = computed(() => menuMap[normalizedRole.value] || []);
const activePath = computed(() => route.path);
const roleLabel = computed(() => roleNameMap[normalizedRole.value] || "系统角色");

function goHome() {
  router.push("/home");
}
</script>

<style scoped>
.sidebar {
  width: 236px;
  border-right: 1px solid rgba(15, 23, 42, 0.08);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(248, 250, 252, 0.92)),
    radial-gradient(circle at top left, rgba(34, 197, 94, 0.12), transparent 40%);
  backdrop-filter: blur(16px);
  height: calc(100vh - 60px);
  position: sticky;
  top: 60px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 14px;
  cursor: pointer;
  border-bottom: 1px solid rgba(15, 23, 42, 0.06);
}

.brand-mark {
  width: 40px;
  height: 40px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  color: #fff;
  font-weight: 800;
  letter-spacing: 0.04em;
  background: linear-gradient(135deg, #0f766e, #22c55e);
  box-shadow: 0 12px 24px rgba(15, 118, 110, 0.2);
}

.brand-title {
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
}

.brand-subtitle {
  margin-top: 2px;
  font-size: 12px;
  color: #64748b;
}

.menu-scroll {
  height: calc(100% - 74px);
}

.menu {
  border-right: none;
  background: transparent;
  padding: 12px 10px 18px;
}

.menu :deep(.el-menu-item) {
  height: 44px;
  margin-bottom: 6px;
  border-radius: 12px;
  color: #334155;
}

.menu :deep(.el-menu-item.is-active) {
  color: #0f172a;
  background: linear-gradient(90deg, rgba(226, 232, 240, 0.88), rgba(220, 252, 231, 0.92));
}
</style>
