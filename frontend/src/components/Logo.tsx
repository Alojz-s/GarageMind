import { Link } from 'react-router'

type LogoVariant = 'full' | 'mark'

interface LogoProps {
  variant: LogoVariant
  to?: string
  className?: string
}

export default function Logo({ variant, to, className = '' }: LogoProps) {
  const classNames =
    variant === 'full'
      ? `garagemind-logo${className ? ` ${className}` : ''}`
      : `app__logo${className ? ` ${className}` : ''}`

  const label = 'GarageMind'
  const body =
    variant === 'full' ? (
      <>
        Garage<span className="app__logo-accent">M</span>ind
      </>
    ) : (
      <>
        G<span className="app__logo-accent">M</span>
      </>
    )

  if (to === undefined) {
    return (
      <span className={classNames} aria-label={label}>
        {body}
      </span>
    )
  }

  return (
    <Link to={to} className={classNames} aria-label={label}>
      {body}
    </Link>
  )
}
