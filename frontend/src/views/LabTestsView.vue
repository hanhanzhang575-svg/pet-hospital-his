<template>
  <div class="lab-tests-page">
    <el-row :gutter="12">
      <el-col :xs="24" :lg="16">
        <el-card class="panel-card" shadow="never">
          <template #header>
            <div class="header-row">
              <div>
                <div class="title">待检样本队列</div>
                <div class="subtitle">按紧急度 + 等待时长排序，优先处理危急样本</div>
              </div>
              <el-button :loading="loading" @click="loadData">刷新</el-button>
            </div>
          </template>
          <el-empty v-if="rows.length === 0" description="当前无待检任务，已展示演示队列" />
          <el-table :data="displayRows" border stripe height="420">
            <el-table-column prop="record_code" label="诊单号" width="140" />
            <el-table-column prop="pet_name" label="宠物" min-width="120" />
            <el-table-column label="项目" min-width="180">
              <template #default="{ row }">
                <el-tag v-for="item in row.exam_items || []" :key="`${row.id}-${item}`" style="margin-right: 4px">{{ item }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="requesting_doctor" label="申请医生" width="120" />
            <el-table-column prop="urgency_level" label="紧急度" width="96" />
            <el-table-column label="等待" width="90">
              <template #default="{ row }">{{ waitMinutes(row) }}分钟</template>
            </el-table-column>
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button size="small" type="success" @click="startExam(row)">开始</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="8">
        <el-card class="panel-card" shadow="never">
          <template #header><div class="title">实验室增强模块</div></template>
          <div class="module-list">
            <div class="module-item">
              <div class="module-name">样本追踪链路</div>
              <div class="module-desc">登记 → 接收 → 检测 → 复核 → 报告发布</div>
            </div>
            <div class="module-item">
              <div class="module-name">TAT 时效监控</div>
              <div class="module-desc">急诊目标 ≤ 30 分钟，常规目标 ≤ 120 分钟</div>
            </div>
            <div class="module-item">
              <div class="module-name">质量控制提醒</div>
              <div class="module-desc">每日开机质控、异常漂移校准、批间比对</div>
            </div>
            <div class="module-item">
              <div class="module-name">危急值升级策略</div>
              <div class="module-desc">危急值触发医生即时通知与二次确认</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import { fetchPendingTests, startLabExam } from "../api/lab";
import { useAuthStore } from "../store";
import { getErrorMessage } from "../utils/status";

const authStore = useAuthStore();
const loading = ref(false);
const rows = ref([]);

const demoRows = [
  {
    id: "demo-1",
    appointment_id: 10001,
    record_code: "DEMO-LAB-001",
    pet_name: "可乐",
    exam_items: ["WBC", "RBC", "ALT"],
    requesting_doctor: "李医生",
    urgency_level: "急诊",
    requested_at: new Date(Date.now() - 22 * 60000).toISOString()
  },
  {
    id: "demo-2",
    appointment_id: 10002,
    record_code: "DEMO-LAB-002",
    pet_name: "布丁",
    exam_items: ["BUN", "Creatinine"],
    requesting_doctor: "张医生",
    urgency_level: "常规",
    requested_at: new Date(Date.now() - 48 * 60000).toISOString()
  }
];

const displayRows = computed(() => (rows.value.length ? rows.value : demoRows));

function waitMinutes(row) {
  const d = new Date(row.requested_at || "");
  if (Number.isNaN(d.getTime())) return 0;
  return Math.max(0, Math.round((Date.now() - d.getTime()) / 60000));
}

async function loadData() {
  loading.value = true;
  try {
    const res = await fetchPendingTests(authStore.clinicId || "");
    rows.value = res.data || [];
  } catch (error) {
    rows.value = [];
    ElMessage.error(getErrorMessage(error, "待检队列加载失败"));
  } finally {
    loading.value = false;
  }
}

async function startExam(row) {
  if (String(row.id).startsWith("demo-")) {
    ElMessage.info("演示数据不可操作，请先创建真实检验任务");
    return;
  }
  try {
    await startLabExam(row.appointment_id);
    ElMessage.success("已开始检验");
    await loadData();
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "开始检验失败"));
  }
}

onMounted(loadData);
</script>

<style scoped>
.lab-tests-page { padding: 14px; }
.panel-card { border-radius: 14px; margin-bottom: 12px; }
.header-row { display: flex; justify-content: space-between; align-items: center; gap: 8px; }
.title { font-weight: 700; color: #0f172a; }
.subtitle { font-size: 12px; color: #64748b; margin-top: 4px; }
.module-list { display: grid; gap: 10px; }
.module-item { border: 1px solid #e5e7eb; border-radius: 10px; padding: 10px; background: #f8fafc; }
.module-name { font-weight: 600; color: #0f172a; }
.module-desc { margin-top: 4px; font-size: 12px; color: #475569; line-height: 1.5; }
</style>
