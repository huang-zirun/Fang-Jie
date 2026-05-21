"""add market_hots table

Revision ID: a1b2c3d4e5f6
Revises: 248b8ff4b8f4
Create Date: 2026-05-21 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '248b8ff4b8f4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'market_hots',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('platform_id', sa.Uuid(), nullable=False),
        sa.Column('keyword', sa.String(length=100), nullable=False),
        sa.Column('hot_type', sa.String(length=30), nullable=False),
        sa.Column('analysis_result', sa.JSON(), nullable=True),
        sa.Column('recommended_structures', sa.JSON(), nullable=True),
        sa.Column('priority_boost', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['platform_id'], ['platforms.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('market_hots', schema=None) as batch_op:
        batch_op.create_index('ix_market_hots_platform_id', ['platform_id'])


def downgrade() -> None:
    op.drop_table('market_hots')
