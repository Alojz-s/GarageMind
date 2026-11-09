import type { ReactNode } from 'react'

interface AlertProps {
  kind?: 'error' | 'info'
  children: ReactNode
}

export default function Alert({ kind = 'info', children }: AlertProps) {
  return (
    <p className={`app-alert app-alert--${kind}`} role={kind === 'error' ? 'alert' : 'status'}>
      {children}
    </p>
  )
}
