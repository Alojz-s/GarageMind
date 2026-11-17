"""login failures (per-IP limit)

Revision ID: d3b7a1c9e5f2
Revises: cb0dcfee4a5f
Create Date: 2026-11-17 16:40:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d3b7a1c9e5f2"
down_revision: str | Sequence[str] | None = "cb0dcfee4a5f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "login_failures",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ip", sa.String(length=45), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_login_failures")),
    )
    op.create_index("ix_login_failures_ip_created_at", "login_failures", ["ip", "created_at"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_login_failures_ip_created_at", table_name="login_failures")
    op.drop_table("login_failures")
