<template>
  <div class="page">
    <el-card class="glass-card">
      <template #header>
        <div class="header-row">
          <span>电子病历库（含跨院区筛选）</span>
          <el-space>
            <el-select v-model="clinic" style="width: 170px" @change="changeClinic">
              <el-option label="C001 沙河口" value="C001" />
              <el-option label="C002 甘井子" value="C002" />
              <el-option label="C003 高新园区" value="C003" />
            </el-select>
            <el-button :loading="loading" @click="loadData">刷新</el-button>
          </el-space>
        </div>
      </template>
      <el-alert v-if="showCrossBanner" type="warning" :closable="false" show-icon style="margin-bottom: 10px">
        您正在查看{{ clinicName(clinic) }}病历数据，此操作已记录审计日志
      </el-alert>
      <el-table :data="rows" border>
        <el-table-column prop="record_no" label="病历号" min-width="150" />
        <el-table-column prop="pet_name" label="宠物" width="140" />
        <el-table-column prop="owner_name" label="主人" width="120" />
        <el-table-column prop="vet_name" label="医生" width="120" />
        <el-table-column prop="diagnosis" label="诊断" min-width="180" />
        <el-table-column prop="created_at" label="时间" min-width="170" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import http from "../api/http";
import { getMedicalRecords } from "../api/medicalRecords";
import { getErrorMessage } from "../utils/status";

const currentClinic = ref("C001");
const clinic = ref("C001");
const loading = ref(false);
const rows = ref([]);
const showCrossBanner = ref(false);

function clinicName(id) {
  if (id === "C001") return "沙河口院区";
  if (id === "C002") return "甘井子院区";
  return "高新园区";
}

async function writeAudit(actionClinic) {
  await http.post("/tasks/coordination/audit", {
    action: "跨院区病历访问",
    target_type: "medical_records",
    target_id: actionClinic,
    clinic_id: actionClinic,
    details: `跨院区病历访问审计：${currentClinic.value} -> ${actionClinic}`
  });
}

async function changeClinic(nextClinic) {
  if (nextClinic !== currentClinic.value) {
    try {
      await ElMessageBox.confirm(
        `您即将访问[${clinicName(nextClinic)}]的病历数据，此操作将被记录在审计日志中，是否继续？`,
        "跨院区授权确认",
        { type: "warning", confirmButtonText: "继续访问", cancelButtonText: "取消" }
      );
      await writeAudit(nextClinic);
      showCrossBanner.value = true;
      await loadData();
    } catch {
      clinic.value = currentClinic.value;
    }
    return;
  }
  showCrossBanner.value = false;
  await loadData();
}

async function loadData() {
  loading.value = true;
  try {
    const res = await getMedicalRecords({ page: 1, size: 100, clinic_id: clinic.value });
    rows.value = res.data || [];
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "病历加载失败"));
  } finally {
    loading.value = false;
  }
}

onMounted(async () => {
  try {
    const me = await http.get("/auth/me");
    currentClinic.value = me.data?.clinic_id || "C001";
    clinic.value = currentClinic.value;
    await loadData();
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "初始化失败"));
  }
});
</script>

<style scoped>
.page { padding: 16px; }
.glass-card { border-radius: 20px; }
.header-row { display: flex; justify-content: space-between; align-items: center; }
</style>

