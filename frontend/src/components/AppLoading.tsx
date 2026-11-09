type AppLoadingProps = {
  label?: string
  variant?: 'app' | 'landing'
}

export default function AppLoading({
  label = 'Loading…',
  variant = 'app',
}: AppLoadingProps) {
  return (
    <div className={`app-loading app-loading--${variant}`} role="status" aria-live="polite">
      <p className="app-loading__text">{label}</p>
    </div>
  )
}
