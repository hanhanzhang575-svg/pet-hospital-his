<template>
  <div class="medical-record-page">
    <!-- 病历封面 -->
    <div class="record-header">
      <div class="hospital-name">白之助宠物医院</div>
      <div class="record-title">电子病历</div>
      <el-divider />
      <el-row :gutter="20">
        <el-col :xs="24" :sm="12">
          <div class="header-item">
            <span class="label">病历号：</span>
            <span class="value">{{ record.record_no }}</span>
          </div>
          <div class="header-item">
            <span class="label">宠物姓名：</span>
            <span class="value">{{ petInfo.name }}</span>
          </div>
          <div class="header-item">
            <span class="label">物种/品种：</span>
            <span class="value">{{ petInfo.species }}/{{ petInfo.breed }}</span>
          </div>
        </el-col>
        <el-col :xs="24" :sm="12">
          <div class="header-item">
            <span class="label">就诊时间：</span>
            <span class="value">{{ formatDate(record.created_at) }}</span>
          </div>
          <div class="header-item">
            <span class="label">主人：</span>
            <span class="value">{{ ownerInfo.name }}</span>
          </div>
          <div class="header-item">
            <span class="label">联系电话：</span>
            <span class="value">{{ ownerInfo.phone }}</span>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 操作栏 -->
    <div class="toolbar">
      <el-space>
        <el-tag :type="isLatest ? 'danger' : 'info'">{{ isLatest ? '可编辑' : '只读' }}</el-tag>
        <el-button v-if="isLatest && !editMode" type="primary" @click="editMode = true">编辑</el-button>
        <el-button v-if="editMode" type="success" @click="saveChanges" :loading="saving">保存</el-button>
        <el-button v-if="editMode" @click="cancelEdit">取消</el-button>
        <el-button @click="printRecord">打印</el-button>
        <el-button @click="goBack">返回</el-button>
      </el-space>
    </div>

    <!-- 主诉和现病史 -->
    <el-card class="record-section">
      <template #header>
        <span>
          <el-icon><Document /></el-icon>
          主诉与现病史
        </span>
      </template>
      <el-form :model="editForm" label-width="100px" v-if="editMode">
        <el-form-item label="主诉">
          <el-input v-model="editForm.chief_complaint" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <div v-else class="field-display">
        <strong>主诉：</strong>
        <p>{{ record.chief_complaint || '——' }}</p>
      </div>
    </el-card>

    <!-- 体格检查 -->
    <el-card class="record-section">
      <template #header>
        <span>
          <el-icon><Check /></el-icon>
          体格检查
        </span>
      </template>
      <el-form :model="editForm" label-width="100px" v-if="editMode">
        <el-form-item label="检查记录">
          <el-input v-model="editForm.exam_notes" type="textarea" :rows="4" />
        </el-form-item>
      </el-form>
      <div v-else class="field-display">
        <strong>检查记录：</strong>
        <p>{{ record.exam_notes || '——' }}</p>
      </div>
    </el-card>

    <!-- 诊断 -->
    <el-card class="record-section">
      <template #header>
        <span>
          <el-icon><CircleCheck /></el-icon>
          诊断
        </span>
      </template>
      <el-form :model="editForm" label-width="100px" v-if="editMode">
        <el-form-item label="诊断结论">
          <el-input v-model="editForm.diagnosis" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <div v-else class="field-display">
        <strong>诊断：</strong>
        <el-tag type="warning" effect="light" style="margin: 8px 0">
          {{ record.diagnosis || '待补充' }}
        </el-tag>
      </div>
    </el-card>

    <el-card class="record-section">
      <template #header>
        <span>
          <el-icon><Document /></el-icon>
          诊疗计划（Plan）
        </span>
      </template>
      <el-form :model="editForm" label-width="100px" v-if="editMode">
        <el-form-item label="计划">
          <el-input v-model="editForm.treatment_plan" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <div v-else class="field-display">
        <strong>计划：</strong>
        <p>{{ record.treatment_plan || '——' }}</p>
      </div>
    </el-card>

    <!-- 处方信息 -->
    <el-card class="record-section">
      <template #header>
        <span>
          <el-icon><Document /></el-icon>
          处方信息
        </span>
      </template>
      <el-table :data="prescriptions" border stripe>
        <el-table-column prop="prescription_code" label="处方号" width="120" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="开具时间" width="180" :formatter="dateFormatter" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="viewPrescription(row)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="prescriptions.length === 0" description="暂无处方记录" />
    </el-card>

    <!-- 住院信息 -->
    <el-card class="record-section">
      <template #header>
        <span>
          <el-icon><DArrowRight /></el-icon>
          住院信息
        </span>
      </template>
      <el-table :data="inpatientRecords" border stripe>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="inpatientStatusType(row.status)">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="admission_time" label="入院时间" width="180" :formatter="dateFormatter" />
        <el-table-column prop="discharge_time" label="出院时间" width="180" :formatter="dateFormatter" />
        <el-table-column prop="deposit_amount" label="押金" width="100">
          <template #default="{ row }">¥{{ row.deposit_amount }}</template>
        </el-table-column>
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="viewInpatient(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="inpatientRecords.length === 0" description="暂无住院记录" />
    </el-card>

    <!-- 医生签名 -->
    <div class="signature-section">
      <div class="signature-item">
        <label>就诊医生：</label>
        <span>{{ doctorName }}</span>
      </div>
      <div class="signature-item">
        <label>记录时间：</label>
        <span>{{ formatDate(record.created_at) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { Document, Check, CircleCheck, DArrowRight } from "@element-plus/icons-vue";
import { getMedicalRecord, updateMedicalRecord } from "../api/medicalRecords";
import http from "../api/http";
import { getErrorMessage } from "../utils/status";

const route = useRoute();
const router = useRouter();
const recordId = route.params.id;

const record = ref({});
const petInfo = ref({});
const ownerInfo = ref({});
const doctorName = ref("");
const prescriptions = ref([]);
const inpatientRecords = ref([]);

const editMode = ref(false);
const saving = ref(false);
const editForm = ref({
  chief_complaint: "",
  exam_notes: "",
  diagnosis: "",
  treatment_plan: ""
});

const isLatest = computed(() => {
  return true;
});

onMounted(async () => {
  await loadRecordDetail();
});

async function loadRecordDetail() {
  try {
    const res = await getMedicalRecord(recordId);
    if (res.code === 200 && res.data) {
      record.value = res.data;
      editForm.value = {
        chief_complaint: res.data.chief_complaint || "",
        exam_notes: res.data.exam_notes || "",
        diagnosis: res.data.diagnosis || "",
        treatment_plan: res.data.treatment_plan || ""
      };
      
      await Promise.all([
        loadPetInfo(res.data.pet_id),
        loadDoctorInfo(res.data.vet_id),
        loadRelatedData(res.data.id)
      ]);
    }
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "病历加载失败"));
  }
}

async function loadPetInfo(petId) {
  try {
    const res = await http.get(`/pets/${petId}`);
    if (res.code === 200 && res.data) {
      petInfo.value = res.data;
      if (res.data.owner_id) {
        const ownerRes = await http.get(`/owners/${res.data.owner_id}`);
        if (ownerRes.code === 200) {
          ownerInfo.value = ownerRes.data;
        }
      }
    }
  } catch (error) {
    console.error("Failed to load pet info:", error);
  }
}

async function loadDoctorInfo(doctorId) {
  try {
    const res = await http.get(`/users/${doctorId}`);
    if (res.code === 200) {
      doctorName.value = res.data.full_name || "未知医生";
    }
  } catch (error) {
    console.error("Failed to load doctor info:", error);
  }
}

async function loadRelatedData(recordId) {
  try {
    const presRes = await http.get(`/prescriptions?medical_record_id=${recordId}`);
    if (presRes.code === 200) {
      prescriptions.value = Array.isArray(presRes.data) ? presRes.data : [];
    }
    
    const inpatRes = await http.get(`/inpatient-records?medical_record_id=${recordId}`);
    if (inpatRes.code === 200) {
      inpatientRecords.value = Array.isArray(inpatRes.data) ? inpatRes.data : [];
    }
  } catch (error) {
    console.error("Failed to load related data:", error);
  }
}

async function saveChanges() {
  saving.value = true;
  try {
    await updateMedicalRecord(recordId, {
      chief_complaint: editForm.value.chief_complaint,
      exam_notes: editForm.value.exam_notes,
      diagnosis: editForm.value.diagnosis,
      treatment_plan: editForm.value.treatment_plan
    });
    record.value.chief_complaint = editForm.value.chief_complaint;
    record.value.exam_notes = editForm.value.exam_notes;
    record.value.diagnosis = editForm.value.diagnosis;
    record.value.treatment_plan = editForm.value.treatment_plan;
    editMode.value = false;
    ElMessage.success("病历已保存");
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "保存失败"));
  } finally {
    saving.value = false;
  }
}

function cancelEdit() {
  editForm.value = {
    chief_complaint: record.value.chief_complaint || "",
    exam_notes: record.value.exam_notes || "",
    diagnosis: record.value.diagnosis || "",
    treatment_plan: record.value.treatment_plan || ""
  };
  editMode.value = false;
}

function formatDate(dateStr) {
  if (!dateStr) return "——";
  const date = new Date(dateStr);
  return date.toLocaleDateString("zh-CN") + " " + date.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
}

function dateFormatter(row) {
  return formatDate(row.created_at || row.admission_time || row.discharge_time);
}

function statusType(status) {
  const map = { "待缴费": "warning", "已缴费": "success", "已发药": "info", "已失效": "danger" };
  return map[status] || "info";
}

function inpatientStatusType(status) {
  const map = { "待入院": "warning", "住院观察": "info", "术后监护": "danger", "待出院": "success", "已出院": "success" };
  return map[status] || "info";
}

function viewPrescription(row) {
  router.push({ name: "prescription-create", query: { medicalRecordId: String(record.value.id || row.medical_record_id || "") } });
}

function viewInpatient(row) {
  router.push({ name: "inpatient", query: { recordId: String(row.id || "") } });
}

function printRecord() {
  window.print();
}

function goBack() {
  router.back();
}
</script>

<style scoped>
.medical-record-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px;
  background: #fff;
}

.record-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 30px;
  border-radius: 8px 8px 0 0;
  text-align: center;
  margin-bottom: 20px;
}

.hospital-name {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 10px;
}

.record-title {
  font-size: 32px;
  font-weight: bold;
  margin-bottom: 20px;
  letter-spacing: 4px;
}

.header-item {
  line-height: 2;
  text-align: left;
}

.header-item .label {
  font-weight: bold;
  min-width: 80px;
  display: inline-block;
}

.header-item .value {
  color: #fff;
  font-size: 14px;
}

.toolbar {
  background: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  margin-bottom: 20px;
  border-left: 4px solid #667eea;
}

.record-section {
  margin-bottom: 20px;
}

:deep(.record-section .el-card__header) {
  background: #f5f7fa;
  border-bottom: 2px solid #667eea;
  font-weight: bold;
}

.field-display {
  padding: 10px 0;
  line-height: 1.8;
}

.field-display strong {
  color: #333;
  margin-right: 10px;
}

.field-display p {
  margin: 8px 0;
  color: #606266;
  padding: 10px;
  background: #f9f9f9;
  border-left: 3px solid #667eea;
  border-radius: 2px;
}

.signature-section {
  margin-top: 40px;
  padding: 30px;
  border-top: 2px dashed #ddd;
  text-align: right;
}

.signature-item {
  margin-bottom: 20px;
  font-size: 14px;
}

.signature-item label {
  font-weight: bold;
  margin-right: 20px;
  min-width: 80px;
  display: inline-block;
  text-align: left;
}

@media print {
  .toolbar {
    display: none;
  }
  .medical-record-page {
    margin: 0;
    padding: 0;
  }
}
</style>
