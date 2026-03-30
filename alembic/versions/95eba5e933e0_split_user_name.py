"""add bio to user

Revision ID: 95eba5e933e0
Revises: 
Create Date: 2026-03-30 19:36:49.507249

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '95eba5e933e0'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1. Schema change: Add the new columns
    op.add_column('user', sa.Column('first_name', sa.String(50), nullable=True))
    op.add_column('user', sa.Column('last_name', sa.String(50), nullable=True))

    # 2. Data change: Use op.execute to run raw SQL that splits the string
    # (Example syntax varies by database dialect, this is roughly PostgreSQL)
    op.execute("""
    UPDATE user
    SET first_name = SUBSTR(full_name, 1, INSTR(full_name, ' ') - 1),
        last_name  = SUBSTR(full_name, INSTR(full_name, ' ') + 1)
    """)
    # 3. Schema change: Safely drop the old column now that data is moved
    op.drop_column('user', 'full_name')

def downgrade():
    # You must write the exact reverse logic here!
    op.add_column('user', sa.Column('full_name', sa.String(100), nullable=True))
    op.execute("UPDATE user SET full_name = first_name || ' ' || last_name")
    op.drop_column('user', 'first_name')
    op.drop_column('user', 'last_name')