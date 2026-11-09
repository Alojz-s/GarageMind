import { apiRequest } from './client'

export interface Band {
  id: number
  name: string
  bio: string
}

export function fetchBands(): Promise<Band[]> {
  return apiRequest<Band[]>('GET', '/bands')
}

export function createBand(name: string, bio: string): Promise<Band> {
  return apiRequest<Band>('POST', '/bands', { name, bio })
}

export function updateBand(id: number, name: string, bio: string): Promise<Band> {
  return apiRequest<Band>('PUT', `/bands/${id}`, { name, bio })
}
