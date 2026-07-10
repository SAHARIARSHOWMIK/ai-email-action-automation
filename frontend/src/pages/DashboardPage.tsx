import {
  Activity,
  ArrowRight,
  Bot,
  CheckCircle2,
  Clock3,
  Gauge,
  Inbox,
  ListTodo,
  RefreshCw,
  ShieldAlert,
  Sparkles,
  WandSparkles,
} from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { api } from '../api'
import { Badge } from '../components/Badge'
import type { DashboardOverview, DemoBootstrapResult } from '../types'

const PIE_COLORS = ['#7c5cff', '#16c7a2', '#ffb547', '#ff6b7a', '#47a5ff', '#b16cff', '#9aa7bd']

function pretty(value: string) {
  return value
    .replace('CREATE_', '')
    .replaceAll('_', ' ')
    .toLowerCase()
    .replace(/\b\w/g, (letter) => letter.toUpperCase())
}

export default function DashboardPage() {
  const [overview, setOverview] = useState<DashboardOverview | null>(null)
  const [loading, setLoading] = useState(true)
  const [bootstrapping, setBootstrapping] = useState(false)
  const [message, setMessage] = useState<DemoBootstrapResult | null>(null)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const load = async () => {
    try {
      setLoading(true)
      setOverview(await api.overview())
      setError('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load dashboard')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [])

  const intentData = useMemo(
    () => Object.entries(overview?.intent_distribution || {}).map(([name, value]) => ({ name: pretty(name), value })),
    [overview],
  )
  const actionData = useMemo(
    () => Object.entries(overview?.action_type_distribution || {}).map(([name, value]) => ({ name: pretty(name), value })),
    [overview],
  )

  const bootstrap = async () => {
    setBootstrapping(true)
    try {
      const result = await api.bootstrapDemo()
      setMessage(result)
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Demo bootstrap failed')
    } finally {
      setBootstrapping(false)
    }
  }

  if (loading && !overview) return <div className="page-loader"><RefreshCw className="spin" /> Loading operations workspace…</div>

  const m = overview?.metrics

  return (
    <div className="page-stack">
      <section className="hero-panel">
        <div className="hero-copy">
          <Badge tone="purple"><Sparkles size={13} /> Intelligent operations</Badge>
          <h1>Turn every important email into a controlled business action.</h1>
          <p>
            MailPilot AI classifies incoming work, prepares the next step, and keeps a human reviewer in control before anything is executed.
          </p>
          <div className="hero-actions">
            <button className="button button-primary" onClick={bootstrap} disabled={bootstrapping}>
              {bootstrapping ? <RefreshCw size={17} className="spin" /> : <WandSparkles size={17} />}
              {bootstrapping ? 'Preparing workspace…' : 'Load complete demo workflow'}
            </button>
            <button className="button button-secondary" onClick={() => navigate('/approvals')}>
              Review pending actions <ArrowRight size={17} />
            </button>
          </div>
          {message && (
            <div className="inline-success">
              <CheckCircle2 size={17} /> {message.emails_total} emails ready · {message.actions_created} new actions planned
            </div>
          )}
          {error && <div className="inline-error">{error}</div>}
        </div>
        <div className="hero-visual">
          <div className="ai-orbit">
            <div className="orbit-ring orbit-ring-one" />
            <div className="orbit-ring orbit-ring-two" />
            <div className="ai-core"><Bot size={38} /></div>
            <div className="orbit-node node-mail"><Inbox size={19} /></div>
            <div className="orbit-node node-approve"><CheckCircle2 size={19} /></div>
            <div className="orbit-node node-task"><ListTodo size={19} /></div>
          </div>
          <div className="hero-stat-card hero-stat-one"><span>Confidence</span><strong>{Math.round((overview?.average_confidence || 0) * 100)}%</strong></div>
          <div className="hero-stat-card hero-stat-two"><span>Approval control</span><strong>Always on</strong></div>
        </div>
      </section>

      <section className="section-heading-row">
        <div>
          <span className="eyebrow">Live workflow</span>
          <h2>Operations overview</h2>
        </div>
        <button className="icon-button refresh-button" onClick={() => void load()} title="Refresh dashboard"><RefreshCw size={17} /></button>
      </section>

      <section className="metric-grid">
        <article className="metric-card metric-violet"><div className="metric-icon"><Inbox size={21} /></div><div><span>Synced emails</span><strong>{m?.total_emails || 0}</strong><small>{overview?.analysis_rate || 0}% analyzed</small></div></article>
        <article className="metric-card metric-amber"><div className="metric-icon"><Clock3 size={21} /></div><div><span>Pending approval</span><strong>{m?.pending_actions || 0}</strong><small>Human review required</small></div></article>
        <article className="metric-card metric-green"><div className="metric-icon"><CheckCircle2 size={21} /></div><div><span>Executed actions</span><strong>{m?.executed_actions || 0}</strong><small>{overview?.completion_rate || 0}% workflow completion</small></div></article>
        <article className="metric-card metric-red"><div className="metric-icon"><ShieldAlert size={21} /></div><div><span>High-priority emails</span><strong>{overview?.high_priority_emails || 0}</strong><small>{m?.escalated_emails || 0} escalations</small></div></article>
        <article className="metric-card metric-blue"><div className="metric-icon"><ListTodo size={21} /></div><div><span>Open tasks</span><strong>{overview?.open_tasks || 0}</strong><small>Internal follow-up queue</small></div></article>
        <article className="metric-card metric-slate"><div className="metric-icon"><Gauge size={21} /></div><div><span>Automation rate</span><strong>{overview?.automation_rate || 0}%</strong><small>Completed through safe execution</small></div></article>
      </section>

      <section className="dashboard-grid">
        <article className="panel chart-panel chart-wide">
          <div className="panel-heading"><div><span className="eyebrow">Decision intelligence</span><h3>Recommended action mix</h3></div><Badge tone="info">Structured AI output</Badge></div>
          {actionData.length ? (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={actionData} margin={{ top: 14, right: 8, left: -15, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1c2a3d" vertical={false} />
                <XAxis dataKey="name" tick={{ fill: '#8290a7', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis allowDecimals={false} tick={{ fill: '#8290a7', fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip cursor={{ fill: 'rgba(124,92,255,.08)' }} contentStyle={{ background: '#101b2b', border: '1px solid #26364d', borderRadius: 12 }} />
                <Bar dataKey="value" radius={[8, 8, 2, 2]} fill="#7c5cff" />
              </BarChart>
            </ResponsiveContainer>
          ) : <EmptyChart />}
        </article>

        <article className="panel chart-panel">
          <div className="panel-heading"><div><span className="eyebrow">Inbox intelligence</span><h3>Intent distribution</h3></div></div>
          {intentData.length ? (
            <div className="pie-layout">
              <ResponsiveContainer width="60%" height={260}>
                <PieChart><Pie data={intentData} dataKey="value" nameKey="name" innerRadius={58} outerRadius={91} paddingAngle={3}>{intentData.map((_, index) => <Cell key={index} fill={PIE_COLORS[index % PIE_COLORS.length]} />)}</Pie><Tooltip contentStyle={{ background: '#101b2b', border: '1px solid #26364d', borderRadius: 12 }} /></PieChart>
              </ResponsiveContainer>
              <div className="chart-legend">{intentData.slice(0, 6).map((item, index) => <div key={item.name}><span style={{ background: PIE_COLORS[index % PIE_COLORS.length] }} /><label>{item.name}</label><strong>{item.value}</strong></div>)}</div>
            </div>
          ) : <EmptyChart />}
        </article>

        <article className="panel activity-panel">
          <div className="panel-heading"><div><span className="eyebrow">Traceability</span><h3>Recent activity</h3></div><button className="text-button" onClick={() => navigate('/audit')}>Full audit <ArrowRight size={14} /></button></div>
          <div className="activity-list">
            {(overview?.recent_activity || []).slice(0, 7).map((item) => (
              <div className="activity-item" key={item.id}>
                <div className="activity-dot"><Activity size={14} /></div>
                <div><strong>{pretty(item.event_type)}</strong><span>{item.message}</span></div>
                <time>{new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</time>
              </div>
            ))}
            {!overview?.recent_activity.length && <div className="empty-state compact"><Activity size={23} /><span>Run the demo workflow to populate the audit trail.</span></div>}
          </div>
        </article>
      </section>

      <section className="workflow-strip">
        {[
          ['01', 'Sync', 'Bring Gmail or demo messages into a traceable inbox.'],
          ['02', 'Analyze', 'Extract intent, urgency, confidence, dates, and reply needs.'],
          ['03', 'Plan', 'Convert structured analysis into safe proposed actions.'],
          ['04', 'Approve', 'Let a human edit, approve, reject, or escalate.'],
          ['05', 'Execute', 'Create drafts, events, tasks, and auditable outcomes.'],
        ].map(([number, title, text]) => <div className="workflow-step" key={number}><span>{number}</span><strong>{title}</strong><p>{text}</p></div>)}
      </section>
    </div>
  )
}

function EmptyChart() {
  return <div className="empty-state chart-empty"><Bot size={30} /><strong>No workflow data yet</strong><span>Load the demo workflow to see analytics.</span></div>
}
