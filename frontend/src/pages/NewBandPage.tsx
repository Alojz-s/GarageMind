import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router'
import { createBand } from '../api/bands'
import Alert from '../components/Alert'
import PageHeader from '../components/PageHeader'
import { formatApiError } from '../messages/apiErrors'

export default function NewBandPage() {
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [bio, setBio] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await createBand(name, bio)
      navigate('/bands')
    } catch (err) {
      setError(formatApiError(err))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <PageHeader title="Add band" subtitle="Publish a new band to the Bands page." />
      <form className="app-card app-card--narrow app-form" onSubmit={handleSubmit}>
        <label className="app-field">
          Band name
          <input
            className="app-input"
            name="name"
            maxLength={200}
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
        </label>
        <label className="app-field">
          Bio
          <textarea
            className="app-input"
            name="bio"
            rows={6}
            value={bio}
            onChange={(e) => setBio(e.target.value)}
            required
          />
        </label>
        {error && <Alert kind="error">{error}</Alert>}
        <button type="submit" className="gm-btn" disabled={submitting}>
          Publish
        </button>
      </form>
    </>
  )
}
