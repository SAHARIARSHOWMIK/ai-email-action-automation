import { CheckCircle2, Circle, ListTodo, RefreshCw, RotateCcw } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { api } from '../api'
import { Badge } from '../components/Badge'
import type { TaskItem } from '../types'

export default function TasksPage() {
  const [tasks, setTasks] = useState<TaskItem[]>([])
  const [filter, setFilter] = useState<'all' | 'open' | 'done'>('all')
  const [busy, setBusy] = useState<number | null>(null)
  const [error, setError] = useState('')

  const load = async () => {
    try {
      setTasks(await api.listTasks())
      setError('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load tasks')
    }
  }

  useEffect(() => { void load() }, [])

  const visible = useMemo(() => tasks.filter((task) => filter === 'all' || task.status === filter), [tasks, filter])
  const openCount = tasks.filter((task) => task.status === 'open').length
  const doneCount = tasks.filter((task) => task.status === 'done').length

  const update = async (task: TaskItem) => {
    setBusy(task.id)
    try {
      if (task.status === 'open') await api.completeTask(task.id)
      else await api.reopenTask(task.id)
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not update task')
    } finally {
      setBusy(null)
    }
  }

  return (
    <div className="page-stack">
      <section className="page-header">
        <div><span className="eyebrow">Internal follow-up</span><h1>Task Workspace</h1><p>Track internal actions created from invoices, deadlines, and operational emails.</p></div>
        <button className="button button-secondary" onClick={() => void load()}><RefreshCw size={16} /> Refresh</button>
      </section>

      <section className="task-summary-grid">
        <article className="panel task-summary-card"><div className="task-summary-icon open"><Circle size={22} /></div><div><span>Open tasks</span><strong>{openCount}</strong><small>Require follow-up</small></div></article>
        <article className="panel task-summary-card"><div className="task-summary-icon done"><CheckCircle2 size={22} /></div><div><span>Completed</span><strong>{doneCount}</strong><small>Resolved internal work</small></div></article>
        <article className="panel task-summary-card"><div className="task-summary-icon total"><ListTodo size={22} /></div><div><span>Total tasks</span><strong>{tasks.length}</strong><small>Created by approved actions</small></div></article>
      </section>

      {error && <div className="inline-error">{error}</div>}

      <section className="panel task-panel">
        <div className="panel-heading task-panel-heading">
          <div><span className="eyebrow">Action queue</span><h3>Operational tasks</h3></div>
          <div className="segmented-control">
            {(['all', 'open', 'done'] as const).map((value) => <button key={value} className={filter === value ? 'active' : ''} onClick={() => setFilter(value)}>{value}</button>)}
          </div>
        </div>
        <div className="task-list">
          {visible.map((task) => (
            <article className={`task-row ${task.status === 'done' ? 'task-row-done' : ''}`} key={task.id}>
              <button className="task-check" onClick={() => void update(task)} disabled={busy === task.id}>{task.status === 'done' ? <CheckCircle2 size={22} /> : <Circle size={22} />}</button>
              <div className="task-copy"><div><strong>{task.title}</strong><Badge tone={task.status === 'done' ? 'success' : 'warning'}>{task.status}</Badge></div><p>{task.description || 'No additional description was provided.'}</p><span>Created {new Date(task.created_at).toLocaleString()} · Action #{task.action_id}</span></div>
              <div className="task-due"><span>Due date</span><strong>{task.due_date || 'Not specified'}</strong></div>
              <button className="button button-ghost" onClick={() => void update(task)} disabled={busy === task.id}>{task.status === 'done' ? <><RotateCcw size={15} /> Reopen</> : <><CheckCircle2 size={15} /> Complete</>}</button>
            </article>
          ))}
          {!visible.length && <div className="empty-state large-empty"><ListTodo size={36} /><strong>No tasks found</strong><span>Execute a CREATE_TASK action to create internal follow-up work.</span></div>}
        </div>
      </section>
    </div>
  )
}
