<template>
  <div class="dispatch-page">
    <el-row :gutter="12">
      <el-col :xs="24" :lg="15">
        <el-card class="glass-card" shadow="never">
          <template #header><span>跨院区协调中心（总览）</span></template>
          <el-table :data="rows" border stripe>
            <el-table-column prop="clinic_name" label="院区" width="140" />
            <el-table-column prop="doctor_load" label="医生负载" width="110" />
            <el-table-column prop="cage_idle" label="空闲笼舍" width="110" />
            <el-table-column prop="daily_completed_visits" label="当日门诊完成数" width="140" />
            <el-table-column prop="daily_surgeries" label="手术台数" width="110" />
            <el-table-column prop="inventory_risk" label="库存风险" width="110" />
            <el-table-column label="操作" width="240" fixed="right">
              <template #default="{ row }">
                <el-space>
                  <el-button class="agile-btn" type="success" size="small" @click="openReferral(row)">发起转诊</el-button>
                  <el-button class="agile-btn" type="primary" size="small" :disabled="row.doctor_load !== '高'" @click="openSupport(row)">医生支援</el-button>
                </el-space>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="9">
        <el-card class="glass-card" shadow="never">
          <template #header><span>调度流量图（模拟）</span></template>
          <div ref="flowRef" class="chart" />
          <el-divider />
          <div class="flow-hint">
            <div>建议：优先将高负载院区的慢病复诊转移到空闲院区。</div>
            <div>策略：先转诊后支援，避免双向资源冲突。</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="glass-card" style="margin-top: 12px" shadow="never">
      <template #header><span>转诊记录</span></template>
      <el-table :data="referrals" border>
        <el-table-column prop="pet_name" label="患宠" min-width="160" />
        <el-table-column prop="from_clinic_name" label="来源院区" width="120" />
        <el-table-column prop="to_clinic_name" label="目标院区" width="120" />
        <el-table-column prop="target_cage_code" label="目标笼舍" width="120" />
        <el-table-column prop="reason" label="转诊原因" min-width="180" />
        <el-table-column prop="eta_time" label="预计转诊时间" min-width="160" />
        <el-table-column prop="status" label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="row.status === '待接收' ? 'warning' : row.status === '已接收' ? 'info' : 'success'">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="referralVisible" title="发起转诊" width="620px">
      <el-form :model="referralForm" label-width="110px">
        <el-form-item label="患宠">
          <el-select v-model="referralForm.pet_id" filterable style="width: 100%">
            <el-option v-for="pet in pets" :key="pet.id" :label="`${pet.name}(${pet.species}/${pet.breed || '-'})`" :value="pet.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="目标院区">
          <el-select v-model="referralForm.to_clinic_id" style="width: 100%" @change="loadCages">
            <el-option label="C001 沙河口" value="C001" />
            <el-option label="C002 甘井子" value="C002" />
            <el-option label="C003 高新园区" value="C003" />
          </el-select>
        </el-form-item>
        <el-form-item label="目标笼舍">
          <el-select v-model="referralForm.target_cage_id" style="width: 100%">
            <el-option v-for="c in cages" :key="c.id" :label="`${c.cage_code}(${c.zone_type})`" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="转诊原因"><el-input v-model="referralForm.reason" type="textarea" :rows="3" /></el-form-item>
        <el-form-item label="预计转诊时间"><el-date-picker v-model="referralForm.eta_time" type="datetime" style="width:100%" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button class="agile-btn" @click="referralVisible = false">取消</el-button>
        <el-button class="agile-btn" type="success" :loading="submittingReferral" @click="submitReferral">提交</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="supportVisible" title="医生支援申请" width="560px">
      <el-form :model="supportForm" label-width="110px">
        <el-form-item label="目标院区">
          <el-select v-model="supportForm.to_clinic_id" style="width: 100%" @change="loadDoctors">
            <el-option label="C001 沙河口" value="C001" />
            <el-option label="C002 甘井子" value="C002" />
            <el-option label="C003 高新园区" value="C003" />
          </el-select>
        </el-form-item>
        <el-form-item label="支援医生">
          <el-select v-model="supportForm.target_doctor_id" style="width:100%">
            <el-option v-for="d in doctors" :key="d.id" :label="d.full_name" :value="d.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="支援时段"><el-input v-model="supportForm.support_period" placeholder="例如：本周三 14:00-18:00" /></el-form-item>
        <el-form-item label="支援原因"><el-input v-model="supportForm.reason" type="textarea" :rows="3" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button class="agile-btn" @click="supportVisible = false">取消</el-button>
        <el-button class="agile-btn" type="primary" :loading="submittingSupport" @click="submitSupport">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import * as echarts from "echarts";
import { nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import http from "../api/http";
import { fetchPets } from "../api/pets";
import { fetchDoctors } from "../api/users";
import { getErrorMessage } from "../utils/status";

const rows = ref([]);
const referrals = ref([]);
const pets = ref([]);
const doctors = ref([]);
const cages = ref([]);
const flowRef = ref(null);
let flowChart = null;

const referralVisible = ref(false);
const supportVisible = ref(false);
const submittingReferral = ref(false);
const submittingSupport = ref(false);

const referralForm = ref({
  pet_id: null,
  from_clinic_id: "C001",
  to_clinic_id: "C002",
  target_cage_id: null,
  reason: "",
  eta_time: ""
});
const supportForm = ref({
  from_clinic_id: "C001",
  to_clinic_id: "C002",
  target_doctor_id: null,
  support_period: "",
  reason: ""
});

function renderFlow() {
  if (flowRef.value && !flowChart) flowChart = echarts.init(flowRef.value);
  const points = rows.value.map((x, idx) => ({ name: x.clinic_name, value: [idx * 130 + 40, idx % 2 ? 180 : 80] }));
  flowChart?.setOption({
    xAxis: { show: false, min: 0, max: 320 },
    yAxis: { show: false, min: 0, max: 260 },
    series: [
      {
        type: "graph",
        coordinateSystem: "cartesian2d",
        symbolSize: 56,
        label: { show: true, formatter: "{b}" },
        data: points,
        links: [
          { source: 0, target: 1, lineStyle: { width: 3, color: "#3b82f6" } },
          { source: 1, target: 2, lineStyle: { width: 2, color: "#22c55e" } },
          { source: 2, target: 0, lineStyle: { width: 2, color: "#f59e0b" } }
        ],
        lineStyle: { curveness: 0.2 },
        roam: false
      }
    ]
  });
}

async function loadOverview() {
  const res = await http.get("/tasks/coordination/overview");
  rows.value = res.data || [];
}

async function loadReferrals() {
  const res = await http.get("/tasks/coordination/referrals");
  referrals.value = res.data || [];
}

async function loadBaseData() {
  const petRes = await fetchPets();
  pets.value = petRes.data || [];
}

async function loadCages() {
  if (!referralForm.value.to_clinic_id) return;
  const res = await http.get("/tasks/coordination/available-cages", { params: { clinic_id: referralForm.value.to_clinic_id } });
  cages.value = res.data || [];
}

async function loadDoctors() {
  const res = await fetchDoctors(supportForm.value.to_clinic_id || "");
  doctors.value = res.data || [];
}

function openReferral(row) {
  referralForm.value.from_clinic_id = row.clinic_id;
  referralForm.value.to_clinic_id = row.clinic_id === "C001" ? "C002" : "C001";
  referralVisible.value = true;
  loadCages();
}

function openSupport(row) {
  supportForm.value.from_clinic_id = row.clinic_id;
  supportForm.value.to_clinic_id = row.clinic_id === "C001" ? "C003" : "C001";
  supportVisible.value = true;
  loadDoctors();
}

async function submitReferral() {
  submittingReferral.value = true;
  try {
    await http.post("/tasks/coordination/referrals", {
      ...referralForm.value,
      eta_time: referralForm.value.eta_time ? new Date(referralForm.value.eta_time).toISOString() : null
    });
    ElMessage.success("转诊申请已提交并通知目标院区护士");
    referralVisible.value = false;
    await loadReferrals();
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "转诊提交失败"));
  } finally {
    submittingReferral.value = false;
  }
}

async function submitSupport() {
  submittingSupport.value = true;
  try {
    await http.post("/tasks/coordination/doctor-support", supportForm.value);
    ElMessage.success("医生支援申请已提交并通知目标医生与两院区主任");
    supportVisible.value = false;
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "支援申请失败"));
  } finally {
    submittingSupport.value = false;
  }
}

onMounted(async () => {
  try {
    await Promise.all([loadOverview(), loadReferrals(), loadBaseData()]);
    await nextTick();
    renderFlow();
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "协调中心加载失败"));
  }
});

onBeforeUnmount(() => {
  flowChart?.dispose();
});
</script>

<style scoped>
.dispatch-page { padding: 16px; background: linear-gradient(145deg, #f6fbff 0%, #fff8ef 100%); }
.glass-card { border-radius: 20px; }
.chart { height: 280px; }
.flow-hint { color: #475569; font-size: 13px; line-height: 1.8; display: grid; gap: 6px; }
</style>
