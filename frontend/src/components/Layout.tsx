import { useEffect, useId, useState } from 'react'
import { NavLink, Outlet } from 'react-router'
import { useAuth } from '../auth/AuthContext'
import { hasPermission } from '../auth/permissions'
import type { Me } from '../api/auth'
import Logo from './Logo'
import { postAuthPath } from '../auth/paths'
import { formatRoleLabel } from '../messages/apiErrors'
import '../styles/garagemind.css'
import '../styles/app.css'

interface NavItem {
  to: string
  label: string
  end?: boolean
}

interface NavSections {
  app: NavItem[]
  admin: NavItem[]
}

function buildNavSections(user: Me): NavSections {
  const app: NavItem[] = []
  if (hasPermission(user, 'bands.read')) app.push({ to: '/bands', label: 'Bands', end: true })
  if (hasPermission(user, 'bands.write')) app.push({ to: '/bands/new', label: 'Add band' })

  const admin: NavItem[] = []
  if (hasPermission(user, 'users.manage')) admin.push({ to: '/admin/users', label: 'Users' })
  if (hasPermission(user, 'settings.manage')) admin.push({ to: '/admin/settings', label: 'Settings' })
  if (admin.length > 0) admin.push({ to: '/status', label: 'System status' })
  else app.push({ to: '/status', label: 'System status' })

  return { app, admin }
}

function NavItemLink({
  item,
  onNavigate,
}: {
  item: NavItem
  onNavigate: () => void
}) {
  return (
    <li>
      <NavLink
        to={item.to}
        end={item.end}
        className={({ isActive }) => `app__nav-link${isActive ? ' is-active' : ''}`}
        onClick={onNavigate}
      >
        {item.label}
      </NavLink>
    </li>
  )
}

export default function Layout() {
  const { user, logout } = useAuth()
  const [menuOpen, setMenuOpen] = useState(false)
  const drawerId = useId()

  useEffect(() => {
    if (!menuOpen) return
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setMenuOpen(false)
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [menuOpen])

  // Przy wymuszonej zmianie hasła użytkownik ma dostęp tylko do tego formularza.
  const showMenu = user !== null && !user.must_change_password
  const closeMenu = () => setMenuOpen(false)
  const navSections = user ? buildNavSections(user) : { app: [], admin: [] }

  return (
    <div className="garagemind-landing app">
      <div className="garagemind-section-bg app__bg" aria-hidden>
        <img src="/garagemind/Sekcja2.png" alt="" />
      </div>

      <div className="garagemind-container app__frame">
        <header className="app__topbar">
          <div className="app__brand-row">
            <div className="app__brand-cluster">
              {showMenu && (
                <button
                  type="button"
                  className="app__menu-btn"
                  aria-label={menuOpen ? 'Close menu' : 'Open menu'}
                  aria-expanded={menuOpen}
                  aria-controls={drawerId}
                  onClick={() => setMenuOpen((open) => !open)}
                >
                  <span className="app__menu-line" />
                  <span className="app__menu-line" />
                  <span className="app__menu-line" />
                </button>
              )}
              <Logo
                variant="mark"
                to={user && showMenu ? postAuthPath(user) : '/change-password'}
              />
            </div>
            <p className="app__session">
              <span className="app__session-name">{user?.login}</span>
              <span className="app__session-role">{user ? formatRoleLabel(user.role) : null}</span>
            </p>
          </div>
        </header>

        {showMenu && (
          <>
            <button
              type="button"
              className={`app__backdrop${menuOpen ? ' is-visible' : ''}`}
              aria-label="Close menu"
              aria-hidden={!menuOpen}
              tabIndex={-1}
              onClick={closeMenu}
            />
            <aside id={drawerId} className={`app__drawer${menuOpen ? ' is-open' : ''}`} inert={!menuOpen}>
              <nav aria-label="Application">
                <ul className="app__nav">
                  {navSections.app.map((item) => (
                    <NavItemLink key={item.to} item={item} onNavigate={closeMenu} />
                  ))}
                  {navSections.admin.length > 0 && (
                    <>
                      <li className="app__nav-divider" aria-hidden />
                      {navSections.admin.map((item) => (
                        <NavItemLink key={item.to} item={item} onNavigate={closeMenu} />
                      ))}
                    </>
                  )}
                  <li className="app__nav-divider" aria-hidden />
                  <NavItemLink
                    item={{ to: '/', label: 'View site' }}
                    onNavigate={closeMenu}
                  />
                  <NavItemLink
                    item={{ to: '/change-password', label: 'Password' }}
                    onNavigate={closeMenu}
                  />
                  <li>
                    <button
                      type="button"
                      className="app__nav-link"
                      onClick={() => {
                        closeMenu()
                        void logout()
                      }}
                    >
                      Sign out
                    </button>
                  </li>
                </ul>
              </nav>
            </aside>
          </>
        )}

        <main className="app__content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
