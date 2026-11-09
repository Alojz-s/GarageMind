import { useEffect, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router'
import { changePassword, fetchPasswordPolicy } from '../api/auth'
import { ApiError, type Violation } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import Alert from '../components/Alert'
import PageHeader from '../components/PageHeader'

export default function ChangePasswordPage() {
  const { user, refreshUser } = useAuth()
  const navigate = useNavigate()
  const [requirements, setRequirements] = useState<string[]>([])
  const [oldPassword, setOldPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [newPasswordConfirm, setNewPasswordConfirm] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [violations, setViolations] = useState<Violation[]>([])
  const [submitting, setSubmitting] = useState(false)
  const forced = user?.must_change_password ?? false

  useEffect(() => {
    fetchPasswordPolicy()
      .then((policy) => setRequirements(policy.requirements))
      .catch(() => setRequirements([]))
  }, [])

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError(null)
    setViolations([])
    setSubmitting(true)
    try {
      await changePassword(oldPassword, newPassword, newPasswordConfirm)
      await refreshUser()
      navigate('/articles', { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
      setViolations(err instanceof ApiError ? err.violations : [])
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <PageHeader
        title="Change password"
        subtitle={forced ? 'You must set a new password before continuing.' : undefined}
      />
      <form className="app-card app-card--narrow app-form" onSubmit={handleSubmit}>
        {requirements.length > 0 && (
          <ul className="app-hints">
            {requirements.map((requirement) => (
              <li key={requirement}>{requirement}</li>
            ))}
          </ul>
        )}
        <label className="app-field">
          Current password
          <input
            className="app-input"
            name="old_password"
            type="password"
            autoComplete="current-password"
            value={oldPassword}
            onChange={(e) => setOldPassword(e.target.value)}
            required
          />
        </label>
        <label className="app-field">
          New password
          <input
            className="app-input"
            name="new_password"
            type="password"
            autoComplete="new-password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            required
          />
        </label>
        <label className="app-field">
          Confirm new password
          <input
            className="app-input"
            name="new_password_confirm"
            type="password"
            autoComplete="new-password"
            value={newPasswordConfirm}
            onChange={(e) => setNewPasswordConfirm(e.target.value)}
            required
          />
        </label>
        {violations.length > 0 && (
          <ul className="app-hints app-hints--error">
            {violations.map((violation) => (
              <li key={violation.code}>{violation.message}</li>
            ))}
          </ul>
        )}
        {error && <Alert kind="error">{error}</Alert>}
        <button type="submit" className="gm-btn" disabled={submitting}>
          Update password
        </button>
      </form>
    </>
  )
}
