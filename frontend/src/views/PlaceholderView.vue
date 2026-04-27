<template>
  <div class="placeholder">
    <el-empty :description="`${title}模块建设中`">
      <el-text type="info">该页面已接入RBAC路由与菜单，可继续按业务需求扩展。</el-text>
    </el-empty>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useRoute } from "vue-router";

const route = useRoute();
const title = computed(() => String(route.meta?.title || "功能"));
</script>

<style scoped>
.placeholder {
  min-height: 60vh;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>

