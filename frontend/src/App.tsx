import { lazy, Suspense, useEffect, useState } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { RefreshCw } from 'lucide-react'
import { api } from './api'
import { Layout } from './components/Layout'
import type { Health } from './types'

const DashboardPage = lazy(() => import('./pages/DashboardPage'))
const InboxPage = lazy(() => import('./pages/InboxPage'))
const ApprovalPage = lazy(() => import('./pages/ApprovalPage'))
const TasksPage = lazy(() => import('./pages/TasksPage'))
const HistoryPage = lazy(() => import('./pages/HistoryPage'))
const AuditPage = lazy(() => import('./pages/AuditPage'))
const IntegrationsPage = lazy(() => import('./pages/IntegrationsPage'))

function RouteLoader() {
  return <div className="page-loader"><RefreshCw className="spin" /> Loading workspace…</div>
}

export default function App() {
  const [health, setHealth] = useState<Health | null>(null)

  useEffect(() => {
    api.health().then(setHealth).catch(() => setHealth(null))
    const timer = window.setInterval(() => api.health().then(setHealth).catch(() => setHealth(null)), 30_000)
    return () => window.clearInterval(timer)
  }, [])

  return (
    <Layout health={health}>
      <Suspense fallback={<RouteLoader />}>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/inbox" element={<InboxPage />} />
          <Route path="/approvals" element={<ApprovalPage />} />
          <Route path="/tasks" element={<TasksPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/audit" element={<AuditPage />} />
          <Route path="/integrations" element={<IntegrationsPage health={health} />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </Layout>
  )
}
