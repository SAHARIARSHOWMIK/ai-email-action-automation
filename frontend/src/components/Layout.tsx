import {
  Activity,
  CheckCircle2,
  ClipboardCheck,
  History,
  Inbox,
  LayoutDashboard,
  ListTodo,
  MailCheck,
  Menu,
  Settings2,
  ShieldCheck,
  Sparkles,
  X,
} from 'lucide-react'
import { useState, type ReactNode } from 'react'
import { NavLink } from 'react-router-dom'
import type { Health } from '../types'

const nav = [
  { to: '/', label: 'Overview', icon: LayoutDashboard },
  { to: '/inbox', label: 'Smart Inbox', icon: Inbox },
  { to: '/approvals', label: 'Approval Queue', icon: ClipboardCheck },
  { to: '/tasks', label: 'Tasks', icon: ListTodo },
  { to: '/history', label: 'Execution History', icon: History },
  { to: '/audit', label: 'Audit Trail', icon: Activity },
  { to: '/integrations', label: 'Integrations', icon: Settings2 },
]

interface LayoutProps {
  children: ReactNode
  health: Health | null
}

export function Layout({ children, health }: LayoutProps) {
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <div className="app-shell">
      <aside className={`sidebar ${mobileOpen ? 'sidebar-open' : ''}`}>
        <div className="brand-row">
          <div className="brand-mark"><MailCheck size={23} /></div>
          <div>
            <div className="brand-title">MailPilot AI</div>
            <div className="brand-subtitle">Operations Console</div>
          </div>
          <button className="icon-button mobile-only" onClick={() => setMobileOpen(false)} aria-label="Close navigation">
            <X size={18} />
          </button>
        </div>

        <div className="workspace-card">
          <div className="workspace-icon"><Sparkles size={17} /></div>
          <div>
            <span>Workspace</span>
            <strong>Automation Lab</strong>
          </div>
          <CheckCircle2 size={16} className="workspace-check" />
        </div>

        <nav className="nav-list">
          <span className="nav-section-label">Workspace</span>
          {nav.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) => `nav-item ${isActive ? 'nav-item-active' : ''}`}
              onClick={() => setMobileOpen(false)}
            >
              <Icon size={18} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="safety-card">
            <ShieldCheck size={20} />
            <div>
              <strong>Human approval enforced</strong>
              <span>No action is sent automatically.</span>
            </div>
          </div>
          <div className="profile-row">
            <div className="avatar">SS</div>
            <div>
              <strong>Shahariar Showmik</strong>
              <span>Automation Engineer</span>
            </div>
          </div>
        </div>
      </aside>

      {mobileOpen && <button className="sidebar-backdrop" onClick={() => setMobileOpen(false)} aria-label="Close navigation" />}

      <main className="main-area">
        <header className="topbar">
          <button className="icon-button mobile-menu" onClick={() => setMobileOpen(true)} aria-label="Open navigation">
            <Menu size={20} />
          </button>
          <div className="breadcrumb-copy">
            <span>AI workflow automation</span>
            <strong>Human-in-the-loop email operations</strong>
          </div>
          <div className="topbar-actions">
            <div className={`system-pill ${health?.status === 'ok' ? 'system-pill-ok' : ''}`}>
              <span className="status-dot" />
              {health ? `${health.status.toUpperCase()} · ${health.demo_mode ? 'DEMO' : 'LIVE'}` : 'CONNECTING'}
            </div>
          </div>
        </header>
        <div className="content-area">{children}</div>
      </main>
    </div>
  )
}
