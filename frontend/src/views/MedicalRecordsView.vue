<template>
  <div class="page">
    <el-card>
      <template #header>
        <div class="header-row">
          <span>电子病历库</span>
          <el-button :loading="loading" @click="loadRecords">刷新</el-button>
        </div>
      </template>

      <!-- 筛选工具栏 -->
      <el-form :model="filters" label-width="80px" style="margin-bottom: 20px">
        <el-row :gutter="20">
          <el-col :xs="24" :sm="12" :md="6">
            <el-form-item label="宠物">
              <el-select v-model="filters.pet_id" clearable placeholder="选择宠物">
                <el-option v-for="pet in petList" :key="pet.id" :label="pet.name" :value="pet.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <el-form-item label="医生">
              <el-select v-model="filters.vet_id" clearable placeholder="选择医生">
                <el-option v-for="vet in vetList" :key="vet.id" :label="vet.full_name" :value="vet.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <el-form-item label="就诊时间">
              <el-date-picker v-model="filters.date_range" type="daterange" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <el-space>
              <el-button type="primary" @click="searchRecords">搜索</el-button>
              <el-button @click="resetFilters">重置</el-button>
            </el-space>
          </el-col>
        </el-row>
      </el-form>

      <!-- 病历列表 -->
        <el-empty v-if="!loading && records.length === 0" description="暂无病历记录" />
        <el-table v-else :data="records" border stripe v-loading="loading" :row-class-name="rowClassName">
        <el-table-column prop="record_no" label="病历号" width="140" />
        <el-table-column label="宠物信息" width="180">
          <template #default="{ row }">
            <div>
                <el-link type="primary" @click="openPetTimeline(row)">{{ row.pet_name }}</el-link>
                <el-text type="info" size="small">{{ row.pet_species }}/{{ row.pet_breed }}</el-text>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="主人信息" width="160">
          <template #default="{ row }">
            <div>
              <div>{{ row.owner_name }}</div>
              <el-text type="info" size="small">{{ row.owner_phone }}</el-text>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="就诊医生" width="120">
          <template #default="{ row }">
            {{ row.vet_name }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="就诊时间" width="180" :formatter="formatDate" />
        <el-table-column label="主诉" width="150">
          <template #default="{ row }">
            <el-text truncated>{{ row.chief_complaint || "——" }}</el-text>
          </template>
        </el-table-column>
        <el-table-column label="诊断" width="150">
          <template #default="{ row }">
            <el-tag v-if="row.diagnosis" type="warning" effect="light">{{ row.diagnosis }}</el-tag>
            <el-text v-else type="info">待补充</el-text>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag v-if="row.is_voided" type="info">已作废</el-tag>
            <el-tag v-else type="success">有效</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-space :size="20">
              <el-button link type="primary" size="small" @click="viewDetail(row)">查看</el-button>
              <el-button v-if="isLatest(row) && !row.is_voided" link type="success" size="small" @click="editRecord(row)">编辑</el-button>
              <el-dropdown trigger="click" @command="(cmd) => handleRowCommand(cmd, row)">
                <el-button link type="info" size="small">更多</el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="void" :disabled="row.is_voided">作废</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </el-space>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.size"
        :page-sizes="[10, 20, 50]"
        :total="pagination.total"
        layout="total, sizes, prev, pager, next, jumper"
        style="margin-top: 20px; text-align: right"
        @change="loadRecords"
      />
      <div class="list-meta">共{{ records.length }}条记录，最后更新时间 {{ lastUpdated || "--:--" }}</div>
    </el-card>

    <el-drawer v-model="timelineVisible" size="500px" title="电子病历全景时间轴">
      <template v-if="petProfile">
        <el-card class="glass-card" style="margin-bottom: 12px">
          <div><strong>{{ petProfile.name }}</strong>（{{ petProfile.species }}/{{ petProfile.breed || "-" }}）</div>
          <div>主人：{{ petProfile.owner_name || "-" }} / {{ petProfile.owner_phone || "-" }}</div>
          <div>毛色：{{ petProfile.color || "-" }}</div>
        </el-card>
      </template>
      <el-empty v-if="timelineLoading" description="时间轴加载中..." />
      <el-empty v-else-if="timelineRows.length === 0" description="暂无历史病历" />
      <el-timeline v-else>
        <el-timeline-item
          v-for="item in timelineRows"
          :key="item.record_id"
          :type="item.is_emergency ? 'danger' : 'primary'"
          :timestamp="formatTimelineDate(item.created_at)"
        >
          <el-card class="glass-card">
            <div style="font-weight:700;">{{ item.record_no }} · {{ item.diagnosis || "待诊断" }}</div>
            <div style="margin:6px 0;">{{ item.chief_complaint || "无主诉" }}</div>
            <div>
              <el-tag v-if="item.is_emergency" type="danger" size="small">急诊</el-tag>
              <el-tag
                v-for="drug in item.drug_tags || []"
                :key="`${item.record_id}-${drug}`"
                size="small"
                type="warning"
                style="margin-left:4px"
              >
                {{ drug }}
              </el-tag>
              <el-tag size="small" type="info" style="margin-left:4px">住院{{ item.inpatient_days || 0 }}天</el-tag>
            </div>
          </el-card>
        </el-timeline-item>
      </el-timeline>
      <el-card v-if="timelineRows.length > 0" class="glass-card" style="margin-top: 12px">
        <el-row :gutter="12">
          <el-col :span="8"><el-statistic title="总就诊次数" :value="timelineSummary.total_visits" /></el-col>
          <el-col :span="8"><el-statistic title="急诊次数" :value="timelineSummary.emergency_visits" /></el-col>
          <el-col :span="8"><el-statistic title="累计住院天数" :value="timelineSummary.total_inpatient_days" /></el-col>
        </el-row>
        <el-row :gutter="12" style="margin-top: 8px">
          <el-col :span="8"><el-statistic title="处方条目数" :value="timelineSummary.prescription_tags" /></el-col>
          <el-col :span="8"><el-statistic title="最近诊断" :value="timelineSummary.last_diagnosis" /></el-col>
          <el-col :span="8"><el-statistic title="最近就诊" :value="timelineSummary.latest_visit" /></el-col>
        </el-row>
      </el-card>
    </el-drawer>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { getMedicalRecords, voidMedicalRecord } from "../api/medicalRecords";
import { fetchPetHistoryTimeline } from "../api/vetWorkbench";
import http from "../api/http";
import { getErrorMessage } from "../utils/status";

const router = useRouter();

const records = ref([]);
const petList = ref([]);
const vetList = ref([]);
const loading = ref(false);
const lastUpdated = ref("");
const timelineVisible = ref(false);
const timelineLoading = ref(false);
const petProfile = ref(null);
const timelineRows = ref([]);
const timelineSummary = computed(() => {
  const rows = timelineRows.value || [];
  const prescriptionTags = rows.reduce((acc, item) => acc + ((item.drug_tags || []).length || 0), 0);
  const totalInpatientDays = rows.reduce((acc, item) => acc + (Number(item.inpatient_days) || 0), 0);
  const emergencyVisits = rows.filter((item) => Boolean(item.is_emergency)).length;
  const latest = rows[0] || {};
  const latestDate = latest.created_at ? formatTimelineDate(latest.created_at).split(" ")[0] : "--";
  return {
    total_visits: rows.length,
    emergency_visits: emergencyVisits,
    total_inpatient_days: totalInpatientDays,
    prescription_tags: prescriptionTags,
    last_diagnosis: latest.diagnosis || "--",
    latest_visit: latestDate,
  };
});

const filters = ref({
  pet_id: null,
  vet_id: null,
  date_range: null
});

const pagination = ref({
  page: 1,
  size: 10,
  total: 0
});

onMounted(async () => {
  await Promise.all([loadPets(), loadVets(), loadRecords()]);
});

async function loadPets() {
  try {
    const res = await http.get("/pets?limit=1000");
    petList.value = res.data || [];
  } catch (error) {
    console.error("Failed to load pets:", error);
  }
}

async function loadVets() {
  try {
    const res = await http.get("/users?role=doctor&limit=1000");
    vetList.value = res.data || [];
  } catch (error) {
    console.error("Failed to load vets:", error);
  }
}

async function loadRecords() {
  loading.value = true;
  try {
    const params = {
      page: pagination.value.page,
      size: pagination.value.size,
      pet_id: filters.value.pet_id,
      vet_id: filters.value.vet_id
    };
    const res = await getMedicalRecords(params);
    records.value = res.data || [];
    pagination.value.total = res.total || 0;
    lastUpdated.value = new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "病历加载失败"));
  } finally {
    loading.value = false;
  }
}

function searchRecords() {
  pagination.value.page = 1;
  loadRecords();
}

function resetFilters() {
  filters.value = { pet_id: null, vet_id: null, date_range: null };
  pagination.value.page = 1;
  loadRecords();
}

function formatDate(row) {
  if (!row.created_at) return "——";
  const date = new Date(row.created_at);
  return date.toLocaleDateString("zh-CN") + " " + date.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
}

function isLatest(row) {
  // 实际应从后端判断，这里只是示意最新一条
  return row.id === records.value[0]?.id;
}

function viewDetail(row) {
  router.push({ name: "medical-record-detail", params: { id: row.id } });
}

function editRecord(row) {
  router.push({ name: "medical-record-detail", params: { id: row.id, edit: true } });
}

async function voidRecord(row) {
  try {
    const { value } = await ElMessageBox.prompt(
      "请输入作废原因，该操作将被审计日志永久记录",
      "作废病历",
      {
        confirmButtonText: "确认作废",
        cancelButtonText: "取消",
        inputPattern: /^.{2,}$/,
        inputErrorMessage: "作废原因至少2个字",
        type: "warning"
      }
    );
    await ElMessageBox.confirm(`确认作废病历 ${row.record_no}？`, "二次确认", {
      confirmButtonText: "确认",
      cancelButtonText: "取消",
      type: "warning"
    });
    await voidMedicalRecord(row.id, value);
    ElMessage.success("病历已作废");
    loadRecords();
  } catch (error) {
    if (error !== "cancel" && error !== "close") {
      ElMessage.error(getErrorMessage(error, "作废失败"));
    }
  }
}

function handleRowCommand(command, row) {
  if (command === "void") {
    voidRecord(row);
  }
}

function rowClassName({ row }) {
  return row.is_voided ? "void-row" : "";
}

function formatTimelineDate(value) {
  if (!value) return "--";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "--";
  return `${d.toLocaleDateString("zh-CN")} ${d.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" })}`;
}

async function openPetTimeline(row) {
  if (!row?.pet_id) return;
  timelineVisible.value = true;
  timelineLoading.value = true;
  try {
    const res = await fetchPetHistoryTimeline(row.pet_id);
    petProfile.value = res.data?.pet_profile || null;
    timelineRows.value = res.data?.timeline || [];
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "时间轴加载失败"));
    petProfile.value = null;
    timelineRows.value = [];
  } finally {
    timelineLoading.value = false;
  }
}
</script>

<style scoped>
.page {
  padding: 16px;
}
.header-row { display: flex; justify-content: space-between; align-items: center; }
.list-meta { margin-top: 10px; color: #909399; font-size: 12px; }
:deep(.void-row > td) { background: #f8fafc !important; color: #94a3b8 !important; }
</style>
