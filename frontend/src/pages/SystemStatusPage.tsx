import { useEffect, useState } from 'react'
import { fetchHealth, type HealthResponse } from '../api/health'
import Alert from '../components/Alert'
import PageHeader from '../components/PageHeader'

type State =
  | { kind: 'loading' }
  | { kind: 'loaded'; health: HealthResponse }
  | { kind: 'unreachable'; message: string }

function StatusRow({ label, ok }: { label: string; ok: boolean | null }) {
  const modifier = ok === null ? 'pending' : ok ? 'ok' : 'error'
  const text = ok === null ? 'checking…' : ok ? 'ok' : 'error'
  return (
    <li className="app-status-row">
      <span>{label}</span>
      <span className={`app-badge app-badge--${modifier}`}>{text}</span>
    </li>
  )
}

export default function SystemStatusPage() {
  const [state, setState] = useState<State>({ kind: 'loading' })
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    fetchHealth(controller.signal)
      .then((health) => setState({ kind: 'loaded', health }))
      .catch((error: unknown) => {
        if (controller.signal.aborted) return
        setState({
          kind: 'unreachable',
          message: error instanceof Error ? error.message : String(error),
        })
      })
    return () => controller.abort()
  }, [attempt])

  const refresh = () => {
    setState({ kind: 'loading' })
    setAttempt((n) => n + 1)
  }

  let backendOk: boolean | null = null
  let databaseOk: boolean | null = null
  if (state.kind === 'loaded') {
    backendOk = state.health.status === 'ok'
    databaseOk = state.health.database === 'ok'
  } else if (state.kind === 'unreachable') {
    backendOk = false
    databaseOk = false
  }

  return (
    <>
      <PageHeader title="System status" />
      <div className="app-stack app-stack--narrow">
      <section className="app-card">
        <ul className="app-status-list">
          <StatusRow label="Backend" ok={backendOk} />
          <StatusRow label="Database" ok={databaseOk} />
        </ul>
        {state.kind === 'unreachable' && (
          <div className="app-stack">
            <Alert kind="error">Cannot reach the backend ({state.message}).</Alert>
          </div>
        )}
        <button
          type="button"
          className="gm-btn gm-btn--secondary gm-btn--sm"
          onClick={refresh}
          disabled={state.kind === 'loading'}
        >
          Refresh
        </button>
      </section>
      </div>
    </>
  )
}
