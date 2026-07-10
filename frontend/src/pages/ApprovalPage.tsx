import {
  CalendarDays,
  Check,
  CheckCircle2,
  ChevronDown,
  ClipboardCheck,
  FilePenLine,
  Loader2,
  Mail,
  Play,
  RefreshCw,
  ShieldAlert,
  Trash2,
  X,
} from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { api } from '../api'
import { Badge } from '../components/Badge'
import type { ActionItem, EmailItem } from '../types'

const statusTone = (status: string) => {
  if (['approved', 'executed'].includes(status)) return 'success' as const
  if (['rejected', 'failed'].includes(status)) return 'danger' as const
  if (status === 'escalated') return 'purple' as const
  return 'warning' as const
}

const actionIcon = (type: string) => {
  if (type === 'CREATE_CALENDAR_EVENT') return <CalendarDays size={20} />
  if (type === 'CREATE_GMAIL_DRAFT') return <Mail size={20} />
  if (type === 'ESCALATE') return <ShieldAlert size={20} />
  return <ClipboardCheck size={20} />
}

const prettyAction = (value: string) => value.replace('CREATE_', '').replaceAll('_', ' ').toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase())

export default function ApprovalPage() {
  const [actions, setActions] = useState<ActionItem[]>([])
  const [emails, setEmails] = useState<EmailItem[]>([])
  const [filter, setFilter] = useState('active')
  const [busy, setBusy] = useState('')
  const [expanded, setExpanded] = useState<number | null>(null)
  const [draftPayloads, setDraftPayloads] = useState<Record<number, string>>({})
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')

  const load = async () => {
    try {
      const [actionRows, emailRows] = await Promise.all([api.listActions(), api.listEmails()])
      setActions(actionRows)
      setEmails(emailRows)
      setDraftPayloads(Object.fromEntries(actionRows.map((action) => [action.id, JSON.stringify(action.payload || {}, null, 2)])))
      setError('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load approval queue')
    }
  }

  useEffect(() => { void load() }, [])

  const emailIndex = useMemo(() => new Map(emails.map((email) => [email.id, email])), [emails])
  const visible = actions.filter((action) => {
    if (filter === 'active') return ['pending', 'edited', 'approved', 'failed'].includes(action.status)
    if (filter === 'awaiting') return ['pending', 'edited'].includes(action.status)
    if (filter === 'approved') return action.status === 'approved'
    if (filter === 'failed') return action.status === 'failed'
    return true
  })

  const run = async (key: string, callback: () => Promise<unknown>, success: string) => {
    setBusy(key)
    setNotice('')
    setError('')
    try {
      await callback()
      setNotice(success)
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Action failed')
    } finally {
      setBusy('')
    }
  }

  const savePayload = async (action: ActionItem) => {
    try {
      const parsed = JSON.parse(draftPayloads[action.id] || '{}') as Record<string, unknown>
      await run(`save-${action.id}`, () => api.editAction(action.id, parsed), `Action #${action.id} updated and returned to review.`)
    } catch (err) {
      setError(err instanceof Error ? `Invalid payload JSON: ${err.message}` : 'Invalid payload JSON')
    }
  }

  const counts = {
    awaiting: actions.filter((a) => ['pending', 'edited'].includes(a.status)).length,
    approved: actions.filter((a) => a.status === 'approved').length,
    failed: actions.filter((a) => a.status === 'failed').length,
  }

  return (
    <div className="page-stack">
      <section className="page-header">
        <div><span className="eyebrow">Human decision gate</span><h1>Approval Queue</h1><p>Edit, approve, reject, or execute each proposed action with complete traceability.</p></div>
        <button className="button button-secondary" onClick={() => void load()}><RefreshCw size={16} /> Refresh queue</button>
      </section>

      <section className="approval-summary">
        <button className={`approval-filter ${filter === 'awaiting' ? 'active' : ''}`} onClick={() => setFilter('awaiting')}><span className="approval-filter-icon filter-amber"><FilePenLine size={18} /></span><div><strong>{counts.awaiting}</strong><span>Awaiting decision</span></div></button>
        <button className={`approval-filter ${filter === 'approved' ? 'active' : ''}`} onClick={() => setFilter('approved')}><span className="approval-filter-icon filter-green"><CheckCircle2 size={18} /></span><div><strong>{counts.approved}</strong><span>Ready to execute</span></div></button>
        <button className={`approval-filter ${filter === 'failed' ? 'active' : ''}`} onClick={() => setFilter('failed')}><span className="approval-filter-icon filter-red"><ShieldAlert size={18} /></span><div><strong>{counts.failed}</strong><span>Needs retry</span></div></button>
        <button className={`approval-filter ${filter === 'active' ? 'active' : ''}`} onClick={() => setFilter('active')}><span className="approval-filter-icon filter-violet"><ClipboardCheck size={18} /></span><div><strong>{actions.filter((a) => ['pending', 'edited', 'approved', 'failed'].includes(a.status)).length}</strong><span>All active work</span></div></button>
      </section>

      {notice && <div className="inline-success"><CheckCircle2 size={17} /> {notice}</div>}
      {error && <div className="inline-error">{error}</div>}

      <section className="approval-list">
        {visible.map((action) => {
          const email = emailIndex.get(action.email_id)
          const isOpen = expanded === action.id
          const waiting = ['pending', 'edited'].includes(action.status)
          const executable = ['approved', 'failed'].includes(action.status)
          return (
            <article className="approval-card" key={action.id}>
              <div className="approval-card-main">
                <div className={`approval-action-icon type-${action.action_type.toLowerCase()}`}>{actionIcon(action.action_type)}</div>
                <div className="approval-card-copy">
                  <div className="approval-title-row"><h3>{prettyAction(action.action_type)}</h3><Badge tone={statusTone(action.status)}>{action.status}</Badge><span className="action-number">Action #{action.id}</span></div>
                  <p className="approval-email-title">{email?.subject || `Email #${action.email_id}`}</p>
                  <span className="approval-email-meta">From {email?.sender || 'unknown sender'} · Proposed {new Date(action.created_at).toLocaleString()}</span>
                  {action.reason && <div className="reason-box"><ShieldAlert size={15} /><span>{action.reason}</span></div>}
                </div>
                <button className={`expand-button ${isOpen ? 'expanded' : ''}`} onClick={() => setExpanded(isOpen ? null : action.id)}><ChevronDown size={19} /></button>
              </div>

              <div className="approval-preview">
                {Object.entries(action.payload || {}).slice(0, 4).map(([key, value]) => <div key={key}><span>{key.replaceAll('_', ' ')}</span><strong>{Array.isArray(value) ? value.join(', ') : String(value ?? '—')}</strong></div>)}
              </div>

              {isOpen && (
                <div className="approval-editor">
                  <div className="editor-heading"><div><strong>Editable action payload</strong><span>Changes are audited and require approval again.</span></div><Badge tone="info">JSON contract</Badge></div>
                  <textarea value={draftPayloads[action.id] || '{}'} onChange={(event) => setDraftPayloads((current) => ({ ...current, [action.id]: event.target.value }))} spellCheck={false} />
                  {action.execution_result && <div className={`execution-result ${action.status === 'failed' ? 'execution-result-error' : ''}`}><strong>Last execution result</strong><pre>{JSON.stringify(action.execution_result, null, 2)}</pre></div>}
                </div>
              )}

              <div className="approval-card-actions">
                <button className="button button-ghost" onClick={() => setExpanded(isOpen ? null : action.id)}><FilePenLine size={16} /> {isOpen ? 'Close details' : 'Inspect payload'}</button>
                {waiting && <button className="button button-secondary" onClick={() => void savePayload(action)} disabled={busy === `save-${action.id}`}>{busy === `save-${action.id}` ? <Loader2 size={16} className="spin" /> : <FilePenLine size={16} />} Save changes</button>}
                {waiting && <button className="button button-danger-soft" onClick={() => run(`reject-${action.id}`, () => api.rejectAction(action.id, 'Rejected by human reviewer'), `Action #${action.id} rejected.`)} disabled={busy === `reject-${action.id}`}><X size={16} /> Reject</button>}
                {waiting && <button className="button button-success" onClick={() => run(`approve-${action.id}`, () => api.approveAction(action.id), `Action #${action.id} approved for execution.`)} disabled={busy === `approve-${action.id}`}>{busy === `approve-${action.id}` ? <Loader2 size={16} className="spin" /> : <Check size={16} />} Approve</button>}
                {executable && <button className="button button-primary" onClick={() => run(`execute-${action.id}`, () => api.executeAction(action.id), action.status === 'failed' ? `Action #${action.id} retried.` : `Action #${action.id} executed.`)} disabled={busy === `execute-${action.id}`}>{busy === `execute-${action.id}` ? <Loader2 size={16} className="spin" /> : <Play size={16} />} {action.status === 'failed' ? 'Retry execution' : 'Execute action'}</button>}
              </div>
            </article>
          )
        })}
        {!visible.length && <div className="panel empty-state large-empty"><ClipboardCheck size={38} /><strong>No actions in this queue</strong><span>Analyze and plan an email, or choose another queue filter.</span></div>}
      </section>
    </div>
  )
}
