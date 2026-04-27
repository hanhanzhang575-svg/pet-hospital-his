<template>
  <div class="page">
    <el-card>
      <template #header>
        <div class="header-row">
          <span>住院管理</span>
          <el-space>
            <el-select v-model="clinicFilter" placeholder="选择院区" style="width: 160px" @change="loadAll">
              <el-option label="C001 沙河口" value="C001" />
              <el-option label="C002 甘井子" value="C002" />
              <el-option label="C003 高新园区" value="C003" />
            </el-select>
            <el-switch v-model="emergencyMode" inline-prompt active-text="急诊模式" inactive-text="普通模式" />
            <el-button type="primary" :loading="loading" :disabled="loading" @click="loadAll">刷新</el-button>
            <el-button type="primary" :disabled="loading" @click="openCreateDialog">新建住院</el-button>
          </el-space>
        </div>
      </template>
      <el-breadcrumb separator="/" style="margin-bottom: 10px">
        <el-breadcrumb-item @click="router.push('/home')">首页</el-breadcrumb-item>
        <el-breadcrumb-item>住院管理</el-breadcrumb-item>
      </el-breadcrumb>

      <el-skeleton :loading="loading" :rows="6" animated>
        <template #default>
          <el-table :data="records" border>
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="pet_name" label="宠物" min-width="160" />
            <el-table-column prop="doctor_name" label="医生" min-width="140" />
            <el-table-column prop="clinic_name" label="院区" min-width="120" />
            <el-table-column prop="admission_time" label="入院时间" min-width="170" />
            <el-table-column label="押金余额" width="240">
              <template #default="{ row }">
                <el-tooltip :content="balanceTooltip(row)">
                  <span class="deposit-wrap">
                    <el-text :type="getBalanceType(row)">{{ getBalance(row).toFixed(2) }}</el-text>
                    <span v-if="getBalance(row) <= 0">🔒</span>
                    <span v-else-if="getBalance(row) < 200">🔴</span>
                    <span v-else-if="getBalance(row) <= 500">⚠️</span>
                    <el-tag v-if="getBalance(row) <= 0" type="danger" size="small">已停药</el-tag>
                    <el-badge v-if="getBalance(row) <= 0" value="停药中" type="danger" />
                  </span>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="120">
              <template #default="{ row }">
                <el-tag :type="getStatusTagType(row.status)">{{ mapStatus(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="220">
              <template #default="{ row }">
                <el-button size="small" :disabled="loading || getBalance(row) <= 0" @click="openUpdateDialog(row)">更新</el-button>
                <el-button
                  size="small"
                  type="warning"
                  :disabled="loading || row.status === '已出院' || getBalance(row) <= 0"
                  @click="confirmDischarge(row)"
                >
                  出院
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          <div class="list-meta">
            共{{ records.length }}条记录，最后更新时间 {{ lastUpdated || "--:--" }}
          </div>
        </template>
      </el-skeleton>
    </el-card>

    <el-card class="cage-card">
      <template #header>
        <div class="header-row">
          <span>可视化笼舍地图（影院选座风格）</span>
          <el-space>
            <el-icon v-if="refreshingCages" class="spin"><Loading /></el-icon>
            <el-tag style="background:#e8f9ee;color:#2f9f5a;border:none">空闲</el-tag>
            <el-tag style="background:#e8f3ff;color:#3d7edb;border:none">占用</el-tag>
            <el-tag type="info">消毒/故障</el-tag>
          </el-space>
        </div>
      </template>
      <el-skeleton :loading="loadingCages" :rows="4" animated>
        <template #default>
          <div v-for="zone in zoneGroups" :key="zone" class="zone-block">
            <div class="zone-title">{{ zone }}</div>
            <div class="cage-grid">
              <el-tooltip
                v-for="cell in zoneGridMap[zone]"
                :key="cell.index"
                :content="cell.tooltip"
                placement="top"
              >
                <div
                  class="cage-cell"
                  :class="[
                    cell.className,
                    { recommended: recommendedCageId === cell.id, emergency_vip: emergencyMode && zone === 'VIP' && cell.className === 'idle' }
                  ]"
                  @click="onCageClick(cell)"
                >
                  <div class="cage-code">{{ cell.label }}</div>
                  <div class="cage-content" v-if="cell.className === 'busy'">
                    <span class="pet-icon">{{ cell.petSpecies === "猫" ? "🐱" : "🐶" }}</span>
                    <span class="pet-name">{{ cell.petName || `#${cell.petId || '-'}` }}</span>
                  </div>
                  <div class="pet-icon-idle" v-else-if="cell.className === 'idle'">
                    {{ zone === "猫区" ? "🐱" : zone === "犬区" ? "🐶" : "🏥" }}
                  </div>
                  <el-icon v-if="cell.className === 'repair' || cell.className === 'pending_clean'" class="lock-icon"><Lock /></el-icon>
                </div>
              </el-tooltip>
            </div>
          </div>
        </template>
      </el-skeleton>
      <el-text type="info">每30秒自动刷新笼舍状态</el-text>
    </el-card>

    <el-drawer v-model="drawerVisible" title="住院体征监控记录" size="480px">
      <template v-if="drawerRecord">
        <el-descriptions :column="1" border style="margin-bottom: 12px">
          <el-descriptions-item label="宠物名称">{{ drawerRecord.pet_name }}</el-descriptions-item>
          <el-descriptions-item label="物种/品种">{{ drawerRecord.pet_species || "--" }} / {{ drawerRecord.pet_breed || "--" }}</el-descriptions-item>
          <el-descriptions-item label="入住天数">{{ drawerRecord.stay_days || 0 }} 天</el-descriptions-item>
          <el-descriptions-item label="主治医生">{{ drawerRecord.doctor_name || drawerRecord.doctor_id }}</el-descriptions-item>
            <el-descriptions-item label="押金余额">
              <el-tooltip :content="balanceTooltip(drawerRecord)">
                <span class="deposit-wrap">
                  <el-text :type="getBalanceType(drawerRecord)">¥{{ Number(drawerRecord.deposit_balance || 0).toFixed(2) }}</el-text>
                  <span v-if="Number(drawerRecord.deposit_balance || 0) <= 0">🔒</span>
                  <span v-else-if="Number(drawerRecord.deposit_balance || 0) < 200">🔴</span>
                  <span v-else-if="Number(drawerRecord.deposit_balance || 0) <= 500">⚠️</span>
                  <el-tag v-if="Number(drawerRecord.deposit_balance || 0) <= 0" type="danger" size="small">已停药</el-tag>
                </span>
              </el-tooltip>
            </el-descriptions-item>
        </el-descriptions>
      </template>
      <el-form label-width="120px" style="margin-bottom: 12px">
        <el-form-item label="体温(℃)">
          <el-input-number v-model="vitalForm.temperature" :step="0.1" :class="{ 'abnormal-input': isTempAbnormal }" style="width: 100%" />
          <div v-if="isTempAbnormal" class="warn-text">⚠️ 体温异常！该物种正常范围为{{ speciesTempRange[0] }}-{{ speciesTempRange[1] }}℃</div>
        </el-form-item>
        <el-form-item label="心率(bpm)">
          <el-input-number v-model="vitalForm.heart_rate" :step="1" :class="{ 'abnormal-input': isHrAbnormal }" style="width: 100%" />
          <div v-if="isHrAbnormal" class="warn-text">⚠️ 心率异常！该物种正常范围为{{ speciesHrRange[0] }}-{{ speciesHrRange[1] }}bpm</div>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="vitalForm.notes" type="textarea" :rows="3" placeholder="选填" />
        </el-form-item>
        <el-form-item>
          <el-button class="agile-btn" type="success" :loading="vitalSubmitting" @click="submitVitals">提交体征</el-button>
        </el-form-item>
      </el-form>
      <el-timeline>
        <el-timeline-item
          v-for="item in drawerVitals"
          :key="item.time"
          :timestamp="item.time"
          type="primary"
        >
          <el-card>
            <div>体温：{{ item.temperature }}℃</div>
            <div>心率：{{ item.heartRate }} 次/分</div>
            <div>备注：{{ item.note }}</div>
          </el-card>
        </el-timeline-item>
      </el-timeline>
      <el-empty v-if="drawerVitals.length === 0" description="暂无体征记录" />
    </el-drawer>

    <el-dialog v-model="createVisible" title="办理入院（向导）" width="760px">
      <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-width="120px">
        <el-steps :active="inpatientStep" finish-status="success" align-center style="margin-bottom: 16px">
          <el-step title="基本信息" />
          <el-step title="笼舍与时间" />
          <el-step title="押金确认" />
        </el-steps>
        <div v-show="inpatientStep === 0">
        <el-form-item label="院区" prop="clinic_id">
          <el-select v-model="createForm.clinic_id" placeholder="选择院区" style="width: 100%" @change="loadDoctorsForCreate">
            <el-option label="C001 沙河口" value="C001" />
            <el-option label="C002 甘井子" value="C002" />
            <el-option label="C003 高新园区" value="C003" />
          </el-select>
        </el-form-item>
        <el-form-item label="宠物ID" prop="pet_id">
          <el-input-number v-model="createForm.pet_id" :min="1" :max="999999" style="width: 100%" />
        </el-form-item>
        <el-form-item label="医生" prop="doctor_id">
          <el-select v-model="createForm.doctor_id" placeholder="选择医生" style="width: 100%">
            <el-option v-for="d in doctorOptions" :key="d.id" :label="`${d.full_name}(${d.id})`" :value="d.id" />
          </el-select>
        </el-form-item>
        </div>
        <div v-show="inpatientStep === 1">
        <el-form-item label="优先病区" prop="preferred_zone_type">
          <el-select v-model="createForm.preferred_zone_type" style="width: 100%">
            <el-option label="犬区" value="犬区" />
            <el-option label="猫区" value="猫区" />
            <el-option label="VIP" value="VIP" />
            <el-option label="ICU" value="ICU" />
            <el-option label="隔离" value="隔离" />
          </el-select>
        </el-form-item>
        <el-form-item label="自动推荐笼舍">
          <el-space>
            <el-button :loading="allocating" :disabled="allocating" @click="recommendCage">推荐笼舍</el-button>
            <el-text v-if="recommendedCageCode" type="success">推荐：{{ recommendedCageCode }}</el-text>
            <el-button v-if="recommendedCageId" type="primary" @click="useRecommendedCage">使用推荐</el-button>
          </el-space>
        </el-form-item>
        <el-form-item label="笼舍" prop="cage_id">
          <el-popover
            v-model:visible="cagePickerVisible"
            placement="bottom-start"
            width="520"
            trigger="click"
          >
            <template #reference>
              <el-button class="agile-btn" style="width: 100%">
                {{ selectedCreateCageLabel || "选择笼舍（矩阵视图）" }}
              </el-button>
            </template>
            <div class="picker-groups">
              <div v-for="group in cagePickerGroups" :key="group.zone" class="picker-group">
                <div class="picker-title">{{ group.zone }}</div>
                <div class="picker-grid">
                  <button
                    v-for="c in group.items"
                    :key="c.id"
                    type="button"
                    class="picker-cage glass-card"
                    :class="[`status-${c.status}`]"
                    :disabled="c.status !== 'available'"
                    @click="selectCreateCage(c)"
                  >
                    <span>{{ c.code }}</span>
                    <span v-if="c.status === 'occupied'">🚫</span>
                  </button>
                </div>
              </div>
            </div>
          </el-popover>
        </el-form-item>
        <el-form-item label="入院时间" prop="admission_time">
          <el-date-picker
            v-model="createForm.admission_time"
            type="datetime"
            value-format="YYYY-MM-DDTHH:mm:ss"
            placeholder="选择入院时间"
            style="width: 100%"
            :editable="false"
          />
        </el-form-item>
        </div>
        <div v-show="inpatientStep === 2">
        <el-form-item label="押金" prop="deposit_amount">
          <el-input-number v-model="createForm.deposit_amount" :min="0" :max="50000" :step="100" style="width: 100%" />
        </el-form-item>
        <el-form-item label="已消费" prop="consumed_amount">
          <el-input-number v-model="createForm.consumed_amount" :min="0" :max="50000" :step="50" style="width: 100%" />
        </el-form-item>
        <el-alert type="info" :closable="false" show-icon title="请确认押金与已消费金额后提交办理入院。" />
        </div>
      </el-form>
      <template #footer>
        <el-button :disabled="creating" @click="createVisible = false">取消</el-button>
        <el-button v-if="inpatientStep > 0" :disabled="creating" @click="inpatientStep -= 1">上一步</el-button>
        <el-button v-if="inpatientStep < 2" type="primary" :disabled="creating" @click="nextInpatientStep">下一步</el-button>
        <el-button v-else type="primary" :loading="creating" :disabled="creating" @click="submitCreate">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="updateVisible" title="更新住院记录" width="520px">
      <el-form ref="updateFormRef" :model="updateForm" :rules="updateRules" label-width="110px">
        <el-form-item label="状态" prop="status">
          <el-select v-model="updateForm.status" style="width: 100%">
            <el-option label="住院观察" value="住院观察" />
            <el-option label="术后监护" value="术后监护" />
            <el-option label="待出院" value="待出院" />
            <el-option label="已出院" value="已出院" />
          </el-select>
        </el-form-item>
        <el-form-item label="押金" prop="deposit_amount">
          <el-input-number v-model="updateForm.deposit_amount" :min="0" :max="50000" :step="100" style="width: 100%" />
        </el-form-item>
        <el-form-item label="已消费" prop="consumed_amount">
          <el-input-number v-model="updateForm.consumed_amount" :min="0" :max="50000" :step="50" style="width: 100%" />
        </el-form-item>
        <el-form-item label="出院时间">
          <el-date-picker
            v-model="updateForm.discharge_time"
            type="datetime"
            value-format="YYYY-MM-DDTHH:mm:ss"
            placeholder="选择出院时间"
            style="width: 100%"
            :editable="false"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button :disabled="updating" @click="updateVisible = false">取消</el-button>
        <el-button type="primary" :loading="updating" :disabled="updating" @click="submitUpdate">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { Loading, Lock } from "@element-plus/icons-vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../store";

import { fetchDoctors } from "../api/users";
import { allocateCage, createInpatientRecord, fetchCages, fetchInpatientRecords, updateInpatientRecord } from "../api/inpatient";
import { fetchPets } from "../api/pets";
import { createVitalSigns } from "../api/nursing";
import { getErrorMessage, getStatusTagType } from "../utils/status";

const clinicFilter = ref("C001");
const router = useRouter();
const authStore = useAuthStore();
const loading = ref(false);
const loadingCages = ref(false);
const refreshingCages = ref(false);
const lastUpdated = ref("");
const creating = ref(false);
const updating = ref(false);
const allocating = ref(false);
const records = ref([]);
const cages = ref([]);
const pets = ref([]);
const doctorOptions = ref([]);
const createVisible = ref(false);
const updateVisible = ref(false);
const editingRecordId = ref(null);
const createFormRef = ref(null);
const updateFormRef = ref(null);
const emergencyMode = ref(false);
const recommendedCageId = ref(null);
const recommendedCageCode = ref("");
const drawerVisible = ref(false);
const drawerVitals = ref([]);
const drawerRecord = ref(null);
const cagePickerVisible = ref(false);
const vitalSubmitting = ref(false);
const inpatientStep = ref(0);
let cageTimer = null;

const zoneGroups = ["犬区", "猫区", "VIP", "ICU", "隔离"];

const createForm = ref({
  pet_id: 1,
  cage_id: null,
  doctor_id: null,
  clinic_id: "C001",
  preferred_zone_type: "犬区",
  admission_time: "",
  deposit_amount: 1000,
  consumed_amount: 0,
  status: "待入院"
});

const updateForm = ref({
  status: "住院观察",
  deposit_amount: 1000,
  consumed_amount: 0,
  discharge_time: ""
});

const createRules = {
  pet_id: [{ required: true, message: "请填写宠物ID", trigger: "blur" }],
  doctor_id: [{ required: true, message: "请选择医生", trigger: "change" }],
  clinic_id: [{ required: true, message: "请选择院区", trigger: "change" }],
  admission_time: [{ required: true, message: "请选择入院时间", trigger: "change" }],
  cage_id: [{ required: true, message: "请选择笼舍", trigger: "change" }]
};

const updateRules = {
  status: [{ required: true, message: "请选择状态", trigger: "change" }]
};

const cageGrid = computed(() => {
  return (cages.value || []).slice(0, 72).map((item, idx) => {
    const status = item.status || "空闲";
    let className = "idle";
    if (["住院中", "待入院", "住院观察", "术后监护"].includes(status)) className = "busy";
    if (status === "待清洁") className = "pending_clean";
    if (status === "维修") className = "repair";
    if (status === "临时启用") className = "temp";
    const record = records.value.find((r) => r.cage_id === item.id);
    const pet = pets.value.find((p) => p.id === record?.pet_id);
    const doctor = doctorOptions.value.find((d) => d.id === record?.doctor_id);
    const days = record?.admission_time
      ? Math.max(1, Math.floor((Date.now() - new Date(record.admission_time).getTime()) / 86400000))
      : 0;
    return {
      id: item.id,
      index: idx + 1,
      zone: item.zone_type,
      label: item.cage_code,
      petId: record?.pet_id || null,
      petName: record?.pet_name || "",
      petSpecies: pet?.species || "",
      className,
      tooltip: `状态：${status} | 宠物：${record?.pet_name || record?.pet_id || "-"} | 入住天数：${days || "-"} | 主治医生：${record?.doctor_name || doctor?.full_name || record?.doctor_id || "-"}` 
    };
  });
});

const cagePickerList = ref([
  { id: "C-01", code: "C-01", zone: "猫病房区", status: "available" },
  { id: "C-02", code: "C-02", zone: "猫病房区", status: "occupied" },
  { id: "C-03", code: "C-03", zone: "猫病房区", status: "cleaning" },
  { id: "C-04", code: "C-04", zone: "猫病房区", status: "available" },
  { id: "D-01", code: "D-01", zone: "犬病房区", status: "available" },
  { id: "D-02", code: "D-02", zone: "犬病房区", status: "occupied" },
  { id: "D-03", code: "D-03", zone: "犬病房区", status: "cleaning" },
  { id: "D-04", code: "D-04", zone: "犬病房区", status: "available" }
]);

const cagePickerGroups = computed(() => {
  const groups = [
    { zone: "猫病房区", items: [] },
    { zone: "犬病房区", items: [] }
  ];
  cagePickerList.value.forEach((item) => {
    const group = groups.find((g) => g.zone === item.zone);
    if (group) group.items.push(item);
  });
  return groups;
});

const selectedCreateCageLabel = computed(() => {
  const selected = cagePickerList.value.find((c) => String(c.id) === String(createForm.value.cage_id));
  if (selected) return `${selected.code}（${selected.zone}）`;
  const dbCage = cages.value.find((c) => String(c.id) === String(createForm.value.cage_id));
  return dbCage ? `${dbCage.cage_code}（${dbCage.zone_type}）` : "";
});

const zoneGridMap = computed(() => {
  const map = {
    犬区: [],
    猫区: [],
    VIP: [],
    ICU: [],
    隔离: []
  };
  cageGrid.value.forEach((cell) => {
    if (map[cell.zone]) map[cell.zone].push(cell);
  });
  return map;
});

const speciesTempRange = computed(() => {
  const species = String(drawerRecord.value?.pet_species || "");
  if (species === "犬") return [38.0, 39.5];
  if (species === "猫") return [38.1, 39.2];
  return [38.0, 40.0];
});
const speciesHrRange = computed(() => {
  const species = String(drawerRecord.value?.pet_species || "");
  if (species === "犬") return [60, 140];
  if (species === "猫") return [120, 240];
  return [60, 220];
});
const vitalForm = ref({ temperature: 38.5, heart_rate: 110, notes: "" });
const isTempAbnormal = computed(() => {
  const val = Number(vitalForm.value.temperature || 0);
  const [min, max] = speciesTempRange.value;
  return val < min || val > max;
});
const isHrAbnormal = computed(() => {
  const val = Number(vitalForm.value.heart_rate || 0);
  const [min, max] = speciesHrRange.value;
  return val < min || val > max;
});

function getBalance(row) {
  if (row && row.deposit_balance !== undefined && row.deposit_balance !== null) {
    return Number(row.deposit_balance || 0);
  }
  return (row.deposit_amount || 0) - (row.consumed_amount || 0);
}

function getBalanceType(row) {
  const balance = getBalance(row);
  if (balance <= 0) return "danger";
  if (balance < 200) return "danger";
  if (balance <= 500) return "warning";
  return "success";
}

function balanceTooltip(row) {
  const b = getBalance(row);
  if (b <= 0) return "押金严重不足，系统已通知前台催缴（停药中）";
  if (b < 200) return "押金严重不足，系统已通知前台催缴";
  if (b <= 500) return "押金预警，系统已通知前台催缴";
  return "押金余额正常";
}

function mapStatus(status) {
  if (status === "待入院") return "🕐待入院";
  if (status === "住院观察") return "🩺住院观察";
  if (status === "已出院") return "✅已出院";
  if (status === "急诊") return "🚨急诊";
  return status;
}

async function loadDoctorsForCreate() {
  try {
    const result = await fetchDoctors(createForm.value.clinic_id);
    doctorOptions.value = result.data || [];
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "医生列表加载失败"));
  }
}

async function loadAll() {
  loading.value = true;
  loadingCages.value = true;
  try {
    const [recordsResult, cagesResult, doctorsResult, petsResult] = await Promise.all([
      fetchInpatientRecords(clinicFilter.value),
      fetchCages(clinicFilter.value),
      fetchDoctors(clinicFilter.value),
      fetchPets()
    ]);
    records.value = recordsResult.data || [];
    cages.value = cagesResult.data || [];
    doctorOptions.value = doctorsResult.data || [];
    pets.value = petsResult.data || [];
    lastUpdated.value = new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "住院数据加载失败"));
  } finally {
    loading.value = false;
    loadingCages.value = false;
  }
}

function openCreateDialog() {
  recommendedCageId.value = null;
  recommendedCageCode.value = "";
  createForm.value = {
    pet_id: 1,
    cage_id: null,
    doctor_id: null,
    clinic_id: clinicFilter.value,
    preferred_zone_type: emergencyMode.value ? "VIP" : "犬区",
    admission_time: "",
    deposit_amount: 1000,
    consumed_amount: 0,
    status: "待入院"
  };
  createVisible.value = true;
  inpatientStep.value = 0;
  loadDoctorsForCreate();
}

function nextInpatientStep() {
  if (inpatientStep.value === 0 && (!createForm.value.pet_id || !createForm.value.doctor_id)) {
    ElMessage.warning("请先完成宠物与医生信息");
    return;
  }
  if (inpatientStep.value === 1 && (!createForm.value.cage_id || !createForm.value.admission_time)) {
    ElMessage.warning("请先选择笼舍与入院时间");
    return;
  }
  inpatientStep.value += 1;
}

function onCageClick(cell) {
  if (cell.className === "idle") {
    openCreateDialog();
    createForm.value.cage_id = cell.id;
    return;
  }
  if (cell.className === "busy") {
    const record = records.value.find((r) => r.cage_id === cell.id);
    const pet = pets.value.find((p) => p.id === Number(record?.pet_id));
    const days = record?.admission_time
      ? Math.max(1, Math.floor((Date.now() - new Date(record.admission_time).getTime()) / 86400000))
      : 0;
    drawerRecord.value = {
      ...record,
      pet_name: record?.pet_name || cell.petName || "",
      pet_species: pet?.species || cell.petSpecies || "",
      pet_breed: pet?.breed || "",
      stay_days: days,
      deposit_balance: Number(record?.deposit_amount || 0) - Number(record?.consumed_amount || 0),
    };
    drawerVisible.value = true;
    drawerVitals.value = [
      { time: "今天 08:30", temperature: 38.6, heartRate: 112, note: "精神状态稳定，食欲一般" },
      { time: "今天 14:00", temperature: 38.9, heartRate: 118, note: "轻度焦虑，建议观察" },
      { time: "今天 20:10", temperature: 38.5, heartRate: 108, note: "状态平稳" }
    ];
    vitalForm.value = { temperature: 38.5, heart_rate: 110, notes: "" };
  }
}

async function submitVitals() {
  if (!drawerRecord.value?.id) {
    ElMessage.error("未找到住院记录");
    return;
  }
  vitalSubmitting.value = true;
  try {
    await createVitalSigns({
      inpatient_record_id: Number(drawerRecord.value.id),
      temperature: Number(vitalForm.value.temperature),
      heart_rate: Number(vitalForm.value.heart_rate),
      notes: vitalForm.value.notes || "",
    });
    ElMessage.success("体征录入成功，已通知主治医生");
    await loadAll();
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "体征录入失败"));
  } finally {
    vitalSubmitting.value = false;
  }
}

async function recommendCage() {
  allocating.value = true;
  try {
    const result = await allocateCage({
      pet_id: Number(createForm.value.pet_id),
      clinic_id: createForm.value.clinic_id,
      preferred_zone_type: createForm.value.preferred_zone_type,
      is_emergency: emergencyMode.value
    });
    recommendedCageId.value = result.data.id;
    recommendedCageCode.value = result.data.cage_code;
    await loadAll();
    ElMessage.success("已生成笼舍推荐，请点击“使用推荐”");
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "笼舍推荐失败"));
  } finally {
    allocating.value = false;
  }
}

function useRecommendedCage() {
  createForm.value.cage_id = recommendedCageId.value;
}

function selectCreateCage(cage) {
  const dbCage = cages.value.find((item) => String(item.cage_code) === String(cage.code));
  createForm.value.cage_id = dbCage?.id ?? cage.id;
  cagePickerVisible.value = false;
}

async function submitCreate() {
  if (!createFormRef.value) return;
  await createFormRef.value.validate();
  const numericCageId = Number(createForm.value.cage_id);
  if (!Number.isFinite(numericCageId)) {
    ElMessage.error("请选择有效笼舍");
    return;
  }
  creating.value = true;
  try {
    await createInpatientRecord({
      ...createForm.value,
      pet_id: Number(createForm.value.pet_id),
      cage_id: numericCageId,
      doctor_id: Number(createForm.value.doctor_id),
      deposit_amount: Number(createForm.value.deposit_amount),
      consumed_amount: Number(createForm.value.consumed_amount)
    });
    ElMessage.success("住院记录创建成功");
    createVisible.value = false;
    await loadAll();
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "住院记录创建失败"));
  } finally {
    creating.value = false;
  }
}

function openUpdateDialog(row) {
  editingRecordId.value = row.id;
  updateForm.value = {
    status: row.status,
    deposit_amount: row.deposit_amount,
    consumed_amount: row.consumed_amount,
    discharge_time: row.discharge_time || ""
  };
  updateVisible.value = true;
}

async function submitUpdate() {
  if (!editingRecordId.value || !updateFormRef.value) return;
  await updateFormRef.value.validate();
  const payload = {
    ...updateForm.value,
    deposit_amount: Number(updateForm.value.deposit_amount),
    consumed_amount: Number(updateForm.value.consumed_amount),
    discharge_time: updateForm.value.discharge_time || null
  };
  updating.value = true;
  try {
    await updateInpatientRecord(editingRecordId.value, payload);
    ElMessage.success("住院记录更新成功");
    updateVisible.value = false;
    await loadAll();
  } catch (error) {
    ElMessage.error(String(getErrorMessage(error, "住院记录更新失败")));
  } finally {
    updating.value = false;
  }
}

async function confirmDischarge(row) {
  try {
    await ElMessageBox.confirm("出院操作不可逆，是否继续？", "确认出院", {
      type: "warning",
      confirmButtonText: "确认出院",
      confirmButtonClass: "el-button--danger",
      cancelButtonText: "取消"
    });
    editingRecordId.value = row.id;
    updateForm.value = {
      status: "已出院",
      deposit_amount: row.deposit_amount,
      consumed_amount: row.consumed_amount,
      discharge_time: new Date().toISOString().slice(0, 19)
    };
    await submitUpdate();
  } catch {
    // 用户取消不提示
  }
}

onMounted(async () => {
  if (authStore.clinicId) {
    clinicFilter.value = authStore.clinicId;
    createForm.value.clinic_id = authStore.clinicId;
  }
  await loadAll();
  cageTimer = window.setInterval(async () => {
    refreshingCages.value = true;
    await loadAll();
    refreshingCages.value = false;
  }, 30000);
});

onUnmounted(() => {
  if (cageTimer) window.clearInterval(cageTimer);
});
</script>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.list-meta { margin-top: 10px; color: #909399; font-size: 12px; }
.spin { animation: spin 1s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

.cage-card {
  margin-top: 4px;
}

.zone-block {
  margin-bottom: 14px;
}

.zone-title {
  margin-bottom: 6px;
  color: #606266;
  font-weight: 600;
}

.cage-grid {
  display: grid;
  grid-template-columns: repeat(9, minmax(0, 1fr));
  gap: 8px;
}

.cage-cell {
  border-radius: 6px;
  color: #303133;
  font-size: 12px;
  min-height: 46px;
  text-align: center;
  display: grid;
  align-content: center;
  justify-items: center;
  cursor: pointer;
}

.cage-code {
  font-size: 11px;
  line-height: 14px;
}

.cage-cell.idle {
  background: #e8f9ee;
  border: 1px solid #b7ebc8;
}

.cage-cell.busy {
  background: #e8f3ff;
  border: 1px solid #bfdcff;
}

.cage-cell.pending_clean {
  background: #f2f3f5;
  border: 1px dashed #c0c4cc;
}

.cage-cell.repair {
  background: #f2f3f5;
  border: 1px dashed #c0c4cc;
}

.cage-cell.temp {
  background: #fff3e8;
  border: 1px solid #ffd8b2;
}

.cage-content {
  margin-top: 2px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.pet-name {
  font-size: 10px;
}

.pet-icon {
  font-size: 16px;
  line-height: 1;
}

.pet-icon-idle {
  font-size: 14px;
  opacity: 0.75;
}

.lock-icon {
  margin-top: 2px;
}

.warn-text {
  color: #ef4444;
  margin-top: 6px;
  font-size: 12px;
}

:deep(.abnormal-input .el-input__wrapper) {
  box-shadow: 0 0 0 1px #ef4444 inset !important;
}

.cage-cell.recommended {
  box-shadow: 0 0 0 2px #409eff inset, 0 0 10px rgba(64, 158, 255, 0.8);
  animation: recommendedBlink 1s infinite;
}

.cage-cell.emergency_vip {
  box-shadow: 0 0 0 2px #e6a23c inset, 0 0 10px rgba(230, 162, 60, 0.8);
}

.picker-groups {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.picker-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.picker-title {
  font-weight: 600;
  color: #334155;
}

.picker-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

.picker-cage {
  border: 0;
  border-radius: 12px;
  min-height: 54px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 10px;
  cursor: pointer;
  font-weight: 600;
}

.picker-cage.status-available {
  background: #22c55e;
  color: #ffffff;
}

.picker-cage.status-occupied {
  background: #9ca3af;
  color: #ffffff;
  cursor: not-allowed;
}

.picker-cage.status-cleaning {
  background: #f59e0b;
  color: #ffffff;
  cursor: not-allowed;
}

@keyframes recommendedBlink {
  0% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
  100% {
    opacity: 1;
  }
}
</style>

