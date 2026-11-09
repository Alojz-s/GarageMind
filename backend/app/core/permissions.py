BANDS_READ = "bands.read"
BANDS_WRITE = "bands.write"
USERS_MANAGE = "users.manage"
SETTINGS_MANAGE = "settings.manage"

ROLE_PERMISSION_MATRIX: dict[str, list[str]] = {
    "Administrator": [BANDS_READ, USERS_MANAGE, SETTINGS_MANAGE],
    "Audytor": [BANDS_READ],
    "Redaktor": [BANDS_READ, BANDS_WRITE],
    "Czytelnik": [BANDS_READ],
}
