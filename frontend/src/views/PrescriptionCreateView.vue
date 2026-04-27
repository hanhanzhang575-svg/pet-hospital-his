<template>
  <div class="page">
    <el-row v-if="!initialized" :gutter="16">
      <el-col :span="24">
        <el-card class="glass-card">
          <el-skeleton :rows="6" animated />
        </el-card>
      </el-col>
    </el-row>
    <el-row v-else :gutter="16">
      <el-col :span="24" v-if="loadingPage">
        <el-card class="glass-card">
          <el-skeleton :rows="6" animated />
        </el-card>
      </el-col>
      <el-col :span="24" v-else-if="pageError">
        <el-card class="glass-card">
          <el-empty :description="pageError">
            <el-button class="agile-btn" type="primary" @click="initPage">重试加载</el-button>
          </el-empty>
        </el-card>
      </el-col>
      <template v-else>
      <el-col :span="8">
        <el-card class="glass-card">
          <template #header><span>处方信息</span></template>
          <el-alert v-if="contextLocked" type="info" :closable="false" show-icon>已从待诊队列带入宠物与医生信息并锁定</el-alert>
          <div class="pet-card">
            <div><strong>宠物：</strong>{{ petInfo?.name || "-" }}</div>
            <div><strong>物种/品种：</strong>{{ petInfo?.species || "-" }}/{{ petInfo?.breed || "-" }}</div>
            <div><strong>过敏史：</strong><span class="allergy">{{ (petInfo?.allergy_history || []).join("、") || "无" }}</span></div>
            <div><strong>本次主诉：</strong>{{ chiefComplaint || "未录入" }}</div>
          </div>

          <el-form :model="form" label-width="92px" style="margin-top: 12px">
            <el-form-item label="宠物">
              <el-select
                v-model="form.pet_id"
                filterable
                remote
                reserve-keyword
                :remote-method="searchPets"
                :loading="searchingPets"
                style="width: 100%"
                :disabled="contextLocked"
              >
                <el-option
                  v-for="p in petOptions"
                  :key="p.id"
                  :label="`${p?.name}(${p?.species}/${p?.breed || '-'})-主人${p?.owner_name || p?.owner_id}`"
                  :value="p.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="医生">
              <el-select v-model="form.doctor_id" filterable style="width: 100%" :disabled="contextLocked">
                <el-option
                  v-for="d in doctorOptions"
                  :key="d.id"
                  :label="`${d.full_name}-内科-今日剩余${Math.max(0, 8 - (d.loadCount || 0))}号${(d.loadCount || 0) >= 8 ? '(今日已满)' : ''}`"
                  :value="d.id"
                  :disabled="(d.loadCount || 0) >= 8"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="诊断结论">
              <el-input v-model="form.diagnosis_name" type="textarea" :rows="3" />
            </el-form-item>
            <el-form-item label="用药理由">
              <el-input v-model="form.usage_reason" type="textarea" :rows="2" />
            </el-form-item>
          </el-form>

          <el-divider>药品选择</el-divider>
          <el-input v-model="drugKeyword" placeholder="支持拼音首字母/名称检索" />
          <div class="drug-grid">
            <el-card v-for="drug in filteredDrugs" :key="drug.id" class="drug-card" shadow="hover">
              <div class="drug-head">
                <strong>{{ drug.name }}</strong>
                <el-tag :type="isContraindicated(drug.name) ? 'danger' : 'success'">
                  {{ isContraindicated(drug.name) ? "⚠️禁用" : "✅安全" }}
                </el-tag>
              </div>
              <el-space>
                <el-input-number
                  :model-value="getDrugField(drug?.id, 'quantity', 1)"
                  :min="1"
                  :max="30"
                  size="small"
                  @update:model-value="(val) => setDrugField(drug?.id, 'quantity', val)"
                />
                <el-select
                  :model-value="getDrugField(drug?.id, 'frequency', 'bid')"
                  size="small"
                  style="width: 98px"
                  @update:model-value="(val) => setDrugField(drug?.id, 'frequency', val)"
                >
                  <el-option label="qd" value="qd" />
                  <el-option label="bid" value="bid" />
                  <el-option label="tid" value="tid" />
                </el-select>
                <el-input-number
                  :model-value="getDrugField(drug?.id, 'days', 3)"
                  :min="1"
                  :max="30"
                  size="small"
                  @update:model-value="(val) => setDrugField(drug?.id, 'days', val)"
                />
              </el-space>
              <el-button size="small" type="primary" style="margin-top: 8px" @click="toggleDrug(drug)">
                {{ selectedDrugIds.has(drug.id) ? "移除" : "添加" }}
              </el-button>
            </el-card>
          </div>
          <el-space style="margin-top: 12px">
            <el-button type="success" class="agile-btn" :loading="submitting" @click="submit">提交处方</el-button>
            <el-button type="primary" class="agile-btn" @click="loadAdoptedDiagnosis">从AI采纳</el-button>
          </el-space>
        </el-card>
      </el-col>

      <el-col :span="10">
        <el-card class="glass-card">
          <template #header><span>AI辅助（Top3 鉴别诊断）</span></template>
          <el-space style="margin-bottom: 12px">
            <el-button type="info" :loading="ragLoading" @click="triggerRAGAnalysis">刷新AI分析</el-button>
            <el-link type="primary" @click="goToAIDiagnosis">展开完整AI分析</el-link>
          </el-space>
          <el-empty v-if="!ragResult" description="当前暂无AI分析" />
          <div v-else>
            <div v-for="(item, idx) in (ragResult.diagnosis_list || []).slice(0, 3)" :key="idx" class="diag-row">
              <div class="diag-title">{{ item.name }}</div>
              <el-progress :percentage="Math.round((item.confidence || 0) * 100)" />
              <el-text type="info">{{ item.evidence }}</el-text>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="glass-card">
          <template #header><span>物种禁忌速查</span></template>
          <div v-for="name in speciesContraList" :key="name" :class="['contra-item', { blink: selectedDrugNames.includes(name) }]">
            {{ name }}
          </div>
        </el-card>
      </el-col>
      </template>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import http from "../api/http";
import { getErrorMessage } from "../utils/status";
import { fetchDoctors } from "../api/users";
import { fetchPets } from "../api/pets";

const router = useRouter();

const form = ref({
  medical_record_id: 1,
  doctor_id: 2,
  pet_id: 1,
  clinic_id: "C001",
  diagnosis_name: "",
  usage_reason: ""
});
const petInfo = ref({});
const chiefComplaint = ref("");
const contextLocked = ref(false);
const doctorOptions = ref([]);
const petOptions = ref([]);
const searchingPets = ref(false);
const ragLoading = ref(false);
const ragResult = ref(null);
const submitting = ref(false);
const loadingPage = ref(false);
const initialized = ref(false);
const pageError = ref("");
const selectedDrugIds = ref(new Set());
const drugKeyword = ref("");
const allDrugs = ref([
  { id: 1, name: "阿莫西林" },
  { id: 2, name: "阿司匹林" },
  { id: 3, name: "布洛芬" },
  { id: 4, name: "对乙酰氨基酚" },
  { id: 5, name: "甲硝唑" },
  { id: 6, name: "木糖醇解毒支持" }
]);
const drugForm = ref({});

const selectedDrugNames = computed(() =>
  [...selectedDrugIds.value].map((id) => allDrugs.value.find((x) => x.id === id)?.name).filter(Boolean)
);
const filteredDrugs = computed(() =>
  allDrugs.value.filter((x) => !drugKeyword.value || x?.name.toLowerCase().includes(drugKeyword.value.toLowerCase()))
);
const speciesContraList = computed(() => {
  const species = String(petInfo.value?.species || "");
  if (species.includes("猫")) return ["对乙酰氨基酚", "阿司匹林", "布洛芬"];
  if (species.includes("犬")) return ["木糖醇"];
  return [];
});

function ensureDrugForm() {
  allDrugs.value.forEach((d) => {
    if (!drugForm.value[d.id]) {
      drugForm.value[d.id] = { quantity: 1, frequency: "bid", days: 3 };
    }
  });
}

function getDrugField(drugId, field, fallback) {
  if (!drugId) return fallback;
  return drugForm.value?.[drugId]?.[field] ?? fallback;
}

function setDrugField(drugId, field, value) {
  if (!drugId) return;
  if (!drugForm.value[drugId]) {
    drugForm.value[drugId] = { quantity: 1, frequency: "bid", days: 3 };
  }
  drugForm.value[drugId][field] = value;
}

function isContraindicated(name) {
  return speciesContraList.value.includes(name);
}

function toggleDrug(drug) {
  if (selectedDrugIds.value.has(drug.id)) {
    selectedDrugIds.value.delete(drug.id);
  } else {
    selectedDrugIds.value.add(drug.id);
  }
  selectedDrugIds.value = new Set(selectedDrugIds.value);
}

async function searchPets(keyword) {
  searchingPets.value = true;
  try {
    const res = await fetchPets();
    const key = String(keyword || "").trim().toLowerCase();
    petOptions.value = (res?.data || []).filter((p) => !key || `${p?.name}${p?.breed || ""}${String(p?.owner_id || "")}`.toLowerCase().includes(key));
  } catch (error) {
    console.error("搜索宠物失败:", error);
    petOptions.value = [];
  } finally {
    searchingPets.value = false;
  }
}

async function initPage() {
  initialized.value = false;
  loadingPage.value = true;
  pageError.value = "";
  try {
    ensureDrugForm();
    
    // 并行加载医生和宠物列表
    let doctorRes;
    try {
      doctorRes = await fetchDoctors("C001");
      if (!doctorRes?.data) {
        throw new Error("医生列表加载失败");
      }
      doctorOptions.value = (doctorRes?.data || []).map((d) => ({ ...d, loadCount: 0 }));
    } catch (error) {
      console.error("医生列表加载错误:", error);
      pageError.value = "医生列表加载失败";
      throw error;
    }
    
    try {
      await searchPets("");
      if (!petOptions.value || petOptions.value.length === 0) {
        console.warn("宠物列表为空");
      }
    } catch (error) {
      console.error("宠物列表加载错误:", error);
      // 不中断，允许继续
    }
    
    // 加载上下文（会话存储）
    try {
      const raw = window.sessionStorage.getItem("consultation_context");
      if (raw) {
        const context = JSON.parse(raw);
        if (context?.appointment_id) {
          form.value.medical_record_id = Number(context.appointment_id);
          form.value.pet_id = Number(context.pet_id || form.value.pet_id);
          form.value.doctor_id = Number(context.vet_id || form.value.doctor_id);
          contextLocked.value = true;
        }
      }
    } catch (storageError) {
      console.warn("会话存储读取失败:", storageError);
      contextLocked.value = false;
    }
    
    // 加载宠物信息
    try {
      await loadContextPet();
    } catch (error) {
      console.error("宠物信息加载错误:", error);
      petInfo.value = {};
    }
    
  } catch (error) {
    const msg = error?.message || String(error) || "处方页面初始化失败";
    pageError.value = msg.length > 100 ? msg.substring(0, 100) + "..." : msg;
    console.error("页面初始化最终错误:", error);
  } finally {
    loadingPage.value = false;
    initialized.value = true;
  }
}


async function loadContextPet() {
  try {
    const res = await fetchPets();
    const list = res?.data || [];
    const target = list.find((x) => x?.id === form.value.pet_id) || list[0] || {};
    petInfo.value = target || {};
  } catch (error) {
    console.error("加载宠物信息失败:", error);
    petInfo.value = {};
    throw error;
  }
}

function loadAdoptedDiagnosis() {
  const rawPlan = window.sessionStorage.getItem("ai_adopted_plan");
  if (rawPlan) {
    try {
      const aiData = JSON.parse(rawPlan);
      const mapped = {
        diagnosis_name: aiData?.diagnosis || "",
        usage_reason: aiData?.treatment_plan || ""
      };
      Object.assign(form.value, mapped);
      if (Array.isArray(aiData?.medications) && aiData.medications.length > 0) {
        const nameToDrug = new Map(allDrugs.value.map((d) => [d.name, d]));
        aiData.medications.forEach((item) => {
          const drug = nameToDrug.get(item?.drug_name || "");
          if (!drug) return;
          selectedDrugIds.value.add(drug.id);
          selectedDrugIds.value = new Set(selectedDrugIds.value);
        });
      }
      ElMessage.success(`已采纳AI诊断：${mapped.diagnosis_name || "已回填"}`);
      triggerRAGAnalysis();
      try {
        window.sessionStorage.removeItem("ai_adopted_plan");
      } catch {
        // ignore
      }
      return;
    } catch {
      // fallback to legacy key
    }
  }
  const diagnosis = window.sessionStorage.getItem("adopted_diagnosis") || "";
  if (!diagnosis) {
    ElMessage.warning("请先在AI辅助诊断页执行分析并一键采纳");
    return;
  }
  form.value.diagnosis_name = diagnosis;
  ElMessage.success(`已采纳AI诊断：${diagnosis}`);
  triggerRAGAnalysis();
}

async function triggerRAGAnalysis() {
  ragLoading.value = true;
  try {
    ragResult.value = {
      diagnosis_list: [
        { name: form?.value?.diagnosis_name || "慢性胃肠炎", confidence: 0.88, evidence: "症状与体征匹配" },
        { name: "食物不耐受", confidence: 0.67, evidence: "反复呕吐与腹泻" },
        { name: "胰腺炎", confidence: 0.53, evidence: "需结合生化结果" }
      ]
    };
  } finally {
    ragLoading.value = false;
  }
}

async function submit() {
  if (!form.value.diagnosis_name) {
    ElMessage.warning("请填写诊断结论");
    return;
  }
  const selected = allDrugs.value.filter((x) => selectedDrugIds.value.has(x.id));
  if (selected.length === 0) {
    ElMessage.warning("请至少添加一种药品");
    return;
  }
  const conflict = selected.some((x) => isContraindicated(x.name));
  const summary = selected.map((x) => `${x?.name} x${drugForm.value?.[x?.id]?.quantity || 1}`).join("、");
  const totalEstimate = selected.reduce((sum, x) => sum + Number(drugForm.value?.[x?.id]?.quantity || 1) * 80, 0);
  try {
    await ElMessageBox.confirm(
      `请再次核对患宠身份！\n\n宠物：${petInfo.value?.name || form.value.pet_id}\n药品：${summary}\n总金额预估：¥${totalEstimate}\n提交后将通知药房扣减库存${conflict ? "\n⚠️ 当前处方包含物种禁忌药物，请确认风险已知晓" : ""}`,
      "确认提交处方？",
      { confirmButtonText: "确认提交", cancelButtonText: "撤销返回", type: conflict ? "warning" : "info" }
    );
  } catch {
    return;
  }

  submitting.value = true;
  try {
    await http.post("/prescriptions", {
      medical_record_id: form.value.medical_record_id,
      doctor_id: form.value.doctor_id,
      clinic_id: form.value.clinic_id,
      diagnosis: form.value.diagnosis_name,
      usage_reason: form.value.usage_reason,
      items: selected.map((x) => ({
        drug_id: x.id,
        dosage: "按医嘱",
        frequency: drugForm.value?.[x?.id]?.frequency || "bid",
        duration_days: drugForm.value?.[x?.id]?.days || 3,
        quantity: drugForm.value?.[x?.id]?.quantity || 1
      }))
    });
    ElMessage.success("处方已提交，药房将收到实时通知");
    router.back();
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "处方提交失败"));
  } finally {
    submitting.value = false;
  }
}

function goToAIDiagnosis() {
  router.push({ name: "ai-diagnosis" });
}

onMounted(() => {
  initPage().catch((error) => {
    console.error("处方页面挂载失败:", error);
    pageError.value = "数据加载失败，请稍后重试";
    loadingPage.value = false;
    initialized.value = true;
  });
});
</script>

<style scoped>
.page { padding: 16px; }
.glass-card { border-radius: 20px; }
.pet-card { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 10px; color: #334155; }
.allergy { background: #fee2e2; color: #b91c1c; padding: 2px 6px; border-radius: 6px; }
.drug-grid { margin-top: 10px; display: grid; grid-template-columns: 1fr; gap: 8px; max-height: 420px; overflow: auto; }
.drug-card { border-radius: 12px; }
.drug-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.diag-row { margin-bottom: 12px; padding: 10px; background: #f8fafc; border-radius: 10px; }
.diag-title { font-weight: 700; margin-bottom: 6px; }
.contra-item { padding: 8px 10px; border: 1px solid #e2e8f0; border-radius: 8px; margin-bottom: 8px; }
.blink { animation: blink-danger .8s linear infinite; border-color: #ef4444; color: #b91c1c; background: #fef2f2; }
@keyframes blink-danger { 0%,100% { opacity: 1; } 50% { opacity: .35; } }
</style>

