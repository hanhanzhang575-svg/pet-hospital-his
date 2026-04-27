<template>
  <div class="page">
    <el-card class="glass-card">
      <template #header>
        <div class="header-row">
          <span>权限矩阵（操作级）</span>
          <el-space>
            <el-input
              v-model="unlockPassword"
              type="password"
              placeholder="管理员二次密码"
              show-password
              style="width: 180px"
            />
            <el-button type="primary" size="small" @click="unlockEdit">解锁编辑</el-button>
          </el-space>
        </div>
      </template>

      <el-table :data="rows" border>
        <el-table-column prop="feature" label="功能点" min-width="220" />
        <el-table-column v-for="role in roleColumns" :key="role.key" :label="role.label" min-width="120">
          <template #default="{ row }">
            <template v-if="editable">
              <el-select v-model="row[role.key]" size="small" style="width: 108px">
                <el-option label="✅可操作" value="✅可操作" />
                <el-option label="👁只读" value="👁只读" />
                <el-option label="❌无权限" value="❌无权限" />
              </el-select>
            </template>
            <el-tag v-else :type="stateType(row[role.key])" effect="dark">{{ row[role.key] }}</el-tag>
          </template>
        </el-table-column>
      </el-table>

      <div class="tips">
        本系统权限控制分三层：路由层（页面访问控制）/组件层（按钮v-permission指令）/数据层（敏感字段脱敏过滤）<br />
        基于策略执行点(PEP)在数据进入AI推理前进行实体级权限二次验证
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { ElMessage } from "element-plus";

const editable = ref(false);
const unlockPassword = ref("");

const roleColumns = [
  { key: "receptionist", label: "前台接诊员" },
  { key: "doctor", label: "执业兽医师" },
  { key: "nurse", label: "护理人员" },
  { key: "pharmacist", label: "药房人员" },
  { key: "manager", label: "院区主任" },
  { key: "admin", label: "系统管理员" }
];

const rows = [
  row("门诊挂号-查看", "✅可操作", "✅可操作", "👁只读", "❌无权限", "✅可操作", "✅可操作"),
  row("门诊挂号-新建", "✅可操作", "❌无权限", "❌无权限", "❌无权限", "✅可操作", "✅可操作"),
  row("门诊挂号-取消", "✅可操作", "❌无权限", "❌无权限", "❌无权限", "✅可操作", "✅可操作"),
  row("电子病历-查看", "👁只读", "✅可操作", "👁只读", "❌无权限", "✅可操作", "✅可操作"),
  row("电子病历-编辑", "❌无权限", "✅可操作", "❌无权限", "❌无权限", "👁只读", "✅可操作"),
  row("电子病历-作废", "❌无权限", "👁只读", "❌无权限", "❌无权限", "✅可操作", "✅可操作"),
  row("处方-开具", "❌无权限", "✅可操作", "❌无权限", "❌无权限", "👁只读", "✅可操作"),
  row("处方-撤回", "❌无权限", "✅可操作", "❌无权限", "❌无权限", "✅可操作", "✅可操作"),
  row("住院-申请", "❌无权限", "✅可操作", "👁只读", "❌无权限", "✅可操作", "✅可操作"),
  row("住院-护理记录", "❌无权限", "👁只读", "✅可操作", "❌无权限", "✅可操作", "✅可操作"),
  row("库存-查看", "❌无权限", "👁只读", "❌无权限", "✅可操作", "✅可操作", "✅可操作"),
  row("库存-出入库", "❌无权限", "❌无权限", "❌无权限", "✅可操作", "👁只读", "✅可操作"),
  row("库存-采购申请", "❌无权限", "❌无权限", "❌无权限", "✅可操作", "👁只读", "✅可操作"),
  row("采购-审批", "❌无权限", "❌无权限", "❌无权限", "❌无权限", "✅可操作", "✅可操作"),
  row("跨院区-病历调阅", "❌无权限", "👁只读", "❌无权限", "❌无权限", "✅可操作", "✅可操作")
];

function unlockEdit() {
  if (unlockPassword.value !== "admin123") {
    ElMessage.error("管理员密码错误");
    return;
  }
  editable.value = true;
  ElMessage.success("已解锁权限编辑");
}

function row(feature, receptionist, doctor, nurse, pharmacist, manager, admin) {
  return { feature, receptionist, doctor, nurse, pharmacist, manager, admin };
}

function stateType(value) {
  if (String(value).includes("✅")) return "success";
  if (String(value).includes("👁")) return "primary";
  return "danger";
}
</script>

<style scoped>
.page { padding: 16px; }
.header-row { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.tips { margin-top: 12px; color: #64748b; font-size: 12px; line-height: 1.7; }
</style>
