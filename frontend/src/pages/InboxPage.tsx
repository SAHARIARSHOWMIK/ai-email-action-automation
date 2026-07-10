import {
  ArrowRight,
  Bot,
  CalendarDays,
  CheckCircle2,
  Clock3,
  Inbox,
  Loader2,
  Mail,
  RefreshCw,
  Search,
  ShieldAlert,
  Sparkles,
  WandSparkles,
} from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { api } from '../api'
import { Badge } from '../components/Badge'
import type { ActionItem, EmailItem } from '../types'

const intentLabels: Record<string, string> = {
  meeting_request: 'Meeting request',
  invoice_payment: 'Invoice & payment',
  customer_complaint: 'Customer complaint',
  job_recruitment: 'Recruitment',
  project_update: 'Project update',
  deadline_reminder: 'Deadline reminder',
  general_information: 'General information',
  spam_or_ignore: 'Low-value / ignore',
  unknown: 'Unclear intent',
}

function priorityTone(priority?: string) {
  if (priority === 'high') return 'danger' as const
  if (priority === 'medium') return 'warning' as const
  return 'neutral' as const
}

export default function InboxPage() {
  const [emails, setEmails] = useState<EmailItem[]>([])
  const [actions, setActions] = useState<ActionItem[]>([])
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [detail, setDetail] = useState<EmailItem | null>(null)
  const [query, setQuery] = useState('')
  const [priority, setPriority] = useState('all')
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState('')
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')

  const load = async (keepSelection = true) => {
    setLoading(true)
    try {
      const [emailRows, actionRows] = await Promise.all([api.listEmails(), api.listActions()])
      setEmails(emailRows)
      setActions(actionRows)
      const id = keepSelection && selectedId ? selectedId : emailRows[0]?.id || null
      setSelectedId(id)
      if (id) setDetail(await api.getEmail(id))
      setError('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load inbox')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load(false)
  }, [])

  const selectEmail = async (id: number) => {
    setSelectedId(id)
    setNotice('')
    try {
      setDetail(await api.getEmail(id))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load email')
    }
  }

  const filtered = useMemo(() => {
    const normalized = query.toLowerCase().trim()
    return emails.filter((email) => {
      const matchesQuery = !normalized || `${email.subject} ${email.sender} ${email.body}`.toLowerCase().includes(normalized)
      const matchesPriority = priority === 'all' || email.analysis?.priority === priority
      return matchesQuery && matchesPriority
    })
  }, [emails, query, priority])

  const relatedActions = actions.filter((action) => action.email_id === selectedId)

  const run = async (name: string, callback: () => Promise<unknown>, success: string) => {
    setBusy(name)
    setNotice('')
    setError('')
    try {
      await callback()
      setNotice(success)
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : `${name} failed`)
    } finally {
      setBusy('')
    }
  }

  return (
    <div className="page-stack">
      <section className="page-header">
        <div><span className="eyebrow">AI-assisted triage</span><h1>Smart Inbox</h1><p>Inspect incoming work, understand the AI decision, and prepare the next safe action.</p></div>
        <div className="page-actions">
          <button className="button button-secondary" onClick={() => void load()}><RefreshCw size={16} /> Refresh</button>
          <button className="button button-primary" onClick={() => run('sync', api.syncEmails, 'Inbox synchronized successfully.')} disabled={busy === 'sync'}>{busy === 'sync' ? <Loader2 size={16} className="spin" /> : <Mail size={16} />} Sync emails</button>
        </div>
      </section>

      {notice && <div className="inline-success"><CheckCircle2 size={17} /> {notice}</div>}
      {error && <div className="inline-error">{error}</div>}

      <section className="inbox-layout panel">
        <aside className="mail-list-pane">
          <div className="mail-list-toolbar">
            <div className="search-field"><Search size={16} /><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search sender or subject…" /></div>
            <select value={priority} onChange={(e) => setPriority(e.target.value)}><option value="all">All priorities</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option></select>
          </div>
          <div className="mail-list-count">{filtered.length} messages</div>
          <div className="mail-list">
            {loading ? <div className="page-loader"><Loader2 className="spin" /> Loading inbox…</div> : filtered.map((email) => (
              <button key={email.id} className={`mail-row ${selectedId === email.id ? 'mail-row-active' : ''}`} onClick={() => void selectEmail(email.id)}>
                <div className="sender-avatar">{email.sender.slice(0, 1).toUpperCase()}</div>
                <div className="mail-row-copy">
                  <div className="mail-row-top"><strong>{email.sender.split('<')[0].trim()}</strong><time>{new Date(email.synced_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}</time></div>
                  <span className="mail-subject">{email.subject}</span>
                  <p>{email.body.replace(/\s+/g, ' ').slice(0, 90)}{email.body.length > 90 ? '…' : ''}</p>
                  <div className="mail-tags">
                    {email.analysis ? <Badge tone={priorityTone(email.analysis.priority)}>{email.analysis.priority}</Badge> : <Badge tone="info">Not analyzed</Badge>}
                    {email.analysis && <span>{intentLabels[email.analysis.intent] || email.analysis.intent}</span>}
                  </div>
                </div>
              </button>
            ))}
            {!loading && !filtered.length && <div className="empty-state"><Inbox size={30} /><strong>No matching emails</strong><span>Try another filter or synchronize the inbox.</span></div>}
          </div>
        </aside>

        <section className="mail-detail-pane">
          {!detail ? (
            <div className="empty-state detail-empty"><Mail size={34} /><strong>Select an email</strong><span>Choose a message from the inbox to inspect its AI analysis.</span></div>
          ) : (
            <>
              <div className="mail-detail-header">
                <div><div className="detail-kicker"><Badge tone={detail.is_demo ? 'purple' : 'success'}>{detail.is_demo ? 'Controlled demo email' : 'Gmail message'}</Badge></div><h2>{detail.subject}</h2><p>From <strong>{detail.sender}</strong> · {new Date(detail.synced_at).toLocaleString()}</p></div>
                <div className="mail-detail-actions">
                  <button className="button button-secondary" disabled={busy === 'analyze'} onClick={() => run('analyze', () => api.analyzeEmail(detail.id), 'AI analysis completed.')}>
                    {busy === 'analyze' ? <Loader2 size={16} className="spin" /> : <Sparkles size={16} />} {detail.analysis ? 'Re-analyze' : 'Analyze email'}
                  </button>
                  <button className="button button-primary" disabled={!detail.analysis || busy === 'plan'} onClick={() => run('plan', () => api.planEmail(detail.id), 'Workflow action planned for approval.')}>
                    {busy === 'plan' ? <Loader2 size={16} className="spin" /> : <WandSparkles size={16} />} Plan next action
                  </button>
                </div>
              </div>

              <div className="email-body-card"><div className="email-body-label"><Mail size={15} /> Original message</div><div className="email-body-text">{detail.body}</div></div>

              <div className="analysis-grid">
                <article className="analysis-card">
                  <div className="panel-heading"><div><span className="eyebrow">Structured decision</span><h3>AI analysis</h3></div><Bot size={22} className="muted-icon" /></div>
                  {detail.analysis ? (
                    <>
                      <div className="analysis-summary-row"><div className="confidence-ring" style={{ '--score': `${Math.round(detail.analysis.confidence_score * 100) * 3.6}deg` } as React.CSSProperties}><span>{Math.round(detail.analysis.confidence_score * 100)}%</span></div><div><Badge tone={priorityTone(detail.analysis.priority)}>{detail.analysis.priority} priority</Badge><h4>{intentLabels[detail.analysis.intent] || detail.analysis.intent}</h4><p>{detail.analysis.summary}</p></div></div>
                      <div className="analysis-facts">
                        <div><span>Recommended action</span><strong>{detail.analysis.requested_action.replace('CREATE_', '').replaceAll('_', ' ')}</strong></div>
                        <div><span>Reply required</span><strong>{detail.analysis.requires_reply ? 'Yes' : 'No'}</strong></div>
                        <div><span>Deadline</span><strong>{detail.analysis.deadline || 'Not detected'}</strong></div>
                        <div><span>Meeting</span><strong>{detail.analysis.meeting_date ? `${detail.analysis.meeting_date} · ${detail.analysis.meeting_time || 'time unclear'}` : 'Not detected'}</strong></div>
                      </div>
                    </>
                  ) : <div className="empty-state compact"><Bot size={27} /><strong>Analysis not run</strong><span>Analyze this email to extract intent, priority, confidence, and action data.</span></div>}
                </article>

                <article className="analysis-card">
                  <div className="panel-heading"><div><span className="eyebrow">Safe response</span><h3>Suggested reply</h3></div><ShieldAlert size={21} className="muted-icon" /></div>
                  {detail.analysis?.suggested_reply ? <div className="reply-preview"><span>Draft preview</span><p>{detail.analysis.suggested_reply}</p><small>This is only a suggestion. Gmail actions create a draft and still require approval.</small></div> : <div className="empty-state compact"><Mail size={27} /><strong>No draft needed</strong><span>The current analysis does not recommend a reply draft.</span></div>}
                </article>
              </div>

              <article className="panel related-actions-panel">
                <div className="panel-heading"><div><span className="eyebrow">Workflow state</span><h3>Proposed actions</h3></div><Badge tone={relatedActions.length ? 'warning' : 'neutral'}>{relatedActions.length} action{relatedActions.length === 1 ? '' : 's'}</Badge></div>
                {relatedActions.length ? <div className="related-action-list">{relatedActions.map((action) => <div className="related-action" key={action.id}><div className={`action-type-icon action-${action.action_type.toLowerCase()}`}>{action.action_type.includes('CALENDAR') ? <CalendarDays size={18} /> : action.action_type === 'ESCALATE' ? <ShieldAlert size={18} /> : <ArrowRight size={18} />}</div><div><strong>{action.action_type.replace('CREATE_', '').replaceAll('_', ' ')}</strong><span>{action.reason || 'Generated from the structured AI decision.'}</span></div><Badge tone={action.status === 'approved' || action.status === 'executed' ? 'success' : action.status === 'rejected' || action.status === 'failed' ? 'danger' : 'warning'}>{action.status}</Badge></div>)}</div> : <div className="empty-state compact"><Clock3 size={27} /><strong>No action planned</strong><span>Complete the AI analysis, then plan the next action.</span></div>}
              </article>
            </>
          )}
        </section>
      </section>
    </div>
  )
}
