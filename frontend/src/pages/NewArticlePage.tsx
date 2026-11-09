import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router'
import { createArticle } from '../api/articles'
import Alert from '../components/Alert'
import PageHeader from '../components/PageHeader'

export default function NewArticlePage() {
  const navigate = useNavigate()
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await createArticle(title, content)
      navigate('/articles')
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <PageHeader title="Add band" subtitle="Publish a new band to the Bands page." />
      <form className="app-card app-card--narrow app-form" onSubmit={handleSubmit}>
        <label className="app-field">
          Name
          <input
            className="app-input"
            name="title"
            maxLength={200}
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
          />
        </label>
        <label className="app-field">
          Description
          <textarea
            className="app-input"
            name="content"
            rows={6}
            value={content}
            onChange={(e) => setContent(e.target.value)}
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
