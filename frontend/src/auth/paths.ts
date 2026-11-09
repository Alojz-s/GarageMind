import type { Me } from '../api/auth'

/** Default in-app destination after authentication (not the marketing landing). */
export function postAuthPath(user: Me): string {
  return user.must_change_password ? '/change-password' : '/bands'
}

/** ACC / JOIN NOW: sign-in for guests, app entry when logged in. */
export function accountLinkPath(user: Me | null): string {
  return user ? postAuthPath(user) : '/login'
}

/** BANDS nav: protected list for members; guests go to sign-in. */
export function bandsLinkPath(user: Me | null): string {
  return user ? postAuthPath(user) : '/login'
}
