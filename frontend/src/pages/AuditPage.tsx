import { Activity, Download, Filter, RefreshCw, Search } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { api } from '../api'
import { Badge } from '../components/Badge'
import type { AuditItem } from '../types'

const pretty = (value: string) => value.replaceAll('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase())

export default function AuditPage() {
  const [logs, setLogs] = useState<AuditItem[]>([])
  const [query, setQuery] = useState('')
  const [eventType, setEventType] = useState('all')
  const [error, setError] = useState('')

  const load = async () => {
    try {
      setLogs(await api.listAuditLogs())
      setError('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load audit logs')
    }
  }

  useEffect(() => { void load() }, [])
  const eventTypes = useMemo(() => [...new Set(logs.map((log) => log.event_type))].sort(), [logs])
  const filtered = useMemo(() => logs.filter((log) => {
    const matchesEvent = eventType === 'all' || log.event_type === eventType
    const term = query.toLowerCase().trim()
    const matchesQuery = !term || `${log.message} ${log.event_type} ${log.related_email_id || ''} ${log.related_action_id || ''}`.toLowerCase().includes(term)
    return matchesEvent && matchesQuery
  }), [logs, eventType, query])

  const download = () => {
    const blob = new Blob([JSON.stringify(filtered, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = 'mailpilot-audit-log.json'
    anchor.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="page-stack">
      <section className="page-header">
        <div><span className="eyebrow">Append-only traceability</span><h1>Audit Trail</h1><p>Every sync, AI decision, approval, edit, rejection, task update, and execution is preserved.</p></div>
        <div className="page-actions"><button className="button button-secondary" onClick={() => void load()}><RefreshCw size={16} /> Refresh</button><button className="button button-primary" onClick={download}><Download size={16} /> Export JSON</button></div>
      </section>
      {error && <div className="inline-error">{error}</div>}
      <section className="panel audit-panel">
        <div className="audit-toolbar"><div className="search-field"><Search size={16} /><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search messages, email IDs, or action IDs…" /></div><div className="select-with-icon"><Filter size={15} /><select value={eventType} onChange={(e) => setEventType(e.target.value)}><option value="all">All event types</option>{eventTypes.map((type) => <option key={type} value={type}>{pretty(type)}</option>)}</select></div><Badge tone="info">{filtered.length} events</Badge></div>
        <div className="audit-table-wrap"><table className="data-table"><thead><tr><th>Timestamp</th><th>Event</th><th>Related record</th><th>Message</th><th>Details</th></tr></thead><tbody>{filtered.map((log) => <tr key={log.id}><td><strong>{new Date(log.created_at).toLocaleDateString()}</strong><span>{new Date(log.created_at).toLocaleTimeString()}</span></td><td><Badge tone={log.event_type.includes('failed') || log.event_type.includes('rejected') ? 'danger' : log.event_type.includes('approved') || log.event_type.includes('executed') || log.event_type.includes('completed') ? 'success' : 'neutral'}>{pretty(log.event_type)}</Badge></td><td><span>{log.related_email_id ? `Email #${log.related_email_id}` : '—'}</span><span>{log.related_action_id ? `Action #${log.related_action_id}` : ''}</span></td><td>{log.message}</td><td>{log.details ? <details><summary>View</summary><pre>{JSON.stringify(log.details, null, 2)}</pre></details> : '—'}</td></tr>)}</tbody></table></div>
        {!filtered.length && <div className="empty-state large-empty"><Activity size={36} /><strong>No matching audit events</strong><span>Adjust the filters or run a workflow.</span></div>}
      </section>
    </div>
  )
}
