<template>
  <div class="app-layout">
    <NavSide />
    <div class="main-content">
      <div class="page-header">
        <h2>📄 报告解读</h2>
        <p>上传医疗检查报告，AI自动提取指标并生成通俗解读</p>
      </div>

      <div class="card-container">
        <el-card style="margin-bottom: 20px; border-radius: 12px;">
          <el-upload
            class="upload-area"
            drag
            :auto-upload="false"
            :on-change="handleFileChange"
            :limit="1"
            accept=".jpg,.jpeg,.png,.bmp,.webp,.pdf"
            :file-list="fileList"
          >
            <el-icon :size="48" color="#409eff"><UploadFilled /></el-icon>
            <div class="el-upload__text">
              将医疗报告拖到此处，或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持 JPG/PNG/PDF 格式（演示模式下使用模拟数据）
              </div>
            </template>
          </el-upload>

          <div style="text-align: center; margin-top: 16px;" v-if="currentFile">
            <el-button type="primary" size="large" :loading="loading" @click="uploadReport">
              <el-icon><Document /></el-icon> 开始解读报告
            </el-button>
            <p style="color:#909399; font-size:12px; margin-top:8px;">
              💡 当前为Mock演示模式，将使用模拟报告数据进行演示
            </p>
          </div>
        </el-card>

        <!-- Results -->
        <div v-if="reportResult">
          <!-- Action buttons -->
          <div style="display:flex; gap:12px; margin-bottom:16px; align-items:center;">
            <el-button type="primary" @click="exportReport">
              <el-icon><Printer /></el-icon> 导出报告
            </el-button>
            <span style="color:#909399; font-size:12px;">可将解读结果保存为PDF或打印</span>
          </div>

          <el-card style="margin-bottom: 16px; border-radius: 12px;" v-if="reportResult.raw_text">
            <template #header><strong>📋 OCR识别结果</strong></template>
            <pre class="report-text">{{ reportResult.raw_text }}</pre>
          </el-card>

          <el-card style="margin-bottom: 16px; border-radius: 12px;" v-if="reportResult.indicators && reportResult.indicators.length">
            <template #header><strong>🔬 指标分析</strong></template>
            <div class="indicator-table">
              <div class="indicator-header">
                <span class="ind-col-name">指标名称</span>
                <span class="ind-col-val">检测值</span>
                <span class="ind-col-unit">单位</span>
                <span class="ind-col-range">参考范围</span>
                <span class="ind-col-bar">偏差</span>
                <span class="ind-col-status">状态</span>
              </div>
              <div
                v-for="(row, idx) in reportResult.indicators"
                :key="idx"
                :class="['indicator-row', indicatorClass(row)]"
              >
                <span class="ind-col-name">{{ row.name }}</span>
                <span class="ind-col-val">{{ row.value }}</span>
                <span class="ind-col-unit">{{ row.unit }}</span>
                <span class="ind-col-range">{{ row.range }}</span>
                <span class="ind-col-bar">
                  <span :class="['deviation-bar', indicatorClass(row)]" :style="deviationWidth(row)">
                    {{ indicatorArrow(row) }}
                  </span>
                </span>
                <span class="ind-col-status">
                  <el-tag
                    :type="row.status === '正常' ? 'success' : row.status === '偏高' ? 'danger' : 'warning'"
                    size="small"
                    effect="dark"
                  >
                    {{ row.status === '偏高' ? '↑ ' : row.status === '偏低' ? '↓ ' : '' }}{{ row.status }}
                  </el-tag>
                </span>
              </div>
            </div>
          </el-card>

          <el-card style="margin-bottom: 16px; border-radius: 12px;" v-if="reportResult.interpretation">
            <template #header><strong>📝 AI解读</strong></template>
            <div class="interpretation-content" v-html="formatText(reportResult.interpretation)"></div>
          </el-card>

          <el-card style="margin-bottom: 16px; border-radius: 12px;" v-if="reportResult.advice">
            <template #header><strong>💡 综合评估与建议</strong></template>
            <div class="interpretation-content" v-html="formatText(reportResult.advice)"></div>
          </el-card>

          <el-alert
            title="⚠️ 重要提示"
            description="以上报告解读由AI生成，仅供健康参考，不能替代专业医生的诊断。如有指标异常或身体不适，请及时前往医院就诊。"
            type="warning"
            :closable="false"
            show-icon
          />
        </div>

        <!-- History -->
        <div v-if="reports.length > 0" style="margin-top: 32px;">
          <h3 style="margin-bottom: 16px;">📚 历史报告</h3>
          <el-table :data="reports" style="width: 100%; border-radius: 8px;">
            <el-table-column prop="filename" label="文件名" />
            <el-table-column label="上传时间" width="180">
              <template #default="{ row }">
                {{ formatTime(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200">
              <template #default="{ row }">
                <el-button size="small" type="primary" link @click="viewReport(row)">
                  <el-icon><View /></el-icon> 查看详情
                </el-button>
                <el-popconfirm title="确定删除该报告吗？" @confirm="deleteReport(row.id)">
                  <template #reference>
                    <el-button size="small" type="danger" link>
                      <el-icon><Delete /></el-icon> 删除
                    </el-button>
                  </template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import NavSide from '../components/NavSide.vue'
import { reportAPI } from '../api'
import { ElMessage } from 'element-plus'

const currentFile = ref(null)
const fileList = ref([])
const loading = ref(false)
const reportResult = ref(null)
const reports = ref([])

function formatText(text) {
  return text ? text.replace(/\n/g, '<br>') : ''
}

function formatTime(t) {
  return t ? t.slice(0, 16).replace('T', ' ') : ''
}

// ---- Indicator visualization helpers ----

function indicatorClass(row) {
  if (row.status === '偏高') return 'ind-high'
  if (row.status === '偏低') return 'ind-low'
  return 'ind-normal'
}

function indicatorArrow(row) {
  if (row.status === '偏高') return '↑'
  if (row.status === '偏低') return '↓'
  return ''
}

function deviationWidth(row) {
  // Calculate a rough width based on how far the value is from the reference range
  // Parse value and range (simple heuristic)
  try {
    const val = parseFloat(row.value)
    const rangeParts = String(row.range || '').split('-')
    if (rangeParts.length !== 2) return { width: '0%' }
    const lo = parseFloat(rangeParts[0])
    const hi = parseFloat(rangeParts[1])
    const mid = (lo + hi) / 2
    const span = hi - lo
    if (span <= 0) return { width: '0%' }
    // How far is val from the nearest bound, as a percentage of span
    let pct = 0
    if (row.status === '偏高') {
      pct = Math.min(100, Math.max(5, ((val - hi) / span) * 100))
    } else if (row.status === '偏低') {
      pct = Math.min(100, Math.max(5, ((lo - val) / span) * 100))
    }
    return { width: pct + '%' }
  } catch {
    return { width: '0%' }
  }
}

// ---- Export report as PDF (via browser print) ----

function exportReport() {
  if (!reportResult.value) return
  const r = reportResult.value
  const now = new Date().toLocaleString('zh-CN')

  // Build a clean report HTML
  let indicatorsHtml = ''
  if (r.indicators && r.indicators.length) {
    indicatorsHtml = '<h3>📋 指标分析</h3><table><thead><tr><th>指标</th><th>值</th><th>单位</th><th>参考范围</th><th>状态</th></tr></thead><tbody>'
    for (const ind of r.indicators) {
      const color = ind.status === '偏高' ? '#f56c6c' : ind.status === '偏低' ? '#e6a23c' : '#67c23a'
      indicatorsHtml += `<tr><td>${ind.name}</td><td>${ind.value}</td><td>${ind.unit}</td><td>${ind.range}</td><td style="color:${color};font-weight:bold">${ind.status}</td></tr>`
    }
    indicatorsHtml += '</tbody></table>'
  }

  const html = `<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><title>医疗报告解读</title>
<style>
  body { font-family: "Microsoft YaHei", sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; color: #333; }
  h1 { border-bottom: 2px solid #409eff; padding-bottom: 8px; }
  h3 { color: #409eff; margin-top: 24px; }
  table { width: 100%; border-collapse: collapse; margin: 12px 0; }
  th, td { border: 1px solid #dcdfe6; padding: 8px 12px; text-align: left; }
  th { background: #f5f7fa; }
  .footer { margin-top: 32px; padding-top: 16px; border-top: 1px solid #ddd; color: #999; font-size: 12px; }
  pre { white-space: pre-wrap; background: #f5f7fa; padding: 12px; border-radius: 6px; font-size: 13px; }
</style></head><body>
  <h1>🏥 AI医疗报告解读</h1>
  <p>文件名：${r.filename || '-'} | 导出时间：${now}</p>
  ${r.raw_text ? '<h3>📋 OCR识别结果</h3><pre>' + r.raw_text + '</pre>' : ''}
  ${indicatorsHtml}
  ${r.interpretation ? '<h3>📝 AI解读</h3><p>' + r.interpretation.replace(/\\n/g, '<br>') + '</p>' : ''}
  ${r.advice ? '<h3>💡 综合评估与建议</h3><p>' + r.advice.replace(/\\n/g, '<br>') + '</p>' : ''}
  <div class="footer">⚠️ 以上内容由AI生成，仅供健康参考，不能替代专业医生诊断。</div>
</body></html>`

  const w = window.open('', '_blank', 'width=900,height=700')
  if (w) {
    w.document.write(html)
    w.document.close()
    // Trigger print after rendering
    setTimeout(() => { w.print() }, 500)
  }
}

// ---- Delete report ----

async function deleteReport(id) {
  try {
    await reportAPI.deleteReport(id)
    // Refresh list
    const listRes = await reportAPI.getList()
    reports.value = listRes.reports
    // If the deleted report is currently shown, clear it
    if (reportResult.value && reportResult.value.id === id) {
      reportResult.value = null
    }
    ElMessage.success('报告已删除')
  } catch { ElMessage.error('删除失败，请稍后重试') }
}

onMounted(async () => {
  try {
    const res = await reportAPI.getList()
    reports.value = res.reports
  } catch { /* ignore */ }
})

function handleFileChange(file) {
  currentFile.value = file.raw
  fileList.value = [file]
}

async function uploadReport() {
  if (!currentFile.value) return
  loading.value = true
  try {
    const formData = new FormData()
    formData.append('file', currentFile.value)
    const res = await reportAPI.upload(formData)
    reportResult.value = res.report
    const listRes = await reportAPI.getList()
    reports.value = listRes.reports
  } catch { /* handled by interceptor */ }
  finally { loading.value = false }
}

async function viewReport(report) {
  try {
    const res = await reportAPI.getDetail(report.id)
    reportResult.value = res.report
  } catch { /* ignore */ }
}
</script>

<style scoped>
.upload-area { width: 100%; }
.report-text {
  background: #f5f7fa;
  padding: 16px;
  border-radius: 8px;
  font-size: 13px;
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-word;
  color: #303133;
}
.interpretation-content {
  line-height: 1.8;
  color: #303133;
  font-size: 14px;
}
/* ---- Indicator table visualization ---- */
.indicator-table {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  overflow: hidden;
}
.indicator-header {
  display: flex;
  background: #f5f7fa;
  padding: 10px 16px;
  font-weight: 600;
  font-size: 13px;
  color: #606266;
  border-bottom: 2px solid #dcdfe6;
}
.indicator-row {
  display: flex;
  padding: 10px 16px;
  align-items: center;
  border-bottom: 1px solid #ebeef5;
  font-size: 13px;
  transition: background 0.2s;
}
.indicator-row:last-child { border-bottom: none; }
.indicator-row.ind-high { background: #fef0f0; }
.indicator-row.ind-low { background: #fdf6ec; }
.indicator-row.ind-normal { background: #fff; }
.indicator-row:hover { filter: brightness(0.97); }
.ind-col-name { flex: 0 0 200px; font-weight: 500; }
.ind-col-val { flex: 0 0 90px; font-weight: 700; color: #303133; }
.ind-col-unit { flex: 0 0 70px; color: #909399; font-size: 12px; }
.ind-col-range { flex: 0 0 120px; color: #909399; font-size: 12px; }
.ind-col-bar { flex: 1; min-width: 50px; padding: 0 8px; }
.ind-col-status { flex: 0 0 80px; text-align: right; }
.deviation-bar {
  display: inline-block;
  height: 6px;
  border-radius: 3px;
  min-width: 4px;
}
.deviation-bar.ind-high { background: #f56c6c; }
.deviation-bar.ind-low { background: #e6a23c; }
.deviation-bar.ind-normal { background: #67c23a; }
</style>
