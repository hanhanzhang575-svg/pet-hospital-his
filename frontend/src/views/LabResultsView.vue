<template>
  <div class="lab-result-page">
    <el-card class="panel-card">
      <template #header>
        <div class="header-row">
          <span>{{ embedded ? '录入检验结果' : '检验报告库' }}</span>
          <el-space v-if="!embedded">
            <el-date-picker v-model="filters.date_range" type="daterange" value-format="YYYY-MM-DD" />
            <el-input v-model="filters.pet_name" placeholder="按宠物筛选" style="width: 180px" />
            <el-select v-model="filters.exam_type" placeholder="检验类型" style="width: 180px" clearable>
              <el-option label="血常规" value="blood_routine" />
              <el-option label="生化全套" value="biochemistry" />
              <el-option label="尿常规" value="urinalysis" />
              <el-option label="X光" value="xray" />
              <el-option label="B超" value="ultrasound" />
            </el-select>
            <el-button @click="loadHistory">筛选</el-button>
          </el-space>
        </div>
      </template>

      <template v-if="currentOrder">
        <el-row :gutter="12" class="mb12">
          <el-col :xs="24" :lg="16">
            <el-card class="sub-card" shadow="never">
              <template #header>患宠信息</template>
              <el-descriptions border :column="2" size="small">
                <el-descriptions-item label="宠物">{{ currentOrder.pet_name || '-' }}</el-descriptions-item>
                <el-descriptions-item label="物种">{{ currentOrder.pet_species || '-' }}</el-descriptions-item>
                <el-descriptions-item label="品种">{{ currentOrder.pet_breed || '-' }}</el-descriptions-item>
                <el-descriptions-item label="年龄">{{ currentOrder.pet_age_years || '-' }} 岁</el-descriptions-item>
                <el-descriptions-item label="体重">{{ currentOrder.pet_weight || '-' }} kg</el-descriptions-item>
                <el-descriptions-item label="申请医生">{{ currentOrder.requesting_doctor || '-' }}</el-descriptions-item>
                <el-descriptions-item label="主诉" :span="2">{{ currentOrder.chief_complaint || '无' }}</el-descriptions-item>
              </el-descriptions>
            </el-card>
          </el-col>
          <el-col :xs="24" :lg="8">
            <el-card class="sub-card" shadow="never">
              <template #header>实时判定</template>
              <div class="metric-box">
                <div>异常指标: <b>{{ abnormalMetricCount }}</b></div>
                <div>危急指标: <b class="danger">{{ criticalMetricCount }}</b></div>
                <div>异常占比: <b>{{ abnormalRatio }}</b></div>
              </div>
              <el-alert
                v-if="criticalMetricCount > 0"
                type="error"
                :closable="false"
                show-icon
                title="存在危急值，提交后将触发医生端高优先通知"
                style="margin-top: 10px"
              />
            </el-card>
          </el-col>
        </el-row>

        <el-tabs v-model="tab">
          <el-tab-pane label="生化录入" name="bio">
            <el-select v-model="examType" style="width: 220px; margin-bottom: 10px">
              <el-option label="血常规" value="blood_routine" />
              <el-option label="生化全套" value="biochemistry" />
              <el-option label="尿常规" value="urinalysis" />
              <el-option label="X光" value="xray" />
              <el-option label="B超" value="ultrasound" />
            </el-select>

            <el-table :data="metricRows" border>
              <el-table-column prop="metric" label="指标" width="170" />
              <el-table-column label="输入值" width="180">
                <template #default="{ row }">
                  <el-input-number v-model="structuredData[row.metric]" :step="0.1" controls-position="right" style="width: 150px" />
                </template>
              </el-table-column>
              <el-table-column prop="rangeText" label="参考范围" width="220" />
              <el-table-column label="判定" min-width="180">
                <template #default="{ row }">
                  <el-tag v-if="row.level === 'critical'" type="danger">危急值</el-tag>
                  <el-tag v-else-if="row.level === 'high' || row.level === 'low'" type="warning">异常</el-tag>
                  <el-tag v-else type="success">正常</el-tag>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>

          <el-tab-pane label="影像上传" name="img">
            <el-upload drag multiple action="#" :auto-upload="false" :on-change="onImageChange">
              <div>拖拽或点击上传影像（X光 / B超 / 皮肤）</div>
            </el-upload>
            <div class="img-grid">
              <div v-for="(img, i) in imageFiles" :key="`${img.name}-${i}`" class="img-item">
                <div class="img-name">{{ img.name }}</div>
                <el-select v-model="img.type" size="small" style="width: 140px">
                  <el-option label="X光片" value="xray" />
                  <el-option label="B超图像" value="ultrasound" />
                  <el-option label="皮肤照片" value="skin" />
                  <el-option label="其他" value="other" />
                </el-select>
                <el-tag type="success" size="small">已纳入 AI 分析</el-tag>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>

        <div class="actions">
          <el-button @click="saveDraft">保存草稿</el-button>
          <el-button type="success" :loading="submitting" @click="submitReport">提交检验报告</el-button>
        </div>
      </template>

      <el-row v-else :gutter="12">
        <el-col :xs="24" :lg="10">
          <el-card class="sub-card" shadow="never">
            <template #header>已完成检验</template>
            <el-empty v-if="historyRows.length === 0" description="暂无数据" />
            <el-table v-else :data="historyRows" border @row-click="selectHistory" height="520">
              <el-table-column prop="record_code" label="诊单号" width="130" />
              <el-table-column prop="pet_name" label="宠物" min-width="110" />
              <el-table-column prop="exam_type" label="类型" width="120" />
              <el-table-column prop="completed_at" label="完成时间" min-width="150" />
            </el-table>
          </el-card>
        </el-col>

        <el-col :xs="24" :lg="14">
          <el-card class="sub-card" shadow="never">
            <template #header>报告详情</template>
            <el-empty v-if="!selectedHistory" description="请从左侧选择一条记录" />
            <template v-else>
              <el-descriptions border :column="2" size="small" class="mb12">
                <el-descriptions-item label="宠物">{{ selectedHistory.pet_name }}</el-descriptions-item>
                <el-descriptions-item label="物种">{{ selectedHistory.pet_species }}</el-descriptions-item>
                <el-descriptions-item label="检验类型">{{ selectedHistory.exam_type }}</el-descriptions-item>
                <el-descriptions-item label="申请医生">{{ selectedHistory.requesting_doctor }}</el-descriptions-item>
              </el-descriptions>
              <el-table :data="historyMetricRows" border>
                <el-table-column prop="metric" label="指标" width="160" />
                <el-table-column prop="value" label="结果" width="120" />
                <el-table-column label="判定" width="120">
                  <template #default="{ row }">
                    <el-tag v-if="row.level === 'critical'" type="danger">危急</el-tag>
                    <el-tag v-else-if="row.level === 'high' || row.level === 'low'" type="warning">异常</el-tag>
                    <el-tag v-else type="success">正常</el-tag>
                  </template>
                </el-table-column>
              </el-table>

              <div class="gallery">
                <div v-for="(img, i) in selectedHistory.image_files || []" :key="i" class="gallery-item">
                  <el-image :src="img.url || img" fit="cover" :preview-src-list="(selectedHistory.image_files || []).map((x) => x.url || x)" />
                </div>
              </div>
            </template>
          </el-card>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { useRoute } from "vue-router";
import { fetchLabResults, submitLabResult } from "../api/lab";
import { useAuthStore } from "../store";
import { getErrorMessage } from "../utils/status";

const props = defineProps({
  embedded: { type: Boolean, default: false },
  defaultOrder: { type: Object, default: null }
});

const emit = defineEmits(["submitted"]);
const route = useRoute();
const authStore = useAuthStore();

const tab = ref("bio");
const submitting = ref(false);
const examType = ref("blood_routine");
const structuredData = ref({});
const imageFiles = ref([]);
const currentOrder = ref(null);
const historyRows = ref([]);
const selectedHistory = ref(null);
const demoHistoryRows = [
  {
    id: "demo-r-1",
    appointment_id: 9001,
    record_code: "DEMO-REPORT-001",
    pet_name: "泡芙",
    pet_species: "犬",
    exam_type: "biochemistry",
    requesting_doctor: "李医生",
    completed_at: "2026-04-15T09:20:00",
    structured_data: { ALT: 132, AST: 55, BUN: 18, Creatinine: 1.2, GLU: 126, TP: 66 },
    image_files: [],
    abnormal_count: 2,
    critical_count: 0
  },
  {
    id: "demo-r-2",
    appointment_id: 9002,
    record_code: "DEMO-REPORT-002",
    pet_name: "芝麻",
    pet_species: "猫",
    exam_type: "blood_routine",
    requesting_doctor: "张医生",
    completed_at: "2026-04-15T10:05:00",
    structured_data: { WBC: 22.1, RBC: 6.3, HGB: 130, HCT: 39, PLT: 280 },
    image_files: [],
    abnormal_count: 2,
    critical_count: 1
  }
];

const filters = ref({ date_range: null, pet_name: route.query.pet || "", exam_type: "" });

const metricDefs = {
  blood_routine: {
    WBC: { 犬: [6, 17], 猫: [5.5, 19.5], 其他: [0, 9999] },
    RBC: { 犬: [5.5, 8.5], 猫: [5, 10], 其他: [0, 9999] },
    HGB: { 犬: [120, 180], 猫: [80, 150], 其他: [0, 9999] },
    HCT: { 犬: [37, 55], 猫: [24, 45], 其他: [0, 9999] },
    PLT: { 犬: [200, 500], 猫: [300, 700], 其他: [0, 9999] }
  },
  biochemistry: {
    ALT: { 犬: [10, 100], 猫: [10, 100], 其他: [0, 9999] },
    AST: { 犬: [10, 50], 猫: [10, 50], 其他: [0, 9999] },
    BUN: { 犬: [7, 27], 猫: [14, 36], 其他: [0, 9999] },
    Creatinine: { 犬: [0.5, 1.5], 猫: [0.6, 2.4], 其他: [0, 9999] },
    GLU: { 犬: [70, 138], 猫: [64, 170], 其他: [0, 9999] },
    TP: { 犬: [54, 82], 猫: [57, 89], 其他: [0, 9999] }
  }
};

const speciesKey = computed(() => {
  const text = String(currentOrder.value?.pet_species || "");
  if (text.includes("犬")) return "犬";
  if (text.includes("猫")) return "猫";
  return "其他";
});

const metricRows = computed(() => {
  const defs = metricDefs[examType.value] || {};
  return Object.keys(defs).map((metric) => {
    const [min, max] = defs[metric][speciesKey.value] || defs[metric].其他;
    const value = Number(structuredData.value[metric]);
    let level = "normal";
    if (Number.isFinite(value)) {
      if (value < min / 2 || value > max * 2) level = "critical";
      else if (value < min) level = "low";
      else if (value > max) level = "high";
    }
    return { metric, rangeText: `${min}-${max}`, value, level };
  });
});

const abnormalMetricCount = computed(() => metricRows.value.filter((x) => x.level === "high" || x.level === "low" || x.level === "critical").length);
const criticalMetricCount = computed(() => metricRows.value.filter((x) => x.level === "critical").length);
const abnormalRatio = computed(() => `${((abnormalMetricCount.value / Math.max(metricRows.value.length, 1)) * 100).toFixed(1)}%`);

const historyMetricRows = computed(() => {
  const data = selectedHistory.value?.structured_data || {};
  const type = selectedHistory.value?.exam_type || "biochemistry";
  const defs = metricDefs[type] || {};
  const spText = String(selectedHistory.value?.pet_species || "");
  const sp = spText.includes("犬") ? "犬" : spText.includes("猫") ? "猫" : "其他";

  return Object.keys(data).map((metric) => {
    const value = Number(data[metric]);
    const [min, max] = defs[metric]?.[sp] || defs[metric]?.其他 || [0, 9999];
    let level = "normal";
    if (value < min / 2 || value > max * 2) level = "critical";
    else if (value < min) level = "low";
    else if (value > max) level = "high";
    return { metric, value, level };
  });
});

async function loadHistory() {
  const params = { clinic_id: authStore.clinicId || undefined };
  if (filters.value.pet_name) params.pet_name = filters.value.pet_name;
  if (filters.value.exam_type) params.exam_type = filters.value.exam_type;
  if (filters.value.date_range?.[0]) params.date_from = filters.value.date_range[0];
  if (filters.value.date_range?.[1]) params.date_to = filters.value.date_range[1];

  const res = await fetchLabResults(params);
  historyRows.value = (res.data && res.data.length) ? res.data : demoHistoryRows;
  if (historyRows.value.length && !selectedHistory.value) selectedHistory.value = historyRows.value[0];
}

function selectHistory(row) {
  selectedHistory.value = row;
}

function onImageChange(file) {
  imageFiles.value.push({ name: file.name, type: "xray", url: file.url || file.name });
}

function saveDraft() {
  const key = `lab_draft_${currentOrder.value?.appointment_id || "default"}`;
  window.sessionStorage.setItem(
    key,
    JSON.stringify({ examType: examType.value, structuredData: structuredData.value, imageFiles: imageFiles.value })
  );
  ElMessage.success("草稿已保存");
}

async function submitReport() {
  const hasMetric = Object.values(structuredData.value || {}).some((v) => v !== null && v !== undefined && String(v) !== "");
  if (!hasMetric && imageFiles.value.length === 0) {
    ElMessage.warning("请至少填写一个指标或上传一张图像");
    return;
  }

  if (criticalMetricCount.value > 0) {
    try {
      await ElMessageBox.confirm("检测到危急值，提交后将触发医生端高优先提醒，确认提交？", "危急值确认", {
        confirmButtonText: "确认",
        cancelButtonText: "取消",
        type: "warning"
      });
    } catch {
      return;
    }
  }

  submitting.value = true;
  try {
    await submitLabResult({
      appointment_id: Number(currentOrder.value?.appointment_id || 0),
      exam_type: examType.value,
      structured_data: structuredData.value,
      image_files: imageFiles.value.map((item) => item.url || item.name),
      notes: ""
    });

    ElMessage.success("报告提交成功");
    emit("submitted");

    if (!props.embedded) {
      currentOrder.value = null;
      structuredData.value = {};
      imageFiles.value = [];
      await loadHistory();
    }
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "提交报告失败"));
  } finally {
    submitting.value = false;
  }
}

onMounted(async () => {
  if (props.defaultOrder) {
    currentOrder.value = props.defaultOrder;
  } else {
    await loadHistory();
  }
});

watch(
  () => props.defaultOrder,
  (value) => {
    if (value) {
      currentOrder.value = value;
      structuredData.value = {};
      imageFiles.value = [];
    }
  }
);
</script>

<style scoped>
.lab-result-page {
  padding: 12px;
}
.panel-card,
.sub-card {
  border-radius: 12px;
}
.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}
.mb12 { margin-bottom: 12px; }
.metric-box {
  display: grid;
  gap: 8px;
  color: #334155;
}
.danger { color: #ef4444; }
.img-grid {
  margin-top: 12px;
  display: grid;
  gap: 8px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}
.img-item {
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 8px;
  display: grid;
  gap: 6px;
}
.img-name {
  font-size: 12px;
  color: #334155;
}
.actions {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
.gallery {
  margin-top: 12px;
  display: grid;
  gap: 8px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}
.gallery-item {
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  overflow: hidden;
  padding: 6px;
}
@media (max-width: 900px) {
  .header-row {
    flex-direction: column;
    align-items: flex-start;
  }
  .img-grid,
  .gallery {
    grid-template-columns: 1fr;
  }
}
</style>

