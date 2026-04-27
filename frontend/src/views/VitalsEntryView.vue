<template>
  <div class="vitals-entry-page">
    <div class="bg-layer" />
    <div class="color-wash" />

    <div class="main-container">
      <header class="vitals-header glass-card">
        <div class="header-content">
          <div class="title-group">
            <span class="system-tag">Vital Signs Telemetry</span>
            <h2>生命体征遥测录入终端</h2>
            <p>正在为住院编号 [ {{ form.recordId }} ] 的病患进行实时体征监控数据封装</p>
          </div>
          <el-button class="action-btn" @click="router.push('/nursing-logs')">
            <i class="el-icon-back"></i> 返回护理日志
          </el-button>
        </div>
      </header>

      <div class="content-grid">
        <section class="glass-card panel-card">
          <div class="panel-header">
            <h3><i class="el-icon-edit-outline"></i> 实时指标采集</h3>
          </div>
          <div class="panel-body">
            <el-form :model="form" label-position="top">
              <div class="input-group">
                <el-form-item label="核心体温监测 (℃)">
                  <el-input-number 
                    v-model.number="form.temperature" 
                    :step="0.1" 
                    :precision="1"
                    class="wide-input"
                    :class="{ 'danger-state': !temperatureInRange }"
                  />
                  <transition name="el-fade-in">
                    <div v-if="!temperatureInRange" class="alert-text">
                      ⚠️ 临床预警：{{ temperatureHint }}
                    </div>
                  </transition>
                </el-form-item>

                <el-form-item label="静息心率遥测 (bpm)">
                  <el-input-number 
                    v-model.number="form.heartRate" 
                    :step="1" 
                    class="wide-input"
                    :class="{ 'danger-state': !heartRateInRange }"
                  />
                  <transition name="el-fade-in">
                    <div v-if="!heartRateInRange" class="alert-text">
                      ⚠️ 临床预警：{{ heartRateHint }}
                    </div>
                  </transition>
                </el-form-item>

                <el-form-item label="当前体重基准 (kg)">
                  <el-input-number v-model.number="form.weightKg" :precision="2" class="wide-input" />
                </el-form-item>

                <el-form-item label="临床特征记述">
                  <el-input 
                    v-model="form.notes" 
                    type="textarea" 
                    :rows="4" 
                    placeholder="请输入病患精神状态、黏膜颜色或异常行为描述..." 
                  />
                </el-form-item>
              </div>

              <button class="submit-action-btn" :disabled="submitting" @click.prevent="submit">
                {{ submitting ? '数据同步中...' : '确认并存入 HIS 数据库' }}
              </button>
            </el-form>
          </div>
        </section>

        <section class="glass-card panel-card">
          <div class="panel-header">
            <h3><i class="el-icon-time"></i> 体征时间序列追踪</h3>
          </div>
          <div class="panel-body table-view">
            <el-table 
              :data="logs" 
              v-loading="loadingLogs" 
              height="100%" 
              class="professional-table"
            >
              <el-table-column label="采集时间" width="120">
                <template #default="scope">
                  {{ scope.row.logged_at ? new Date(scope.row.logged_at).toLocaleTimeString() : '-' }}
                </template>
              </el-table-column>
              <el-table-column prop="temperature" label="体温" width="80" />
              <el-table-column prop="heart_rate" label="心率" width="80" />
              <el-table-column prop="notes" label="临床记述" show-overflow-tooltip />
              <el-table-column label="操作" width="180">
                <template #default="{ row }">
                  <el-button
                    link
                    type="danger"
                    :disabled="!canUndo(row)"
                    @click="undoLog(row)"
                  >
                    {{ canUndo(row) ? "撤回记录" : "已过撤回时限" }}
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { fetchNursingLogs, createNursingLog, voidNursingLog } from '@/api/inpatient'
import { getErrorMessage } from '@/utils/status'

const route = useRoute()
const router = useRouter()

const loadingLogs = ref(false)
const submitting = ref(false)
const logs = ref([])

// 保持你原始的逻辑和变量名
const form = ref({
  recordId: route.query.recordId || '',
  temperature: 38.5,
  heartRate: 100,
  weightKg: 5.0,
  notes: ''
})

const temperatureInRange = computed(() => form.value.temperature >= 37.5 && form.value.temperature <= 39.2)
const heartRateInRange = computed(() => form.value.heartRate >= 70 && form.value.heartRate <= 140)

const temperatureHint = computed(() => form.value.temperature < 37.5 ? '体温过低' : '发热预警')
const heartRateHint = computed(() => form.value.heartRate < 70 ? '心动过缓' : '应激/心动过速')

const loadLogs = async () => {
  if (!form.value.recordId) {
    logs.value = []
    return
  }
  loadingLogs.value = true
  try {
    const res = await fetchNursingLogs(form.value.recordId)
    logs.value = res.data || []
  } catch (error) {
    ElMessage.error('无法调取历史遥测数据')
  } finally {
    loadingLogs.value = false
  }
}

const submit = async () => {
  if (!form.value.recordId) {
    ElMessage.warning('缺少住院记录ID，请从护理日志进入当前页面')
    return
  }
  if (!temperatureInRange.value || !heartRateInRange.value) {
    ElMessage.warning('录入数据包含临床危急值，请确认录入无误')
  }
  submitting.value = true
  try {
    await createNursingLog(form.value.recordId, {
      temperature: form.value.temperature,
      heart_rate: form.value.heartRate,
      notes: form.value.notes
    })
    ElMessage.success('体征数据包封装成功')
    form.value.notes = ''
    await loadLogs()
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '数据库写入失败'))
  } finally {
    submitting.value = false
  }
}

const canUndo = (row) => {
  if (!row?.undo_deadline) return false
  return new Date(row.undo_deadline).getTime() > Date.now()
}

const undoLog = async (row) => {
  if (!form.value.recordId || !row?.id) return
  try {
    const { value } = await ElMessageBox.prompt('请输入撤回原因（可选）', '撤回体征记录', {
      confirmButtonText: '确认撤回',
      cancelButtonText: '取消',
      inputPlaceholder: '例如：误录体温单位',
      inputValue: ''
    })
    await voidNursingLog(form.value.recordId, row.id, value || '')
    ElMessage.success('撤回成功')
    await loadLogs()
  } catch (error) {
    if (error === 'cancel' || error === 'close') return
    ElMessage.error(getErrorMessage(error, '撤回失败'))
  }
}

onMounted(loadLogs)
</script>

<style scoped>
.vitals-entry-page {
  position: relative;
  min-height: 100vh;
  padding: 30px;
  background: #f4f7f9;
  font-family: 'PingFang SC', sans-serif;
  overflow: hidden;
}

.bg-layer { position: absolute; inset: 0; opacity: 0.1; z-index: 0; }
.color-wash { position: absolute; inset: 0; background: linear-gradient(135deg, rgba(64,158,255,0.05) 0%, transparent 100%); z-index: 1; }

.main-container {
  position: relative;
  z-index: 10;
  max-width: 1300px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 25px;
}

.glass-card {
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(15px);
  border: 1px solid rgba(255, 255, 255, 0.5);
  border-radius: 20px;
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.05);
}

.vitals-header { padding: 25px 35px; }
.header-content { display: flex; justify-content: space-between; align-items: center; }
.system-tag { color: #409eff; font-weight: 700; font-size: 13px; letter-spacing: 1px; }
.title-group h2 { margin: 8px 0 5px; font-size: 26px; color: #1a2b3c; font-weight: 800; }
.title-group p { margin: 0; color: #5c6b7a; font-size: 14px; }

/* 核心修复：强制 Grid 布局，锁定左小右大的黄金比例 */
.content-grid {
  display: grid;
  grid-template-columns: 1fr 1.3fr;
  gap: 25px;
  height: calc(100vh - 250px);
}

.panel-card { display: flex; flex-direction: column; overflow: hidden; }
.panel-header { padding: 15px 25px; border-bottom: 1px solid rgba(0,0,0,0.05); }
.panel-header h3 { margin: 0; font-size: 17px; color: #1a2b3c; }
.panel-body { padding: 25px; flex: 1; overflow-y: auto; }

.wide-input { width: 100%; }
.danger-state :deep(.el-input__wrapper) { box-shadow: 0 0 0 1px #f56c6c inset !important; }
.alert-text { color: #f56c6c; font-size: 12px; margin-top: 5px; font-weight: 600; }

.submit-action-btn {
  width: 100%; padding: 15px; background: #409eff; color: white; border: none;
  border-radius: 12px; font-size: 16px; font-weight: 700; cursor: pointer; transition: 0.3s;
}
.submit-action-btn:hover { background: #66b1ff; box-shadow: 0 8px 15px rgba(64,158,255,0.2); }

.professional-table { background: transparent !important; }
.professional-table :deep(th) { background: rgba(240,244,247,0.5) !important; color: #1a2b3c; }
</style>
