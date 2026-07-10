export type Intent =
  | 'meeting_request'
  | 'invoice_payment'
  | 'customer_complaint'
  | 'job_recruitment'
  | 'project_update'
  | 'deadline_reminder'
  | 'general_information'
  | 'spam_or_ignore'
  | 'unknown'

export type Priority = 'low' | 'medium' | 'high'
export type ActionStatus = 'pending' | 'approved' | 'rejected' | 'edited' | 'executed' | 'failed' | 'escalated'
export type ActionType = 'CREATE_GMAIL_DRAFT' | 'CREATE_CALENDAR_EVENT' | 'CREATE_TASK' | 'ESCALATE' | 'IGNORE'

export interface Health {
  status: string
  app_name: string
  env: string
  demo_mode: boolean
  database_connected: boolean
}

export interface EmailAnalysis {
  id: number
  email_id: number
  intent: Intent
  priority: Priority
  requires_reply: boolean
  requested_action: ActionType
  confidence_score: number
  summary: string
  suggested_reply: string
  deadline?: string | null
  meeting_date?: string | null
  meeting_time?: string | null
  raw_ai_response?: unknown
  created_at: string
}

export interface EmailItem {
  id: number
  gmail_message_id: string
  sender: string
  subject: string
  body: string
  received_at?: string | null
  synced_at: string
  is_demo: boolean
  analysis?: EmailAnalysis | null
}

export interface ActionItem {
  id: number
  email_id: number
  analysis_id?: number | null
  action_type: ActionType
  status: ActionStatus
  payload?: Record<string, unknown> | null
  reason?: string | null
  created_at: string
  approved_at?: string | null
  executed_at?: string | null
  execution_result?: Record<string, unknown> | null
}

export interface TaskItem {
  id: number
  action_id: number
  title: string
  description: string
  due_date?: string | null
  status: 'open' | 'done'
  created_at: string
}

export interface AuditItem {
  id: number
  event_type: string
  related_email_id?: number | null
  related_action_id?: number | null
  message: string
  details?: Record<string, unknown> | null
  created_at: string
}

export interface Metrics {
  total_emails: number
  emails_analyzed: number
  pending_actions: number
  approved_actions: number
  executed_actions: number
  escalated_emails: number
}

export interface DashboardOverview {
  metrics: Metrics
  analysis_rate: number
  completion_rate: number
  automation_rate: number
  average_confidence: number
  high_priority_emails: number
  open_tasks: number
  intent_distribution: Record<string, number>
  priority_distribution: Record<string, number>
  action_status_distribution: Record<string, number>
  action_type_distribution: Record<string, number>
  recent_activity: AuditItem[]
}

export interface DemoBootstrapResult {
  emails_total: number
  emails_added: number
  emails_analyzed: number
  actions_created: number
  message: string
}
