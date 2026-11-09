import { Link } from 'react-router'
import { useAuth } from '../auth/AuthContext'
import '../styles/garagemind.css'

const BANDS = [
  {
    name: 'Voidbringer',
    description:
      'Atmospheric black metal from the Pacific Northwest with crushing live sets and DIY merch.',
  },
  {
    name: 'Ironclad',
    description:
      'Technical death metal with a raw, basement-show energy and a growing run of underground releases.',
  },
  {
    name: 'Casketborn',
    description:
      'Heavy doom with crushing riffs and a live presence built for small rooms and loud crowds.',
  },
] as const

export default function HomePage() {
  const { user } = useAuth()
  const accountPath = user ? '/articles' : '/login'

  return (
    <div className="garagemind-landing">
      <section className="garagemind-hero" aria-labelledby="hero-heading">
        <div className="garagemind-section-bg garagemind-hero__bg" aria-hidden>
          <img src="/garagemind/Sekcja1.png" alt="" />
        </div>
        <div className="garagemind-container garagemind-hero__shell">
          <header className="garagemind-header">
            <Link to="/" className="garagemind-logo">
              GarageMind
            </Link>
            <nav aria-label="Main">
              <ul className="garagemind-nav">
                <li>
                  <Link to="/articles">BANDS</Link>
                </li>
                <li>
                  <Link to={accountPath}>ACC</Link>
                </li>
              </ul>
            </nav>
          </header>
          <div className="garagemind-hero__body">
            <h1 id="hero-heading" className="garagemind-hero__title">
              OUT OF THE GARAGE
            </h1>
            <Link to={accountPath} className="gm-btn garagemind-cta">
              JOIN NOW
            </Link>
          </div>
        </div>
      </section>

      <section className="garagemind-featured" aria-labelledby="featured-heading">
        <div className="garagemind-section-bg garagemind-featured__bg" aria-hidden>
          <img src="/garagemind/Sekcja2.png" alt="" />
        </div>
        <div className="garagemind-container garagemind-featured__inner">
          <h2 id="featured-heading" className="garagemind-featured__heading">
            Featured{' '}
            <span className="garagemind-featured__heading-accent">Bands</span>
          </h2>
          <ul className="garagemind-bands">
            {BANDS.map((band) => (
              <li key={band.name} className="garagemind-band-card">
                <img
                  className="garagemind-band-card__image"
                  src="/garagemind/BandPlaceholder.png"
                  alt=""
                />
                <h3 className="garagemind-band-card__name">{band.name}</h3>
                <p className="garagemind-band-card__description">{band.description}</p>
              </li>
            ))}
          </ul>
        </div>
      </section>
    </div>
  )
}
