import { CalendarDays, CheckCircle2, History, Mail, RefreshCw, ShieldAlert, XCircle } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { api } from '../api'
import { Badge } from '../components/Badge'
import type { ActionItem, EmailItem } from '../types'

const terminal = new Set(['executed', 'escalated', 'failed', 'rejected'])
const pretty = (value: string) => value.replace('CREATE_', '').replaceAll('_', ' ').toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase())

export default function HistoryPage() {
  const [actions, setActions] = useState<ActionItem[]>([])
  const [emails, setEmails] = useState<EmailItem[]>([])
  const [filter, setFilter] = useState('all')
  const [error, setError] = useState('')

  const load = async () => {
    try {
      const [actionRows, emailRows] = await Promise.all([api.listActions(), api.listEmails()])
      setActions(actionRows.filter((action) => terminal.has(action.status)))
      setEmails(emailRows)
      setError('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load execution history')
    }
  }

  useEffect(() => { void load() }, [])
  const emailIndex = useMemo(() => new Map(emails.map((email) => [email.id, email])), [emails])
  const visible = actions.filter((action) => filter === 'all' || action.status === filter)

  const icon = (action: ActionItem) => {
    if (action.status === 'failed' || action.status === 'rejected') return <XCircle size={20} />
    if (action.status === 'escalated') return <ShieldAlert size={20} />
    if (action.action_type === 'CREATE_CALENDAR_EVENT') return <CalendarDays size={20} />
    if (action.action_type === 'CREATE_GMAIL_DRAFT') return <Mail size={20} />
    return <CheckCircle2 size={20} />
  }

  return (
    <div className="page-stack">
      <section className="page-header">
        <div><span className="eyebrow">Execution outcomes</span><h1>Workflow History</h1><p>Inspect completed, escalated, rejected, and failed actions with their provider results.</p></div>
        <button className="button button-secondary" onClick={() => void load()}><RefreshCw size={16} /> Refresh</button>
      </section>
      {error && <div className="inline-error">{error}</div>}
      <section className="panel history-panel">
        <div className="panel-heading"><div><span className="eyebrow">Traceable outcomes</span><h3>Execution timeline</h3></div><select value={filter} onChange={(e) => setFilter(e.target.value)}><option value="all">All outcomes</option><option value="executed">Executed</option><option value="escalated">Escalated</option><option value="failed">Failed</option><option value="rejected">Rejected</option></select></div>
        <div className="history-list">
          {visible.map((action) => {
            const email = emailIndex.get(action.email_id)
            const tone = action.status === 'executed' ? 'success' : action.status === 'escalated' ? 'purple' : 'danger'
            return <article className="history-row" key={action.id}><div className={`history-icon history-${action.status}`}>{icon(action)}</div><div className="history-copy"><div><strong>{pretty(action.action_type)}</strong><Badge tone={tone}>{action.status}</Badge></div><h4>{email?.subject || `Email #${action.email_id}`}</h4><span>{action.reason || 'Workflow action completed through the human approval pipeline.'}</span></div><div className="history-time"><span>{new Date(action.executed_at || action.created_at).toLocaleDateString()}</span><strong>{new Date(action.executed_at || action.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</strong></div><details><summary>Provider result</summary><pre>{JSON.stringify(action.execution_result || { status: action.status }, null, 2)}</pre></details></article>
          })}
          {!visible.length && <div className="empty-state large-empty"><History size={38} /><strong>No completed workflow actions</strong><span>Approve and execute a proposed action to populate this timeline.</span></div>}
        </div>
      </section>
    </div>
  )
}
