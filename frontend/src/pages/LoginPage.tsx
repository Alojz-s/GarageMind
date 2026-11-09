import { useState, type FormEvent } from 'react'
import { Link, Navigate } from 'react-router'
import { ApiError } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import '../styles/garagemind.css'

const INVALID_CREDENTIALS = 'Invalid username or password.'

export default function LoginPage() {
  const { user, loading, notice, login } = useAuth()
  const [loginName, setLoginName] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  if (loading) return null
  if (user) return <Navigate to="/articles" replace />

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await login(loginName, password)
    } catch (err) {
      // Backend zwraca polski komunikat; dla 401 pokazujemy ujednolicony angielski.
      if (err instanceof ApiError && err.status === 401) setError(INVALID_CREDENTIALS)
      else setError(err instanceof Error ? err.message : String(err))
      setPassword('')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="garagemind-landing garagemind-login">
      <div className="garagemind-section-bg garagemind-login__bg" aria-hidden>
        <img src="/garagemind/Sekcja2.png" alt="" />
      </div>

      <div className="garagemind-container garagemind-login__shell">
        <header className="garagemind-header garagemind-login__header">
          <Link to="/" className="garagemind-logo">
            GarageMind
          </Link>
        </header>

        <main className="garagemind-login__main">
          <div className="garagemind-login__panel">
            <h1 className="garagemind-login__title">Account</h1>
            <p className="garagemind-login__subtitle">Sign in to continue.</p>

            <form className="garagemind-login__form" onSubmit={handleSubmit}>
              {notice && <p className="garagemind-login__notice">{notice}</p>}
              <label className="garagemind-login__field">
                <span className="garagemind-login__label">Username</span>
                <input
                  name="login"
                  autoComplete="username"
                  value={loginName}
                  onChange={(e) => setLoginName(e.target.value)}
                  required
                />
              </label>
              <label className="garagemind-login__field">
                <span className="garagemind-login__label">Password</span>
                <input
                  name="password"
                  type="password"
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </label>
              {error && (
                <p className="garagemind-login__error" role="alert">
                  {error}
                </p>
              )}
              <button
                type="submit"
                className="gm-btn gm-btn--block garagemind-login__submit"
                disabled={submitting}
              >
                {submitting ? 'Signing in…' : 'Sign in'}
              </button>
            </form>
          </div>
        </main>
      </div>
    </div>
  )
}
