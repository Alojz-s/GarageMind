import { useLayoutEffect, type CSSProperties } from 'react'
import { Link } from 'react-router'
import { useAuth } from '../auth/AuthContext'
import { accountLinkPath } from '../auth/paths'
import Logo from '../components/Logo'
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

const BFTU_BLOCKS = [
  {
    title: 'YOUR BAND, YOUR SPACE',
    body: "Create your band's own space. Showcase your members, share your story, explore your discography and build your band's identity.",
  },
  {
    title: 'SHARE YOUR STORY',
    body: "Publish articles, announce new releases, share updates and let people know what's happening behind the scenes.",
  },
  {
    title: 'KEEP IT LIVE',
    body: 'Promote upcoming shows, share event details and keep your audience informed about where to find you next.',
  },
  {
    title: 'DISCOVER THE SCENE',
    body: 'Explore other underground bands, discover new sounds and become part of a community built around independent music.',
  },
] as const

const HOW_IT_WORKS_STEPS = [
  {
    number: '01',
    title: 'CREATE YOUR ACCOUNT',
    body: 'Join GarageMind and become part of the underground music community. All you need is an account to get started.',
  },
  {
    number: '02',
    title: 'CREATE OR JOIN A BAND',
    body: "Set up your band's profile or join an existing one. Bring your bandmates together in one place.",
  },
  {
    number: '03',
    title: 'MAKE SOME NOISE',
    body: "Share your band's story, publish articles, showcase releases and announce upcoming gigs.",
  },
  {
    number: '04',
    title: 'EXPLORE THE UNDERGROUND',
    body: 'Discover other bands, follow their activity and connect with the underground music scene.',
  },
] as const

function revealDelay(index: number, stepMs = 90): CSSProperties {
  return { '--gm-reveal-delay': `${index * stepMs}ms` } as CSSProperties
}

export default function HomePage() {
  const { user } = useAuth()
  const accountPath = accountLinkPath(user)

  useLayoutEffect(() => {
    const root = document.querySelector('.garagemind-landing')
    if (!root) {
      return undefined
    }

    const nodes = root.querySelectorAll('.gm-reveal')
    const motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
    if (
      nodes.length === 0 ||
      motionQuery.matches ||
      typeof IntersectionObserver === 'undefined'
    ) {
      return undefined
    }

    root.classList.add('garagemind-landing--js')

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) {
            return
          }
          entry.target.classList.add('gm-reveal--visible')
          observer.unobserve(entry.target)
        })
      },
      { root: null, rootMargin: '0px 0px -6% 0px', threshold: 0.08 },
    )

    nodes.forEach((node) => observer.observe(node))

    return () => {
      observer.disconnect()
      root.classList.remove('garagemind-landing--js')
    }
  }, [])

  return (
    <div className="garagemind-landing">
      <section className="garagemind-hero" aria-labelledby="hero-heading">
        <div className="garagemind-section-bg garagemind-hero__bg" aria-hidden>
          <img src="/garagemind/Sekcja1.png" alt="" />
        </div>
        <div className="garagemind-container garagemind-hero__shell">
          <header className="garagemind-header garagemind-hero__enter garagemind-hero__enter--header">
            <Logo variant="full" to="/" />
            <nav aria-label="Main">
              <ul className="garagemind-nav">
                <li>
                  <Link to={accountPath}>SIGN IN</Link>
                </li>
              </ul>
            </nav>
          </header>
          <div className="garagemind-hero__body">
            <h1 id="hero-heading" className="garagemind-hero__title garagemind-hero__enter">
              OUT OF THE GARAGE
            </h1>
            <p className="garagemind-hero__tagline garagemind-hero__enter garagemind-hero__enter--tagline">
              Discover underground bands. Share your sound. Find your scene.
            </p>
            <Link
              to={accountPath}
              className="gm-btn garagemind-cta garagemind-hero__enter garagemind-hero__enter--cta"
            >
              JOIN NOW
            </Link>
          </div>
        </div>
      </section>

      <section className="garagemind-bftu" aria-labelledby="bftu-heading">
        <div className="garagemind-container garagemind-bftu__inner">
          <h2 id="bftu-heading" className="garagemind-bftu__title gm-reveal">
            <span className="garagemind-featured__heading-accent">Built for the Underground</span>
          </h2>
          <ul className="garagemind-bftu__columns">
            {BFTU_BLOCKS.map((block, index) => (
              <li
                key={block.title}
                className="garagemind-bftu__column gm-reveal"
                style={revealDelay(index, 100)}
              >
                <h3 className="garagemind-bftu__column-title">{block.title}</h3>
                <p className="garagemind-bftu__column-body">{block.body}</p>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="garagemind-featured" aria-labelledby="featured-heading">
        <div className="garagemind-section-bg garagemind-featured__bg" aria-hidden>
          <img src="/garagemind/Sekcja2.png" alt="" />
        </div>
        <div className="garagemind-container garagemind-featured__inner">
          <h2 id="featured-heading" className="garagemind-featured__heading gm-reveal">
            Featured{' '}
            <span className="garagemind-featured__heading-accent">Bands</span>
          </h2>
          <p className="garagemind-featured__note gm-reveal" style={revealDelay(1, 80)}>
            A taste of the scene. Sign in to browse the full band directory.
          </p>
          <ul className="garagemind-bands">
            {BANDS.map((band, index) => (
              <li
                key={band.name}
                className="garagemind-band-card gm-reveal"
                style={revealDelay(index, 110)}
              >
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

      <section className="garagemind-how-it-works" aria-labelledby="how-it-works-heading">
        <div className="garagemind-container garagemind-how-it-works__inner">
          <h2 id="how-it-works-heading" className="garagemind-how-it-works__heading gm-reveal">
            GET STARTED. GET LOUD.
          </h2>
          <p className="garagemind-how-it-works__subheading gm-reveal" style={revealDelay(1, 80)}>
            Getting your band out of the garage has never been easier.
          </p>
          <ol className="garagemind-timeline">
            {HOW_IT_WORKS_STEPS.map((step, index) => (
              <li
                key={step.number}
                className="garagemind-timeline__step gm-reveal"
                style={revealDelay(index, 100)}
              >
                <span className="garagemind-timeline__number" aria-hidden>
                  {step.number}
                </span>
                <h3 className="garagemind-timeline__title">{step.title}</h3>
                <p className="garagemind-timeline__body">{step.body}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section className="garagemind-closing" aria-labelledby="closing-heading">
        <div className="garagemind-container garagemind-closing__inner">
          <h2 id="closing-heading" className="garagemind-closing__title gm-reveal">
            Ready to get <span className="garagemind-featured__heading-accent">loud</span>?
          </h2>
          <div className="gm-reveal" style={revealDelay(1, 100)}>
            <Link to={accountPath} className="gm-btn garagemind-cta">
              JOIN NOW
            </Link>
          </div>
        </div>
      </section>

      <footer className="garagemind-footer">
        <div className="garagemind-container">
          <p className="garagemind-footer__text gm-reveal">© 2026 GarageMind® All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}
