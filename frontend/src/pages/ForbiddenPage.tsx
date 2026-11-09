import { Link } from 'react-router'
import PageHeader from '../components/PageHeader'

export default function ForbiddenPage() {
  return (
    <>
      <PageHeader title="Access denied" subtitle="Error 403" />
      <div className="app-stack app-stack--narrow">
        <section className="app-card app-stack">
          <p className="app-text">You do not have permission to view this page.</p>
          <Link to="/articles" className="gm-btn gm-btn--secondary gm-btn--sm">
            Back to bands
          </Link>
        </section>
      </div>
    </>
  )
}
