<template>
  <div class="page layout-bg">
    <el-card class="glass-card main-card stagger-in-1">
      <template #header>
        <div class="header-row">
          <span class="page-title">🩺 接诊工作台 <span class="sub-badge pulse-badge">进行中</span></span>
          <div class="action-cluster">
            <el-button class="agile-btn btn-primary" :loading="saving" @click="saveRecord">
              <span class="btn-text">💾 保存病历</span>
            </el-button>
            <el-button class="agile-btn btn-success" @click="toPrescription">
              <span class="btn-text">💊 进入处方开具</span>
            </el-button>
          </div>
        </div>
      </template>

      <div class="info-panel mb24 stagger-in-2">
        <el-descriptions :column="3" border class="cute-descriptions">
          <el-descriptions-item>
            <template #label><div class="desc-label">📅 预约 ID</div></template>
            <span class="code-font">{{ consultation.appointment_id || "-" }}</span>
          </el-descriptions-item>
          <el-descriptions-item>
            <template #label><div class="desc-label">🐾 宠物 ID</div></template>
            <span class="fw-bold text-primary">#{{ consultation.pet_id || "-" }}</span>
          </el-descriptions-item>
          <el-descriptions-item>
            <template #label><div class="desc-label">👨‍⚕️ 主治医生 ID</div></template>
            <span class="fw-bold text-success">#{{ consultation.vet_id || "-" }}</span>
          </el-descriptions-item>
        </el-descriptions>
      </div>

        <div class="medical-record-form stagger-in-3">
          <div class="form-banner">📝 门诊病历记录 (SOAP)</div>
        
          <el-form :model="form" label-position="top" class="modern-form">
          <el-form-item>
            <template #label>
              <div class="custom-label">
                <span class="label-title">S - 主诉 (Subjective)</span>
                <span class="label-desc">记录宠物主人描述的症状、持续时间及既往病史。</span>
              </div>
            </template>
            <el-input 
              v-model="form.chief_complaint" 
              type="textarea" 
              :rows="4" 
              placeholder="例如：宠物主人代诉，患犬昨日起频繁呕吐，食欲废绝，精神沉郁..."
              class="agile-textarea" 
            />
          </el-form-item>
          
            <el-form-item>
              <template #label>
                <div class="custom-label">
                  <span class="label-title">O - 客观查体 (Objective)</span>
                  <span class="label-desc">记录体格检查（TPR）、触诊及初步检验结果。</span>
                </div>
              </template>
              <el-input 
                v-model="form.exam_notes" 
                type="textarea" 
                :rows="5" 
                placeholder="例如：T:39.2℃, P:120bpm, R:30bpm。腹部触诊敏感，可视黏膜微红，听诊心肺音正常..."
                class="agile-textarea" 
              />
            </el-form-item>

            <el-form-item>
              <template #label>
                <div class="custom-label">
                  <span class="label-title">A - 确诊结论 (Assessment)</span>
                  <span class="label-desc">提交病历前将触发AI主动监听相关性校验。</span>
                </div>
              </template>
              <el-input
                v-model="form.diagnosis"
                type="textarea"
                :rows="3"
                placeholder="例如：慢性肾功能不全伴脱水"
                class="agile-textarea"
              />
            </el-form-item>
            <el-form-item>
              <template #label>
                <div class="custom-label">
                  <span class="label-title">P - 诊疗计划 (Plan)</span>
                  <span class="label-desc">记录治疗方案、复查与随访计划。</span>
                </div>
              </template>
              <el-input
                v-model="form.treatment_plan"
                type="textarea"
                :rows="3"
                placeholder="例如：补液+止吐48小时，复查肝肾指标并评估是否住院"
                class="agile-textarea"
              />
            </el-form-item>
          </el-form>
        </div>

    </el-card>

    <el-dialog v-model="warningDialogVisible" title="AI主动监听预警" width="560px" class="glass-card">
      <div class="warning-card">
        <div class="warning-title">检测到诊断与生化指标相关性偏低</div>
        <div class="warning-line">相关性评分：{{ warningState.correlationScore }}</div>
        <div class="warning-line">预警信息：{{ warningState.message }}</div>
        <el-input
          v-model="warningState.reason"
          type="textarea"
          :rows="3"
          placeholder="请填写继续提交的医学理由"
        />
      </div>
      <template #footer>
        <el-button @click="warningDialogVisible = false">取消</el-button>
        <el-button class="agile-btn btn-success" :loading="saving" @click="confirmSubmitAfterWarning">
          已知晓风险并提交
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
// ==========================================
// 逻辑代码层 (完全保持不变)
// ==========================================
import { computed, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { createMedicalRecord } from "../api/vetWorkbench";
import { checkActiveListener, createAiAuditLog } from "../api/ai";
import { getErrorMessage } from "../utils/status";

const router = useRouter();
const consultation = computed(() => {
  try {
    return JSON.parse(window.sessionStorage.getItem("consultation_context") || "{}");
  } catch {
    return {};
  }
});

const form = ref({
  appointment_id: consultation.value.appointment_id || 1,
  pet_id: consultation.value.pet_id || 1,
  vet_id: consultation.value.vet_id || 2,
  chief_complaint: "",
  exam_notes: "",
  diagnosis: "",
  treatment_plan: ""
});
const saving = ref(false);
const warningDialogVisible = ref(false);
const warningState = ref({
  correlationScore: 0,
  message: "",
  reason: ""
});

async function saveRecord() {
  if (!form.value.diagnosis.trim()) {
    ElMessage.warning("请先填写确诊结论后再提交病历");
    return;
  }

  saving.value = true;
  try {
    const listenerRes = await checkActiveListener({
      appointment_id: form.value.appointment_id,
      pet_id: form.value.pet_id,
      diagnosis_text: form.value.diagnosis,
      threshold: 0.45,
      doctor_id: form.value.vet_id
    });
    const listenerData = listenerRes?.data || {};
    if (!listenerData.can_submit) {
      ElMessage.info(listenerData.message || "AI监听静默等待：条件未满足");
      return;
    }

    if (listenerData.warning_triggered) {
      warningState.value = {
        correlationScore: listenerData.correlation_score ?? 0,
        message: listenerData.message || "相关性低于阈值，请填写说明后提交",
        reason: ""
      };
      warningDialogVisible.value = true;
      return;
    }

    const payload = {
      appointment_id: form.value.appointment_id,
      pet_id: form.value.pet_id,
      vet_id: form.value.vet_id,
      chief_complaint: form.value.chief_complaint,
      exam_notes: form.value.exam_notes,
      diagnosis: form.value.diagnosis,
      treatment_plan: form.value.treatment_plan
    };
    await createMedicalRecord(payload);
    ElMessage.success("病历已成功保存至档案");
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "保存病历失败"));
  } finally {
    saving.value = false;
  }
}

async function confirmSubmitAfterWarning() {
  if (!warningState.value.reason.trim()) {
    ElMessage.warning("请填写说明原因后再提交");
    return;
  }

  saving.value = true;
  try {
    const payload = {
      appointment_id: form.value.appointment_id,
      pet_id: form.value.pet_id,
      vet_id: form.value.vet_id,
      chief_complaint: form.value.chief_complaint,
      exam_notes: form.value.exam_notes,
      diagnosis: form.value.diagnosis,
      treatment_plan: form.value.treatment_plan
    };
    const submitRes = await createMedicalRecord(payload);
    const medicalRecordId = submitRes?.data?.id;
    if (medicalRecordId) {
      await createAiAuditLog({
        medical_record_id: medicalRecordId,
        doctor_id: form.value.vet_id,
        ai_suggestion: warningState.value.message,
        doctor_decision: "医生已知晓风险并提交病历",
        deviation_reason: warningState.value.reason.trim(),
        correlation_score: Number(warningState.value.correlationScore || 0),
        warning_triggered: true
      });
    }
    warningDialogVisible.value = false;
    ElMessage.success("病历已提交，预警说明已记录");
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "提交病历失败"));
  } finally {
    saving.value = false;
  }
}

function toPrescription() {
  router.push("/prescription-create");
}
</script>

<style scoped>
/* ====================================================
   全局变量与基础设定 (Spring 物理曲线)
   ==================================================== */
:root {
  --primary: #3B82F6;
  --primary-hover: #2563EB;
  --success: #10B981;
  --success-hover: #059669;
  --bg-page: #F8FAFC;
  --surface: #FFFFFF;
  --text-main: #1E293B;
  --text-sub: #64748B;
  --spring: cubic-bezier(0.34, 1.56, 0.64, 1);
  --smooth: cubic-bezier(0.4, 0, 0.2, 1);
}

.layout-bg {
  background-color: var(--bg-page);
  min-height: 100vh;
  padding: 24px;
  font-family: 'Nunito', ui-rounded, 'Hiragino Maru Gothic ProN', 'PingFang SC', sans-serif;
  display: flex;
  justify-content: center; /* 居中显示工作台 */
}

.fw-bold { font-weight: 800; }
.text-primary { color: var(--primary); }
.text-success { color: var(--success); }
.mb24 { margin-bottom: 24px; }

/* ====================================================
   玻璃态主卡片 & 标题栏
   ==================================================== */
:deep(.glass-card) {
  width: 100%;
  max-width: 900px; /* 控制接诊页面的最大宽度，提升阅读体验 */
  border-radius: 20px !important; 
  border: 1px solid rgba(226, 232, 240, 0.8) !important;
  box-shadow: 0 20px 40px -10px rgba(15, 23, 42, 0.05), 0 10px 15px -5px rgba(15, 23, 42, 0.02) !important;
  background: var(--surface); 
  overflow: visible;
}

:deep(.glass-card > .el-card__header) {
  background: linear-gradient(to right, #FFFFFF, #F8FAFC); 
  border-bottom: 1px solid #F1F5F9;
  padding: 20px 24px; 
  border-radius: 20px 20px 0 0;
}

.header-row { 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  flex-wrap: wrap; /* 适配窄屏幕 */
  gap: 16px;
}

.page-title { 
  font-size: 22px; 
  font-weight: 800; 
  color: var(--text-main); 
  letter-spacing: 0.5px; 
  display: flex; 
  align-items: center; 
  gap: 12px;
}

/* 呼吸灯徽章 */
.sub-badge { 
  font-size: 13px; 
  background: #ECFDF5; 
  color: #059669; 
  padding: 4px 12px; 
  border-radius: 20px; 
  font-weight: 800; 
  border: 1px solid #A7F3D0;
}
@keyframes pulse-glow {
  0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4); }
  70% { box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
  100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
}
.pulse-badge {
  animation: pulse-glow 2s infinite;
}

.action-cluster {
  display: flex;
  gap: 12px;
}

/* ====================================================
   Q弹操作按钮 (防隐身强化)
   ==================================================== */
.agile-btn {
  border-radius: 100px !important; 
  height: 44px !important; 
  font-weight: 800 !important; 
  padding: 0 24px !important;
  transition: all 0.3s var(--spring) !important; 
  border: none !important;
  font-size: 15px !important;
}

.btn-primary {
  background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%) !important;
  color: #FFFFFF !important;
  text-shadow: 0px 1px 2px rgba(0, 0, 0, 0.3) !important; 
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3) !important;
}
.btn-primary:hover:not(:disabled):not(.is-loading) {
  transform: translateY(-2px) scale(1.02) !important;
  box-shadow: 0 6px 16px rgba(59, 130, 246, 0.4) !important;
  background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
}
.btn-primary:disabled,
.btn-primary.is-loading {
  background: #F1F5F9 !important; color: #475569 !important; text-shadow: none !important; border: 1px solid #CBD5E1 !important; box-shadow: none !important;
}

.btn-success {
  background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
  color: #FFFFFF !important;
  text-shadow: 0px 1px 2px rgba(0, 0, 0, 0.3) !important; 
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3) !important;
}
.btn-success:hover:not(:disabled) {
  transform: translateY(-2px) scale(1.02) !important;
  box-shadow: 0 6px 16px rgba(16, 185, 129, 0.4) !important;
  background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
}

/* ====================================================
   极客风基础信息描述列
   ==================================================== */
.info-panel {
  background: #F8FAFC;
  border-radius: 16px;
  padding: 8px;
  border: 1px dashed #E2E8F0;
}

:deep(.cute-descriptions) { 
  border-radius: 12px; 
  overflow: hidden; 
  border: 1px solid #F1F5F9; 
}
:deep(.cute-descriptions .el-descriptions__label) { 
  background-color: #F1F5F9 !important; 
  font-weight: 800; 
  color: #475569; 
  width: 140px; 
}
:deep(.cute-descriptions .el-descriptions__content) { 
  background-color: #FFFFFF;
  color: #1E293B; 
  font-size: 15px;
}

.desc-label { display: flex; align-items: center; gap: 6px; }

.code-font {
  font-family: 'JetBrains Mono', monospace; 
  font-size: 15px; 
  color: #475569;
  background: #F1F5F9;
  padding: 4px 10px;
  border-radius: 8px;
  font-weight: 700;
}

/* ====================================================
   数字病历本表单 (Digital Chart)
   ==================================================== */
.medical-record-form {
  background: #FFFFFF;
  border-radius: 16px;
  border: 1px solid #E2E8F0;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02);
  overflow: hidden;
  position: relative;
}
/* 模拟病历本左侧的装订色条 */
.medical-record-form::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 6px;
  background: var(--primary);
  border-radius: 16px 0 0 16px;
}

.form-banner {
  background: #EFF6FF;
  padding: 12px 24px;
  font-weight: 800;
  color: #1E40AF;
  border-bottom: 1px solid #BFDBFE;
  font-size: 15px;
  margin-left: 6px; /* 避开装订条 */
}

.modern-form {
  padding: 24px 32px 16px 32px;
}

.custom-label {
  display: flex;
  flex-direction: column;
  line-height: 1.4;
  margin-bottom: 8px;
}
.label-title {
  font-size: 16px;
  font-weight: 800;
  color: var(--text-main);
}
.label-desc {
  font-size: 13px;
  font-weight: 600;
  color: #94A3B8;
  margin-top: 4px;
}

/* Q弹多行输入框 */
:deep(.agile-textarea .el-textarea__inner) {
  border-radius: 12px !important; 
  background-color: #F8FAFC; 
  box-shadow: 0 0 0 1px #E2E8F0 inset !important; 
  transition: all 0.3s var(--spring) !important;
  font-size: 15px;
  padding: 16px;
  color: #1E293B;
  line-height: 1.6;
}
:deep(.agile-textarea .el-textarea__inner:focus) {
  background-color: #FFFFFF; 
  box-shadow: 0 0 0 2px var(--primary) inset, 0 4px 12px rgba(59, 130, 246, 0.1) !important;
}
:deep(.agile-textarea .el-textarea__inner::placeholder) {
  color: #CBD5E1;
  font-style: italic;
}

/* ====================================================
   阶梯入场动效 (Staggered Animation)
   ==================================================== */
@keyframes fadeInUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
[class*="stagger-in-"] { animation: fadeInUp 0.6s var(--spring) both; }
.stagger-in-1 { animation-delay: 0.1s; }
.stagger-in-2 { animation-delay: 0.2s; }
.stagger-in-3 { animation-delay: 0.3s; }

.warning-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.warning-title {
  color: #ef4444;
  font-weight: 700;
}

.warning-line {
  color: #475569;
  font-size: 14px;
}
</style>
