"""rebrand articles to bands

Revision ID: f8a91c2b4d10
Revises: e476f2a73edd
Create Date: 2026-11-09 14:10:00.000000

"""

from collections.abc import Sequence

from alembic import op

revision: str = "f8a91c2b4d10"
down_revision: str | Sequence[str] | None = "e476f2a73edd"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.rename_table("articles", "bands")
    op.alter_column("bands", "title", new_column_name="name")
    op.alter_column("bands", "content", new_column_name="bio")
    op.execute("UPDATE permissions SET name = 'bands.read' WHERE name = 'articles.read'")
    op.execute("UPDATE permissions SET name = 'bands.write' WHERE name = 'articles.write'")


def downgrade() -> None:
    op.execute("UPDATE permissions SET name = 'articles.read' WHERE name = 'bands.read'")
    op.execute("UPDATE permissions SET name = 'articles.write' WHERE name = 'bands.write'")
    op.alter_column("bands", "bio", new_column_name="content")
    op.alter_column("bands", "name", new_column_name="title")
    op.rename_table("bands", "articles")
