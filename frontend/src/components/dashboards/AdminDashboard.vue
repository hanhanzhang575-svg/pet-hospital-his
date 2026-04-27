<template>
  <el-card class="glass-card">
    <template #header>
      <div class="header-row">
        <span>系统管理员控制台</span>
      <el-space>
        <el-button type="primary" @click="goDataCenter">数据中心</el-button>
        <el-button type="primary" @click="openManual">系统使用手册</el-button>
      </el-space>
      </div>
    </template>
    <el-row :gutter="12">
      <el-col :span="6" v-for="item in cards" :key="item.title">
        <el-card class="glass-card">
          <div class="k">{{ item.title }}</div>
          <div class="v">{{ item.value }}</div>
        </el-card>
      </el-col>
    </el-row>
    <el-dialog v-model="manualVisible" title="系统使用手册（按角色）" fullscreen>
      <el-collapse>
        <el-collapse-item title="前台接诊员" name="1">
          录入主人坐标（latitude/longitude），触发 Owners 插入逻辑；可执行挂号、收费、回访。
        </el-collapse-item>
        <el-collapse-item title="执业兽医师" name="2">
          通过 kg_evidence_id 关联图谱证据；开方后联动 Drugs/Inventory 扣减。
        </el-collapse-item>
        <el-collapse-item title="检验员" name="3">
          处理生化指标录入，Token 失效统一由 Bearer + 登录重发机制处理，401将自动回登录页并可重登。
        </el-collapse-item>
        <el-collapse-item title="管理员" name="4">
          监控 PACI 匹配分值，发布新闻推送，执行物理表维护与审计。
        </el-collapse-item>
        <el-collapse-item title="回访流程 SQL 状态位" name="5">
          状态确认(进行中) -> 建议反馈(进行中) -> 评价归档(已完成)，对应 followup_tasks.status 变更。
        </el-collapse-item>
      </el-collapse>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";

const manualVisible = ref(false);
const router = useRouter();
const cards = [
  { title: "用户管理", value: "已启用" },
  { title: "权限配置", value: "稳定" },
  { title: "审计日志", value: "实时" },
  { title: "联邦学习状态", value: "运行中" }
];

function openManual() {
  manualVisible.value = true;
}

function goDataCenter() {
  router.push("/data-center");
}
</script>

<style scoped>
.k { color: #909399; }
.v { font-size: 28px; font-weight: 700; color: #42b983; }
.header-row { display: flex; justify-content: space-between; align-items: center; }
</style>

