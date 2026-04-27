<template>
  <div class="home-page">
    <el-card class="welcome-card" shadow="never">
      <div class="welcome-header">
        <div>
          <div class="welcome-kicker">今日工作概览</div>
          <h2>欢迎回来，{{ username }}</h2>
          <p class="welcome-desc">{{ roleDesc }}</p>
        </div>
        <el-button type="danger" plain @click="handleLogout">退出登录</el-button>
      </div>
    </el-card>

    <div class="dashboard-container">
      <DoctorDashboard v-if="role === 'doctor'" />
      <NurseDashboard v-else-if="role === 'nurse'" />
      <ReceptionDashboard v-else-if="role === 'receptionist'" />
      <PharmacyDashboard v-else-if="role === 'pharmacist' || role === 'pharmacy'" />
      <ManagerDashboard v-else-if="role === 'manager'" />
      <AdminDashboard v-else-if="role === 'admin'" />
      <LabDashboardView v-else-if="role === 'lab_tech'" />
      <div v-else class="placeholder-dash">
        <el-alert type="warning" :closable="false" title="当前角色暂无专属首页模块" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../store";
import { ElMessage, ElMessageBox } from "element-plus";

import DoctorDashboard from "../components/dashboards/DoctorDashboard.vue";
import NurseDashboard from "../components/dashboards/NurseDashboard.vue";
import ReceptionDashboard from "../components/dashboards/ReceptionDashboard.vue";
import PharmacyDashboard from "../components/dashboards/PharmacyDashboard.vue";
import ManagerDashboard from "../components/dashboards/ManagerDashboard.vue";
import AdminDashboard from "../components/dashboards/AdminDashboard.vue";
import LabDashboardView from "./LabDashboardView.vue";

const router = useRouter();
const authStore = useAuthStore();

const username = computed(() => authStore.displayName || "访客");
const role = computed(() => authStore.role || "");

const roleDescMap = {
  doctor: "面向临床诊疗、病历与处方操作。",
  nurse: "聚焦住院护理、笼舍与体征记录。",
  receptionist: "承担挂号、收费、领养与主人运营前台协同。",
  pharmacist: "负责发药、库存与采购申请。",
  pharmacy: "负责发药、库存与采购申请。",
  manager: "关注院区经营、排班、财务与客户运营。",
  admin: "负责权限配置、审计、联邦学习与数据治理。",
  lab_tech: "负责检验队列、结果录入与报告回传。"
};

const roleDesc = computed(() => roleDescMap[role.value] || "系统用户");

const handleLogout = async () => {
  try {
    await ElMessageBox.confirm("确定退出登录吗？", "提示", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning"
    });
    authStore.logout();
    ElMessage.success("已退出登录");
    router.push("/login");
  } catch {
    // user canceled
  }
};
</script>

<style scoped>
.home-page {
  min-height: 100vh;
  padding: 14px;
  background:
    radial-gradient(circle at top right, rgba(34, 197, 94, 0.1), transparent 28%),
    linear-gradient(145deg, #f8fbff 0%, #fff8f0 100%);
}

.welcome-card {
  margin-bottom: 12px;
  border-radius: 18px;
}

.welcome-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.welcome-kicker {
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #0f766e;
  font-weight: 700;
}

.welcome-header h2 {
  margin: 8px 0 0;
  color: #0f172a;
  font-size: 28px;
}

.welcome-desc {
  margin: 8px 0 0;
  color: #64748b;
  font-size: 14px;
}

.dashboard-container {
  animation: fadeIn 0.25s ease;
}

.placeholder-dash {
  min-height: 260px;
  display: flex;
  align-items: center;
  justify-content: center;
}

@media (max-width: 768px) {
  .welcome-header {
    flex-direction: column;
    align-items: flex-start;
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
