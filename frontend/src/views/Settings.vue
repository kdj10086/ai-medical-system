<template>
  <div class="app-layout">
    <NavSide />
    <div class="main-content">
      <div class="page-header">
        <h2>⚙️ 系统设置</h2>
        <p>配置大语言模型（LLM）API 接口，启用真实 AI 能力</p>
      </div>

      <div class="card-container">
        <!-- LLM Config Card -->
        <el-card style="border-radius: 12px;" v-loading="loading">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <strong>🤖 LLM 模型配置</strong>
              <el-tag :type="hasConfig ? 'success' : 'info'" size="small">
                {{ hasConfig ? '已配置 · ' + configModel : 'Mock 演示模式' }}
              </el-tag>
            </div>
          </template>

          <el-form :model="form" :rules="rules" ref="formRef" label-width="120px" label-position="top">

            <el-alert
              title="配置说明"
              description="支持任意 OpenAI 兼容接口（DeepSeek、通义千问、GLM、OpenAI 等）。配置后将使用真实 AI 进行问诊和报告解读，未配置时使用 Mock 演示模式。"
              type="info"
              :closable="false"
              show-icon
              style="margin-bottom: 20px;"
            />

            <el-row :gutter="16">
              <el-col :span="24">
                <el-form-item label="API 密钥 (Key)" prop="api_key">
                  <el-input
                    v-model="form.api_key"
                    placeholder="sk-xxxxxxxxxxxxxxxx"
                    show-password
                    clearable
                    size="large"
                  >
                    <template #prefix>
                      <el-icon><Key /></el-icon>
                    </template>
                  </el-input>
                  <div class="form-tip">密钥将加密存储在服务器，仅用于调用 AI 服务</div>
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="API 地址 (Base URL)" prop="base_url">
                  <el-input
                    v-model="form.base_url"
                    placeholder="https://api.deepseek.com/v1"
                    clearable
                  >
                    <template #prefix>
                      <el-icon><Link /></el-icon>
                    </template>
                  </el-input>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="模型名称 (Model)" prop="model">
                  <el-input
                    v-model="form.model"
                    placeholder="deepseek-chat"
                    clearable
                  >
                    <template #prefix>
                      <el-icon><Cpu /></el-icon>
                    </template>
                  </el-input>
                </el-form-item>
              </el-col>
            </el-row>

            <el-divider />

            <!-- Presets -->
            <div style="margin-bottom: 16px;">
              <span style="color: #909399; font-size: 13px; margin-right: 8px;">快速预设：</span>
              <el-button
                v-for="preset in presets"
                :key="preset.name"
                size="small"
                @click="applyPreset(preset)"
                style="margin-right: 8px;"
              >
                {{ preset.name }}
              </el-button>
            </div>

            <el-divider />

            <div style="display: flex; gap: 12px;">
              <el-button type="primary" size="large" @click="saveConfig" :loading="saving">
                <el-icon><Check /></el-icon> 保存配置
              </el-button>
              <el-button size="large" @click="testConnection" :loading="testing" :disabled="!form.api_key">
                <el-icon><Connection /></el-icon> 测试连接
              </el-button>
              <el-button size="large" @click="deleteConfig" :disabled="!hasConfig" type="danger" plain>
                <el-icon><Delete /></el-icon> 删除配置
              </el-button>
            </div>

            <!-- Test result -->
            <div v-if="testResult !== null" style="margin-top: 16px;">
              <el-alert
                :title="testResult.message"
                :type="testResult.success ? 'success' : 'error'"
                :closable="true"
                show-icon
                @close="testResult = null"
              />
            </div>
          </el-form>
        </el-card>

        <!-- Info cards -->
        <el-row :gutter="16" style="margin-top: 24px;">
          <el-col :span="8" v-for="card in infoCards" :key="card.title">
            <el-card shadow="hover" style="border-radius: 12px;">
              <div style="text-align: center;">
                <el-icon :size="32" :color="card.color"><component :is="card.icon" /></el-icon>
                <h3 style="margin: 8px 0; font-size: 15px;">{{ card.title }}</h3>
                <p style="color: #909399; font-size: 13px;">{{ card.desc }}</p>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import NavSide from '../components/NavSide.vue'
import { settingsAPI } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const saving = ref(false)
const testing = ref(false)
const testResult = ref(null)
const formRef = ref(null)

const form = reactive({
  api_key: '',
  base_url: 'https://api.deepseek.com/v1',
  model: 'deepseek-chat'
})

const rules = {
  api_key: [{ required: true, message: '请输入API密钥', trigger: 'blur' }]
}

const presets = [
  { name: 'DeepSeek', base_url: 'https://api.deepseek.com/v1', model: 'deepseek-chat' },
  { name: '通义千问', base_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1', model: 'qwen-plus' },
  { name: 'OpenAI', base_url: 'https://api.openai.com/v1', model: 'gpt-4o-mini' },
  { name: 'GLM (智谱)', base_url: 'https://open.bigmodel.cn/api/paas/v4', model: 'glm-4-flash' },
  { name: 'Moonshot', base_url: 'https://api.moonshot.cn/v1', model: 'moonshot-v1-8k' },
]

const hasConfig = ref(false)
const configModel = ref('')

const infoCards = [
  { title: 'DeepSeek', desc: '国产高性价比模型，推荐使用', icon: 'TrendCharts', color: '#409eff' },
  { title: '通义千问', desc: '阿里云大模型，中文理解力强', icon: 'Cloudy', color: '#e6a23c' },
  { title: '任意兼容接口', desc: '支持所有 OpenAI 兼容 API', icon: 'Connection', color: '#67c23a' },
]

function applyPreset(preset) {
  form.base_url = preset.base_url
  form.model = preset.model
  ElMessage.info(`已应用 ${preset.name} 预设`)
}

onMounted(async () => {
  loading.value = true
  try {
    const res = await settingsAPI.getLLMConfig()
    if (res.config) {
      form.api_key = res.config.api_key || ''
      form.base_url = res.config.base_url
      form.model = res.config.model
      hasConfig.value = true
      configModel.value = res.config.model
    }
  } catch { /* ignore */ }
  finally { loading.value = false }
})

async function saveConfig() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  saving.value = true
  try {
    const res = await settingsAPI.saveLLMConfig({
      api_key: form.api_key,
      base_url: form.base_url,
      model: form.model
    })
    hasConfig.value = true
    configModel.value = form.model
    ElMessage.success(res.message || '配置保存成功')
  } catch { /* handled by interceptor */ }
  finally { saving.value = false }
}

async function testConnection() {
  testing.value = true
  testResult.value = null
  try {
    const res = await settingsAPI.testConnection({
      api_key: form.api_key,
      base_url: form.base_url,
      model: form.model
    })
    testResult.value = res
  } catch (err) {
    testResult.value = {
      success: false,
      message: err.response?.data?.error || '连接测试失败'
    }
  }
  finally { testing.value = false }
}

async function deleteConfig() {
  try {
    await ElMessageBox.confirm('确定要删除 LLM 配置吗？删除后将恢复 Mock 演示模式。', '确认删除', {
      type: 'warning'
    })
    await settingsAPI.deleteLLMConfig()
    form.api_key = ''
    hasConfig.value = false
    configModel.value = ''
    testResult.value = null
    ElMessage.success('配置已删除，已恢复Mock模式')
  } catch { /* cancelled or error */ }
}
</script>

<style scoped>
.form-tip {
  color: #909399;
  font-size: 12px;
  margin-top: 4px;
}
</style>
