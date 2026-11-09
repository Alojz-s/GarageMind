"""rename bands db object names

Revision ID: a2c8e19d4f01
Revises: f8a91c2b4d10
Create Date: 2026-11-09 15:30:00.000000

"""

from collections.abc import Sequence

from alembic import op

revision: str = "a2c8e19d4f01"
down_revision: str | Sequence[str] | None = "f8a91c2b4d10"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE bands RENAME CONSTRAINT pk_articles TO pk_bands")
    op.execute("ALTER SEQUENCE articles_id_seq RENAME TO bands_id_seq")


def downgrade() -> None:
    op.execute("ALTER SEQUENCE bands_id_seq RENAME TO articles_id_seq")
    op.execute("ALTER TABLE bands RENAME CONSTRAINT pk_bands TO pk_articles")
