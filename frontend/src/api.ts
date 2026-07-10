import type {
  ActionItem,
  AuditItem,
  DashboardOverview,
  DemoBootstrapResult,
  EmailAnalysis,
  EmailItem,
  Health,
  TaskItem,
} from './types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  })
  if (!response.ok) {
    let message = `${response.status} ${response.statusText}`
    try {
      const data = await response.json()
      message = data.detail || data.message || message
    } catch {
      // Keep HTTP fallback.
    }
    throw new Error(message)
  }
  return response.json() as Promise<T>
}

export const api = {
  health: () => request<Health>('/health'),
  overview: () => request<DashboardOverview>('/dashboard/overview'),
  bootstrapDemo: () => request<DemoBootstrapResult>('/demo/bootstrap', { method: 'POST' }),

  syncEmails: () => request('/emails/sync?max_results=50', { method: 'POST' }),
  listEmails: () => request<EmailItem[]>('/emails?limit=200'),
  getEmail: (id: number) => request<EmailItem>(`/emails/${id}`),
  analyzeEmail: (id: number) => request<EmailAnalysis>(`/emails/${id}/analyze`, { method: 'POST' }),
  planEmail: (id: number, force = false) => request<ActionItem[]>(`/emails/${id}/plan?force=${force}`, { method: 'POST' }),

  listActions: (status?: string) =>
    request<ActionItem[]>(`/actions?limit=200${status ? `&status=${encodeURIComponent(status)}` : ''}`),
  editAction: (id: number, payload: Record<string, unknown>) =>
    request(`/actions/${id}`, { method: 'PATCH', body: JSON.stringify({ payload }) }),
  approveAction: (id: number) => request(`/actions/${id}/approve`, { method: 'POST' }),
  rejectAction: (id: number, reason?: string) =>
    request(`/actions/${id}/reject`, { method: 'POST', body: JSON.stringify({ reason: reason || null }) }),
  executeAction: (id: number) => request(`/actions/${id}/execute`, { method: 'POST' }),

  listTasks: (status?: string) => request<TaskItem[]>(`/tasks${status ? `?status=${status}` : ''}`),
  completeTask: (id: number) => request(`/tasks/${id}/complete`, { method: 'POST' }),
  reopenTask: (id: number) => request(`/tasks/${id}/reopen`, { method: 'POST' }),

  listAuditLogs: () => request<AuditItem[]>('/audit-logs?limit=400'),
}
