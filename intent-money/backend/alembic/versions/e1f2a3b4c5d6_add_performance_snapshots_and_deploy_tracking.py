"""add performance snapshots and deploy tracking

Revision ID: e1f2a3b4c5d6
Revises: 248b8ff4b8f4
Create Date: 2026-05-27 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e1f2a3b4c5d6'
down_revision: Union[str, None] = '248b8ff4b8f4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'performance_snapshots',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('task_id', sa.Uuid(), nullable=False),
        sa.Column('play_count', sa.Integer(), nullable=False),
        sa.Column('comment_count', sa.Integer(), nullable=False),
        sa.Column('message_count', sa.Integer(), nullable=False),
        sa.Column('source', sa.String(20), nullable=False, server_default='manual'),
        sa.Column('snapshot_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['task_id'], ['content_tasks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('performance_snapshots', schema=None) as batch_op:
        batch_op.create_index('ix_performance_snapshots_task_id', ['task_id'])

    with op.batch_alter_table('content_tasks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('deployed_at', sa.DateTime(timezone=True), nullable=True))

    with op.batch_alter_table('diagnosis_results', schema=None) as batch_op:
        batch_op.add_column(sa.Column('snapshot_count', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('days_since_deploy', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('play_trend', sa.String(20), nullable=True))
        batch_op.add_column(sa.Column('avg_daily_play_growth', sa.Float(), nullable=False, server_default='0.0'))


def downgrade() -> None:
    with op.batch_alter_table('diagnosis_results', schema=None) as batch_op:
        batch_op.drop_column('avg_daily_play_growth')
        batch_op.drop_column('play_trend')
        batch_op.drop_column('days_since_deploy')
        batch_op.drop_column('snapshot_count')

    with op.batch_alter_table('content_tasks', schema=None) as batch_op:
        batch_op.drop_column('deployed_at')

    with op.batch_alter_table('performance_snapshots', schema=None) as batch_op:
        batch_op.drop_index('ix_performance_snapshots_task_id')

    op.drop_table('performance_snapshots')
