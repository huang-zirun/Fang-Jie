"""add conversion_paths table

Revision ID: a1b2c3d4e5f6
Revises: 248b8ff4b8f4
Create Date: 2026-05-21 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '248b8ff4b8f4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('conversion_paths', schema=None) as batch_op:
        pass

    op.create_table(
        'conversion_paths',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('intent_id', sa.Uuid(), nullable=False),
        sa.Column('stage', sa.String(length=30), nullable=False),
        sa.Column('title', sa.String(length=100), nullable=False),
        sa.Column('scripts', sa.JSON(), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['intent_id'], ['intents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('conversion_paths', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_conversion_paths_intent_id'), ['intent_id'], unique=False)


def downgrade() -> None:
    op.drop_table('conversion_paths')
