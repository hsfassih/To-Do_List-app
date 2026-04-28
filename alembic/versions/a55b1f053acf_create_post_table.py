"""create post table

Revision ID: a55b1f053acf
Revises: 39b779c30137
Create Date: 2026-03-31 00:09:34.627496

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "a55b1f053acf"
down_revision: Union[str, Sequence[str], None] = "39b779c30137"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass
    op.create_table(
        "post",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("user.id"), nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("post")
