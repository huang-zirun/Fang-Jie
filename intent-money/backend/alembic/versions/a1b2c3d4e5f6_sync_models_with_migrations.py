"""sync models with migrations

Revision ID: a1b2c3d4e5f6
Revises: 6447982821b9
Create Date: 2026-06-04 12:00:00.000000

Fixes discrepancies between SQLAlchemy models and existing migrations:
- users: drop is_active, add is_anonymous and updated_at
- intents: add sort_order, fix description nullable, fix is_active server_default, add unique on name
- platforms: add created_at, add unique on name
- diagnosis_results: add FK on task_id
- user_events: add FK on user_id
- user_platform_accounts: add server_default for cookie_status and bind_status
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '6447982821b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- users table ---
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('is_active')
        batch_op.add_column(sa.Column('is_anonymous', sa.Boolean(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True))

    # --- intents table ---
    with op.batch_alter_table('intents', schema=None) as batch_op:
        batch_op.add_column(sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'))
        batch_op.alter_column('description', nullable=True)
        batch_op.alter_column('is_active', server_default='1')
        batch_op.create_unique_constraint('uq_intents_name', ['name'])

    # --- platforms table ---
    with op.batch_alter_table('platforms', schema=None) as batch_op:
        batch_op.add_column(sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))
        batch_op.create_unique_constraint('uq_platforms_name', ['name'])

    # --- diagnosis_results: add FK on task_id ---
    with op.batch_alter_table('diagnosis_results', schema=None) as batch_op:
        batch_op.create_foreign_key('fk_diagnosis_results_task_id', 'content_tasks', ['task_id'], ['id'], ondelete='CASCADE')

    # --- user_events: add FK on user_id ---
    with op.batch_alter_table('user_events', schema=None) as batch_op:
        batch_op.create_foreign_key('fk_user_events_user_id', 'users', ['user_id'], ['id'], ondelete='SET NULL')

    # --- user_platform_accounts: add server_defaults ---
    with op.batch_alter_table('user_platform_accounts', schema=None) as batch_op:
        batch_op.alter_column('cookie_status', server_default='pending')
        batch_op.alter_column('bind_status', server_default='unbound')


def downgrade() -> None:
    # --- user_platform_accounts ---
    with op.batch_alter_table('user_platform_accounts', schema=None) as batch_op:
        batch_op.alter_column('bind_status', server_default=None)
        batch_op.alter_column('cookie_status', server_default=None)

    # --- user_events ---
    with op.batch_alter_table('user_events', schema=None) as batch_op:
        batch_op.drop_constraint('fk_user_events_user_id', type_='foreignkey')

    # --- diagnosis_results ---
    with op.batch_alter_table('diagnosis_results', schema=None) as batch_op:
        batch_op.drop_constraint('fk_diagnosis_results_task_id', type_='foreignkey')

    # --- platforms table ---
    with op.batch_alter_table('platforms', schema=None) as batch_op:
        batch_op.drop_constraint('uq_platforms_name', type_='unique')
        batch_op.drop_column('created_at')

    # --- intents table ---
    with op.batch_alter_table('intents', schema=None) as batch_op:
        batch_op.drop_constraint('uq_intents_name', type_='unique')
        batch_op.alter_column('is_active', server_default=None)
        batch_op.alter_column('description', nullable=False)
        batch_op.drop_column('sort_order')

    # --- users table ---
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('updated_at')
        batch_op.drop_column('is_anonymous')
        batch_op.add_column(sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'))
