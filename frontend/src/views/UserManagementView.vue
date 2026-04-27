<template>
  <div class="page layout-bg">
    <el-card class="glass-card main-card stagger-in-1">
      <template #header>
        <div class="header-row">
          <span class="page-title">👥 组织架构与用户管理</span>
          <el-space class="action-space">
            <el-select v-model="filters.role" clearable placeholder="🔍 按角色筛选" class="agile-select" style="width: 170px" @change="loadData">
              <el-option label="👑 系统管理员" value="admin" />
              <el-option label="💼 院区主任" value="manager" />
              <el-option label="👨‍⚕️ 执业医生" value="doctor" />
              <el-option label="💉 护理人员" value="nurse" />
              <el-option label="💁 前台接诊" value="receptionist" />
              <el-option label="💊 药房人员" value="pharmacist" />
            </el-select>
            <el-button class="agile-btn btn-ghost" :loading="loading" @click="loadData">
              <span class="btn-text">🔄 刷新列表</span>
            </el-button>
          </el-space>
        </div>
      </template>

      <div class="stagger-in-2">
        <el-table :data="rows" class="cute-table" :header-cell-style="{ background: '#F8FAFC', color: '#475569', fontWeight: '800' }">
          <el-table-column prop="id" label="UID" width="90">
            <template #default="{ row }">
              <span class="code-font text-sub">#{{ row.id }}</span>
            </template>
          </el-table-column>
          
          <el-table-column prop="full_name" label="系统成员" min-width="180">
            <template #default="{ row }">
              <div class="name-cell">
                <div class="avatar-placeholder" :class="getAvatarColor(row.id)">
                  {{ (row.full_name || '?').charAt(0) }}
                </div>
                <span class="fw-bold text-primary">{{ row.full_name }}</span>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column prop="role" label="岗位角色" width="160">
            <template #default="{ row }">
              <el-tag round effect="light" :class="['role-tag', getRoleTagClass(row.role)]">
                {{ formatRole(row.role) }}
              </el-tag>
            </template>
          </el-table-column>
          
          <el-table-column prop="clinic_id" label="归属院区" width="130">
            <template #default="{ row }">
              <el-tag effect="light" type="info" round class="clinic-tag">{{ row.clinic_id || "总群" }}</el-tag>
            </template>
          </el-table-column>
          
          <el-table-column prop="is_active" label="账户状态" width="130">
            <template #default="{ row }">
              <div class="status-cell" :class="row.is_active ? 'status-active' : 'status-inactive'">
                <div class="dot-jelly"></div>
                <span>{{ row.is_active ? "正常启用" : "已封停" }}</span>
              </div>
            </template>
          </el-table-column>
        </el-table>
        
        <div class="list-meta">
          共 <span class="meta-highlight">{{ rows.length }}</span> 位系统成员，最后更新于 {{ lastUpdated || "--:--" }}
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
// ==========================================
// 逻辑代码层 (完全保持不变)
// ==========================================
import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import http from "../api/http";
import { getErrorMessage } from "../utils/status";

const loading = ref(false);
const rows = ref([]);
const lastUpdated = ref("");
const filters = ref({ role: "" });

async function loadData() {
  loading.value = true;
  try {
    const res = await http.get("/users", { params: { role: filters.value.role || undefined } });
    rows.value = res.data || [];
    lastUpdated.value = new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "用户加载失败"));
  } finally {
    loading.value = false;
  }
}

// 纯前端辅助展示函数 (不影响原逻辑)
function formatRole(role) {
  const map = {
    admin: "👑 管理员",
    manager: "💼 院区主任",
    doctor: "👨‍⚕️ 医生",
    nurse: "💉 护理",
    receptionist: "💁 前台",
    pharmacist: "💊 药房"
  };
  return map[role] || role;
}

function getRoleTagClass(role) {
  const map = {
    admin: "role-danger",
    manager: "role-warning",
    doctor: "role-primary",
    nurse: "role-success",
    receptionist: "role-info",
    pharmacist: "role-purple"
  };
  return map[role] || "role-default";
}

function getAvatarColor(id) {
  const colors = ['bg-color-1', 'bg-color-2', 'bg-color-3', 'bg-color-4', 'bg-color-5'];
  return colors[(id || 0) % colors.length];
}

onMounted(loadData);
</script>

<style scoped>
/* ====================================================
   全局变量与基础设定
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
.text-sub { color: #94A3B8; }

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
.page-title { font-size: 20px; font-weight: 800; color: var(--text-main); display: flex; align-items: center;}

/* 控件区 */
.action-space { display: flex; gap: 12px; }
:deep(.agile-select .el-input__wrapper) { border-radius: 12px !important; background-color: #F8FAFC; box-shadow: 0 0 0 1px #E2E8F0 inset !important; transition: all 0.3s var(--spring) !important; }
:deep(.agile-select .el-input__wrapper.is-focus) { background-color: #FFFFFF; box-shadow: 0 0 0 2px var(--primary) inset, 0 4px 12px rgba(59, 130, 246, 0.1) !important; }

/* ====================================================
   Q弹操作按钮
   ==================================================== */
.agile-btn {
  border-radius: 100px !important; height: 36px !important; font-weight: 800 !important; padding: 0 20px !important;
  transition: all 0.3s var(--spring) !important; border: none !important; font-size: 14px !important;
}
.btn-ghost { background-color: #FFFFFF !important; color: #64748B !important; border: 2px solid #E2E8F0 !important; box-shadow: 0 2px 4px rgba(0,0,0,0.02) !important; }
.btn-ghost:hover { border-color: #CBD5E1 !important; color: #1E293B !important; transform: translateY(-2px) !important; }

/* ====================================================
   可爱的数据表格 (无边框悬浮态)
   ==================================================== */
:deep(.cute-table) {
  border-radius: 16px; 
  overflow: hidden; 
  border: 1px solid #F1F5F9;
  --el-table-border-color: #F1F5F9;
}
:deep(.cute-table .el-table__row) { transition: background-color 0.2s var(--smooth); }
:deep(.cute-table .el-table__row:hover > td) { background-color: #F8FAFC !important; }

.code-font { font-family: 'JetBrains Mono', monospace; font-size: 14px; font-weight: 800;}

/* 头像列与名字 */
.name-cell { display: flex; align-items: center; gap: 12px; }
.avatar-placeholder {
  width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
  font-size: 14px; font-weight: 800; color: #FFF; box-shadow: 0 2px 6px rgba(0,0,0,0.1);
}
.bg-color-1 { background: linear-gradient(135deg, #3B82F6, #60A5FA); }
.bg-color-2 { background: linear-gradient(135deg, #10B981, #34D399); }
.bg-color-3 { background: linear-gradient(135deg, #F59E0B, #FBBF24); }
.bg-color-4 { background: linear-gradient(135deg, #8B5CF6, #A78BFA); }
.bg-color-5 { background: linear-gradient(135deg, #EC4899, #F472B6); }

/* 角色标签配色 */
.role-tag { font-weight: 800; border: none; padding: 0 12px;}
.role-danger { background-color: #FEF2F2 !important; color: #DC2626 !important; }
.role-warning { background-color: #FFFBEB !important; color: #D97706 !important; }
.role-primary { background-color: #EFF6FF !important; color: #2563EB !important; }
.role-success { background-color: #ECFDF5 !important; color: #059669 !important; }
.role-info { background-color: #F1F5F9 !important; color: #475569 !important; }
.role-purple { background-color: #F5F3FF !important; color: #7C3AED !important; }

.clinic-tag { font-weight: 800; border: none; background: #F1F5F9; color: #475569;}

/* 状态指示灯 (呼吸发光) */
.status-cell { display: flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 800;}
.dot-jelly { width: 10px; height: 10px; border-radius: 50%; }
.status-active .dot-jelly { background: #10B981; box-shadow: 0 0 8px rgba(16, 185, 129, 0.5); }
.status-active span { color: #059669; }
.status-inactive .dot-jelly { background: #94A3B8; }
.status-inactive span { color: #64748B; opacity: 0.8;}

/* 底部元信息 */
.list-meta { margin-top: 16px; color: #94A3B8; font-size: 13px; font-weight: 600; text-align: right; }
.meta-highlight { color: var(--primary); font-weight: 800; font-size: 15px; }

/* 阶梯动画 */
@keyframes fadeInUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
[class*="stagger-in-"] { animation: fadeInUp 0.6s var(--spring) both; }
.stagger-in-1 { animation-delay: 0.1s; }
.stagger-in-2 { animation-delay: 0.2s; }
</style>