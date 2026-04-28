"""split names

Revision ID: 39b779c30137
Revises: 515a9705851d
Create Date: 2026-03-30 23:34:49.477501

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "39b779c30137"
down_revision: Union[str, Sequence[str], None] = "515a9705851d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add new columns
    op.add_column("user", sa.Column("first_name", sa.String(50), nullable=True))
    op.add_column("user", sa.Column("last_name", sa.String(50), nullable=True))

    # Split full_name into first_name and last_name
    op.execute("""
        UPDATE user
        SET first_name = SUBSTR(full_name, 1, INSTR(full_name, ' ') - 1),
            last_name  = SUBSTR(full_name, INSTR(full_name, ' ') + 1)
    """)

    # Drop the full_name column
    op.drop_column("user", "full_name")


def downgrade() -> None:
    """Downgrade schema."""
    # Add back the full_name column
    op.add_column("user", sa.Column("full_name", sa.String(100), nullable=True))

    # Combine first_name and last_name back into full_name
    op.execute("""
        UPDATE user
        SET full_name = first_name || ' ' || last_name
    """)

    # Drop the split columns
    op.drop_column("user", "first_name")
    op.drop_column("user", "last_name")
