import { useEffect, useState, type FormEvent } from 'react'
import { fetchSecuritySettings, updateSecuritySettings, type SecuritySettings } from '../api/admin'
import { ApiError, type Violation } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import Alert from '../components/Alert'
import PageHeader from '../components/PageHeader'

type NumberField = 'min_password_length' | 'password_validity_days' | 'idle_timeout_minutes'

interface FormState {
  min_password_length: string
  date_rule_enabled: boolean
  password_validity_days: string
  idle_timeout_minutes: string
}

const NUMBER_FIELDS: { name: NumberField; label: string; min: number; max?: number }[] = [
  { name: 'min_password_length', label: 'Minimum password length', min: 15, max: 64 },
  { name: 'password_validity_days', label: 'Password validity (days, 0 = off)', min: 0 },
  { name: 'idle_timeout_minutes', label: 'Session idle timeout (min)', min: 1, max: 120 },
]

function toForm(settings: SecuritySettings): FormState {
  return {
    min_password_length: String(settings.min_password_length),
    date_rule_enabled: settings.date_rule_enabled,
    password_validity_days: String(settings.password_validity_days),
    idle_timeout_minutes: String(settings.idle_timeout_minutes),
  }
}

export default function AdminSettingsPage() {
  const { refreshUser } = useAuth()
  const [form, setForm] = useState<FormState | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [violations, setViolations] = useState<Violation[]>([])
  const [saved, setSaved] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    fetchSecuritySettings()
      .then((settings) => setForm(toForm(settings)))
      .catch((err: unknown) => setError(err instanceof Error ? err.message : String(err)))
  }, [])

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!form) return
    setError(null)
    setViolations([])
    setSaved(false)
    setSubmitting(true)
    try {
      const settings = await updateSecuritySettings({
        min_password_length: Number(form.min_password_length),
        date_rule_enabled: form.date_rule_enabled,
        password_validity_days: Number(form.password_validity_days),
        idle_timeout_minutes: Number(form.idle_timeout_minutes),
      })
      setForm(toForm(settings))
      setSaved(true)
      // Licznik bezczynności bierze limit z /auth/me – odświeżamy go dla bieżącej sesji.
      await refreshUser()
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
      setViolations(err instanceof ApiError ? err.violations : [])
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <PageHeader title="Settings" subtitle="Password policy and session security." />
      <form className="app-card app-card--narrow app-form" onSubmit={handleSubmit}>
        {form && (
          <>
            {NUMBER_FIELDS.map((field) => (
              <label key={field.name} className="app-field">
                {field.label}
                <input
                  className="app-input"
                  name={field.name}
                  type="number"
                  min={field.min}
                  max={field.max}
                  value={form[field.name]}
                  onChange={(e) => setForm({ ...form, [field.name]: e.target.value })}
                  required
                />
              </label>
            ))}
            <label className="app-check">
              <input
                name="date_rule_enabled"
                type="checkbox"
                checked={form.date_rule_enabled}
                onChange={(e) => setForm({ ...form, date_rule_enabled: e.target.checked })}
              />
              Reject dates and years 1950–2030 in passwords
            </label>
          </>
        )}
        {error && <Alert kind="error">{error}</Alert>}
        {violations.length > 0 && (
          <ul className="app-hints app-hints--error">
            {violations.map((violation, index) => (
              <li key={`${violation.code}-${index}`}>{violation.message}</li>
            ))}
          </ul>
        )}
        {saved && <Alert>Settings saved.</Alert>}
        <button type="submit" className="gm-btn" disabled={!form || submitting}>
          Save
        </button>
      </form>
    </>
  )
}
