export type ComponentStatus = 'ok' | 'error'

export interface HealthResponse {
  status: ComponentStatus
  database: ComponentStatus
}

export async function fetchHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const response = await fetch('/api/health', { signal })

  // Odpowiedź 503 też zawiera JSON z informacją, który składnik zawiódł.
  if (!response.ok && response.status !== 503) {
    throw new Error(`HTTP ${response.status}`)
  }
  return (await response.json()) as HealthResponse
}
