<template>
  <div class="page">
    <el-card class="glass-card">
      <template #header>
        <div class="header-row">
          <span>数据库探测器（Database Explorer）</span>
          <el-button type="primary" @click="reload">刷新</el-button>
        </div>
      </template>
      <el-tabs v-model="activeTable" @tab-change="onTableChange">
        <el-tab-pane v-for="name in tables" :key="name" :label="name" :name="name">
          <el-table :data="rows" border>
            <el-table-column v-for="col in columns" :key="col" :prop="col" :label="colLabel(col)" min-width="150">
              <template #default="{ row }">
                <el-link
                  v-if="name === 'medical_records' && col === 'pet_id'"
                  type="primary"
                  @click="tracePet(row)"
                >
                  {{ row[col] }}
                </el-link>
                <span v-else>{{ row[col] }}</span>
              </template>
            </el-table-column>
          </el-table>
          <el-pagination
            style="margin-top: 12px"
            layout="total, prev, pager, next"
            :total="total"
            :page-size="size"
            :current-page="page"
            @current-change="onPageChange"
          />
        </el-tab-pane>
      </el-tabs>
    </el-card>
    <el-card v-if="traceResult" class="glass-card" style="margin-top:12px;border:1px solid #67c23a;">
      <template #header>数据溯源高亮（病历 -> 宠物）</template>
      <div>病历ID：{{ traceResult.record_id }}</div>
      <div>宠物ID：<strong style="color:#67c23a">{{ traceResult.pet_id }}</strong></div>
      <div>宠物名称：{{ traceResult.pet_name }}（{{ traceResult.pet_species }}）</div>
      <div>主人ID：{{ traceResult.owner_id }}</div>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import { fetchDataCenterTables, fetchTableRows, traceMedicalRecord } from "../api/dataCenter";
import { getErrorMessage } from "../utils/status";

const tables = ref([]);
const activeTable = ref("");
const columns = ref([]);
const pkColumns = ref([]);
const fkColumns = ref([]);
const rows = ref([]);
const page = ref(1);
const size = ref(20);
const total = ref(0);
const traceResult = ref(null);

function colLabel(col) {
  const marks = [];
  if (pkColumns.value.includes(col)) marks.push("🔑");
  if (fkColumns.value.includes(col)) marks.push("🔗");
  return `${col}${marks.length ? ` ${marks.join("")}` : ""}`;
}

async function loadTables() {
  const res = await fetchDataCenterTables();
  tables.value = res.data || [];
  activeTable.value = tables.value[0] || "";
}

async function loadRows() {
  if (!activeTable.value) return;
  const res = await fetchTableRows(activeTable.value, page.value, size.value);
  const data = res.data || {};
  columns.value = data.columns || [];
  pkColumns.value = data.pk_columns || [];
  fkColumns.value = data.fk_columns || [];
  rows.value = data.rows || [];
  total.value = Number(data.total || 0);
}

async function reload() {
  try {
    await loadTables();
    page.value = 1;
    await loadRows();
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "数据中心加载失败"));
  }
}

async function onTableChange() {
  page.value = 1;
  traceResult.value = null;
  await loadRows();
}

async function onPageChange(nextPage) {
  page.value = nextPage;
  await loadRows();
}

async function tracePet(row) {
  try {
    const res = await traceMedicalRecord(row.id);
    traceResult.value = res.data || null;
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "数据溯源失败"));
  }
}

onMounted(reload);
</script>

<style scoped>
.page { padding: 16px; }
.header-row { display: flex; justify-content: space-between; align-items: center; }
</style>

