import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Auth APIs
export const authApi = {
  login: () => api.get('/api/auth/login'),
  callback: (code: string) => api.get(`/api/auth/callback?code=${code}`),
  logout: () => api.post('/api/auth/logout'),
  me: () => api.get('/api/auth/me'),
  status: () => api.get('/api/auth/status'),
}

// Email APIs
export const emailApi = {
  list: (maxResults = 20) => api.get(`/api/emails/inbox?max_results=${maxResults}`),
  get: (id: string) => api.get(`/api/emails/${id}`),
  send: (data: any) => api.post('/api/emails/send', data),
  generate: (data: any) => api.post('/api/emails/generate', data),
  draft: (data: any) => api.post('/api/emails/draft', data),
  drafts: () => api.get('/api/emails/drafts'),
  delete: (id: string) => api.delete(`/api/emails/${id}`),
  star: (id: string) => api.post(`/api/emails/${id}/star`),
  markRead: (id: string) => api.post(`/api/emails/${id}/read`),
  followUp: (data: any) => api.post('/api/emails/follow-up', data),
}

// AI APIs
export const aiApi = {
  improve: (text: string) => api.post('/api/ai/improve', { text }),
  summarize: (text: string) => api.post('/api/ai/summarize', { text }),
  translate: (text: string, language: string) => api.post('/api/ai/translate', { text, target_language: language }),
  rewrite: (text: string, tone: string) => api.post('/api/ai/rewrite', { text, tone }),
  suggestReply: (content: string, tone: string) => api.post('/api/ai/suggest-reply', { email_content: content, tone }),
  sentiment: (text: string) => api.post('/api/ai/sentiment', { text }),
  actionItems: (text: string) => api.post('/api/ai/action-items', { text }),
  categorize: (text: string) => api.post('/api/ai/categorize', { text }),
  spamCheck: (text: string) => api.post('/api/ai/spam-check', { text }),
  subjectLines: (text: string, count = 5) => api.post('/api/ai/subject-lines', { text, count }),
  models: () => api.get('/api/ai/models'),
  status: () => api.get('/api/ai/status'),
}

// Template APIs
export const templateApi = {
  list: () => api.get('/api/templates/'),
  builtin: () => api.get('/api/templates/builtin'),
  get: (id: number) => api.get(`/api/templates/${id}`),
  create: (data: any) => api.post('/api/templates/', data),
  update: (id: number, data: any) => api.put(`/api/templates/${id}`, data),
  delete: (id: number) => api.delete(`/api/templates/${id}`),
}

// Contact APIs
export const contactApi = {
  list: (search?: string) => api.get(`/api/contacts/${search ? `?search=${search}` : ''}`),
  get: (id: number) => api.get(`/api/contacts/${id}`),
  create: (data: any) => api.post('/api/contacts/', data),
  update: (id: number, data: any) => api.put(`/api/contacts/${id}`, data),
  delete: (id: number) => api.delete(`/api/contacts/${id}`),
  import: (contacts: any[]) => api.post('/api/contacts/import', { contacts }),
}

// Analytics APIs
export const analyticsApi = {
  get: () => api.get('/api/analytics/'),
  sent: (days = 30) => api.get(`/api/analytics/emails/sent?days=${days}`),
  received: (days = 30) => api.get(`/api/analytics/emails/received?days=${days}`),
  activity: (days = 7) => api.get(`/api/analytics/activity?days=${days}`),
  contactsStats: () => api.get('/api/analytics/contacts/stats'),
}

// Schedule APIs
export const scheduleApi = {
  list: (pendingOnly = true) => api.get(`/api/schedule/?pending_only=${pendingOnly}`),
  get: (id: number) => api.get(`/api/schedule/${id}`),
  create: (data: any) => api.post('/api/schedule/', data),
  cancel: (id: number) => api.delete(`/api/schedule/${id}`),
  process: () => api.post('/api/schedule/process'),
}
