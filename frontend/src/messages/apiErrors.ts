import { ApiError, type Violation } from '../api/client'

const API_ERROR_BY_CODE: Record<string, string> = {
  not_authenticated: 'Not authenticated',
  session_expired: 'Session expired due to inactivity',
  forbidden: 'You do not have permission for this action',
  password_change_required: 'Password change required',
  password_mismatch: 'New password confirmation does not match',
  invalid_old_password: 'Current password is incorrect',
  invalid_role: 'Unknown role',
  user_not_found: 'User not found',
  login_taken: 'Username is already taken',
  band_not_found: 'Band not found',
}

const VIOLATION_BY_CODE: Record<string, string> = {
  too_short: 'Password is too short.',
  too_long: 'Password is too long.',
  common_password: 'Password is too common (banned list).',
  is_date: 'Password cannot be a date.',
  contains_year: 'Password cannot contain a year between 1950 and 2030.',
  reused_password: 'Password must differ from your recent passwords.',
  invalid_min_password_length: 'Minimum password length is out of range.',
  invalid_password_validity_days: 'Password validity (days) is out of range.',
  invalid_idle_timeout: 'Session idle timeout is out of range.',
}

const ROLE_LABELS: Record<string, string> = {
  Administrator: 'Administrator',
  Audytor: 'Auditor',
  Redaktor: 'Editor',
  Czytelnik: 'Reader',
}

export function formatRoleLabel(role: string): string {
  return ROLE_LABELS[role] ?? role
}

export function formatViolation(violation: Violation): string {
  return VIOLATION_BY_CODE[violation.code] ?? violation.message
}

export function formatApiError(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 401 && !error.code) {
      return 'Incorrect username or password'
    }
    if (error.code && API_ERROR_BY_CODE[error.code]) {
      return API_ERROR_BY_CODE[error.code]
    }
    return error.message
  }
  return error instanceof Error ? error.message : String(error)
}
