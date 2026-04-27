<template>
  <div class="page">
    <el-card class="glass-card">
      <template #header>
        <div class="header-row">
          <span>药房工作台 - 待发药队列（已缴费）</span>
          <el-space>
            <el-button :loading="loading" :disabled="loading" @click="loadData">刷新</el-button>
            <el-tag type="success">仅展示已缴费待发药处方</el-tag>
          </el-space>
        </div>
      </template>

      <el-skeleton :loading="loading" :rows="6" animated>
        <template #default>
          <el-alert v-if="loadError" type="error" :title="loadError" show-icon :closable="false" style="margin-bottom: 12px">
            <template #default><el-button size="small" @click="loadData">重试</el-button></template>
          </el-alert>
          <el-empty v-if="rows.length === 0" description="暂无待配药处方，可以休息一下 ☕" />
          <el-table v-else :data="rows" border>
            <el-table-column prop="prescription_code" label="处方编号" min-width="180" />
            <el-table-column prop="pet_name" label="患者" width="180">
              <template #default="{ row }">
                <el-popover placement="right" :width="220" trigger="hover">
                  <template #reference>
                    <el-text>{{ row.pet_name || "-" }}</el-text>
                  </template>
                  <div class="pet-pop">
                    <el-avatar shape="square" :size="56">宠物</el-avatar>
                    <div>
                      <div><strong>{{ row.pet_name || "未知宠物" }}</strong></div>
                      <div>品种：{{ row.pet_breed || "-" }}</div>
                      <div>年龄：{{ getAgeText(row.pet_birth_date) }}</div>
                    </div>
                  </div>
                </el-popover>
              </template>
            </el-table-column>
            <el-table-column label="药品列表" min-width="200">
              <template #default="{ row }">
                {{ (row.drug_list || []).join("、") || "-" }}
              </template>
            </el-table-column>
            <el-table-column prop="medical_record_id" label="病历ID" width="100" />
            <el-table-column prop="created_at" label="开具时间" min-width="170" />
            <el-table-column label="状态" width="120">
              <template #default="{ row }">
                <el-tag :type="getStatusTagType(row.status)">
                  {{ mapStatus(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
          <div class="list-meta">
            共{{ rows.length }}条记录，最后更新时间 {{ lastUpdated || "--:--" }}
          </div>
        </template>
      </el-skeleton>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from "vue";
import { ElMessage } from "element-plus";

import { fetchPrescriptions } from "../api/prescriptions";
import { getErrorMessage, getStatusTagType } from "../utils/status";

const loading = ref(false);
const loadError = ref("");
const rows = ref([]);
const lastUpdated = ref("");
let timer = null;

function getAgeText(birthDate) {
  if (!birthDate) return "-";
  const birth = new Date(birthDate);
  if (Number.isNaN(birth.getTime())) return "-";
  const years = Math.max(0, Math.floor((Date.now() - birth.getTime()) / 31536000000));
  return `${years}岁`;
}

function mapStatus(status) {
  if (status === "已缴费") return "✅ 已缴费待发药";
  if (status === "已发药") return "✅已发药";
  if (status === "已失效") return "❌已失效";
  return status;
}

async function loadData() {
  loading.value = true;
  loadError.value = "";
  try {
    const result = await fetchPrescriptions("C001");
    rows.value = (result.data || []).filter((item) => item.status === "已缴费");
    lastUpdated.value = new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
  } catch (error) {
    loadError.value = getErrorMessage(error, "处方列表加载失败");
    ElMessage.error(loadError.value);
  } finally {
    loading.value = false;
  }
}

onMounted(async () => {
  await loadData();
  timer = window.setInterval(async () => {
    await loadData();
  }, 30000);
});

onUnmounted(() => {
  if (timer) window.clearInterval(timer);
});
</script>

<style scoped>
.page {
  padding: 16px;
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pet-pop {
  display: grid;
  grid-template-columns: 56px 1fr;
  gap: 10px;
  align-items: center;
}
.list-meta { margin-top: 10px; color: #909399; font-size: 12px; }
</style>

