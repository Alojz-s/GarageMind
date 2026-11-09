import type { Me } from '../api/auth'

export function postAuthPath(user: Me): string {
  return user.must_change_password ? '/change-password' : '/bands'
}

export function accountLinkPath(user: Me | null): string {
  return user ? postAuthPath(user) : '/login'
}

export function bandsLinkPath(user: Me | null): string {
  return user ? postAuthPath(user) : '/login'
}
