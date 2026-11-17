"""Per-IP failed login limit (password spraying mitigation), independent of the login used."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import LoginFailure


def _cutoff(window_minutes: int) -> datetime:
    return datetime.now(UTC) - timedelta(minutes=window_minutes)


def prune_old_failures(db: Session, window_minutes: int) -> None:
    """Deletes all rows (any IP) older than the sliding window."""
    db.execute(delete(LoginFailure).where(LoginFailure.created_at < _cutoff(window_minutes)))


def count_failures_in_window(db: Session, ip: str, window_minutes: int) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(LoginFailure)
            .where(LoginFailure.ip == ip, LoginFailure.created_at >= _cutoff(window_minutes))
        )
        or 0
    )


def record_login_failure(db: Session, ip: str | None, window_minutes: int) -> None:
    """Prunes expired rows and stores one failure. Unknown IP (None) is not recorded."""
    prune_old_failures(db, window_minutes)
    if ip is not None:
        db.add(LoginFailure(ip=ip))
    db.flush()


def is_ip_rate_limited(db: Session, settings: Settings, ip: str | None) -> bool:
    """True when the IP reached the limit. Unknown IP (None) is never limited."""
    if ip is None:
        return False
    prune_old_failures(db, settings.ip_login_window_minutes)
    return (
        count_failures_in_window(db, ip, settings.ip_login_window_minutes)
        >= settings.ip_login_max_failures
    )
