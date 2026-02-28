import axios from 'axios'

const BASE = '/api/v1'

const api = axios.create({ baseURL: BASE })

// Attach JWT token from localStorage to every request
api.interceptors.request.use(cfg => {
  const token = localStorage.getItem('token')
  if (token) cfg.headers.Authorization = `Bearer ${token}`
  return cfg
})

// Auto-logout on 401
api.interceptors.response.use(
  r => r,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export default api

// ── Auth ──────────────────────────────────────────────────────────────────────
export const authApi = {
  login: (username: string, password: string) =>
    api.post('/auth/login', { username, password }),
  me: () => api.get('/auth/me'),
}

// ── Cases ─────────────────────────────────────────────────────────────────────
export const casesApi = {
  list: (page = 1, size = 20) => api.get('/cases', { params: { page, size } }),
  get: (id: string) => api.get(`/cases/${id}`),
  create: (data: object) => api.post('/cases', data),
  update: (id: string, data: object) => api.patch(`/cases/${id}`, data),
}

// ── Profiles ──────────────────────────────────────────────────────────────────
export const profilesApi = {
  analyze: (data: object) => api.post('/profiles/analyze', data),
  listByCase: (caseId: string) => api.get(`/profiles/case/${caseId}`),
  getByHash: (hash: string) => api.get(`/profiles/${hash}`),
  getHistory: (hash: string) => api.get(`/profiles/${hash}/history`),
  updateStatus: (profileId: string, status: string) =>
    api.patch(`/profiles/${profileId}/status`, null, { params: { new_status: status } }),
}

// ── Evidence ──────────────────────────────────────────────────────────────────
export const evidenceApi = {
  upload: (formData: FormData) =>
    api.post('/evidence/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
  listByCase: (caseId: string) => api.get(`/evidence/case/${caseId}`),
  verify: (evidenceId: string) => api.get(`/evidence/${evidenceId}/verify`),
}

// ── Registry ──────────────────────────────────────────────────────────────────
export const registryApi = {
  search: (hash: string) => api.get('/registry/search', { params: { hash } }),
  blacklist: () => api.get('/registry/blacklist'),
}

// ── Reports ───────────────────────────────────────────────────────────────────
export const reportsApi = {
  generate: (caseId: string, notes?: string) =>
    api.post('/reports/generate', { case_id: caseId, investigator_notes: notes }),
  download: (reportId: string) => `/api/v1/reports/${reportId}/download`,
}
