<template>
  <div class="ai-page">
    <el-card class="hero-card" shadow="never">
      <div class="hero-row">
        <div>
          <h2>AI 辅助诊断工作台</h2>
          <p>融合 RAG 检索、知识图谱推理与多模态诊断，输出可解释证据与可执行建议。</p>
        </div>
        <div class="hero-actions">
          <el-button @click="fillDemo">载入示例</el-button>
          <el-button type="primary" :loading="analyzing" @click="runPipeline">开始诊断</el-button>
        </div>
      </div>
      <el-steps :active="stepActive" finish-status="success" align-center class="step-bar">
        <el-step title="检索病例" description="RAG Top-K" />
        <el-step title="图谱推理" description="症状-疾病-禁忌" />
        <el-step title="诊断生成" description="结构化建议" />
      </el-steps>
    </el-card>

    <el-row :gutter="12">
      <el-col :xs="24" :lg="8">
        <el-card class="panel-card">
          <template #header>
            <div class="panel-title">输入区</div>
          </template>
          <el-form :model="form" label-width="86px">
            <el-form-item label="物种">
              <el-select v-model="form.pet_info.species" style="width: 100%" @change="onSpeciesChange">
                <el-option v-for="item in speciesOptions" :key="item" :label="item" :value="item" />
              </el-select>
            </el-form-item>
            <el-form-item label="品种">
              <el-input v-model="form.pet_info.breed" />
            </el-form-item>
            <el-form-item label="年龄(岁)">
              <el-input-number v-model="form.pet_info.age" :min="0" :max="25" style="width: 100%" />
            </el-form-item>
            <el-form-item label="体重(kg)">
              <el-input-number v-model="form.pet_info.weight" :min="0" :max="80" :step="0.1" style="width: 100%" />
            </el-form-item>
            <el-form-item label="症状描述">
              <el-input v-model="form.symptoms_text" type="textarea" :rows="4" placeholder="请输入主诉与伴随症状" />
            </el-form-item>
            <el-form-item label="影像上传">
              <el-upload drag multiple :auto-upload="false" :on-change="onImageChange" :show-file-list="true">
                <div class="upload-tip">拖拽或点击上传影像（X光 / B超 / 皮肤图）</div>
              </el-upload>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card class="panel-card">
          <template #header>
            <div class="panel-title">实验室指标（快速录入）</div>
          </template>
          <div class="lab-grid">
            <div v-for="item in panelConfigWithRange" :key="item.key" class="lab-item" :class="{ danger: isOutOfRange(item.key) }">
              <div class="lab-name">{{ item.label }}</div>
              <div class="lab-range">参考 {{ item.rangeText }}</div>
              <el-input-number v-model.number="form.lab_panel[item.key]" :step="0.1" controls-position="right" style="width: 100%" />
            </div>
          </div>
          <el-alert
            v-if="thresholdWarnings.length"
            type="warning"
            :closable="false"
            show-icon
            :title="`发现 ${thresholdWarnings.length} 项异常，建议优先排查`"
            style="margin-top: 10px"
          />
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="16">
        <el-card class="panel-card">
          <template #header>
            <div class="panel-title">诊断输出</div>
          </template>

          <el-row :gutter="10" class="metric-row">
            <el-col :xs="12" :lg="6">
              <div class="metric-box">
                <div class="metric-label">诊断可信度</div>
                <div class="metric-value">{{ confidenceText }}</div>
              </div>
            </el-col>
            <el-col :xs="12" :lg="6">
              <div class="metric-box">
                <div class="metric-label">异常指标占比</div>
                <div class="metric-value">{{ abnormalRatioText }}</div>
              </div>
            </el-col>
            <el-col :xs="12" :lg="6">
              <div class="metric-box">
                <div class="metric-label">证据条数</div>
                <div class="metric-value">{{ chromadbMatches.length }}</div>
              </div>
            </el-col>
            <el-col :xs="12" :lg="6">
              <div class="metric-box">
                <div class="metric-label">运行模式</div>
                <div class="metric-value small">{{ pipelineResult?.degraded ? "离线降级" : "完整链路" }}</div>
              </div>
            </el-col>
          </el-row>

          <el-tabs v-model="activeTab">
            <el-tab-pane label="诊断总览" name="summary">
              <el-empty v-if="diagnosisRows.length === 0" description="暂无诊断结果" />
              <template v-else>
                <el-table :data="diagnosisRows" border size="small">
                  <el-table-column prop="name" label="候选疾病" min-width="170" />
                  <el-table-column label="置信度" width="110">
                    <template #default="{ row }">{{ `${((row.confidence || 0) * 100).toFixed(1)}%` }}</template>
                  </el-table-column>
                  <el-table-column prop="evidence" label="证据" min-width="240" />
                </el-table>

                <el-card class="sub-card" shadow="never">
                  <template #header>关键结论</template>
                  <div class="content-block">{{ llmDiagnosis?.diagnosis || diagnosisRows[0]?.name || "-" }}</div>
                </el-card>

                <el-card class="sub-card" shadow="never">
                  <template #header>处理建议</template>
                  <div class="content-block">{{ llmDiagnosis?.treatment_plan || "暂无" }}</div>
                </el-card>

                <el-card v-if="forbiddenWarnings.length" class="sub-card danger" shadow="never">
                  <template #header>禁忌预警</template>
                  <el-alert v-for="w in forbiddenWarnings" :key="w" :title="w" type="error" show-icon :closable="false" style="margin-bottom: 6px" />
                </el-card>
              </template>
            </el-tab-pane>

            <el-tab-pane label="图谱证据" name="graph">
              <knowledge-graph-viz
                :species="graphSpecies"
                :highlighted-path="pipelineResult?.graph_reasoning_path || []"
                @update:species="(s) => graphSpecies = s"
              />
            </el-tab-pane>

            <el-tab-pane label="检验与用药" name="plan">
              <el-card class="sub-card" shadow="never">
                <template #header>推荐检查</template>
                <el-empty v-if="recommendedExams.length === 0" description="暂无推荐" />
                <el-tag v-for="exam in recommendedExams" :key="exam" style="margin: 4px">{{ exam }}</el-tag>
              </el-card>

              <el-card class="sub-card" shadow="never">
                <template #header>用药建议</template>
                <el-empty v-if="medicationPlan.length === 0" description="暂无建议" />
                <el-table v-else :data="medicationPlan" border size="small">
                  <el-table-column prop="drug_name" label="药物" min-width="130" />
                  <el-table-column prop="dose" label="剂量" min-width="110" />
                  <el-table-column prop="caution" label="注意事项" min-width="200" />
                </el-table>
              </el-card>

              <el-card class="sub-card" shadow="never">
                <template #header>RAG 检索证据</template>
                <el-empty v-if="chromadbMatches.length === 0" description="暂无证据" />
                <ol v-else class="evidence-list">
                  <li v-for="(item, idx) in chromadbMatches" :key="`${idx}-${item}`">{{ item }}</li>
                </ol>
              </el-card>
            </el-tab-pane>
          </el-tabs>

          <div class="footer-actions">
            <el-button type="success" @click="adoptToPrescription">采纳到处方页</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, ref } from "vue";
import { ElMessage } from "element-plus";
import KnowledgeGraphViz from "../components/KnowledgeGraphViz.vue";
import { runFullDiagnosis } from "../api/ai";
import { PET_SPECIES_OPTIONS } from "../constants/petSpecies";
import { getErrorMessage } from "../utils/status";

const speciesOptions = PET_SPECIES_OPTIONS;
const activeTab = ref("summary");
const analyzing = ref(false);
const stepActive = ref(0);
const graphSpecies = ref("猫");
const pipelineResult = ref(null);
const imageFiles = ref([]);

const form = ref({
  symptoms_text: "反复呕吐2天，精神沉郁，食欲下降并伴随腹部触痛",
  pet_info: { species: "猫", breed: "英短", age: 3, weight: 4.6 },
  lab_panel: { wbc: 8.2, alt: 125, ast: 72, bun: 11, cre: 175, plt: 126 }
});

const speciesRanges = {
  猫: { wbc: [5.5, 19.5], alt: [20, 100], ast: [10, 55], bun: [5.7, 12.9], cre: [71, 212], plt: [200, 600] },
  犬: { wbc: [6, 17], alt: [10, 90], ast: [10, 60], bun: [2.5, 9.5], cre: [44, 159], plt: [150, 500] },
  兔: { wbc: [5, 12], alt: [20, 80], ast: [15, 65], bun: [4.5, 12], cre: [40, 140], plt: [250, 650] },
  其他: { wbc: [0, 9999], alt: [0, 9999], ast: [0, 9999], bun: [0, 9999], cre: [0, 9999], plt: [0, 9999] }
};

const panelConfig = [
  { key: "wbc", label: "WBC" },
  { key: "alt", label: "ALT" },
  { key: "ast", label: "AST" },
  { key: "bun", label: "BUN" },
  { key: "cre", label: "CRE" },
  { key: "plt", label: "PLT" }
];

const chromadbMatches = computed(() => pipelineResult.value?.chromadb_matches || []);
const llmDiagnosis = computed(() => pipelineResult.value?.llm_diagnosis || null);
const diagnosisRows = computed(() => llmDiagnosis.value?.differential_diagnosis || []);
const recommendedExams = computed(() => llmDiagnosis.value?.recommended_exams || []);
const medicationPlan = computed(() => llmDiagnosis.value?.medication_plan || []);
const forbiddenWarnings = computed(() => llmDiagnosis.value?.forbidden_warnings || []);

const panelConfigWithRange = computed(() => {
  const ranges = speciesRanges[form.value.pet_info.species] || speciesRanges.其他;
  return panelConfig.map((item) => {
    const [min, max] = ranges[item.key] || [0, 0];
    return { ...item, rangeText: `${min}-${max}` };
  });
});

const abnormalCount = computed(() => panelConfig.filter((item) => isOutOfRange(item.key)).length);
const abnormalRatioText = computed(() => `${((abnormalCount.value / panelConfig.length) * 100).toFixed(1)}%`);
const confidenceText = computed(() => {
  const c = Number(diagnosisRows.value?.[0]?.confidence || 0);
  return `${(Math.max(0, Math.min(1, c)) * 100).toFixed(1)}%`;
});

const thresholdWarnings = computed(() =>
  panelConfigWithRange.value.filter((item) => isOutOfRange(item.key)).map((item) => `${item.label} 超出参考范围 ${item.rangeText}`)
);

function onSpeciesChange() {
  graphSpecies.value = form.value.pet_info.species;
}

function isOutOfRange(key) {
  const ranges = speciesRanges[form.value.pet_info.species] || speciesRanges.其他;
  const value = Number(form.value.lab_panel[key]);
  if (!Number.isFinite(value)) return false;
  const [min, max] = ranges[key] || [0, 9999];
  return value < min || value > max;
}

function onImageChange(file) {
  if (!file.raw) return;
  const reader = new FileReader();
  reader.onload = () => {
    imageFiles.value.push(String(reader.result || ""));
  };
  reader.readAsDataURL(file.raw);
}

function fillDemo() {
  form.value.symptoms_text = "间歇性呕吐，食欲下降，尿量减少，轻度脱水";
  form.value.pet_info = { species: "猫", breed: "布偶", age: 5, weight: 4.2 };
  form.value.lab_panel = { wbc: 9.3, alt: 152, ast: 84, bun: 15.5, cre: 242, plt: 186 };
  graphSpecies.value = "猫";
}

async function runPipeline() {
  if (analyzing.value) return;
  analyzing.value = true;
  stepActive.value = 0;
  try {
    stepActive.value = 1;
    const res = await runFullDiagnosis({
      symptoms_text: form.value.symptoms_text,
      image_files: imageFiles.value,
      pet_info: form.value.pet_info,
      lab_panel: form.value.lab_panel
    });
    stepActive.value = 3;
    pipelineResult.value = res?.data || null;
    activeTab.value = "summary";
    if (!pipelineResult.value?.llm_diagnosis) {
      ElMessage.warning("未获得完整诊断结果，请稍后重试");
      return;
    }
    ElMessage.success(pipelineResult.value?.degraded ? "诊断完成（离线降级模式）" : "诊断完成（完整链路）");
  } catch (error) {
    stepActive.value = 0;
    ElMessage.error(getErrorMessage(error, "诊断执行失败"));
  } finally {
    analyzing.value = false;
  }
}

function adoptToPrescription() {
  const topDisease = diagnosisRows.value?.[0]?.name || llmDiagnosis.value?.diagnosis || "";
  if (!topDisease) {
    ElMessage.warning("暂无可采纳结果");
    return;
  }
  window.sessionStorage.setItem(
    "ai_adopted_plan",
    JSON.stringify({
      diagnosis: topDisease,
      treatment_plan: llmDiagnosis.value?.treatment_plan || "",
      medications: medicationPlan.value,
      recommended_exams: recommendedExams.value,
      source: "ai-full-diagnosis"
    })
  );
  window.sessionStorage.setItem("adopted_diagnosis", topDisease);
  ElMessage.success("已采纳到处方页");
}
</script>

<style scoped>
.ai-page {
  padding: 14px;
  background: linear-gradient(140deg, #f5fbff 0%, #fff6ec 100%);
}
.hero-card,
.panel-card {
  border-radius: 14px;
  margin-bottom: 12px;
}
.panel-card :deep(.el-card__body) {
  padding: 12px;
}
.hero-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}
.hero-row h2 {
  margin: 0;
  font-size: 22px;
  color: #0f172a;
}
.hero-row p {
  margin: 6px 0 0;
  color: #64748b;
  font-size: 13px;
}
.hero-actions {
  display: flex;
  gap: 8px;
}
.step-bar {
  margin-top: 10px;
}
.panel-title {
  font-weight: 700;
  color: #0f172a;
}
.upload-tip {
  font-size: 13px;
  color: #475569;
}
.lab-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}
.lab-item {
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 8px;
  background: #fcfdff;
}
.lab-item.danger {
  border-color: #fca5a5;
  box-shadow: 0 0 0 1px rgba(239, 68, 68, 0.22);
}
.lab-name {
  font-size: 12px;
  font-weight: 700;
  color: #334155;
}
.lab-range {
  font-size: 11px;
  color: #64748b;
  margin-bottom: 4px;
}
.metric-row {
  margin-bottom: 8px;
}
.metric-box {
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 8px;
  background: #fcfdff;
}
.metric-label {
  font-size: 12px;
  color: #64748b;
}
.metric-value {
  margin-top: 3px;
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
}
.metric-value.small {
  font-size: 16px;
}
.sub-card {
  margin-top: 8px;
  border-radius: 10px;
}
.sub-card.danger {
  border-color: rgba(239, 68, 68, 0.4);
}
.content-block {
  line-height: 1.8;
  color: #334155;
}
.evidence-list {
  margin: 0;
  padding-left: 18px;
  color: #334155;
  line-height: 1.7;
}
.footer-actions {
  margin-top: 8px;
  text-align: right;
}
@media (max-width: 900px) {
  .hero-row {
    flex-direction: column;
    align-items: flex-start;
  }
  .lab-grid {
    grid-template-columns: 1fr;
  }
}
</style>

