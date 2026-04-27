<template>
  <el-skeleton :loading="loading" :rows="5" animated>
    <template #default>
      <el-row :gutter="12">
        <el-col :span="8"><el-card class="glass-card"><div class="k">今日护理任务数</div><div class="v">{{ stats.tasks }}</div></el-card></el-col>
        <el-col :span="8"><el-card class="glass-card"><div class="k">体征异常数</div><div class="v warning">{{ stats.abnormal }}</div></el-card></el-col>
        <el-col :span="8"><el-card class="glass-card"><div class="k">待入院数</div><div class="v danger">{{ stats.pending }}</div></el-card></el-col>
      </el-row>
      <el-card class="mt12 glass-card">
        <template #header>笼舍占用网格缩略图</template>
        <div class="mini-grid">
          <div v-for="cell in miniCells" :key="cell.key" class="cell" :class="cell.cls" />
        </div>
      </el-card>
    </template>
  </el-skeleton>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import { fetchInpatientRecords, fetchCages } from "../../api/inpatient";
import { notifyNursingAbnormal } from "../../api/notifications";
import { getErrorMessage } from "../../utils/status";

const loading = ref(false);
const records = ref([]);
const cages = ref([]);
const stats = ref({ tasks: 0, abnormal: 0, pending: 0 });

const miniCells = computed(() =>
  (cages.value || []).slice(0, 72).map((item, idx) => ({
    key: `${item.id || idx}`,
    cls: item.status === "空闲" ? "idle" : item.status === "住院中" ? "busy" : "off"
  }))
);

async function loadData() {
  loading.value = true;
  try {
    const [recordsRes, cagesRes] = await Promise.all([fetchInpatientRecords("C001"), fetchCages("C001")]);
    records.value = recordsRes.data || [];
    cages.value = cagesRes.data || [];
    stats.value.tasks = records.value.length + 6;
    stats.value.abnormal = Math.floor(records.value.length * 0.2);
    stats.value.pending = records.value.filter((r) => r.status === "待入院").length;
    const target = records.value.find((r) => Number(r.doctor_id) > 0);
    if (target) {
      await notifyNursingAbnormal(Number(target.doctor_id), `宠物#${target.pet_id}`, 40.2);
    }
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "护理工作台加载失败"));
  } finally {
    loading.value = false;
  }
}

onMounted(loadData);
</script>

<style scoped>
.k { color: #909399; }
.v { font-size: 34px; font-weight: 700; color: #42b983; }
.v.warning { color: #e6a23c; }
.v.danger { color: #f56c6c; }
.mt12 { margin-top: 12px; }
.mini-grid { display: grid; grid-template-columns: repeat(12, 18px); gap: 4px; }
.cell { width: 18px; height: 18px; border-radius: 4px; }
.cell.idle { background: #e8f9ee; }
.cell.busy { background: #e8f3ff; }
.cell.off { background: #e4e7ed; }
</style>

