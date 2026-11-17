export interface Violation {
  code: string
  message: string
}

export class ApiError extends Error {
  readonly status: number
  readonly code?: string
  readonly violations: Violation[]
  readonly lockedSeconds?: number

  constructor(
    status: number,
    message: string,
    code?: string,
    violations: Violation[] = [],
    lockedSeconds?: number,
  ) {
    super(message)
    this.status = status
    this.code = code
    this.violations = violations
    this.lockedSeconds = lockedSeconds
  }
}

type UnauthorizedHandler = (code?: string) => void

let onUnauthorized: UnauthorizedHandler = () => {}

export function setUnauthorizedHandler(handler: UnauthorizedHandler): void {
  onUnauthorized = handler
}

export async function apiRequest<T>(
  method: string,
  path: string,
  body?: unknown,
  credentials: RequestCredentials = 'include',
): Promise<T> {
  const response = await fetch(`/api${path}`, {
    method,
    credentials,
    headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  })

  if (response.ok) {
    return (response.status === 204 ? undefined : await response.json()) as T
  }

  const error = (await response.json().catch(() => null)) as {
    detail?: unknown
    code?: string
    violations?: Violation[]
    locked_seconds?: number
  } | null
  if (response.status === 401) onUnauthorized(error?.code)
  const message =
    typeof error?.detail === 'string' ? error.detail : `Server error (HTTP ${response.status})`
  throw new ApiError(response.status, message, error?.code, error?.violations, error?.locked_seconds)
}
