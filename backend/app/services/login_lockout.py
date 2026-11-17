"""Czasowa blokada konta po serii błędnych logowań (osobna od ręcznej blokady is_blocked)."""

import math
from datetime import UTC, datetime, timedelta

from app.models import User

LOCKOUT_MINUTES = 15


def locked_seconds(user: User, now: datetime | None = None) -> int:
    """Pozostałe sekundy blokady (0, gdy konto nie jest zablokowane lub blokada wygasła)."""
    if user.locked_until is None:
        return 0
    now = now or datetime.now(UTC)
    remaining = (user.locked_until - now).total_seconds()
    return max(0, math.ceil(remaining))


def register_failed_login(user: User, max_failed_logins: int, now: datetime | None = None) -> None:
    """Zlicza błąd; po osiągnięciu progu zakłada blokadę i zeruje licznik."""
    now = now or datetime.now(UTC)
    user.failed_login_count += 1
    if user.failed_login_count >= max_failed_logins:
        user.locked_until = now + timedelta(minutes=LOCKOUT_MINUTES)
        user.failed_login_count = 0


def reset_lockout(user: User) -> None:
    user.failed_login_count = 0
    user.locked_until = None
