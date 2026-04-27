<template>
  <div class="page">
    <el-card>
      <template #header>
        <div class="header-row">
          <div>
            <div class="title">回访任务（前台）</div>
            <div class="meta">共{{ rows.length }}条任务，最后更新时间 {{ lastUpdated || "--:--" }}</div>
          </div>
          <el-space>
            <el-select v-model="statusFilter" style="width: 140px" @change="loadRows">
              <el-option label="全部状态" value="" />
              <el-option label="待处理" value="待处理" />
              <el-option label="进行中" value="进行中" />
              <el-option label="已完成" value="已完成" />
            </el-select>
            <el-button type="primary" :loading="creating" @click="generateTasks">按RFM生成精简任务</el-button>
          </el-space>
        </div>
      </template>

      <el-alert type="info" :closable="false" show-icon style="margin-bottom: 10px">
        每位客户同一时期仅保留一条待处理回访任务，防止重复建单。
      </el-alert>

      <el-empty v-if="displayRows.length === 0" description="暂无高风险流失客户，继续保持！" />
      <el-table v-else :data="displayRows" border stripe height="420">
        <el-table-column prop="owner_name" label="客户" min-width="140" />
        <el-table-column label="风险" width="120">
          <template #default="{ row }">
            <el-tag :type="riskTag(row.risk_level)" size="small">{{ riskText(row.risk_level) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="风险信息" min-width="220">
          <template #default="{ row }">
            流失风险：{{ riskText(row.risk_level) }} / 未就诊：{{ row.recency_days ?? "--" }}天
          </template>
        </el-table-column>
        <el-table-column prop="script_text" label="建议话术" min-width="220" show-overflow-tooltip />
        <el-table-column label="上次跟进" min-width="220">
          <template #default="{ row }">
            {{ row.followup_detail?.summary || "未开始" }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag>{{ row.status || "待处理" }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-space>
              <el-button type="primary" size="small" :disabled="row.status === '已完成'" @click="openTask(row)">📞 开始回访</el-button>
              <el-button type="success" size="small" :disabled="row.status === '已完成'" @click="markDone(row)">✅ 标记完成</el-button>
            </el-space>
          </template>
        </el-table-column>
      </el-table>

      <el-card class="side-summary" shadow="never" style="margin-top: 12px">
        <template #header>任务统计</template>
        <el-statistic title="高风险任务" :value="highRiskCount" />
        <el-statistic title="待处理任务" :value="pendingCount" style="margin-top: 10px" />
        <el-statistic title="已完成任务" :value="doneCount" style="margin-top: 10px" />
      </el-card>
    </el-card>

      <el-dialog v-model="dialogVisible" title="回访跟进记录" width="640px">
      <el-steps :active="stepActive" finish-status="success" align-center style="margin-bottom: 16px">
        <el-step title="状态确认" description="SQL: status='进行中'" />
        <el-step title="建议反馈" description="SQL: followup_detail.care_feedback" />
        <el-step title="评价归档" description="SQL: status='已完成'" />
      </el-steps>
      <el-form label-width="120px">
        <template v-if="stepActive === 0">
          <el-form-item label="联系结果">
            <el-select v-model="followupForm.contact_result" style="width: 100%">
              <el-option label="接通" value="接通" />
              <el-option label="未接" value="未接" />
              <el-option label="拒接" value="拒接" />
            </el-select>
          </el-form-item>
          <el-form-item label="现状描述">
            <el-input v-model="followupForm.current_status" type="textarea" :rows="3" placeholder="记录食欲、精神、排便等" />
          </el-form-item>
        </template>
        <template v-else-if="stepActive === 1">
          <el-form-item label="护理建议">
            <el-input v-model="followupForm.care_feedback" type="textarea" :rows="4" placeholder="记录护理建议与执行反馈" />
          </el-form-item>
          <el-form-item label="复诊安排">
            <el-date-picker v-model="followupForm.revisit_time" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" style="width: 100%" />
          </el-form-item>
          <el-form-item label="复诊说明">
            <el-input v-model="followupForm.revisit_note" type="textarea" :rows="3" />
          </el-form-item>
        </template>
        <template v-else>
          <el-form-item label="归档备注">
            <el-input v-model="followupForm.note" type="textarea" :rows="3" />
          </el-form-item>
        </template>
      </el-form>
      <template #footer>
        <el-button @click="prevStep" :disabled="stepActive === 0">上一步</el-button>
        <el-button type="primary" @click="nextStep" v-if="stepActive < 2">下一步</el-button>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitFollowup" v-if="stepActive === 2">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import { fetchRfmWarnings } from "../api/ai";
import { createFollowupTasks, fetchFollowupTasks, updateFollowupTask } from "../api/tasks";
import { getErrorMessage } from "../utils/status";

const rows = ref([]);
const creating = ref(false);
const statusFilter = ref("");
const lastUpdated = ref("");
const dialogVisible = ref(false);
const activeTask = ref(null);
const followupForm = ref({
  contact_result: "接通",
  current_status: "",
  care_feedback: "",
  revisit_time: "",
  revisit_note: "",
  note: ""
});
const stepActive = ref(0);

const highRiskCount = computed(() => rows.value.filter((x) => x.risk_level === "high").length);
const pendingCount = computed(() => rows.value.filter((x) => String(x.status || "待处理") === "待处理").length);
const doneCount = computed(() => rows.value.filter((x) => String(x.status || "") === "已完成").length);
const displayRows = computed(() =>
  [...rows.value]
    .sort((a, b) => Number(b.risk_score || 0) - Number(a.risk_score || 0) || Number(b.recency_days || 0) - Number(a.recency_days || 0))
    .slice(0, 30)
);

function riskText(level) {
  if (level === "high") return "高风险";
  if (level === "medium") return "中风险";
  return "低风险";
}

function riskTag(level) {
  if (level === "high") return "danger";
  if (level === "medium") return "warning";
  return "success";
}

function openTask(task) {
  activeTask.value = task;
  const detail = task.followup_detail || {};
  stepActive.value = Number(detail.current_stage || 0);
  followupForm.value = {
    contact_result: detail.contact_result || "接通",
    current_status: detail.current_status || "",
    care_feedback: detail.care_feedback || "",
    revisit_time: detail.revisit_time || "",
    revisit_note: detail.revisit_note || "",
    note: detail.note || ""
  };
  dialogVisible.value = true;
}

async function syncCurrentStage(stage) {
  if (!activeTask.value?.id) return;
  await updateFollowupTask(activeTask.value.id, {
    status: "进行中",
    followup_detail: {
      ...followupForm.value,
      current_stage: stage,
      summary: `${followupForm.value.contact_result || "未知"} / ${followupForm.value.revisit_time || "未约复诊"}`
    }
  });
}

async function nextStep() {
  const next = Math.min(2, stepActive.value + 1);
  try {
    await syncCurrentStage(next);
    stepActive.value = next;
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "步骤保存失败"));
  }
}

function prevStep() {
  stepActive.value = Math.max(0, stepActive.value - 1);
}

async function submitFollowup() {
  if (!activeTask.value?.id) {
    ElMessage.error("任务信息缺失");
    return;
  }
  if (!followupForm.value.note.trim()) {
    ElMessage.warning("请填写归档备注");
    return;
  }
  try {
    await updateFollowupTask(activeTask.value.id, {
      status: "已完成",
      followup_detail: {
        contact_result: followupForm.value.contact_result,
        current_status: followupForm.value.current_status,
        care_feedback: followupForm.value.care_feedback,
        revisit_time: followupForm.value.revisit_time,
        revisit_note: followupForm.value.revisit_note,
        note: followupForm.value.note,
        current_stage: 2,
        summary: `${followupForm.value.contact_result || "未知"} / ${followupForm.value.revisit_time || "未约复诊"}`
      }
    });
    ElMessage.success("回访任务已提交并标记为已完成");
    dialogVisible.value = false;
    await loadRows();
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "提交回访任务失败"));
  }
}

async function markDone(task) {
  try {
    await updateFollowupTask(task.id, { status: "已完成" });
    ElMessage.success("任务已标记完成");
    await loadRows();
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "状态更新失败"));
  }
}

async function loadRows() {
  try {
    const result = await fetchFollowupTasks(statusFilter.value);
    rows.value = result.data || [];
    lastUpdated.value = new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "回访任务加载失败"));
  }
}

async function generateTasks() {
  creating.value = true;
  try {
    const result = await fetchRfmWarnings();
    const highRisk = (result.data || []).filter((x) => x.risk_level !== "low");
    await createFollowupTasks(
      highRisk.slice(0, 5).map((x) => ({
        owner_id: x.owner_id,
        owner_name: x.owner_name,
        risk_score: x.rfm_score,
        risk_level: x.risk_level,
        recency_days: x.recency_days,
        frequency: x.frequency,
        monetary: x.monetary,
        script_text: "您好，这里是白之助宠物医院，近期为毛孩子安排一次复诊评估会更稳妥。"
      }))
    );
    ElMessage.success("已按RFM自动生成回访任务");
    await loadRows();
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "生成回访任务失败"));
  } finally {
    creating.value = false;
  }
}

onMounted(loadRows);
</script>

<style scoped>
.page { padding: 16px; }
.header-row { display: flex; justify-content: space-between; align-items: center; }
.title { font-size: 16px; font-weight: 700; }
.meta { margin-top: 4px; color: #64748b; font-size: 12px; }
.side-summary { height: 100%; }
</style>

