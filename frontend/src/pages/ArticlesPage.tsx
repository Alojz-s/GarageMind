import { useEffect, useState, type FormEvent } from 'react'
import { fetchArticles, updateArticle, type Article } from '../api/articles'
import Alert from '../components/Alert'
import PageHeader from '../components/PageHeader'
import { useAuth } from '../auth/AuthContext'
import { hasPermission } from '../auth/permissions'

export default function ArticlesPage() {
  const { user } = useAuth()
  const canWrite = hasPermission(user, 'articles.write')
  const [articles, setArticles] = useState<Article[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [editing, setEditing] = useState<Article | null>(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    fetchArticles()
      .then(setArticles)
      .catch((err: unknown) => {
        setArticles([])
        setError(err instanceof Error ? err.message : String(err))
      })
  }, [])

  const handleSave = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!editing) return
    setError(null)
    setSaving(true)
    try {
      const saved = await updateArticle(editing.id, editing.title, editing.content)
      setArticles((prev) => prev?.map((a) => (a.id === saved.id ? saved : a)) ?? null)
      setEditing(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <>
      <PageHeader title="Bands" subtitle="Featured bands from the GarageMind scene." />
      <div className="app-stack">
        {error && <Alert kind="error">{error}</Alert>}
        {articles?.length === 0 && !error && (
          <p className="app-card app-empty app-text">No bands yet.</p>
        )}
        <ul className="app-bands">
          {articles?.map((article) => (
            <li key={article.id} className="app-card app-band">
              {editing?.id === article.id ? (
                <form className="app-form app-form--fill" onSubmit={handleSave}>
                  <label className="app-field">
                    Name
                    <input
                      className="app-input"
                      name="title"
                      maxLength={200}
                      value={editing.title}
                      onChange={(e) => setEditing({ ...editing, title: e.target.value })}
                      required
                    />
                  </label>
                  <label className="app-field">
                    Description
                    <textarea
                      className="app-input"
                      name="content"
                      rows={6}
                      value={editing.content}
                      onChange={(e) => setEditing({ ...editing, content: e.target.value })}
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
                  <h2 className="app-card__title">{article.title}</h2>
                  <p className="app-text app-text--pre">{article.content}</p>
                  {canWrite && (
                    <button
                      type="button"
                      className="gm-btn gm-btn--sm gm-btn--secondary"
                      onClick={() => setEditing(article)}
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
