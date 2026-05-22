"""add comment_sentiment to market_hots

Revision ID: d5e6f7a8b9c0
Revises: 248b8ff4b8f4
Create Date: 2026-05-22 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd5e6f7a8b9c0'
down_revision: Union[str, None] = '248b8ff4b8f4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('market_hots', schema=None) as batch_op:
        batch_op.add_column(sa.Column('comment_sentiment', sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('market_hots', schema=None) as batch_op:
        batch_op.drop_column('comment_sentiment')
