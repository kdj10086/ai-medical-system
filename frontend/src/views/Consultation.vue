<template>
  <div class="app-layout">
    <NavSide />
    <div class="main-content">
      <div class="page-header">
        <h2>💬 智能问诊</h2>
        <p>请描述您的不适症状，AI助手将通过多轮对话采集详细信息</p>
      </div>

      <div class="card-container">
        <!-- Emergency warning -->
        <div class="emergency-banner" v-if="showEmergency">
          <el-icon><Warning /></el-icon>
          <span>如出现剧烈胸痛、严重呼吸困难、大出血等急危重症，请立即拨打120或前往急诊科！</span>
        </div>

        <!-- Session bar -->
        <div class="session-bar" v-if="sessions.length > 0">
          <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
            <span style="color: #606266; font-size: 13px;">📋 历史会话：</span>
            <el-select
              v-model="sessionId"
              placeholder="选择会话"
              size="small"
              style="width: 260px;"
              teleported
              @change="switchSession"
            >
              <el-option
                v-for="s in sessions"
                :key="s.session_id"
                :label="`${s.started_at?.slice(0,16) || ''} · ${s.message_count}条消息`"
                :value="s.session_id"
              />
            </el-select>
            <el-tag v-if="sessionId" type="success" size="small" effect="plain">当前会话</el-tag>
            <el-button v-if="sessionId" size="small" type="danger" plain @click="confirmDeleteSession(sessionId)">
              <el-icon><Delete /></el-icon> 删除
            </el-button>
            <el-button size="small" type="primary" plain @click="startNewConsultation">
              <el-icon><Plus /></el-icon> 新问诊
            </el-button>
          </div>
        </div>

        <!-- Chat -->
        <div class="chat-container">
          <div class="chat-messages" ref="chatMessagesRef">
            <!-- Welcome/System message -->
            <div class="chat-message assistant" v-if="messages.length === 0 && !loadingHistory">
              <div class="chat-avatar">🤖</div>
              <div class="chat-bubble">
                您好！我是AI医疗导诊助手。<br><br>
                为了更好地帮助您，请告诉我：<br>
                1️⃣ 您目前最主要的不适症状是什么？<br>
                2️⃣ 这个症状持续了多长时间？<br>
                3️⃣ 症状的严重程度如何？<br><br>
                💡 您也可以用自然语言自由描述您的感受。
              </div>
            </div>

            <div v-if="loadingHistory" style="text-align: center; padding: 40px;">
              <el-icon class="is-loading" :size="32"><Loading /></el-icon>
              <p style="color: #909399; margin-top: 8px;">加载历史记录...</p>
            </div>

            <div
              v-for="(msg, idx) in messages"
              :key="idx"
              :class="['chat-message', msg.role]"
            >
              <div class="chat-avatar">{{ msg.role === 'user' ? '👤' : '🤖' }}</div>
              <div class="chat-bubble">{{ msg.content }}</div>
            </div>

            <!-- Typing indicator -->
            <div class="chat-message assistant" v-if="isTyping">
              <div class="chat-avatar">🤖</div>
              <div class="chat-bubble">
                <span class="typing-dots">思考中<span class="dot">.</span><span class="dot">.</span><span class="dot">.</span></span>
              </div>
            </div>
          </div>

          <!-- Input -->
          <div class="chat-input-area">
            <el-input
              v-model="inputText"
              placeholder="请输入您的症状描述..."
              :disabled="isTyping || consultFinished"
              @keyup.enter="sendMessage"
              size="large"
            >
              <template #append>
                <el-button
                  type="primary"
                  :loading="isTyping"
                  :disabled="!inputText.trim() || consultFinished"
                  @click="sendMessage"
                >
                  发送
                </el-button>
              </template>
            </el-input>
          </div>

          <!-- Actions after consultation -->
          <div v-if="consultFinished" style="padding: 16px 20px; border-top: 1px solid #ebeef5; text-align: center;">
            <el-space>
              <el-button type="primary" @click="$router.push('/recommend')">
                <el-icon><Aim /></el-icon> 查看科室推荐
              </el-button>
              <el-button @click="startNewConsultation">
                <el-icon><Plus /></el-icon> 新一轮问诊
              </el-button>
            </el-space>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import NavSide from '../components/NavSide.vue'
import { consultationAPI } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const messages = ref([])
const sessions = ref([])
const inputText = ref('')
const isTyping = ref(false)
const consultFinished = ref(false)
const showEmergency = ref(false)
const sessionId = ref('')
const loadingHistory = ref(false)
const chatMessagesRef = ref(null)

const STORAGE_KEY = 'consultation_last_session'

function scrollToBottom() {
  nextTick(() => {
    const el = chatMessagesRef.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

onMounted(async () => {
  // Load session list
  try {
    const res = await consultationAPI.getHistory()
    sessions.value = res.sessions || []
  } catch {
    // Silently ignore auth/network errors — user will stay on welcome screen
    sessions.value = []
  }

  // Restore last session
  const lastId = sessionStorage.getItem(STORAGE_KEY)
  if (lastId) {
    await loadSession(lastId)
  } else if (sessions.value.length > 0) {
    // Auto-load the most recent session
    await loadSession(sessions.value[0].session_id)
  }
})

async function loadSession(sid) {
  // Guard against empty/invalid session ids (would hit /session/ → 404)
  if (!sid) {
    sessionId.value = ''
    messages.value = []
    sessionStorage.removeItem(STORAGE_KEY)
    return
  }
  loadingHistory.value = true
  sessionId.value = sid
  try {
    const res = await consultationAPI.getSession(sid)
    messages.value = (res.messages || []).map(m => ({
      role: m.role,
      content: m.message
    }))
    // Check if last message contains symptom summary
    const lastMsg = messages.value[messages.value.length - 1]
    if (lastMsg && lastMsg.content.includes('【症状总结】')) {
      consultFinished.value = true
    }
    if (lastMsg && (lastMsg.content.includes('急诊') || lastMsg.content.includes('120'))) {
      showEmergency.value = true
    }
    sessionStorage.setItem(STORAGE_KEY, sid)
    scrollToBottom()
  } catch (err) {
    // Don't show error for 401 (already handled by interceptor with redirect)
    // For other errors, clear state silently
    if (err.response?.status === 404) {
      // Session no longer exists — clear the stale pointer silently
      sessionStorage.removeItem(STORAGE_KEY)
    } else if (err.response?.status !== 401) {
      ElMessage.error('加载历史会话失败，请稍后重试')
    }
    sessionId.value = ''
    messages.value = []
  }
  finally {
    loadingHistory.value = false
  }
}

async function switchSession(sid) {
  await loadSession(sid)
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || isTyping.value) return

  if (!sessionId.value) {
    sessionId.value = ''   // backend will generate a new one
  }

  messages.value.push({ role: 'user', content: text })
  inputText.value = ''
  scrollToBottom()

  isTyping.value = true
  // Start with an empty assistant bubble that we'll fill in as chunks arrive
  messages.value.push({ role: 'assistant', content: '' })
  const aiIdx = messages.value.length - 1

  try {
    const decoder = new TextDecoder()
    const reader = await consultationAPI.chatStream({
      message: text,
      session_id: sessionId.value
    })

    let buffer = ''
    while (true) {
      const { done, value } = await reader.read()
      if (value) {
        buffer += decoder.decode(value, { stream: true })
        // SSE lines: "data: {...}\n\n"
        let lineEnd
        while ((lineEnd = buffer.indexOf('\n\n')) !== -1) {
          const line = buffer.slice(0, lineEnd)
          buffer = buffer.slice(lineEnd + 2)
          for (const seg of line.split('\n')) {
            if (!seg.startsWith('data: ')) continue
            try {
              const payload = JSON.parse(seg.slice(6))
              if (payload.chunk) {
                messages.value[aiIdx].content += payload.chunk
                scrollToBottom()
              }
              if (payload.done) {
                sessionId.value = payload.session_id
                sessionStorage.setItem(STORAGE_KEY, payload.session_id)
                if (messages.value[aiIdx].content.includes('急诊') || messages.value[aiIdx].content.includes('120')) {
                  showEmergency.value = true
                }
                if (payload.symptom_summary_detected) {
                  consultFinished.value = true
                  ElMessage.success('症状采集完成！可查看科室推荐')
                }
                // Refresh session list
                try {
                  const histRes = await consultationAPI.getHistory()
                  sessions.value = histRes.sessions || []
                } catch { /* ignore */ }
              }
            } catch { /* skip malformed JSON */ }
          }
        }
      }
      if (done) break
    }
  } catch (e) {
    // Remove the empty assistant bubble on error
    if (!messages.value[aiIdx].content) {
      messages.value.splice(aiIdx, 1)
    } else {
      messages.value[aiIdx].content += '\n\n[回复中断，请重试]'
    }
    console.error('Stream error:', e)
  }
  finally {
    isTyping.value = false
    scrollToBottom()
  }
}

function startNewConsultation() {
  messages.value = []
  sessionId.value = ''
  consultFinished.value = false
  showEmergency.value = false
  inputText.value = ''
  sessionStorage.removeItem(STORAGE_KEY)
  ElMessage.info('已开始新一轮问诊')
}

async function confirmDeleteSession(sid) {
  try {
    await ElMessageBox.confirm('确定要删除该会话及其所有消息吗？此操作不可恢复。', '确认删除', {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteSession(sid)
  } catch { /* user cancelled */ }
}

async function deleteSession(sid) {
  try {
    await consultationAPI.deleteSession(sid)
    if (sessionId.value === sid) {
      // If currently viewing this session, reset
      messages.value = []
      sessionId.value = ''
      sessionStorage.removeItem(STORAGE_KEY)
    }
    // Refresh the session list
    const histRes = await consultationAPI.getHistory()
    sessions.value = histRes.sessions || []
    ElMessage.success('会话已删除')
  } catch { ElMessage.error('删除失败，请稍后重试') }
}
</script>

<style scoped>
.session-bar {
  background: #fff;
  border-radius: 12px;
  padding: 12px 16px;
  margin-bottom: 12px;
  box-shadow: 0 1px 6px rgba(0, 0, 0, 0.06);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.typing-dots .dot {
  animation: blink 1.4s infinite;
}
.typing-dots .dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dots .dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes blink {
  0%, 100% { opacity: 0.2; }
  50% { opacity: 1; }
}
</style>
