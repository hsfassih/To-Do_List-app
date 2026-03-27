"""add new column to users table

Revision ID: 7546ccbd2878
Revises: 
Create Date: 2026-03-27 22:22:19.600076

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7546ccbd2878'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        'user', # The name of the table
        sa.Column('new_column_name', sa.String(50), nullable=True) # The new column definition
    )

def downgrade():
    op.drop_column('user', 'new_column_name')
