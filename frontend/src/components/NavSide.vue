<template>
  <div class="nav-side">
    <div class="nav-header">
      <el-icon :size="28" color="#409eff"><Monitor /></el-icon>
      <span class="nav-title">AI医疗导诊</span>
    </div>

    <el-menu
      :default-active="activeMenu"
      router
      background-color="#001529"
      text-color="#ffffffb3"
      active-text-color="#409eff"
      class="nav-menu"
    >
      <el-menu-item index="/">
        <el-icon><HomeFilled /></el-icon>
        <span>首页</span>
      </el-menu-item>
      <el-menu-item index="/consultation">
        <el-icon><ChatDotRound /></el-icon>
        <span>智能问诊</span>
      </el-menu-item>
      <el-menu-item index="/recommend">
        <el-icon><Aim /></el-icon>
        <span>科室推荐</span>
      </el-menu-item>
      <el-menu-item index="/report">
        <el-icon><Document /></el-icon>
        <span>报告解读</span>
      </el-menu-item>
      <el-menu-item index="/records">
        <el-icon><Collection /></el-icon>
        <span>健康档案</span>
      </el-menu-item>
      <el-menu-item index="/settings">
        <el-icon><Setting /></el-icon>
        <span>系统设置</span>
      </el-menu-item>
    </el-menu>

    <div class="nav-footer">
      <div class="user-info">
        <el-icon><User /></el-icon>
        <span>{{ username }}</span>
      </div>
      <el-button text type="danger" size="small" @click="handleLogout">
        <el-icon><SwitchButton /></el-icon>
        退出
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const activeMenu = computed(() => route.path)
const username = computed(() => {
  const user = localStorage.getItem('user')
  if (user) {
    try { return JSON.parse(user).username } catch { return '' }
  }
  return ''
})

function handleLogout() {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  router.push('/login')
}
</script>

<style scoped>
.nav-side {
  width: 220px;
  height: 100%;
  background: #001529;
  display: flex;
  flex-direction: column;
  position: fixed;
  left: 0;
  top: 0;
  z-index: 100;
}

.nav-header {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border-bottom: 1px solid #ffffff1a;
}

.nav-title {
  color: #fff;
  font-size: 17px;
  font-weight: 600;
  letter-spacing: 1px;
}

.nav-menu {
  flex: 1;
  border-right: none;
}

.nav-footer {
  padding: 16px;
  border-top: 1px solid #ffffff1a;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #ffffffb3;
  font-size: 14px;
}
</style>
