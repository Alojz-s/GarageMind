interface PageHeaderProps {
  title: string
  subtitle?: string
}

export default function PageHeader({ title, subtitle }: PageHeaderProps) {
  return (
    <header className="app-page-head">
      <h1 className="app-page-title">{title}</h1>
      {subtitle && <p className="app-page-subtitle">{subtitle}</p>}
    </header>
  )
}
