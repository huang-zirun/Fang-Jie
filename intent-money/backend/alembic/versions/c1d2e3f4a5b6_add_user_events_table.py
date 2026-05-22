"""add user_events table

Revision ID: c1d2e3f4a5b6
Revises: b2c3d4e5f6a7
Create Date: 2026-05-22 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c1d2e3f4a5b6'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'user_events',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=True),
        sa.Column('session_id', sa.String(length=100), nullable=True),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('page', sa.String(length=100), nullable=True),
        sa.Column('duration', sa.Float(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('user_events', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_user_events_user_id'), ['user_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_user_events_session_id'), ['session_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_user_events_event_type'), ['event_type'], unique=False)


def downgrade() -> None:
    op.drop_table('user_events')
