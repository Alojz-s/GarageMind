from datetime import datetime

from sqlalchemy import Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class LoginFailure(Base):
    """One failed login attempt from an IP address (sliding-window limit, M2-D)."""

    __tablename__ = "login_failures"
    __table_args__ = (Index("ix_login_failures_ip_created_at", "ip", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    ip: Mapped[str] = mapped_column(String(45))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
