<template>
  <div class="forbidden-wrap">
    <el-result icon="warning" title="403 无权限访问" sub-title="当前账号没有该页面访问权限，请联系系统管理员。">
      <template #extra>
        <el-button type="primary" @click="goHome">返回工作台</el-button>
      </template>
    </el-result>
  </div>
</template>

<script setup>
import { useRouter } from "vue-router";

const router = useRouter();

function goHome() {
  router.push("/home");
}
</script>

<style scoped>
.forbidden-wrap {
  min-height: 60vh;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>

