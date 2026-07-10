import { Bot, CalendarDays, CheckCircle2, Database, GitBranch, KeyRound, Mail, Server, ShieldCheck, Workflow } from 'lucide-react'
import { Badge } from '../components/Badge'
import type { Health } from '../types'

interface Props { health: Health | null }

export default function IntegrationsPage({ health }: Props) {
  const integrations = [
    { title: 'Gmail API', icon: Mail, status: health?.demo_mode ? 'Demo provider' : 'Configured', text: 'Reads unread messages and creates approved reply drafts without sending automatically.', tone: 'purple' as const },
    { title: 'Google Calendar', icon: CalendarDays, status: health?.demo_mode ? 'Demo provider' : 'Configured', text: 'Creates calendar events only after extracted dates are reviewed and approved.', tone: 'info' as const },
    { title: 'Anthropic Claude', icon: Bot, status: health?.demo_mode ? 'Mock analyzer' : 'Configured', text: 'Produces schema-validated intent, priority, confidence, deadline, and action recommendations.', tone: 'warning' as const },
    { title: 'SQL Database', icon: Database, status: health?.database_connected ? 'Connected' : 'Unavailable', text: 'SQLite for local work and PostgreSQL for the Docker deployment profile.', tone: health?.database_connected ? 'success' as const : 'danger' as const },
  ]

  return (
    <div className="page-stack">
      <section className="page-header"><div><span className="eyebrow">Provider configuration</span><h1>Integrations & Safety</h1><p>Inspect the service architecture, environment mode, and controls that keep external actions safe.</p></div></section>
      <section className="integration-hero panel"><div><Badge tone={health?.demo_mode ? 'purple' : 'success'}>{health?.demo_mode ? 'Controlled demo environment' : 'Live provider environment'}</Badge><h2>{health?.demo_mode ? 'Explore the complete workflow with zero external credentials.' : 'External providers are enabled for this environment.'}</h2><p>Demo mode preserves the real workflow contract while replacing Gmail, Calendar, and LLM calls with deterministic local providers.</p></div><div className="integration-orbit"><Workflow size={42} /><span>Schema validated</span></div></section>
      <section className="integration-grid">{integrations.map(({ title, icon: Icon, status, text, tone }) => <article className="panel integration-card" key={title}><div className="integration-card-top"><div className="integration-icon"><Icon size={23} /></div><Badge tone={tone}>{status}</Badge></div><h3>{title}</h3><p>{text}</p><div className="integration-foot"><CheckCircle2 size={15} /> Health checked by the platform</div></article>)}</section>
      <section className="safety-grid">
        <article className="panel safety-detail"><div className="safety-detail-icon"><ShieldCheck size={24} /></div><div><span className="eyebrow">Control</span><h3>Human approval boundary</h3><p>AI findings are suggestions. Every external action remains blocked until a reviewer approves and explicitly executes it.</p></div></article>
        <article className="panel safety-detail"><div className="safety-detail-icon"><KeyRound size={24} /></div><div><span className="eyebrow">Secrets</span><h3>Environment-based credentials</h3><p>API credentials are read from a local <code>.env</code> file that is excluded from Git and never displayed in the dashboard.</p></div></article>
        <article className="panel safety-detail"><div className="safety-detail-icon"><Server size={24} /></div><div><span className="eyebrow">Deployment</span><h3>Container-ready services</h3><p>Docker Compose runs the React frontend, FastAPI backend, and PostgreSQL database as separate health-aware services.</p></div></article>
        <article className="panel safety-detail"><div className="safety-detail-icon"><GitBranch size={24} /></div><div><span className="eyebrow">Quality</span><h3>CI verification</h3><p>GitHub Actions runs backend tests, frontend type checks, and the production frontend build for every push and pull request.</p></div></article>
      </section>
    </div>
  )
}
