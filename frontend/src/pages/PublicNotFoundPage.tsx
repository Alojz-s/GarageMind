import { Link } from 'react-router'
import { useAuth } from '../auth/AuthContext'
import { accountLinkPath } from '../auth/paths'
import AppLoading from '../components/AppLoading'
import Logo from '../components/Logo'
import '../styles/garagemind.css'

export default function PublicNotFoundPage() {
  const { user, loading } = useAuth()

  if (loading) return <AppLoading variant="landing" />

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
            <h1 className="garagemind-login__title">Page not found</h1>
            <p className="garagemind-login__subtitle">That URL does not exist on GarageMind.</p>
            <div className="garagemind-public-404__actions">
              <Link to="/" className="gm-btn gm-btn--secondary gm-btn--sm">
                Back to home
              </Link>
              <Link to={accountLinkPath(user)} className="gm-btn gm-btn--sm">
                {user ? 'Open app' : 'Sign in'}
              </Link>
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}
