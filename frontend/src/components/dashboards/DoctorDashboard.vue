<template>
  <el-skeleton :loading="loading" :rows="6" animated>
    <template #default>
      <el-row :gutter="12">
        <el-col :span="8"><el-card class="glass-card"><div class="k">待诊患者数</div><div class="v danger">{{ stats.pending }}</div></el-card></el-col>
        <el-col :span="8">
          <el-card class="clickable glass-card" @click="alertsVisible = true">
            <div class="k">AI预警数</div>
            <div class="v warning">{{ stats.aiAlerts }}</div>
          </el-card>
        </el-col>
        <el-col :span="8"><el-card class="glass-card"><div class="k">待审阅报告数</div><div class="v">{{ stats.reports }}</div></el-card></el-col>
      </el-row>
      <div class="ai-banner mt12">
        <div class="left">
          <div class="title">🤖 AI辅助诊断</div>
          <div class="sub">基于KG-RAG知识图谱+多模态影像联合推理</div>
        </div>
        <el-button class="agile-btn" type="primary" @click="router.push('/ai-diagnosis')">立即使用</el-button>
      </div>
      <el-card class="mt12 glass-card">
        <template #header>
          <div class="header-row">
            <span>待诊队列（含优先级）</span>
            <el-tag :type="aiListening ? 'success' : 'info'">AI监听：{{ aiListening ? "监听中" : "已停止" }}</el-tag>
          </div>
        </template>
        <el-empty v-if="queue.length === 0" description="今日暂无待诊患者">
          <el-button class="agile-btn" type="primary" @click="router.push('/appointments')">新建挂号</el-button>
        </el-empty>
        <el-table v-else :data="queue" border>
          <el-table-column prop="record_code" label="诊单编号" min-width="160" />
          <el-table-column prop="pet_name" label="宠物" min-width="120" />
          <el-table-column label="优先级评分" min-width="220">
            <template #default="{ row }">
              <el-space direction="vertical" alignment="start">
                <span>{{ row.priority_score ?? 0 }}</span>
                <el-progress :percentage="Math.min(100, Number(row.priority_score) || 0)" :stroke-width="8" />
              </el-space>
            </template>
          </el-table-column>
          <el-table-column prop="urgency_level" label="紧急程度" width="140">
            <template #default="{ row }">
              <el-tag v-if="row.urgency_level === '急诊'" type="danger">🚨 急诊</el-tag>
              <el-tag v-else-if="row.urgency_level === '优先'" type="warning">⚡ 优先</el-tag>
              <el-tag v-else type="info">{{ row.urgency_level }}</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
      <el-drawer v-model="alertsVisible" title="AI预警详情" size="460px">
        <el-empty v-if="alertRows.length === 0" description="暂无预警数据" />
        <el-table v-else :data="alertRows" border>
          <el-table-column prop="record_code" label="诊单编号" min-width="140" />
          <el-table-column prop="pet_name" label="宠物" min-width="120" />
          <el-table-column prop="priority_score" label="评分" width="90" />
          <el-table-column label="预警级别" width="110">
            <template #default><el-tag type="danger">error</el-tag></template>
          </el-table-column>
        </el-table>
      </el-drawer>
    </template>
  </el-skeleton>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { fetchPendingQueue } from "../../api/vetWorkbench";
import { getErrorMessage } from "../../utils/status";

const router = useRouter();
const loading = ref(false);
const queue = ref([]);
const aiListening = ref(true);
const stats = ref({ pending: 0, aiAlerts: 0, reports: 0 });
const alertsVisible = ref(false);
const alertRows = ref([]);

async function loadData() {
  loading.value = true;
  try {
    const result = await fetchPendingQueue();
    queue.value = (result.data || []).sort((a, b) => Number(b.priority_score || 0) - Number(a.priority_score || 0));
    stats.value.pending = queue.value.length;
    stats.value.aiAlerts = queue.value.filter((x) => x.urgency_level === "急诊").length;
    stats.value.reports = Math.max(0, Math.floor(queue.value.length * 0.6));
    alertRows.value = queue.value.filter((x) => x.urgency_level === "急诊");
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "医生工作台加载失败"));
  } finally {
    loading.value = false;
  }
}

onMounted(loadData);
</script>

<style scoped>
.k { color: #909399; }
.v { font-size: 34px; font-weight: 700; color: #42b983; }
.v.danger { color: #f56c6c; }
.v.warning { color: #e6a23c; }
.mt12 { margin-top: 12px; }
.header-row { display: flex; justify-content: space-between; align-items: center; }
.clickable { cursor: pointer; }
.ai-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  border-radius: 14px;
  border: 1px solid rgba(59,130,246,0.25);
  background: linear-gradient(135deg, rgba(59,130,246,0.1), rgba(139,92,246,0.1));
}
.ai-banner .title { font-weight: 800; color: #1e293b; }
.ai-banner .sub { font-size: 12px; color: #475569; margin-top: 4px; }
</style>

