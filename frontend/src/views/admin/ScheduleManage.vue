<template>
  <div class="schedule-manage-page" v-loading="loading">
    <el-card class="hero-card" shadow="never">
      <div class="hero-row">
        <div>
          <h2>医生与护士排班管理</h2>
          <p>基于 OR-Tools CP-SAT 自动排班，支持管理员在时间线上拖拽微调并实时回写数据库。</p>
        </div>
        <el-space>
          <el-date-picker v-model="startDate" type="date" value-format="YYYY-MM-DD" placeholder="排班起始日" />
          <el-input-number v-model="days" :min="1" :max="31" />
          <el-select v-model="clinicId" clearable placeholder="院区(可选)" style="width: 150px">
            <el-option label="C001 沙河口" value="C001" />
            <el-option label="C002 甘井子" value="C002" />
            <el-option label="C003 高新区" value="C003" />
          </el-select>
          <el-button type="primary" :loading="generating" @click="handleGenerate">自动排班</el-button>
          <el-button :loading="loading" @click="loadTimelineData">刷新</el-button>
        </el-space>
      </div>
    </el-card>

    <el-card class="calendar-card" shadow="never">
      <template #header>
        <div class="panel-title">Resource Timeline（resourceTimelineWeek）</div>
      </template>
      <FullCalendar ref="calendarRef" :options="calendarOptions" />
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import FullCalendar from "@fullcalendar/vue3";
import resourceTimelinePlugin from "@fullcalendar/resource-timeline";
import interactionPlugin from "@fullcalendar/interaction";
import dayGridPlugin from "@fullcalendar/daygrid";
import { fetchSchedulingAssignments, generateSchedule, upsertSchedulingAssignment } from "../../api/scheduling";
import { getErrorMessage } from "../../utils/status";

const loading = ref(false);
const generating = ref(false);
const calendarRef = ref(null);
const startDate = ref(new Date().toISOString().slice(0, 10));
const days = ref(7);
const clinicId = ref("");

const resources = ref([]);
const events = ref([]);

/**
 * 将后端排班记录映射为 FullCalendar 资源。
 * @param {Array<object>} rows
 */
function buildResources(rows) {
  const map = new Map();
  rows.forEach((row) => {
    if (map.has(String(row.employee_id))) return;
    map.set(String(row.employee_id), {
      id: String(row.employee_id),
      title: row.employee_name || `员工#${row.employee_id}`,
      extendedProps: {
        role: row.role_name || "",
        department: row.department || ""
      }
    });
  });
  resources.value = Array.from(map.values());
}

/**
 * 将后端排班记录映射为 FullCalendar event。
 * @param {Array<object>} rows
 */
function buildEvents(rows) {
  events.value = (rows || []).map((row) => ({
    id: String(row.assignment_id),
    resourceId: String(row.employee_id),
    title: `${row.shift_id}（${row.role_name}）`,
    start: row.start_at,
    end: row.end_at,
    editable: true,
    extendedProps: {
      assignmentId: row.assignment_id,
      employeeId: row.employee_id,
      roleName: row.role_name,
      shiftId: row.shift_id
    }
  }));
}

/**
 * 加载时间线数据。
 */
async function loadTimelineData() {
  loading.value = true;
  try {
    const endDateObj = new Date(startDate.value);
    endDateObj.setDate(endDateObj.getDate() + days.value - 1);
    const endDate = endDateObj.toISOString().slice(0, 10);
    const res = await fetchSchedulingAssignments({
      start_date: startDate.value,
      end_date: endDate,
      clinic_id: clinicId.value || undefined
    });
    const rows = res.data || [];
    buildResources(rows);
    buildEvents(rows);
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "排班数据加载失败"));
  } finally {
    loading.value = false;
  }
}

/**
 * 自动排班。
 */
async function handleGenerate() {
  generating.value = true;
  try {
    await generateSchedule({
      start_date: startDate.value,
      days: Number(days.value),
      clinic_id: clinicId.value || null,
      shifts: [
        { shift_id: "早班", start_time: "08:00", end_time: "12:00" },
        { shift_id: "中班", start_time: "12:00", end_time: "18:00" },
        { shift_id: "晚班", start_time: "18:00", end_time: "23:00" }
      ],
      overwrite_existing: true
    });
    ElMessage.success("自动排班完成");
    await loadTimelineData();
  } catch (error) {
    ElMessage.error(getErrorMessage(error, "自动排班失败"));
  } finally {
    generating.value = false;
  }
}

/**
 * 处理 eventDrop：管理员拖拽后同步回后端。
 * @param {import('@fullcalendar/core').EventDropArg} info
 */
async function handleEventDrop(info) {
  const evt = info.event;
  const ext = evt.extendedProps || {};
  const nextEmployeeId = Number(evt.getResources?.()[0]?.id || ext.employeeId);
  const start = evt.start;
  const end = evt.end;
  if (!start || !end || !nextEmployeeId) {
    info.revert();
    ElMessage.error("拖拽数据异常，已回退");
    return;
  }

  try {
    await upsertSchedulingAssignment({
      assignment_id: Number(ext.assignmentId),
      employee_id: nextEmployeeId,
      role_name: ext.roleName,
      work_date: start.toISOString().slice(0, 10),
      shift_id: ext.shiftId,
      start_at: start.toISOString(),
      end_at: end.toISOString(),
      source: "manual"
    });
    ElMessage.success("排班调整已同步");
  } catch (error) {
    info.revert();
    ElMessage.error(getErrorMessage(error, "排班同步失败，已回退"));
  }
}

const calendarOptions = computed(() => ({
  plugins: [resourceTimelinePlugin, interactionPlugin, dayGridPlugin],
  initialView: "resourceTimelineWeek",
  resourceAreaHeaderContent: "医生/护士资源",
  schedulerLicenseKey: "CC-Attribution-NonCommercial-NoDerivatives",
  height: "auto",
  locale: "zh-cn",
  editable: true,
  resourceAreaWidth: "260px",
  resources: resources.value,
  events: events.value,
  eventDrop: handleEventDrop,
  eventResize: handleEventDrop,
  views: {
    resourceTimelineWeek: {
      slotDuration: "04:00:00",
      slotLabelInterval: "12:00:00",
      slotMinWidth: 70
    }
  }
}));

onMounted(loadTimelineData);
</script>

<style scoped>
.schedule-manage-page {
  padding: 14px;
  background: linear-gradient(145deg, #f7fbff 0%, #fff8f0 100%);
  min-height: 100vh;
}

.hero-card,
.calendar-card {
  border-radius: 14px;
  margin-bottom: 12px;
}

.hero-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.hero-row h2 {
  margin: 0;
  color: #0f172a;
}

.hero-row p {
  margin: 6px 0 0;
  color: #64748b;
  font-size: 13px;
}

.panel-title {
  font-weight: 700;
  color: #0f172a;
}
</style>

