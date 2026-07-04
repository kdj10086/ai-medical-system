import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

// Request interceptor - add token
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor - handle errors
api.interceptors.response.use(
  response => response.data,
  error => {
    // Ignore auth errors on login/register endpoints (handled by caller)
    const isAuthEndpoint = error.config?.url?.includes('/auth/')

    if (error.response) {
      const status = error.response.status
      const serverMsg = error.response.data?.error || ''

      if (status === 401) {
        // Token expired or invalid — redirect silently (don't show error)
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        if (!isAuthEndpoint && window.location.pathname !== '/login') {
          window.location.href = '/login'
        }
      } else if (!isAuthEndpoint) {
        // Show server error message for other HTTP errors
        ElMessage.error(serverMsg || `请求失败 (${status})`)
      }
    } else if (error.code === 'ECONNABORTED') {
      // Timeout
      if (!isAuthEndpoint) {
        ElMessage.error('请求超时，请检查网络或后端服务')
      }
    } else {
      // Network error (no response at all — server likely down)
      if (!isAuthEndpoint) {
        ElMessage.error('无法连接后端服务，请确认后端已启动 (localhost:5000)')
      }
    }
    return Promise.reject(error)
  }
)

// ============ Auth API ============
export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data)
}

// ============ Consultation API ============
export const consultationAPI = {
  chat: (data) => api.post('/consultation/chat', data),
  getHistory: () => api.get('/consultation/history'),
  getSession: (sessionId) => api.get(`/consultation/session/${sessionId}`),
  deleteSession: (sessionId) => api.delete(`/consultation/session/${sessionId}`),

  /** SSE streaming chat — returns a ReadableStream to consume line by line.
   *  Usage:
   *    const reader = consultationAPI.chatStream({message, session_id})
   *    for await (const chunk of reader) { ... }
   */
  async chatStream(data) {
    const token = localStorage.getItem('token')
    const resp = await fetch('/api/consultation/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: token ? `Bearer ${token}` : ''
      },
      body: JSON.stringify(data)
    })
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ error: `HTTP ${resp.status}` }))
      throw new Error(err.error || `请求失败 (${resp.status})`)
    }
    return resp.body.getReader()
  }
}

// ============ Recommendation API ============
export const recommendationAPI = {
  recommend: (data) => api.post('/recommendation/recommend', data),
  getDepartments: () => api.get('/recommendation/departments')
}

// ============ Report API ============
export const reportAPI = {
  upload: (formData) => api.post('/report/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  getList: () => api.get('/report/list'),
  getDetail: (id) => api.get(`/report/${id}`),
  deleteReport: (id) => api.delete(`/report/${id}`)
}

// ============ Records API ============
export const recordsAPI = {
  getTimeline: () => api.get('/records/timeline')
}

// ============ Settings API ============
export const settingsAPI = {
  getLLMConfig: () => api.get('/settings/llm'),
  saveLLMConfig: (data) => api.put('/settings/llm', data),
  deleteLLMConfig: () => api.delete('/settings/llm'),
  testConnection: (data) => api.post('/settings/llm/test', data)
}

export default api
