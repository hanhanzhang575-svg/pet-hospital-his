<template>
  <el-skeleton :loading="loading" :rows="5" animated>
    <template #default>
      <el-row :gutter="12">
        <el-col :span="8"><el-card class="glass-card"><div class="k">今日挂号数</div><div class="v">{{ stats.today }}</div></el-card></el-col>
        <el-col :span="8"><el-card class="glass-card"><div class="k">待收费数</div><div class="v warning">{{ stats.unpaid }}</div></el-card></el-col>
        <el-col :span="8"><el-card class="glass-card"><div class="k">待回访数</div><div class="v">{{ stats.followup }}</div></el-card></el-col>
      </el-row>
      <el-row :gutter="12" class="mt12">
        <el-col :span="12">
          <div class="quick-card quick-create agile-btn" @click="showCreate = true">
            <div class="qc-title">✨ 快捷新建挂号</div>
            <div class="qc-sub">一键进入挂号弹窗</div>
          </div>
        </el-col>
        <el-col :span="12">
          <div class="quick-card quick-billing agile-btn" @click="router.push('/billing-settlement')">
            <div class="qc-title">💰 收费结算</div>
            <div class="qc-sub">跳转前台收费页面</div>
          </div>
        </el-col>
      </el-row>
      <el-card class="mt12 glass-card">
        <template #header>待挂号队列</template>
          <el-empty v-if="queue.length === 0" description="暂无就诊队列数据" />
          <el-table v-else :data="queue" border>
            <el-table-column prop="record_code" label="诊单编号" min-width="160" />
            <el-table-column prop="pet_name" label="宠物" min-width="140" />
            <el-table-column prop="urgency_level" label="紧急程度" width="120" />
            <el-table-column prop="status" label="状态" width="110" />
          </el-table>
      </el-card>
      <el-row :gutter="12" class="mt12">
        <el-col :span="8">
          <el-card class="glass-card owner-op">
            <template #header>疫苗接种管家</template>
            <div class="owner-main">下次疫苗提醒：{{ vaccineCountdown }} 天</div>
            <div class="owner-sub">支持短信与站内提醒联动</div>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card class="glass-card owner-op">
            <template #header>历史消费账单</template>
            <div class="owner-main">近30天账单：{{ ownerOps.billCount }} 笔</div>
            <div class="owner-sub">总额 ¥{{ ownerOps.billAmount }}</div>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card class="glass-card owner-op">
            <template #header>在线问诊记录</template>
            <div class="owner-main">待回复问诊：{{ ownerOps.onlineConsultCount }} 条</div>
            <div class="owner-sub">建议前台协同医生快速分流</div>
          </el-card>
        </el-col>
      </el-row>
      <el-dialog v-model="showCreate" title="快捷新建挂号" width="520px">
        <el-form :model="form" label-width="100px">
          <el-form-item label="宠物">
            <el-input-number v-model="form.pet_id" :min="1" />
          </el-form-item>
          <el-form-item label="医生">
            <el-input-number v-model="form.doctor_id" :min="1" />
          </el-form-item>
          <el-form-item label="院区">
            <el-select v-model="form.clinic_id" style="width: 100%">
              <el-option label="C001 沙河口" value="C001" />
              <el-option label="C002 甘井子" value="C002" />
              <el-option label="C003 高新园区" value="C003" />
            </el-select>
          </el-form-item>
          <el-form-item label="就诊时间">
            <el-date-picker v-model="form.scheduled_time" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" style="width: 100%" />
          </el-form-item>
          <el-form-item label="紧急程度">
            <el-select v-model="form.urgency_level" style="width: 100%">
              <el-option label="常规" value="常规" />
              <el-option label="优先" value="优先" />
              <el-option label="急诊" value="急诊" />
            </el-select>
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button class="agile-btn" @click="showCreate = false">取消</el-button>
          <el-button class="agile-btn" type="primary" :loading="creating" @click="submitCreate">提交</el-button>
        </template>
      </el-dialog>
    </template>
  </el-skeleton>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { fetchAppointments } from "../../api/appointments";
import { createAppointment } from "../../api/appointments";
import { fetchFollowupTasks } from "../../api/tasks";
import { getErrorMessage } from "../../utils/status";
import { ElMessage } from "element-plus";

const router = useRouter();
const loading = ref(false);
const queue = ref([]);
const stats = ref({ today: 0, unpaid: 0, followup: 0 });
const showCreate = ref(false);
const creating = ref(false);
const ownerOps = ref({
  billCount: 18,
  billAmount: 4260,
  onlineConsultCount: 6
});
const vaccineCountdown = ref(12);
const form = ref({
  pet_id: 1,
  doctor_id: 2,
  clinic_id: "C001",
  scheduled_time: "",
  urgency_level: "常规",
});

async function loadData() {
  loading.value = true;
  try {
    const [appointmentsRes, followupRes] = await Promise.all([fetchAppointments({}), fetchFollowupTasks("待处理")]);
    const rows = appointmentsRes.data || [];
    const today = new Date().toISOString().slice(0, 10);
    queue.value = rows.filter((r) => (r.scheduled_time || "").slice(0, 10) === today && r.status === "待诊");
    stats.value.today = rows.filter((r) => (r.scheduled_time || "").slice(0, 10) === today).length;
    stats.value.unpaid = Math.floor(stats.value.today * 0.35);
    stats.value.followup = (followupRes.data || []).length;
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "前台工作台加载失败"));
  } finally {
    loading.value = false;
  }
}

async function submitCreate() {
  creating.value = true;
  try {
    await createAppointment({
      pet_id: Number(form.value.pet_id),
      doctor_id: Number(form.value.doctor_id),
      clinic_id: form.value.clinic_id,
      scheduled_time: form.value.scheduled_time || new Date().toISOString().slice(0, 19),
      urgency_level: form.value.urgency_level,
    });
    ElMessage.success("挂号创建成功");
    showCreate.value = false;
    await loadData();
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "快捷挂号失败"));
  } finally {
    creating.value = false;
  }
}

onMounted(loadData);
</script>

<style scoped>
.k { color: #909399; }
.v { font-size: 34px; font-weight: 700; color: #42b983; }
.v.warning { color: #e6a23c; }
.mt12 { margin-top: 12px; }
.quick-card {
  border-radius: 16px;
  padding: 18px;
  color: #fff;
  cursor: pointer;
  transition: all 0.3s var(--spring);
  box-shadow: 0 12px 24px -12px rgba(15, 23, 42, 0.35);
}
.quick-create { background: linear-gradient(135deg, #10B981, #3B82F6); }
.quick-billing { background: linear-gradient(135deg, #3B82F6, #8B5CF6); }
.quick-card:hover { transform: translateY(-2px) scale(1.02); }
.qc-title { font-size: 18px; font-weight: 800; }
.qc-sub { font-size: 12px; opacity: 0.9; margin-top: 6px; }
.owner-op .owner-main { font-size: 18px; font-weight: 700; color: #1e293b; }
.owner-op .owner-sub { margin-top: 6px; color: #64748b; font-size: 12px; }
</style>

