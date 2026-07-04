<template>
  <div class="app-layout">
    <NavSide />
    <div class="main-content">
      <div class="page-header">
        <h2>🏥 欢迎使用AI医疗导诊系统</h2>
        <p>智能症状问诊 · 精准科室推荐 · 医疗报告辅助解读</p>
      </div>

      <!-- Stats -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon blue"><el-icon :size="28"><ChatDotRound /></el-icon></div>
          <div class="stat-info">
            <h3>{{ stats.consultations }}</h3>
            <p>问诊次数</p>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon green"><el-icon :size="28"><Document /></el-icon></div>
          <div class="stat-info">
            <h3>{{ stats.reports }}</h3>
            <p>报告解读</p>
          </div>
        </div>
        <div class="stat-card clickable" @click="showDeptDialog = true">
          <div class="stat-icon orange"><el-icon :size="28"><Aim /></el-icon></div>
          <div class="stat-info">
            <h3>{{ departments.length || 12 }}</h3>
            <p>支持科室</p>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon purple"><el-icon :size="28"><Warning /></el-icon></div>
          <div class="stat-info">
            <h3>AI</h3>
            <p>{{ llmMode }}模式</p>
          </div>
        </div>
      </div>

      <!-- Quick actions -->
      <el-row :gutter="16">
        <el-col :span="8" v-for="action in quickActions" :key="action.path">
          <el-card shadow="hover" class="action-card" @click="$router.push(action.path)">
            <div class="action-content">
              <el-icon :size="36" :color="action.color">{{ action.icon }}</el-icon>
              <div>
                <h3>{{ action.title }}</h3>
                <p>{{ action.desc }}</p>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- Disclaimer -->
      <el-alert
        description="⚠️本系统提供的导诊建议和报告解读仅供参考，不能替代专业医生的诊断和治疗方案。如有身体不适，请及时就医。急重症请立即前往医院急诊科。"
        type="warning"
        show-icon
        :closable="false"
        style="margin-top: 24px"
      />
    </div>

    <!-- All departments dialog -->
    <el-dialog v-model="showDeptDialog" title="🏥 全部支持科室" width="760px" top="5vh">
      <div class="dept-grid">
        <div v-for="d in departments" :key="d.id" class="dept-item">
          <span class="dept-category">{{ d.category }}</span>
          <strong class="dept-name">{{ d.name }}</strong>
          <p class="dept-desc">{{ d.description }}</p>
        </div>
      </div>
      <div v-if="departments.length === 0" style="text-align:center; padding:20px; color:#909399;">
        加载中...
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import NavSide from '../components/NavSide.vue'
import { recordsAPI, recommendationAPI } from '../api'

const stats = ref({ consultations: 0, reports: 0 })
const llmMode = ref('Mock演示')
const showDeptDialog = ref(false)
const departments = ref([])

const quickActions = [
  { title: '智能问诊', desc: '描述症状，AI多轮对话采集信息', path: '/consultation', color: '#409eff' },
  { title: '科室推荐', desc: '基于症状智能匹配就诊科室', path: '/recommend', color: '#67c23a' },
  { title: '报告解读', desc: '上传医疗报告，AI辅助解读', path: '/report',color: '#e6a23c' }
]

// Lazy-load departments only when the dialog opens
watch(showDeptDialog, async (open) => {
  if (open && departments.value.length === 0) {
    try {
      const res = await recommendationAPI.getDepartments()
      departments.value = res.departments || []
    } catch { /* ignore */ }
  }
})

onMounted(async () => {
  try {
    const res = await recordsAPI.getTimeline()
    // Backend returns { consultation_count, report_count }
    stats.value = {
      consultations: res.stats?.consultation_count ?? 0,
      reports: res.stats?.report_count ?? 0
    }
  } catch { /* ignore */ }
})
</script>

<style scoped>
.clickable { cursor: pointer; }
.clickable:hover { box-shadow: 0 2px 12px rgba(0,0,0,0.1); }

.action-card {
  cursor: pointer;
  transition: transform 0.2s;
  border-radius: 12px;
}

.action-card:hover {
  transform: translateY(-3px);
}

.action-content {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px 0;
}

.action-content h3 {
  font-size: 16px;
  color: #303133;
  margin-bottom: 4px;
}

.action-content p {
  font-size: 13px;
  color: #909399;
}

/* Department dialog grid */
.dept-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}
.dept-item {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 12px 14px;
  transition: box-shadow 0.2s;
}
.dept-item:hover {
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.dept-category {
  display: inline-block;
  font-size: 11px;
  color: #909399;
  background: #f5f7fa;
  padding: 1px 6px;
  border-radius: 3px;
  margin-bottom: 4px;
}
.dept-name {
  display: block;
  font-size: 14px;
  color: #303133;
  margin-bottom: 4px;
}
.dept-desc {
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
  margin: 0;
}
</style>
