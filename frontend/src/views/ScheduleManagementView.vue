<template>
  <div class="schedule-page">
    <el-card class="hero-card" shadow="never">
      <div class="hero-row">
        <div>
          <div class="eyebrow">Scheduling Studio</div>
          <h2>排班与号源调度</h2>
          <p>统一查看门诊号源、运营建议与 OR-Tools 自动排班结果。算法会自动补足演示医生和护士，避免人员池过小导致无结果。</p>
        </div>
        <el-space wrap>
          <el-select v-model="clinicId" style="width: 160px" @change="loadAll">
            <el-option label="C001 沙河口" value="C001" />
            <el-option label="C002 甘井子" value="C002" />
            <el-option label="C003 高新区" value="C003" />
          </el-select>
          <el-date-picker v-model="weekPicker" type="week" format="[第] ww [周]" value-format="YYYY-MM-DD" @change="loadAll" />
          <el-button :loading="copying" @click="copyLastWeek">复制上周</el-button>
          <el-button type="primary" :loading="loading || algorithmLoading" @click="loadAll">刷新</el-button>
        </el-space>
      </div>
    </el-card>

    <el-card class="algorithm-card" shadow="never">
      <template #header>
        <div class="panel-header">
          <div>
            <div class="panel-title">OR-Tools CP-SAT 排班算法</div>
            <div class="panel-subtitle">按医生/护士角色分别求解，覆盖早班、中班、晚班，并控制连续工作与晚班均衡。</div>
          </div>
          <el-tag :type="algorithmAssignments.length ? 'success' : 'info'" effect="plain">
            {{ algorithmAssignments.length ? `已生成 ${algorithmAssignments.length} 条` : "暂无算法结果" }}
          </el-tag>
        </div>
      </template>

      <div class="algorithm-layout">
        <section class="algorithm-control">
          <div class="control-title">生成参数</div>
          <el-form label-position="top">
            <el-form-item label="开始日期">
              <el-date-picker v-model="algorithmStartDate" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
            <el-form-item label="排班天数">
              <el-input-number v-model="algorithmDays" :min="1" :max="31" style="width: 100%" />
            </el-form-item>
            <el-form-item label="覆盖旧数据">
              <el-switch v-model="overwriteExisting" active-text="覆盖" inactive-text="追加" />
            </el-form-item>
          </el-form>
          <el-button class="generate-btn" type="primary" :loading="generating" @click="handleGenerateSchedule">
            运行排班算法
          </el-button>
          <div v-if="generationMessage" class="generation-message">{{ generationMessage }}</div>
        </section>

        <section class="staff-panel">
          <div class="staff-head">
            <div>
              <div class="control-title">当前员工池</div>
              <p>运行算法时会把当前院区医生、护士补足到每类至少 6 人。</p>
            </div>
            <el-button text :loading="staffLoading" @click="loadStaff">刷新员工池</el-button>
          </div>

          <div class="staff-grid">
            <div class="staff-box">
              <div class="staff-count">{{ staff.doctor.count }}</div>
              <div class="staff-label">医生</div>
              <div class="staff-list">
                <el-tag v-for="item in staff.doctor.items.slice(0, 8)" :key="item.employee_id" effect="plain">
                  {{ item.employee_name }}
                </el-tag>
              </div>
            </div>
            <div class="staff-box">
              <div class="staff-count">{{ staff.nurse.count }}</div>
              <div class="staff-label">护士</div>
              <div class="staff-list">
                <el-tag v-for="item in staff.nurse.items.slice(0, 8)" :key="item.employee_id" type="success" effect="plain">
                  {{ item.employee_name }}
                </el-tag>
              </div>
            </div>
          </div>
        </section>
      </div>

      <div class="algorithm-metrics">
        <div v-for="item in algorithmMetrics" :key="item.label" class="algorithm-metric">
          <div class="metric-mini-label">{{ item.label }}</div>
          <div class="metric-mini-value">{{ item.value }}</div>
          <div class="metric-mini-note">{{ item.note }}</div>
        </div>
      </div>

      <el-empty v-if="!algorithmAssignments.length && !algorithmLoading" description="还没有算法排班结果，点击上方按钮生成" />
      <div v-else class="schedule-grid" v-loading="algorithmLoading">
        <div v-for="day in algorithmCalendar" :key="day.date" class="schedule-day">
          <div class="schedule-day-head">
            <strong>{{ day.label }}</strong>
            <span>{{ day.date.slice(5) }}</span>
          </div>
          <div v-for="shift in shiftOrder" :key="`${day.date}-${shift}`" class="shift-row">
            <div class="shift-name">{{ shift }}</div>
            <div class="shift-people">
              <span v-for="item in day.shifts[shift]" :key="item.assignment_id" :class="['person-pill', item.role_name]">
                {{ roleText(item.role_name) }} · {{ item.employee_name }}
              </span>
              <span v-if="!day.shifts[shift].length" class="empty-pill">未生成</span>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <el-row :gutter="12" class="kpi-row">
      <el-col v-for="item in kpiCards" :key="item.label" :xs="12" :lg="6">
        <el-card class="kpi-card" shadow="never">
          <div class="kpi-label">{{ item.label }}</div>
          <div class="kpi-value" :class="item.tone">{{ item.value }}</div>
          <div class="kpi-note">{{ item.note }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="12">
      <el-col :xs="24" :lg="9">
        <el-card class="panel-card" shadow="never">
          <template #header>
            <div class="panel-title">智能调度建议</div>
          </template>
          <el-alert
            type="info"
            :closable="false"
            show-icon
            style="margin-bottom: 10px"
            title="基于近 30 天同日同时段需求预测、当前利用率和同科室负载均衡，优先给出扩容或分流建议。"
          />
          <el-collapse v-if="recommendations.length" accordion>
            <el-collapse-item v-for="(item, index) in recommendations.slice(0, 8)" :key="`${index}-${item.message}`" :name="String(index)">
              <template #title>
                <div class="recommend-title">
                  <el-tag :type="priorityType(item.priority)">{{ priorityText(item.priority) }}</el-tag>
                  <span>{{ item.doctor_name || "院区建议" }}</span>
                </div>
              </template>
              <div class="recommend-body">{{ item.message }}</div>
            </el-collapse-item>
          </el-collapse>
          <el-empty v-else description="暂无建议" />
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="15">
        <el-card class="panel-card" shadow="never">
          <template #header>
            <div class="panel-title">医生负载与剩余容量</div>
          </template>
          <div ref="loadBarRef" class="chart" />
        </el-card>
      </el-col>
    </el-row>

    <el-card class="panel-card" shadow="never">
      <template #header>
        <div class="panel-title">周概览</div>
      </template>
      <div class="week-strip">
        <button
          v-for="item in weekDayCards"
          :key="item.date"
          class="day-card"
          :class="{ active: selectedDate === item.date }"
          @click="selectedDate = item.date"
        >
          <div class="day-head">
            <strong>{{ item.label }}</strong>
            <span>{{ item.date.slice(5) }}</span>
          </div>
          <div class="day-metrics">
            <span>时段 {{ item.slotCount }}</span>
            <span>高峰 {{ item.peakCount }}</span>
            <span>利用率 {{ item.utilRate }}%</span>
          </div>
        </button>
      </div>
    </el-card>

    <el-row :gutter="12">
      <el-col :xs="24" :lg="16">
        <el-card class="panel-card" shadow="never">
          <template #header>
            <div class="panel-title">单日号源矩阵（{{ selectedDate }}）</div>
          </template>
          <el-table :data="selectedDoctorRows" border stripe v-loading="loading">
            <el-table-column prop="doctor_name" label="医生" min-width="180">
              <template #default="{ row }">
                <div class="doctor-cell">
                  <span class="avatar">{{ row.avatar || "DR" }}</span>
                  <div>
                    <div class="doctor-name">{{ row.doctor_name }}</div>
                    <div class="doctor-dept">{{ row.department || inferDepartment(row.doctor_name) }}</div>
                  </div>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="上午" min-width="220">
              <template #default="{ row }">
                <div class="slot-card" :class="slotClass(getSlot(row.id, selectedDate, 'morning'))" @click="openSlot(row, selectedDate, 'morning')">
                  <template v-if="getSlot(row.id, selectedDate, 'morning')?.appointment_id">
                    <div class="slot-line">{{ getSlot(row.id, selectedDate, "morning").booked_count }}/{{ getSlot(row.id, selectedDate, "morning").max_capacity }}</div>
                    <el-progress :percentage="quotaPercent(getSlot(row.id, selectedDate, 'morning'))" :status="quotaStatus(getSlot(row.id, selectedDate, 'morning'))" :stroke-width="8" />
                    <div class="slot-note">{{ getSlot(row.id, selectedDate, "morning").is_peak ? "预测高峰" : "常规时段" }}</div>
                  </template>
                  <template v-else>
                    <div class="slot-empty">+ 新增上午排班</div>
                  </template>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="下午" min-width="220">
              <template #default="{ row }">
                <div class="slot-card" :class="slotClass(getSlot(row.id, selectedDate, 'afternoon'))" @click="openSlot(row, selectedDate, 'afternoon')">
                  <template v-if="getSlot(row.id, selectedDate, 'afternoon')?.appointment_id">
                    <div class="slot-line">{{ getSlot(row.id, selectedDate, "afternoon").booked_count }}/{{ getSlot(row.id, selectedDate, "afternoon").max_capacity }}</div>
                    <el-progress :percentage="quotaPercent(getSlot(row.id, selectedDate, 'afternoon'))" :status="quotaStatus(getSlot(row.id, selectedDate, 'afternoon'))" :stroke-width="8" />
                    <div class="slot-note">{{ getSlot(row.id, selectedDate, "afternoon").is_peak ? "预测高峰" : "常规时段" }}</div>
                  </template>
                  <template v-else>
                    <div class="slot-empty">+ 新增下午排班</div>
                  </template>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="8">
        <el-card class="panel-card" shadow="never">
          <template #header>
            <div class="panel-title">医生排班画像</div>
          </template>
          <div class="roster-list">
            <div v-for="item in doctorRoster" :key="item.doctor_id" class="roster-card">
              <div class="roster-top">
                <strong>{{ item.doctor_name }}</strong>
                <el-tag size="small" effect="plain">{{ item.department }}</el-tag>
              </div>
              <div class="roster-meta">
                <span>本周时段 {{ item.slotCount }}</span>
                <span>已预约 {{ item.booked }}</span>
              </div>
              <div class="roster-meta">
                <span>利用率 {{ item.rate }}%</span>
                <span>院区 {{ clinicId }}</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-drawer v-model="slotDrawerVisible" :size="520" title="时段详情">
      <div class="drawer-top">
        <div>{{ drawerSlot.doctor_name }}（{{ drawerSlot.department || "综合门诊" }}）</div>
        <div>{{ drawerSlot.date }} {{ drawerSlot.period === "morning" ? "上午" : "下午" }}</div>
      </div>
      <el-table :data="slotPatients" border>
        <el-table-column prop="pet_name" label="宠物" min-width="100" />
        <el-table-column prop="owner_name" label="主人" min-width="100" />
        <el-table-column prop="urgency_level" label="紧急程度" width="100" />
        <el-table-column prop="status" label="状态" width="100" />
      </el-table>
      <div class="drawer-actions">
        <el-button type="warning" @click="openLeaveResolve">停诊处理</el-button>
      </div>
    </el-drawer>

    <el-dialog v-model="leaveDialogVisible" title="停诊处理" width="520px">
      <div class="leave-text">检测到该时段有 {{ slotPatients.length }} 条预约，是否自动转移至同科室空闲医生？</div>
      <el-form label-width="88px">
        <el-form-item label="停诊原因">
          <el-input v-model="leaveReason" placeholder="短信退号场景必填" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button type="success" :loading="saving" @click="handleLeave('auto_transfer')">自动转移</el-button>
        <el-button type="warning" :loading="saving" @click="handleLeave('sms_cancel')">短信退号</el-button>
        <el-button @click="leaveDialogVisible = false">取消</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="createDialogVisible" title="新增排班" width="520px">
      <el-form label-width="100px">
        <el-form-item label="医生">
          <el-input :model-value="createForm.doctor_name" readonly />
        </el-form-item>
        <el-form-item label="时段">
          <el-input :model-value="`${createForm.date} ${createForm.period === 'morning' ? '上午' : '下午'}`" readonly />
        </el-form-item>
        <el-form-item label="最大接诊数">
          <el-input-number v-model="createForm.max_capacity" :min="1" :max="30" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="createForm.schedule_note" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitCreate">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import * as echarts from "echarts";
import dayjs from "dayjs";
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import {
  copyScheduleFromLastWeek,
  createSchedule,
  fetchSchedulePatients,
  fetchSchedulePeakPrediction,
  fetchScheduleRecommendations,
  fetchScheduleWeek,
  resolveScheduleLeave
} from "../api/appointments";
import { fetchSchedulingAssignments, fetchSchedulingStaff, generateSchedule } from "../api/scheduling";
import { getErrorMessage } from "../utils/status";

const clinicId = ref("C001");
const weekPicker = ref(dayjs().startOf("week").add(1, "day").format("YYYY-MM-DD"));
const selectedDate = ref(dayjs().startOf("week").add(1, "day").format("YYYY-MM-DD"));
const algorithmStartDate = ref(dayjs().startOf("week").add(1, "day").format("YYYY-MM-DD"));
const algorithmDays = ref(7);
const overwriteExisting = ref(true);

const loading = ref(false);
const saving = ref(false);
const copying = ref(false);
const generating = ref(false);
const algorithmLoading = ref(false);
const staffLoading = ref(false);

const doctors = ref([]);
const slots = ref([]);
const recommendations = ref([]);
const peakMap = ref(new Set());
const algorithmAssignments = ref([]);
const generationMessage = ref("");
const staff = ref({
  doctor: { count: 0, items: [] },
  nurse: { count: 0, items: [] }
});

const shiftOrder = ["早班", "中班", "晚班"];
const createDialogVisible = ref(false);
const slotDrawerVisible = ref(false);
const leaveDialogVisible = ref(false);
const leaveReason = ref("");
const slotPatients = ref([]);

const createForm = ref({ doctor_id: 0, doctor_name: "", date: "", period: "morning", max_capacity: 10, schedule_note: "" });
const drawerSlot = ref({ appointment_id: null, doctor_name: "", department: "", date: "", period: "morning" });

const loadBarRef = ref(null);
let loadBarChart = null;

const weekStart = computed(() => {
  const date = weekPicker.value ? dayjs(weekPicker.value) : dayjs();
  return date.startOf("week").add(1, "day").format("YYYY-MM-DD");
});
const weekEnd = computed(() => dayjs(weekStart.value).add(6, "day").format("YYYY-MM-DD"));

const slotRows = computed(() => slots.value.filter((item) => item.appointment_id));
const totalSlots = computed(() => slotRows.value.length);
const fullSlots = computed(() => slotRows.value.filter((item) => Number(item.booked_count || 0) >= Number(item.max_capacity || 0)).length);
const avgUtilRate = computed(() => {
  if (!slotRows.value.length) return 0;
  const sum = slotRows.value.reduce((acc, item) => acc + Number(item.utilization_rate || 0), 0);
  return Number((sum / slotRows.value.length).toFixed(1));
});

const selectedDoctorRows = computed(() =>
  (doctors.value || []).map((item) => ({
    ...item,
    doctor_name: item.full_name || item.doctor_name
  }))
);

const algorithmDoctors = computed(() => new Set(algorithmAssignments.value.filter((x) => x.role_name === "doctor").map((x) => x.employee_id)).size);
const algorithmNurses = computed(() => new Set(algorithmAssignments.value.filter((x) => x.role_name === "nurse").map((x) => x.employee_id)).size);
const algorithmDateCount = computed(() => new Set(algorithmAssignments.value.map((x) => x.date)).size);

const algorithmMetrics = computed(() => [
  { label: "医生覆盖", value: `${algorithmDoctors.value} 人`, note: "参与算法排班的医生" },
  { label: "护士覆盖", value: `${algorithmNurses.value} 人`, note: "参与算法排班的护士" },
  { label: "排班天数", value: `${algorithmDateCount.value} 天`, note: "当前结果覆盖范围" },
  { label: "班次记录", value: `${algorithmAssignments.value.length} 条`, note: "医生与护士合计" }
]);

const kpiCards = computed(() => [
  { label: "有效号源时段", value: totalSlots.value, note: "本周已建立的正式号源", tone: "" },
  { label: "平均利用率", value: `${avgUtilRate.value}%`, note: "用于评估空闲与过载情况", tone: "success" },
  { label: "满载时段", value: fullSlots.value, note: "优先关注调度风险", tone: "warning" },
  { label: "算法排班记录", value: algorithmAssignments.value.length, note: "来自 /scheduling/generate", tone: "primary" }
]);

const weekDayCards = computed(() => {
  const start = dayjs(weekStart.value);
  return Array.from({ length: 7 }, (_, index) => {
    const date = start.add(index, "day").format("YYYY-MM-DD");
    const rows = slots.value.filter((item) => item.date === date && item.appointment_id);
    const booked = rows.reduce((sum, item) => sum + Number(item.booked_count || 0), 0);
    const capacity = rows.reduce((sum, item) => sum + Number(item.max_capacity || 0), 0);
    return {
      date,
      label: ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][index],
      slotCount: rows.length,
      peakCount: rows.filter((item) => item.is_peak || peakMap.value.has(item.appointment_id)).length,
      utilRate: capacity ? Number(((booked / capacity) * 100).toFixed(1)) : 0
    };
  });
});

const algorithmCalendar = computed(() => {
  const grouped = new Map();
  algorithmAssignments.value.forEach((item) => {
    if (!grouped.has(item.date)) {
      grouped.set(item.date, {
        date: item.date,
        label: dayjs(item.date).format("ddd"),
        shifts: Object.fromEntries(shiftOrder.map((shift) => [shift, []]))
      });
    }
    const day = grouped.get(item.date);
    const shift = shiftOrder.includes(item.shift_id) ? item.shift_id : shiftOrder[0];
    day.shifts[shift].push(item);
  });
  return Array.from(grouped.values()).sort((a, b) => a.date.localeCompare(b.date));
});

const doctorRoster = computed(() =>
  selectedDoctorRows.value.map((doctor) => {
    const doctorSlots = slotRows.value.filter((item) => item.doctor_id === doctor.id);
    const booked = doctorSlots.reduce((sum, item) => sum + Number(item.booked_count || 0), 0);
    const capacity = doctorSlots.reduce((sum, item) => sum + Number(item.max_capacity || 0), 0);
    return {
      doctor_id: doctor.id,
      doctor_name: doctor.doctor_name,
      department: doctor.department || inferDepartment(doctor.doctor_name),
      slotCount: doctorSlots.length,
      booked,
      capacity,
      rate: capacity ? Number(((booked / capacity) * 100).toFixed(1)) : 0
    };
  })
);

function inferDepartment(name) {
  const text = String(name || "");
  if (text.includes("内科")) return "内科";
  if (text.includes("外科")) return "外科";
  if (text.includes("皮肤")) return "皮肤科";
  if (text.includes("眼")) return "眼科";
  if (text.includes("牙")) return "牙科";
  return "综合门诊";
}

function priorityType(priority) {
  if (priority === "high") return "danger";
  if (priority === "medium") return "warning";
  return "info";
}

function priorityText(priority) {
  if (priority === "high") return "高优";
  if (priority === "medium") return "中优";
  return "一般";
}

function roleText(roleName) {
  if (roleName === "doctor") return "医生";
  if (roleName === "nurse") return "护士";
  return roleName || "-";
}

function getSlot(doctorId, date, period) {
  return slots.value.find((item) => item.doctor_id === doctorId && item.date === date && item.period === period) || null;
}

function quotaPercent(slot) {
  return Math.min(100, Math.round((Number(slot.booked_count || 0) / Math.max(Number(slot.max_capacity || 1), 1)) * 100));
}

function quotaStatus(slot) {
  const percentage = quotaPercent(slot);
  if (percentage >= 100) return "exception";
  if (percentage >= 80) return "warning";
  return "success";
}

function slotClass(slot) {
  const empty = !slot || !slot.appointment_id;
  const full = !empty && Number(slot.booked_count || 0) >= Number(slot.max_capacity || 0);
  const peak = !empty && (slot.is_peak || peakMap.value.has(slot.appointment_id));
  return { empty, full, peak };
}

function ensureChart() {
  if (loadBarRef.value && !loadBarChart) loadBarChart = echarts.init(loadBarRef.value);
}

function renderLoadBar() {
  ensureChart();
  const rows = doctorRoster.value;
  loadBarChart?.setOption({
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
    legend: { data: ["已预约", "剩余容量"] },
    xAxis: { type: "value" },
    yAxis: { type: "category", data: rows.map((item) => item.doctor_name) },
    series: [
      {
        name: "已预约",
        type: "bar",
        stack: "load",
        data: rows.map((item) => item.booked),
        itemStyle: { color: "#0f766e", borderRadius: [6, 0, 0, 6] }
      },
      {
        name: "剩余容量",
        type: "bar",
        stack: "load",
        data: rows.map((item) => Math.max(item.capacity - item.booked, 0)),
        itemStyle: { color: "#cbd5e1", borderRadius: [0, 6, 6, 0] }
      }
    ],
    grid: { top: 20, right: 20, bottom: 16, left: 74 }
  });
}

async function loadStaff() {
  staffLoading.value = true;
  try {
    const res = await fetchSchedulingStaff({ clinic_id: clinicId.value || undefined });
    staff.value = res.data || staff.value;
  } finally {
    staffLoading.value = false;
  }
}

async function loadAppointmentSchedule() {
  loading.value = true;
  try {
    const [weekRes, peakRes, recRes] = await Promise.all([
      fetchScheduleWeek({ clinicId: clinicId.value, weekStart: weekStart.value }),
      fetchSchedulePeakPrediction({ clinicId: clinicId.value, weekStart: weekStart.value }),
      fetchScheduleRecommendations({ clinicId: clinicId.value, weekStart: weekStart.value })
    ]);
    doctors.value = weekRes.data?.doctors || [];
    slots.value = weekRes.data?.slots || [];
    peakMap.value = new Set((peakRes.data || []).map((item) => item.appointment_id));
    recommendations.value = recRes.data?.recommendations || [];
    const availableDates = weekDayCards.value.map((item) => item.date);
    if (!availableDates.includes(selectedDate.value)) selectedDate.value = availableDates[0] || weekStart.value;
    await nextTick();
    renderLoadBar();
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "排班数据加载失败"));
  } finally {
    loading.value = false;
  }
}

async function loadAlgorithmAssignments() {
  algorithmLoading.value = true;
  try {
    const res = await fetchSchedulingAssignments({
      start_date: weekStart.value,
      end_date: weekEnd.value,
      clinic_id: clinicId.value || undefined
    });
    algorithmAssignments.value = res.data || [];
    if (res.meta?.staff) staff.value = res.meta.staff;
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "算法排班结果加载失败"));
  } finally {
    algorithmLoading.value = false;
  }
}

async function loadAll() {
  algorithmStartDate.value = weekStart.value;
  await Promise.all([loadAppointmentSchedule(), loadAlgorithmAssignments(), loadStaff()]);
}

async function handleGenerateSchedule() {
  generating.value = true;
  generationMessage.value = "";
  try {
    const res = await generateSchedule({
      start_date: algorithmStartDate.value,
      days: Number(algorithmDays.value),
      clinic_id: clinicId.value || null,
      shifts: [
        { shift_id: "早班", start_time: "08:00", end_time: "12:00" },
        { shift_id: "中班", start_time: "12:00", end_time: "18:00" },
        { shift_id: "晚班", start_time: "18:00", end_time: "23:00" }
      ],
      overwrite_existing: overwriteExisting.value
    });
    if (Number(res.code || 200) !== 200) {
      generationMessage.value = res.message || "排班算法未生成结果";
      if (res.data?.staff) staff.value = res.data.staff;
      ElMessage.warning(generationMessage.value);
      return;
    }
    generationMessage.value = res.message || "排班算法已生成结果";
    if (res.data?.staff) staff.value = res.data.staff;
    weekPicker.value = algorithmStartDate.value;
    ElMessage.success(generationMessage.value);
    await loadAlgorithmAssignments();
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "排班算法运行失败"));
  } finally {
    generating.value = false;
  }
}

async function openSlot(doctor, date, period) {
  const current = getSlot(doctor.id, date, period);
  if (!current || !current.appointment_id) {
    createForm.value = {
      doctor_id: doctor.id,
      doctor_name: doctor.full_name || doctor.doctor_name,
      date,
      period,
      max_capacity: 10,
      schedule_note: ""
    };
    createDialogVisible.value = true;
    return;
  }

  drawerSlot.value = {
    appointment_id: current.appointment_id,
    doctor_name: doctor.full_name || doctor.doctor_name,
    department: doctor.department || inferDepartment(doctor.full_name || doctor.doctor_name),
    date,
    period
  };
  slotDrawerVisible.value = true;

  try {
    const res = await fetchSchedulePatients(current.appointment_id);
    slotPatients.value = res.data || [];
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "患者列表加载失败"));
  }
}

async function submitCreate() {
  saving.value = true;
  try {
    await createSchedule({
      doctor_id: createForm.value.doctor_id,
      clinic_id: clinicId.value,
      date: createForm.value.date,
      period: createForm.value.period,
      max_capacity: createForm.value.max_capacity,
      schedule_note: createForm.value.schedule_note
    });
    ElMessage.success("排班新增成功");
    createDialogVisible.value = false;
    await loadAppointmentSchedule();
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "新增排班失败"));
  } finally {
    saving.value = false;
  }
}

function openLeaveResolve() {
  leaveReason.value = "";
  leaveDialogVisible.value = true;
}

async function handleLeave(action) {
  saving.value = true;
  try {
    const res = await resolveScheduleLeave(drawerSlot.value.appointment_id, { action, reason: leaveReason.value });
    ElMessage.success(res.message || "停诊处理完成");
    leaveDialogVisible.value = false;
    slotDrawerVisible.value = false;
    await loadAppointmentSchedule();
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "停诊处理失败"));
  } finally {
    saving.value = false;
  }
}

async function copyLastWeek() {
  copying.value = true;
  try {
    const res = await copyScheduleFromLastWeek({ clinicId: clinicId.value, weekStart: weekStart.value });
    ElMessage.success(res.message || "复制完成");
    await loadAppointmentSchedule();
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "复制排班失败"));
  } finally {
    copying.value = false;
  }
}

function onResize() {
  loadBarChart?.resize();
}

onMounted(async () => {
  await loadAll();
  window.addEventListener("resize", onResize);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", onResize);
  loadBarChart?.dispose();
});
</script>

<style scoped>
.schedule-page {
  padding: 14px;
  background: linear-gradient(145deg, #f6fbff 0%, #fff8ef 100%);
}

.hero-card,
.algorithm-card,
.kpi-card,
.panel-card {
  border-radius: 14px;
  margin-bottom: 12px;
  border: 1px solid rgba(148, 163, 184, 0.16);
}

.hero-row,
.panel-header,
.staff-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 18px;
}

.eyebrow {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #2563eb;
}

.hero-row h2 {
  margin: 8px 0 0;
  font-size: 28px;
  color: #0f172a;
}

.hero-row p,
.panel-subtitle,
.staff-head p {
  margin: 6px 0 0;
  color: #64748b;
  line-height: 1.7;
}

.algorithm-card {
  background: linear-gradient(135deg, #ffffff 0%, #f1f7ff 100%);
}

.algorithm-layout {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 14px;
}

.algorithm-control,
.staff-panel,
.algorithm-metric {
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 12px;
  padding: 14px;
  background: rgba(255, 255, 255, 0.82);
}

.control-title,
.panel-title {
  font-weight: 800;
  color: #0f172a;
}

.generate-btn {
  width: 100%;
}

.generation-message {
  margin-top: 10px;
  color: #2563eb;
  font-size: 13px;
  line-height: 1.6;
}

.staff-grid,
.algorithm-metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.algorithm-metrics {
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin: 12px 0;
}

.staff-box {
  border-radius: 12px;
  padding: 12px;
  background: #f8fafc;
}

.staff-count {
  font-size: 30px;
  font-weight: 800;
  color: #0f766e;
}

.staff-label,
.metric-mini-label {
  color: #64748b;
  font-size: 12px;
}

.staff-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 10px;
}

.metric-mini-value {
  margin-top: 4px;
  font-size: 22px;
  font-weight: 800;
  color: #0f172a;
}

.metric-mini-note,
.kpi-note {
  margin-top: 6px;
  color: #64748b;
  font-size: 12px;
}

.schedule-grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(180px, 1fr));
  gap: 10px;
  overflow-x: auto;
  padding-bottom: 2px;
}

.schedule-day {
  min-width: 180px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 12px;
  padding: 10px;
  background: #fff;
}

.schedule-day-head,
.day-head,
.roster-top,
.roster-meta,
.drawer-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.shift-row {
  margin-top: 10px;
  display: grid;
  gap: 6px;
}

.shift-name {
  color: #334155;
  font-size: 12px;
  font-weight: 800;
}

.shift-people {
  display: grid;
  gap: 6px;
}

.person-pill,
.empty-pill {
  border-radius: 10px;
  padding: 7px 8px;
  font-size: 12px;
  background: #eff6ff;
  color: #1d4ed8;
}

.person-pill.nurse {
  background: #ecfdf5;
  color: #047857;
}

.empty-pill {
  background: #f8fafc;
  color: #94a3b8;
}

.kpi-label {
  color: #64748b;
  font-size: 12px;
}

.kpi-value {
  margin-top: 6px;
  font-size: 28px;
  font-weight: 800;
  color: #0f172a;
}

.kpi-value.success {
  color: #16a34a;
}

.kpi-value.warning {
  color: #d97706;
}

.kpi-value.primary {
  color: #2563eb;
}

.chart {
  width: 100%;
  height: 300px;
}

.recommend-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.recommend-body {
  color: #475569;
  line-height: 1.7;
}

.week-strip {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 10px;
}

.day-card {
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 12px;
  padding: 14px;
  text-align: left;
  background: #fff;
  cursor: pointer;
}

.day-card.active {
  border-color: rgba(37, 99, 235, 0.36);
  box-shadow: 0 12px 22px rgba(37, 99, 235, 0.1);
}

.day-metrics {
  margin-top: 10px;
  display: grid;
  gap: 4px;
  color: #64748b;
  font-size: 12px;
}

.doctor-cell {
  display: flex;
  gap: 10px;
  align-items: center;
}

.avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: #eff6ff;
  color: #2563eb;
  font-size: 12px;
  font-weight: 800;
}

.doctor-name {
  font-weight: 800;
  color: #0f172a;
}

.doctor-dept,
.slot-note,
.slot-empty,
.roster-meta,
.drawer-top,
.leave-text {
  color: #64748b;
  font-size: 12px;
}

.slot-card {
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 12px;
  padding: 10px;
  min-height: 94px;
  cursor: pointer;
  display: grid;
  gap: 6px;
  justify-content: center;
  align-content: center;
  text-align: center;
  background: #fff;
}

.slot-card.empty {
  background: #f8fafc;
  color: #94a3b8;
}

.slot-card.full {
  background: #fef2f2;
  border-color: #fca5a5;
}

.slot-card.peak {
  background: #f5f3ff;
  border-color: #c4b5fd;
}

.slot-line {
  font-size: 13px;
  font-weight: 800;
  color: #334155;
}

.roster-list {
  display: grid;
  gap: 10px;
}

.roster-card {
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 12px;
  padding: 14px;
  background: #fff;
}

.drawer-top {
  margin-bottom: 12px;
  font-size: 14px;
}

.drawer-actions {
  margin-top: 10px;
  text-align: right;
}

.leave-text {
  margin-bottom: 12px;
  font-size: 14px;
}

@media (max-width: 1200px) {
  .algorithm-layout,
  .algorithm-metrics {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .week-strip {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .hero-row,
  .panel-header,
  .staff-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .algorithm-layout,
  .algorithm-metrics,
  .staff-grid {
    grid-template-columns: 1fr;
  }

  .week-strip {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .week-strip {
    grid-template-columns: 1fr;
  }
}
</style>
