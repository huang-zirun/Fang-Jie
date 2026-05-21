"""add market_score to content_structures

Revision ID: 248b8ff4b8f4
Revises: 
Create Date: 2026-05-21 15:57:27.643885

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '248b8ff4b8f4'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('content_structures', schema=None) as batch_op:
        batch_op.add_column(sa.Column('market_score', sa.Float(), nullable=False, server_default='0.0'))


def downgrade() -> None:
    with op.batch_alter_table('content_structures', schema=None) as batch_op:
        batch_op.drop_column('market_score')
