<template>
  <el-skeleton :loading="loading" :rows="5" animated>
    <template #default>
      <el-row :gutter="12">
        <el-col :span="8"><el-card class="glass-card"><div class="k">待发药处方数</div><div class="v">{{ stats.pendingRx }}</div></el-card></el-col>
        <el-col :span="8"><el-card class="glass-card"><div class="k">低库存数</div><div class="v warning">{{ stats.lowStock }}</div></el-card></el-col>
        <el-col :span="8"><el-card class="glass-card"><div class="k">临期药品数</div><div class="v danger">{{ stats.expiring }}</div></el-card></el-col>
      </el-row>
      <el-card class="mt12 glass-card">
        <template #header>待发药列表（已缴费）</template>
        <el-empty v-if="rows.length === 0" description="暂无待发药数据" />
        <el-table v-else :data="rows" border>
          <el-table-column prop="prescription_code" label="处方编号" min-width="180" />
          <el-table-column prop="pet_name" label="患者" width="140" />
          <el-table-column prop="status" label="状态" width="110" />
        </el-table>
      </el-card>
    </template>
  </el-skeleton>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import { fetchPrescriptions } from "../../api/prescriptions";
import { fetchInventoryOverview, fetchExpiryWarnings } from "../../api/inventory";
import { getErrorMessage } from "../../utils/status";

const loading = ref(false);
const rows = ref([]);
const stats = ref({ pendingRx: 0, lowStock: 0, expiring: 0 });

async function loadData() {
  loading.value = true;
  try {
    const [rxRes, invRes, expRes] = await Promise.all([fetchPrescriptions("C001"), fetchInventoryOverview("C001"), fetchExpiryWarnings(30)]);
    const paidRows = (rxRes.data || []).filter((r) => r.status === "已缴费");
    rows.value = paidRows.slice(0, 8);
    const invRows = invRes.data || [];
    stats.value.pendingRx = paidRows.length;
    stats.value.lowStock = invRows.filter((i) => Number(i.stock_qty || 0) < Number(i.safety_stock || 0)).length;
    stats.value.expiring = (expRes.data || []).length;
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "药房工作台加载失败"));
  } finally {
    loading.value = false;
  }
}

onMounted(loadData);
</script>

<style scoped>
.k { color: #909399; }
.v { font-size: 34px; font-weight: 700; color: #42b983; }
.v.warning { color: #e6a23c; }
.v.danger { color: #f56c6c; }
.mt12 { margin-top: 12px; }
</style>

