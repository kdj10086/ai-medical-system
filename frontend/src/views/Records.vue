<template>
  <div class="app-layout">
    <NavSide />
    <div class="main-content">
      <div class="page-header">
        <h2>📋 健康档案</h2>
        <p>查看您的问诊历史与报告解读记录</p>
      </div>

      <div class="card-container">
        <el-card style="margin-bottom: 20px; border-radius: 12px;" v-loading="loading">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <strong>📅 时间线</strong>
              <el-tag type="info" size="small">
                问诊 {{ stats.consultation_count }} 次 · 报告 {{ stats.report_count }} 份
              </el-tag>
            </div>
          </template>

          <el-empty v-if="timeline.length === 0" description="暂无记录，快去使用智能问诊吧！" />

          <div class="timeline-list" v-else>
            <div
              v-for="item in timeline"
              :key="item.id"
              class="timeline-item"
              @click="viewDetail(item)"
            >
              <div style="display: flex; align-items: center; gap: 12px;">
                <el-tag :type="item.type === 'consultation' ? 'primary' : 'success'" size="small">
                  {{ item.type === 'consultation' ? '问诊' : '报告' }}
                </el-tag>
                <span style="flex:1; color:#303133; font-size:14px;">{{ item.preview }}</span>
                <span style="color:#909399; font-size:12px;">
                  {{ formatTime(item.created_at) }}
                </span>
                <el-icon><ArrowRight /></el-icon>
              </div>
            </div>
          </div>
        </el-card>

        <!-- Detail dialog -->
        <el-dialog
          v-model="dialogVisible"
          :title="detailType === 'consultation' ? '问诊详情' : '报告详情'"
          width="700px"
        >
          <div v-if="detailType === 'consultation' && consultationMessages.length">
            <div
              v-for="(msg, idx) in consultationMessages"
              :key="idx"
              :class="['chat-message', msg.role]"
              style="margin-bottom: 12px;"
            >
              <div class="chat-avatar">{{ msg.role === 'user' ? '👤' : '🤖' }}</div>
              <div class="chat-bubble" style="font-size: 13px;">{{ msg.message }}</div>
            </div>
          </div>

          <div v-else-if="detailType === 'report' && reportDetail">
            <p><strong>文件名：</strong>{{ reportDetail.filename }}</p>
            <p><strong>时间：</strong>{{ formatTime(reportDetail.created_at) }}</p>
            <template v-if="reportDetail.indicators && reportDetail.indicators.length">
              <h4 style="margin: 16px 0 8px;">指标摘要</h4>
              <el-table :data="reportDetail.indicators" border size="small">
                <el-table-column prop="name" label="指标" />
                <el-table-column prop="value" label="值" width="80" />
                <el-table-column prop="unit" label="单位" width="80" />
                <el-table-column label="状态" width="80">
                  <template #default="{ row }">
                    <el-tag :type="row.status === '正常' ? 'success' : 'danger'" size="small">
                      {{ row.status }}
                    </el-tag>
                  </template>
                </el-table-column>
              </el-table>
            </template>
            <div v-if="reportDetail.interpretation" style="margin-top: 16px;">
              <h4>解读</h4>
              <div v-html="formatText(reportDetail.interpretation)" style="line-height:1.8; font-size:13px;"></div>
            </div>
            <div v-if="reportDetail.advice" style="margin-top: 16px;">
              <h4>建议</h4>
              <div v-html="formatText(reportDetail.advice)" style="line-height:1.8; font-size:13px;"></div>
            </div>
          </div>
        </el-dialog>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import NavSide from '../components/NavSide.vue'
import { recordsAPI, consultationAPI, reportAPI } from '../api'

const timeline = ref([])
const stats = ref({ consultation_count: 0, report_count: 0 })
const loading = ref(false)

const dialogVisible = ref(false)
const detailType = ref('')
const consultationMessages = ref([])
const reportDetail = ref(null)

function formatText(text) {
  return text ? text.replace(/\n/g, '<br>') : ''
}

function formatTime(t) {
  return t ? t.slice(0, 16).replace('T', ' ') : ''
}

onMounted(async () => {
  loading.value = true
  try {
    const res = await recordsAPI.getTimeline()
    timeline.value = res.timeline
    stats.value = res.stats
  } catch { /* ignore */ }
  finally { loading.value = false }
})

async function viewDetail(item) {
  if (item.type === 'consultation') {
    detailType.value = 'consultation'
    try {
      const res = await consultationAPI.getSession(item.session_id)
      consultationMessages.value = res.messages
    } catch { consultationMessages.value = [] }
    reportDetail.value = null
  } else {
    detailType.value = 'report'
    try {
      const res = await reportAPI.getDetail(item.report_id)
      reportDetail.value = res.report
    } catch { reportDetail.value = null }
    consultationMessages.value = []
  }
  dialogVisible.value = true
}
</script>
