<template>
  <div class="inpatient-page">
    <el-card class="hero-card" shadow="never">
      <div class="hero-row">
        <div>
          <h2>住院申请流程</h2>
          <p>按“信息确认 -> 资源分配 -> 财务确认 -> 医嘱提交”四步完成，减少遗漏和返工。</p>
        </div>
        <el-tag type="info">步骤 {{ step + 1 }}/4</el-tag>
      </div>
      <el-steps :active="step" finish-status="success" align-center>
        <el-step title="基础信息" description="宠物/医生/紧急程度" />
        <el-step title="笼舍推荐" description="约束校验与资源分配" />
        <el-step title="财务与医嘱" description="押金与初始治疗计划" />
        <el-step title="确认提交" description="复核后提交住院单" />
      </el-steps>
    </el-card>

    <el-row :gutter="12">
      <el-col :xs="24" :lg="16">
        <el-card class="panel-card">
          <template #header>
            <div class="panel-title">步骤内容</div>
          </template>

          <el-form :model="form" label-width="110px">
            <template v-if="step === 0">
              <el-form-item label="宠物">
                <el-select v-model="form.pet_id" filterable remote :remote-method="searchPets" :loading="searchingPets" style="width: 100%">
                  <el-option v-for="p in petOptions" :key="p.id" :label="`${p.name} (${p.species}/${p.breed || '-'})`" :value="p.id" />
                </el-select>
              </el-form-item>
              <el-form-item label="院区">
                <el-select v-model="form.clinic_id" style="width: 100%" @change="loadDoctors">
                  <el-option label="C001 沙河口" value="C001" />
                  <el-option label="C002 甘井子" value="C002" />
                  <el-option label="C003 高新区" value="C003" />
                </el-select>
              </el-form-item>
              <el-form-item label="负责医生">
                <el-select v-model="form.doctor_id" filterable style="width: 100%">
                  <el-option
                    v-for="d in doctors"
                    :key="d.id"
                    :label="`${d.full_name}（剩余号源 ${Math.max(0, 8 - (d.loadCount || 0))}）`"
                    :value="d.id"
                    :disabled="(d.loadCount || 0) >= 8"
                  />
                </el-select>
              </el-form-item>
              <el-form-item label="紧急程度">
                <el-radio-group v-model="form.urgency_level">
                  <el-radio label="常规" />
                  <el-radio label="优先" />
                  <el-radio label="急诊" />
                </el-radio-group>
              </el-form-item>
            </template>

            <template v-if="step === 1">
              <el-form-item label="期望病区">
                <el-select v-model="form.preferred_zone_type" style="width: 100%">
                  <el-option label="犬区" value="犬区" />
                  <el-option label="猫区" value="猫区" />
                  <el-option label="VIP" value="VIP" />
                  <el-option label="ICU" value="ICU" />
                  <el-option label="隔离" value="隔离" />
                </el-select>
              </el-form-item>
              <el-form-item label="推荐笼舍">
                <el-space>
                  <el-button :loading="allocating" @click="recommend">执行智能推荐</el-button>
                  <el-button plain @click="smartRecommendFromVisual">算法推荐并选中</el-button>
                  <el-tag v-if="recommended" type="success">{{ recommended.cage_code }} / {{ recommended.zone_type }}</el-tag>
                </el-space>
              </el-form-item>
              <el-form-item label="可视化笼舍">
                <div class="cage-grid">
                  <button
                    v-for="cage in cageOptions"
                    :key="cage.id"
                    type="button"
                    class="cage-cell"
                    :class="{
                      selected: Number(form.cage_id) === Number(cage.id),
                      busy: cage.status !== '空闲'
                    }"
                    :disabled="cage.status !== '空闲'"
                    @click="pickCage(cage)"
                  >
                    <div class="cage-icon">{{ cage.status === "空闲" ? "🟩" : "🟥" }}</div>
                    <div class="cage-code">{{ cage.cage_code }}</div>
                    <div class="cage-meta">{{ cage.zone_type }}</div>
                  </button>
                </div>
              </el-form-item>
              <el-alert v-if="algoTip" :title="algoTip" :type="algoTipType" :closable="false" show-icon />
            </template>

            <template v-if="step === 2">
              <el-form-item label="入院时间">
                <el-date-picker v-model="form.admission_time" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" style="width: 100%" />
              </el-form-item>
              <el-form-item label="押金">
                <el-input-number v-model="form.deposit_amount" :min="500" :max="50000" :step="100" style="width: 220px" />
              </el-form-item>
              <el-form-item label="初始医嘱">
                <el-input v-model="form.notes" type="textarea" :rows="4" placeholder="请输入初始治疗方案、监护等级和注意事项" />
              </el-form-item>
            </template>

            <template v-if="step === 3">
              <el-descriptions border :column="1" class="summary-box">
                <el-descriptions-item label="宠物">{{ selectedPetLabel }}</el-descriptions-item>
                <el-descriptions-item label="院区">{{ form.clinic_id }}</el-descriptions-item>
                <el-descriptions-item label="医生">{{ selectedDoctorLabel }}</el-descriptions-item>
                <el-descriptions-item label="紧急程度">{{ form.urgency_level }}</el-descriptions-item>
                <el-descriptions-item label="笼舍">{{ recommended ? `${recommended.cage_code} (${recommended.zone_type})` : form.cage_id || '-' }}</el-descriptions-item>
                <el-descriptions-item label="押金">￥{{ Number(form.deposit_amount || 0).toFixed(2) }}</el-descriptions-item>
                <el-descriptions-item label="入院时间">{{ form.admission_time || '提交时默认当前时间' }}</el-descriptions-item>
                <el-descriptions-item label="初始医嘱">{{ form.notes || '无' }}</el-descriptions-item>
              </el-descriptions>
            </template>
          </el-form>

          <div class="step-actions">
            <el-button v-if="step > 0" @click="step -= 1">上一步</el-button>
            <el-button v-if="step < 3" type="primary" @click="nextStep">下一步</el-button>
            <el-button v-else type="success" :loading="submitting" @click="submit">确认提交住院申请</el-button>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="8">
        <el-card class="panel-card">
          <template #header>
            <div class="panel-title">流程提示</div>
          </template>
          <ul class="tips-list">
            <li>先确认宠物与医生，系统再开放笼舍推荐。</li>
            <li>笼舍推荐包含物种隔离和急诊优先约束。</li>
            <li>若出现院区满载，建议发起跨院转诊。</li>
            <li>提交前请确认押金和初始医嘱完整。</li>
          </ul>
          <el-alert v-if="form.urgency_level === '急诊'" type="warning" :closable="false" show-icon title="急诊模式已启用：将优先分配可用笼舍并缩短等待流程" />
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="allocMask" width="360px" :show-close="false" :close-on-click-modal="false" :close-on-press-escape="false">
      <div class="alloc-loading">
        <el-icon class="spin"><Loading /></el-icon>
        <div>{{ allocStepText }}</div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { Loading } from "@element-plus/icons-vue";
import { allocateCage, createInpatientRecord, fetchCages } from "../api/inpatient";
import { fetchPets } from "../api/pets";
import { fetchDoctors } from "../api/users";
import { getErrorMessage } from "../utils/status";

const step = ref(0);
const allocating = ref(false);
const submitting = ref(false);
const searchingPets = ref(false);
const allocMask = ref(false);
const allocStepText = ref("正在扫描可用笼舍...");

const recommended = ref(null);
const algoTip = ref("");
const algoTipType = ref("success");
const petOptions = ref([]);
const doctors = ref([]);
const cageOptions = ref([]);

const form = ref({
  pet_id: 1,
  doctor_id: 0,
  clinic_id: "C001",
  preferred_zone_type: "犬区",
  urgency_level: "常规",
  cage_id: null,
  admission_time: "",
  deposit_amount: 1000,
  consumed_amount: 0,
  status: "待入院",
  notes: ""
});

const selectedPet = computed(() => petOptions.value.find((x) => Number(x.id) === Number(form.value.pet_id)) || null);
const selectedDoctor = computed(() => doctors.value.find((x) => Number(x.id) === Number(form.value.doctor_id)) || null);
const selectedPetLabel = computed(() => (selectedPet.value ? `${selectedPet.value.name} (${selectedPet.value.species}/${selectedPet.value.breed || '-'})` : "-"));
const selectedDoctorLabel = computed(() => selectedDoctor.value?.full_name || "-");

async function loadDoctors() {
  try {
    const res = await fetchDoctors(form.value.clinic_id);
    doctors.value = res.data || [];
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "医生列表加载失败"));
  }
}

async function loadCages() {
  try {
    const res = await fetchCages(form.value.clinic_id, form.value.preferred_zone_type || "");
    cageOptions.value = (res.data || []).slice(0, 16);
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "笼舍列表加载失败"));
  }
}

async function searchPets(keyword) {
  searchingPets.value = true;
  try {
    const res = await fetchPets();
    const key = String(keyword || "").trim().toLowerCase();
    petOptions.value = (res.data || []).filter((p) => !key || `${p.name}${p.species}${p.breed || ""}`.toLowerCase().includes(key));
  } finally {
    searchingPets.value = false;
  }
}

function nextStep() {
  if (step.value === 0 && (!form.value.pet_id || !form.value.doctor_id)) {
    ElMessage.warning("请先选择宠物和医生");
    return;
  }
  if (step.value === 1 && !form.value.cage_id) {
    ElMessage.warning("请先确认笼舍");
    return;
  }

  const species = String(selectedPet.value?.species || "");
  if (
    step.value === 1 &&
    species &&
    ((species.includes("猫") && form.value.preferred_zone_type === "犬区") || (species.includes("犬") && form.value.preferred_zone_type === "猫区"))
  ) {
    ElMessageBox.alert("当前病区与物种不匹配，系统已拦截该分配。", "约束拦截", { type: "error" });
    return;
  }

  step.value += 1;
}

async function recommend() {
  allocating.value = true;
  allocMask.value = true;

  const flowTexts = form.value.urgency_level === "急诊"
    ? ["扫描病区资源...", "执行急诊优先策略...", "校验物种隔离约束...", "锁定最优笼舍..."]
    : ["扫描病区资源...", "校验物种隔离约束...", "评估紧急程度与病区匹配...", "生成推荐结果..."];

  for (let i = 0; i < flowTexts.length; i += 1) {
    allocStepText.value = flowTexts[i];
    // eslint-disable-next-line no-await-in-loop
    await new Promise((resolve) => window.setTimeout(resolve, 420));
  }

  try {
    const res = await allocateCage({
      pet_id: form.value.pet_id,
      clinic_id: form.value.clinic_id,
      preferred_zone_type: form.value.preferred_zone_type,
      is_emergency: form.value.urgency_level === "急诊"
    });
    recommended.value = res.data;
    form.value.cage_id = res.data.id;

    algoTipType.value = form.value.urgency_level === "急诊" ? "warning" : "success";
    algoTip.value = form.value.urgency_level === "急诊"
      ? `急诊策略已触发，推荐 ${res.data.cage_code}（${res.data.zone_type}）。`
      : `已推荐 ${res.data.cage_code}（${res.data.zone_type}），满足当前约束条件。`;
  } catch (error) {
    const msg = getErrorMessage(error, "笼舍推荐失败");
    if (String(msg).includes("跨院")) {
      algoTipType.value = "info";
      algoTip.value = "当前院区容量紧张，建议触发跨院转诊方案。";
    } else {
      ElMessage.error(msg);
    }
  } finally {
    allocMask.value = false;
    allocating.value = false;
    await loadCages();
  }
}

function pickCage(cage) {
  if (cage.status !== "空闲") return;
  form.value.cage_id = cage.id;
  recommended.value = cage;
}

async function smartRecommendFromVisual() {
  await recommend();
  const best = cageOptions.value.find((x) => Number(x.id) === Number(form.value.cage_id))
    || cageOptions.value.find((x) => x.status === "空闲");
  if (best) pickCage(best);
}

async function submit() {
  submitting.value = true;
  try {
    await createInpatientRecord({
      pet_id: Number(form.value.pet_id),
      cage_id: Number(form.value.cage_id),
      doctor_id: Number(form.value.doctor_id),
      clinic_id: form.value.clinic_id,
      admission_time: form.value.admission_time || new Date().toISOString().slice(0, 19),
      deposit_amount: Number(form.value.deposit_amount),
      consumed_amount: Number(form.value.consumed_amount),
      status: "待入院"
    });
    ElMessage.success("住院申请提交成功");
    step.value = 0;
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "住院申请提交失败"));
  } finally {
    submitting.value = false;
  }
}

loadDoctors();
searchPets("");
loadCages();
</script>

<style scoped>
.inpatient-page {
  padding: 14px;
  background: linear-gradient(145deg, #f4fbff 0%, #fff7ed 100%);
}
.hero-card,
.panel-card {
  border-radius: 14px;
  margin-bottom: 12px;
}
.hero-row {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: center;
  margin-bottom: 10px;
}
.hero-row h2 {
  margin: 0;
  font-size: 22px;
  color: #0f172a;
}
.hero-row p {
  margin: 6px 0 0;
  font-size: 13px;
  color: #64748b;
}
.panel-title {
  font-weight: 700;
  color: #0f172a;
}
.step-actions {
  margin-top: 14px;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
.summary-box {
  margin-top: 4px;
}
.tips-list {
  margin: 0 0 12px;
  padding-left: 18px;
  color: #334155;
  line-height: 1.8;
}
.cage-grid {
  width: 100%;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}
.cage-cell {
  border: 1px solid #d1d5db;
  background: #fff;
  border-radius: 10px;
  padding: 8px;
  text-align: center;
  cursor: pointer;
}
.cage-cell.selected {
  border-color: #22c55e;
  box-shadow: 0 0 0 2px rgba(34, 197, 94, 0.2);
}
.cage-cell.busy {
  opacity: 0.55;
  cursor: not-allowed;
}
.cage-icon { font-size: 18px; }
.cage-code { font-weight: 700; color: #0f172a; margin-top: 2px; }
.cage-meta { font-size: 11px; color: #64748b; margin-top: 2px; }
.alloc-loading {
  display: grid;
  gap: 8px;
  justify-items: center;
}
.spin {
  animation: spin 1s linear infinite;
  font-size: 22px;
}
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
@media (max-width: 900px) {
  .hero-row {
    flex-direction: column;
    align-items: flex-start;
  }
  .cage-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>

