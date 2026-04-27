<template>
  <div class="page">
    <el-card>
      <template #header>
        <div class="header-row">
          <span>{{ title }}</span>
          <el-button size="small" :loading="loading" @click="loadData">刷新</el-button>
        </div>
      </template>
      <el-alert type="info" :closable="false" show-icon style="margin-bottom: 10px">
        {{ processText }}
      </el-alert>
      <el-row :gutter="12" class="mb12">
        <el-col :span="8"><el-card><div class="k">总记录</div><div class="v">{{ rows.length }}</div></el-card></el-col>
        <el-col :span="8"><el-card><div class="k">高优先级</div><div class="v warning">{{ highPriorityCount }}</div></el-card></el-col>
      </el-row>
      <div ref="chartRef" class="chart" />
      <el-table :data="rows" border>
        <el-table-column v-for="col in columns" :key="col.prop" :prop="col.prop" :label="col.label" :min-width="col.width || 120">
          <template v-if="col.prop === 'status'" #default="{ row }">
            {{ mapStatus(row.status) }}
          </template>
          <template v-else-if="col.prop === 'urgency_level'" #default="{ row }">
            {{ mapStatus(row.urgency_level) }}
          </template>
        </el-table-column>
      </el-table>
      <div class="list-meta">共{{ rows.length }}条记录，最后更新时间 {{ lastUpdated || "--:--" }}</div>
    </el-card>
  </div>
</template>

<script setup>
import * as echarts from "echarts";
import { computed, nextTick, onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { ElMessage } from "element-plus";
import { fetchAppointments } from "../api/appointments";
import { fetchInpatientRecords } from "../api/inpatient";
import { fetchInventoryOverview } from "../api/inventory";
import { fetchPurchaseTasks } from "../api/tasks";
import { getErrorMessage } from "../utils/status";

const route = useRoute();
const loading = ref(false);
const rows = ref([]);
const chartRef = ref(null);
const lastUpdated = ref("");
let chart = null;

const title = computed(() => String(route.meta?.title || "模块"));

const moduleConfig = {
  "电子病历": {
    processText: "过程：待诊→接诊→病历归档→复查提醒",
    columns: [
      { prop: "record_code", label: "诊单号", width: 180 },
      { prop: "pet_id", label: "宠物ID" },
      { prop: "status", label: "状态" },
      { prop: "urgency_level", label: "紧急度" }
    ],
    loader: async () => (await fetchAppointments({ clinicId: "C001" })).data || []
  },
  "跨院区病历": {
    processText: "过程：申请调阅→权限校验→审计落库→只读浏览",
    columns: [
      { prop: "record_code", label: "诊单号", width: 180 },
      { prop: "clinic_id", label: "院区" },
      { prop: "status", label: "状态" }
    ],
    loader: async () => (await fetchAppointments({})).data || []
  },
  "笼舍状态": {
    processText: "过程：空闲监控→住院占用→待清洁→再次开放",
    columns: [
      { prop: "id", label: "记录ID" },
      { prop: "pet_id", label: "宠物ID" },
      { prop: "status", label: "住院状态" }
    ],
    loader: async () => (await fetchInpatientRecords("C001")).data || []
  },
  "护理日志": {
    processText: "过程：体征录入→异常检测→医生确认→护理闭环",
    columns: [
      { prop: "id", label: "住院ID" },
      { prop: "pet_id", label: "宠物ID" },
      { prop: "doctor_id", label: "责任医生" },
      { prop: "status", label: "状态" }
    ],
    loader: async () => (await fetchInpatientRecords("C001")).data || []
  },
  "体征录入": {
    processText: "过程：体温/心率上报→阈值判断→异常实时推送",
    columns: [
      { prop: "id", label: "住院ID" },
      { prop: "pet_id", label: "宠物ID" },
      { prop: "consumed_amount", label: "已消费" }
    ],
    loader: async () => (await fetchInpatientRecords("C001")).data || []
  },
  "EOQ补货建议": {
    processText: "过程：需求预测→EOQ计算→低库存识别→补货建议生成",
    columns: [
      { prop: "drug_name", label: "药品" },
      { prop: "stock_qty", label: "当前库存" },
      { prop: "safety_stock", label: "安全库存" }
    ],
    loader: async () => (await fetchInventoryOverview("C001")).data || []
  },
  "采购申请": {
    processText: "过程：低库存触发→自动生成申请→审批流转",
    columns: [
      { prop: "id", label: "任务ID" },
      { prop: "drug_id", label: "药品ID" },
      { prop: "suggested_qty", label: "建议采购量" },
      { prop: "status", label: "状态" }
    ],
    loader: async () => (await fetchPurchaseTasks()).data || []
  },
  "运营看板": {
    processText: "过程：门诊量/住院率/库存预警/营收四维监控",
    columns: [
      { prop: "record_code", label: "诊单号", width: 180 },
      { prop: "clinic_id", label: "院区" },
      { prop: "priority_score", label: "优先级评分" }
    ],
    loader: async () => (await fetchAppointments({})).data || []
  },
  "采购审批": {
    processText: "过程：待审→通过/驳回→同步库存计划",
    columns: [
      { prop: "id", label: "申请ID" },
      { prop: "drug_id", label: "药品ID" },
      { prop: "status", label: "审批状态" }
    ],
    loader: async () => (await fetchPurchaseTasks()).data || []
  },
  "排班管理": {
    processText: "过程：排班制定→冲突检测→医生通知",
    columns: [
      { prop: "record_code", label: "诊单号", width: 180 },
      { prop: "doctor_id", label: "医生ID" },
      { prop: "scheduled_time", label: "时段", width: 200 }
    ],
    loader: async () => (await fetchAppointments({ clinicId: "C001" })).data || []
  },
  "财务台账": {
    processText: "过程：订单归集→结算对账→日报生成",
    columns: [
      { prop: "record_code", label: "诊单号", width: 180 },
      { prop: "pet_id", label: "宠物ID" },
      { prop: "status", label: "收费状态" }
    ],
    loader: async () => (await fetchAppointments({ clinicId: "C001" })).data || []
  },
  "跨院区调度": {
    processText: "过程：院区负载评估→资源调度→审计留痕",
    columns: [
      { prop: "record_code", label: "诊单号", width: 180 },
      { prop: "clinic_id", label: "院区" },
      { prop: "urgency_level", label: "紧急级别" }
    ],
    loader: async () => (await fetchAppointments({})).data || []
  },
  "用户管理": {
    processText: "过程：账号创建→角色绑定→院区归属",
    columns: [
      { prop: "record_code", label: "示例关联单号", width: 180 },
      { prop: "doctor_id", label: "用户ID" },
      { prop: "clinic_id", label: "院区" }
    ],
    loader: async () => (await fetchAppointments({ clinicId: "C001" })).data || []
  },
  "权限配置": {
    processText: "过程：角色矩阵定义→路由权限生效→按钮级控制",
    columns: [
      { prop: "record_code", label: "路由业务单号", width: 180 },
      { prop: "status", label: "权限态" },
      { prop: "urgency_level", label: "优先级" }
    ],
    loader: async () => (await fetchAppointments({ clinicId: "C001" })).data || []
  },
  "审计日志": {
    processText: "过程：关键操作上报→实时通知→可追溯查询",
    columns: [
      { prop: "id", label: "任务ID" },
      { prop: "owner_name", label: "对象" },
      { prop: "status", label: "状态" }
    ],
    loader: async () => (await fetchPurchaseTasks()).data || []
  },
  "联邦学习状态": {
    processText: "过程：节点在线检测→轮次聚合→指标监控",
    columns: [
      { prop: "record_code", label: "轮次编号", width: 180 },
      { prop: "clinic_id", label: "节点院区" },
      { prop: "status", label: "状态" }
    ],
    loader: async () => (await fetchAppointments({})).data || []
  }
};

const processText = computed(() => moduleConfig[title.value]?.processText || "标准业务流程：录入→校验→处理→追踪");
const columns = computed(() => moduleConfig[title.value]?.columns || []);
const highPriorityCount = computed(() =>
  rows.value.filter((x) => Number(x.priority_score || 0) >= 80 || String(x.urgency_level || "").includes("急诊")).length
);

function mapStatus(status) {
  if (status === "待诊") return "🕐待诊";
  if (status === "就诊中") return "🩺就诊中";
  if (status === "已完成") return "✅已完成";
  if (status === "急诊") return "🚨急诊";
  return status || "-";
}

async function renderChart() {
  await nextTick();
  if (!chartRef.value) return;
  if (!chart) chart = echarts.init(chartRef.value);
  const statusMap = new Map();
  for (const row of rows.value) {
    const key = String(row.status || row.urgency_level || "未知");
    statusMap.set(key, (statusMap.get(key) || 0) + 1);
  }
  chart.setOption({
    tooltip: { trigger: "item" },
    legend: { top: 0 },
    series: [
      {
        type: "pie",
        radius: ["35%", "62%"],
        data: Array.from(statusMap.entries()).map(([name, value]) => ({ name, value }))
      }
    ]
  });
}

async function loadData() {
  loading.value = true;
  try {
    const loader = moduleConfig[title.value]?.loader;
    rows.value = loader ? await loader() : [];
    lastUpdated.value = new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
    await renderChart();
  } catch (error) {
    ElMessage.error(getErrorMessage(error, `${title.value}数据加载失败`));
  } finally {
    loading.value = false;
  }
}

onMounted(loadData);
</script>

<style scoped>
.page { padding: 16px; }
.header-row { display: flex; align-items: center; justify-content: space-between; }
.mb12 { margin-bottom: 12px; }
.k { color: #909399; }
.v { font-size: 28px; font-weight: 700; color: #42b983; }
.v.warning { color: #e6a23c; }
.chart { width: 100%; height: 280px; margin-bottom: 10px; }
.list-meta { margin-top: 10px; color: #909399; font-size: 12px; }
</style>

