<template>
  <div class="page">
    <el-card class="glass-card">
      <template #header>
        <div class="header-row">
          <span>护理日志（可追踪流程）</span>
          <el-button class="agile-btn" :loading="loading" @click="loadData">刷新</el-button>
        </div>
      </template>
      <el-empty v-if="rows.length === 0" description="今日暂无护理记录" />
      <el-table v-else :data="rows" border>
        <el-table-column prop="id" label="住院记录ID" width="120" />
        <el-table-column prop="pet_name" label="宠物" min-width="160" />
        <el-table-column prop="status" label="状态" width="120" />
        <el-table-column prop="admission_time" label="入院时间" min-width="180" />
        <el-table-column label="下一步" min-width="180">
          <template #default="{ row }">
            <el-tag type="success">前往体征录入</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140">
          <template #default="{ row }">
              <el-button class="agile-btn" type="primary" size="small" @click="goVitals(row)">录入体征</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="list-meta">共{{ rows.length }}条记录，最后更新时间 {{ lastUpdated || "--:--" }}</div>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { fetchInpatientRecords } from "../api/inpatient";
import { useAuthStore } from "../store";
import { getErrorMessage } from "../utils/status";

const router = useRouter();
const authStore = useAuthStore();
const loading = ref(false);
const rows = ref([]);
const lastUpdated = ref("");

async function loadData() {
  loading.value = true;
  try {
    const res = await fetchInpatientRecords(authStore.clinicId || "");
    rows.value = res.data || [];
    lastUpdated.value = new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "护理日志加载失败"));
  } finally {
    loading.value = false;
  }
}

function goVitals(row) {
  router.push({ name: "vitals-entry", query: { recordId: String(row.id) } });
}

onMounted(loadData);
</script>

<style scoped>
.page { padding: 16px; }
.header-row { display: flex; justify-content: space-between; align-items: center; }
.list-meta { margin-top: 10px; color: #909399; font-size: 12px; }
</style>
