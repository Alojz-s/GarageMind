import { Link } from 'react-router'
import PageHeader from '../components/PageHeader'

export default function NotFoundPage() {
  return (
    <>
      <PageHeader title="Page not found" subtitle="Error 404" />
      <div className="app-stack app-stack--narrow">
        <section className="app-card app-stack">
          <p className="app-text">The page you are looking for does not exist.</p>
          <Link to="/articles" className="gm-btn gm-btn--secondary gm-btn--sm">
            Back to bands
          </Link>
        </section>
      </div>
    </>
  )
}
