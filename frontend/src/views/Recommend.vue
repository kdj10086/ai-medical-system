<template>
  <div class="app-layout">
    <NavSide />
    <div class="main-content">
      <div class="page-header">
        <h2>🎯 科室推荐</h2>
        <p>基于您的症状描述，智能匹配最合适的就诊科室</p>
      </div>

      <div class="card-container">
        <!-- Session selector -->
        <el-card style="margin-bottom: 20px; border-radius: 12px;">
          <div style="margin-bottom: 16px;">
            <div style="margin-bottom: 8px; color: #606266; font-size: 14px; font-weight: 500;">
              📋 选择问诊记录
            </div>
            <div style="display: flex; gap: 12px; align-items: center;">
              <el-select
                v-model="selectedSession"
                placeholder="点击选择一次问诊会话"
                style="width: 380px;"
                clearable
                teleported
                @change="onSessionChange"
                @visible-change="onSelectVisible"
              >
                <el-option
                  v-for="s in sessions"
                  :key="s.session_id"
                  :label="`${formatSessionLabel(s)}`"
                  :value="s.session_id"
                />
              </el-select>
              <el-button type="primary" @click="loadRecommendation" :loading="loading" :disabled="!selectedSession && !customSymptoms.trim()">
                <el-icon><Aim /></el-icon> 开始推荐
              </el-button>
            </div>
            <div v-if="selectedSession" style="margin-top: 8px; color: #409eff; font-size: 12px;">
              ✅ 已选择会话: {{ selectedSession }}
            </div>
          </div>

          <el-divider />

          <div>
            <div style="margin-bottom: 8px; color: #606266; font-size: 14px; font-weight: 500;">
              ✏️ 或直接输入症状
            </div>
            <el-input
              v-model="customSymptoms"
              type="textarea"
              :rows="2"
              placeholder="如：头痛、发烧、咳嗽三天，体温38.5度..."
              style="width: 100%;"
            />
            <el-button type="primary" @click="loadRecommendation" :loading="loading" :disabled="!selectedSession && !customSymptoms.trim()" style="margin-top: 8px;">
              <el-icon><Search /></el-icon> 分析症状并推荐科室
            </el-button>
          </div>
        </el-card>

        <!-- Results -->
        <div v-if="recommendations.length > 0">
          <h3 style="margin-bottom: 16px;">📋 推荐结果</h3>
          <div
            v-for="(rec, idx) in recommendations"
            :key="idx"
            :class="['dept-card', `top-${idx + 1}`]"
          >
            <div class="dept-card-header">
              <div>
                <el-tag :type="idx === 0 ? 'danger' : idx === 1 ? 'warning' : 'primary'" size="small">
                  推荐 {{ idx + 1 }}
                </el-tag>
                <h3 style="display: inline; margin-left: 8px;">{{ rec.department.name }}</h3>
              </div>
              <el-tag>{{ rec.department.category }}</el-tag>
            </div>
            <p style="color: #606266; margin: 12px 0;">{{ rec.department.description }}</p>
            <el-progress
              :percentage="rec.match_percentage"
              :color="idx === 0 ? '#f56c6c' : idx === 1 ? '#e6a23c' : '#409eff'"
              :stroke-width="8"
            />
            <div v-if="rec.matched_keywords && rec.matched_keywords.length" style="margin-top: 8px; display: flex; gap: 6px; flex-wrap: wrap; align-items: center;">
              <span style="color: #909399; font-size: 12px;">匹配症状：</span>
              <el-tag
                v-for="kw in rec.matched_keywords"
                :key="kw"
                :type="idx === 0 ? 'danger' : idx === 1 ? 'warning' : ''"
                size="small"
                effect="plain"
              >{{ kw }}</el-tag>
            </div>
            <div v-if="rec.department.advice" style="margin-top: 12px;">
              <el-alert :title="rec.department.advice" type="info" :closable="false" show-icon>
                <template #title>
                  <span style="font-size: 13px;">💡 挂号建议：{{ rec.department.advice }}</span>
                </template>
              </el-alert>
            </div>
          </div>

          <el-alert
            title="⚠️ 温馨提示"
            description="以上科室推荐基于症状关键词匹配，仅供参考。如症状复杂或涉及多科室，建议先前往全科门诊或咨询医院分诊台。急重症请立即前往急诊科。"
            type="warning"
            :closable="false"
            show-icon
            style="margin-top: 16px;"
          />
        </div>

        <!-- Empty state -->
        <el-empty v-if="!loading && recommendations.length === 0 && !selectedSession && !customSymptoms"
          description="请选择问诊记录或输入症状描述以获取科室推荐" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import NavSide from '../components/NavSide.vue'
import { consultationAPI, recommendationAPI } from '../api'
import { ElMessage } from 'element-plus'

const sessions = ref([])
const selectedSession = ref('')
const customSymptoms = ref('')
const recommendations = ref([])
const loading = ref(false)

onMounted(async () => {
  try {
    const res = await consultationAPI.getHistory()
    sessions.value = res.sessions || []
  } catch { /* ignore */ }
})

function formatSessionLabel(s) {
  const time = s.started_at ? s.started_at.slice(0, 16).replace('T', ' ') : '未知时间'
  return `${time} · ${s.message_count}条消息 · ID:${s.session_id}`
}

function onSessionChange(val) {
  if (val) {
    ElMessage.success(`已选择会话 ${val}`)
  }
}

function onSelectVisible(visible) {
  // Refresh session list when dropdown opens
  if (visible) {
    consultationAPI.getHistory().then(res => {
      sessions.value = res.sessions || []
    }).catch(() => {})
  }
}

async function loadRecommendation() {
  if (!selectedSession.value && !customSymptoms.value.trim()) {
    ElMessage.warning('请选择问诊记录或输入症状描述')
    return
  }

  loading.value = true
  recommendations.value = []
  try {
    const res = await recommendationAPI.recommend({
      session_id: selectedSession.value || undefined,
      symptoms: customSymptoms.value.trim() || undefined
    })
    recommendations.value = res.recommendations || []
    if (recommendations.value.length === 0) {
      ElMessage.info('未能匹配到合适的科室，请尝试更详细的症状描述')
    }
  } catch { /* handled by interceptor */ }
  finally { loading.value = false }
}
</script>
