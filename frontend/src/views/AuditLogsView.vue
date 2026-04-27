<template>
  <div class="page">
    <el-card class="glass-card">
      <template #header>
        <div class="header-row">
          <span>审计追踪日志</span>
          <el-space>
            <el-select v-model="filters.action_type" clearable placeholder="操作类型" style="width: 160px">
              <el-option v-for="t in actionTypes" :key="t" :label="t" :value="t" />
            </el-select>
            <el-input v-model="filters.actor" clearable placeholder="操作人" style="width: 160px" />
            <el-input v-model="filters.target" clearable placeholder="操作对象" style="width: 180px" />
          </el-space>
        </div>
      </template>

      <el-row :gutter="12" class="summary-row">
        <el-col :span="8"><el-statistic title="今日操作总数" :value="filteredLogs.length" /></el-col>
        <el-col :span="8"><el-statistic title="高风险操作数" :value="highRiskCount" /></el-col>
        <el-col :span="8"><el-statistic title="异常操作数" :value="abnormalCount" /></el-col>
      </el-row>

      <el-collapse v-model="collapsePanels" class="log-collapse">
        <el-collapse-item title="高风险操作" name="high-risk">
          <el-table :data="grouped.highRisk" border size="small" height="180">
            <el-table-column prop="timestamp" label="时间" width="160" />
            <el-table-column prop="actor_name" label="人员" width="120" />
            <el-table-column prop="action_type" label="动作" width="120" />
            <el-table-column prop="target" label="对象" min-width="180" />
          </el-table>
        </el-collapse-item>
        <el-collapse-item title="失败操作" name="failed">
          <el-table :data="grouped.failed" border size="small" height="160">
            <el-table-column prop="timestamp" label="时间" width="160" />
            <el-table-column prop="actor_name" label="人员" width="120" />
            <el-table-column prop="action_type" label="动作" width="120" />
            <el-table-column prop="target" label="对象" min-width="180" />
          </el-table>
        </el-collapse-item>
      </el-collapse>

      <el-empty v-if="filteredLogs.length === 0" description="今日暂无审计记录" />
      <el-table v-else :data="filteredLogs" border height="360">
        <el-table-column prop="timestamp" label="时间戳" width="180" />
        <el-table-column label="操作主体" min-width="220">
          <template #default="{ row }">
            {{ row.actor_name }}/{{ row.actor_role }}/{{ row.ip }}
          </template>
        </el-table-column>
        <el-table-column label="操作类型" width="120">
          <template #default="{ row }">
            <el-tag :type="tagType(row.action_type)" :effect="isHighRisk(row.action_type) ? 'dark' : 'light'">
              {{ row.action_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="target" label="操作对象" min-width="160" />
        <el-table-column label="变更详情" min-width="300">
          <template #default="{ row }">
            <el-popover trigger="click" width="420">
              <template #reference>
                <el-button size="small">展开</el-button>
              </template>
              <div class="diff-block">
                <div><strong>旧值：</strong>{{ row.old_value }}</div>
                <div><strong>新值：</strong>{{ row.new_value }}</div>
              </div>
            </el-popover>
          </template>
        </el-table-column>
        <el-table-column label="操作结果" width="110">
          <template #default="{ row }">
            <el-text :type="row.result === '成功' ? 'success' : 'danger'">{{ row.result === "成功" ? "✓ 成功" : "✗ 失败" }}</el-text>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { computed, ref } from "vue";

const actionTypes = ["CREATE", "UPDATE", "DELETE", "READ_PHI", "VOID"];
const filters = ref({ action_type: "", actor: "", target: "" });
const collapsePanels = ref(["high-risk"]);

const logs = ref([
  {
    id: 1,
    timestamp: "2026-04-10 10:22:15",
    actor_name: "王院长",
    actor_role: "admin",
    ip: "192.168.1.105",
    action_type: "READ_PHI",
    target: "病历MR20260410001",
    old_value: '{diagnosis:"肠胃炎"}',
    new_value: '{diagnosis:"急性胃炎伴脱水"}',
    result: "成功"
  },
  {
    id: 2,
    timestamp: "2026-04-10 11:08:09",
    actor_name: "张医生",
    actor_role: "doctor",
    ip: "192.168.1.126",
    action_type: "UPDATE",
    target: "处方RX20260410018",
    old_value: "{status:'待缴费'}",
    new_value: "{status:'已缴费'}",
    result: "成功"
  },
  {
    id: 3,
    timestamp: "2026-04-10 12:41:02",
    actor_name: "周主任",
    actor_role: "manager",
    ip: "192.168.1.88",
    action_type: "VOID",
    target: "病历MR20260409003",
    old_value: "{is_voided:false}",
    new_value: "{is_voided:true}",
    result: "失败"
  }
]);

const filteredLogs = computed(() =>
  logs.value.filter((x) => {
    if (filters.value.action_type && x.action_type !== filters.value.action_type) return false;
    if (filters.value.actor && !`${x.actor_name}${x.actor_role}`.includes(filters.value.actor)) return false;
    if (filters.value.target && !String(x.target || "").includes(filters.value.target)) return false;
    return true;
  })
);

const highRiskCount = computed(() => filteredLogs.value.filter((x) => isHighRisk(x.action_type)).length);
const abnormalCount = computed(() => filteredLogs.value.filter((x) => x.result !== "成功").length);
const grouped = computed(() => ({
  highRisk: filteredLogs.value.filter((x) => isHighRisk(x.action_type)),
  failed: filteredLogs.value.filter((x) => x.result !== "成功")
}));

function isHighRisk(actionType) {
  return ["READ_PHI", "VOID", "DELETE"].includes(actionType);
}

function tagType(actionType) {
  if (actionType === "CREATE") return "success";
  if (actionType === "UPDATE") return "primary";
  if (actionType === "DELETE") return "danger";
  if (actionType === "READ_PHI") return "warning";
  if (actionType === "VOID") return "info";
  return "";
}
</script>

<style scoped>
.page { padding: 16px; }
.header-row { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.summary-row { margin-bottom: 12px; }
.log-collapse { margin-bottom: 12px; }
.diff-block { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Courier New", monospace; line-height: 1.7; }
</style>
