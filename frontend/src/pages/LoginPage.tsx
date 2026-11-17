import { useEffect, useState, type FormEvent } from 'react'
import { Navigate } from 'react-router'
import { useAuth } from '../auth/AuthContext'
import AppLoading from '../components/AppLoading'
import Logo from '../components/Logo'
import TurnstileWidget from '../components/TurnstileWidget'
import { useCaptchaConfig } from '../auth/useCaptchaConfig'
import { postAuthPath } from '../auth/paths'
import { ApiError } from '../api/client'
import { formatApiError } from '../messages/apiErrors'
import '../styles/garagemind.css'

function formatRemaining(seconds: number): string {
  const minutes = Math.floor(seconds / 60)
  const rest = String(seconds % 60).padStart(2, '0')
  return `${minutes}:${rest}`
}

export default function LoginPage() {
  const { user, loading, notice, login } = useAuth()
  const [loginName, setLoginName] = useState('')
  const [password, setPassword] = useState('')
  const [website, setWebsite] = useState('')
  const captcha = useCaptchaConfig()
  const [captchaToken, setCaptchaToken] = useState<string | null>(null)
  const [captchaReset, setCaptchaReset] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [lockedUntil, setLockedUntil] = useState<number | null>(null)
  const [remaining, setRemaining] = useState(0)

  useEffect(() => {
    if (lockedUntil === null) return
    const tick = () => {
      const left = Math.ceil((lockedUntil - Date.now()) / 1000)
      if (left <= 0) {
        setLockedUntil(null)
        setRemaining(0)
      } else {
        setRemaining(left)
      }
    }
    tick()
    const timer = window.setInterval(tick, 1000)
    return () => window.clearInterval(timer)
  }, [lockedUntil])

  if (loading) return <AppLoading variant="landing" />
  if (user) return <Navigate to={postAuthPath(user)} replace />

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await login(loginName, password, website, captchaToken)
    } catch (err) {
      if (err instanceof ApiError && err.code === 'account_locked' && err.lockedSeconds) {
        setLockedUntil(Date.now() + err.lockedSeconds * 1000)
        setRemaining(err.lockedSeconds)
      }
      setError(formatApiError(err))
      setPassword('')
      setCaptchaReset((n) => n + 1)
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
          <Logo variant="full" to="/" />
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
              <div className="honeypot-field" aria-hidden="true">
                <label>
                  Website
                  <input
                    name="website"
                    type="text"
                    tabIndex={-1}
                    autoComplete="off"
                    value={website}
                    onChange={(e) => setWebsite(e.target.value)}
                  />
                </label>
              </div>
              {captcha?.enabled && captcha.site_key && (
                <TurnstileWidget
                  siteKey={captcha.site_key}
                  onToken={setCaptchaToken}
                  resetKey={captchaReset}
                />
              )}
              {lockedUntil !== null && (
                <p className="garagemind-login__error" role="alert">
                  Account temporarily locked. Try again in {formatRemaining(remaining)}.
                </p>
              )}
              {error && lockedUntil === null && (
                <p className="garagemind-login__error" role="alert">
                  {error}
                </p>
              )}
              <button
                type="submit"
                className="gm-btn gm-btn--block garagemind-login__submit"
                disabled={
                  submitting || lockedUntil !== null || (captcha?.enabled === true && !captchaToken)
                }
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
