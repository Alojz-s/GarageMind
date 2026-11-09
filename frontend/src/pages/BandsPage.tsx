import { useEffect, useState, type FormEvent } from 'react'
import { fetchBands, updateBand, type Band } from '../api/bands'
import Alert from '../components/Alert'
import PageHeader from '../components/PageHeader'
import { useAuth } from '../auth/AuthContext'
import { hasPermission } from '../auth/permissions'
import { formatApiError } from '../messages/apiErrors'

export default function BandsPage() {
  const { user } = useAuth()
  const canWrite = hasPermission(user, 'bands.write')
  const [bands, setBands] = useState<Band[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [editing, setEditing] = useState<Band | null>(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    fetchBands()
      .then(setBands)
      .catch((err: unknown) => {
        setBands([])
        setError(formatApiError(err))
      })
  }, [])

  const handleSave = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!editing) return
    setError(null)
    setSaving(true)
    try {
      const saved = await updateBand(editing.id, editing.name, editing.bio)
      setBands((prev) => prev?.map((b) => (b.id === saved.id ? saved : b)) ?? null)
      setEditing(null)
    } catch (err) {
      setError(formatApiError(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <>
      <PageHeader title="Bands" subtitle="Featured bands from the GarageMind scene." />
      <div className="app-stack">
        {error && <Alert kind="error">{error}</Alert>}
        {bands?.length === 0 && !error && (
          <p className="app-card app-empty app-text">No bands yet.</p>
        )}
        <ul className="app-bands">
          {bands?.map((band) => (
            <li key={band.id} className="app-card app-band">
              {editing?.id === band.id ? (
                <form className="app-form app-form--fill" onSubmit={handleSave}>
                  <label className="app-field">
                    Band name
                    <input
                      className="app-input"
                      name="name"
                      maxLength={200}
                      value={editing.name}
                      onChange={(e) => setEditing({ ...editing, name: e.target.value })}
                      required
                    />
                  </label>
                  <label className="app-field">
                    Bio
                    <textarea
                      className="app-input"
                      name="bio"
                      rows={6}
                      value={editing.bio}
                      onChange={(e) => setEditing({ ...editing, bio: e.target.value })}
                      required
                    />
                  </label>
                  <div className="app-actions">
                    <button type="submit" className="gm-btn gm-btn--sm" disabled={saving}>
                      Save
                    </button>
                    <button
                      type="button"
                      className="gm-btn gm-btn--sm gm-btn--secondary"
                      disabled={saving}
                      onClick={() => setEditing(null)}
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              ) : (
                <>
                  <h2 className="app-card__title">{band.name}</h2>
                  <p className="app-text app-text--pre">{band.bio}</p>
                  {canWrite && (
                    <button
                      type="button"
                      className="gm-btn gm-btn--sm gm-btn--secondary"
                      onClick={() => setEditing(band)}
                    >
                      Edit
                    </button>
                  )}
                </>
              )}
            </li>
          ))}
        </ul>
      </div>
    </>
  )
}
