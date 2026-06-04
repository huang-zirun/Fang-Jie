"""add_user_platform_accounts_table

Revision ID: 6447982821b9
Revises: 000000000000
Create Date: 2026-06-01 11:30:04.410512

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '6447982821b9'
down_revision: Union[str, None] = '000000000000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('user_platform_accounts',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('platform', sa.String(length=20), nullable=False),
    sa.Column('platform_user_id', sa.String(length=100), nullable=True),
    sa.Column('platform_nickname', sa.String(length=100), nullable=True),
    sa.Column('platform_avatar', sa.String(length=500), nullable=True),
    sa.Column('encrypted_cookie', sa.Text(), nullable=True),
    sa.Column('cookie_iv', sa.String(length=64), nullable=True),
    sa.Column('cookie_status', sa.String(length=20), nullable=False),
    sa.Column('cookie_set_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('cookie_expires_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('last_validated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('bind_status', sa.String(length=20), nullable=False),
    sa.Column('bind_method', sa.String(length=20), nullable=True),
    sa.Column('login_session_id', sa.String(length=100), nullable=True),
    sa.Column('qr_code_url', sa.String(length=500), nullable=True),
    sa.Column('login_expires_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('login_session_id'),
    sa.UniqueConstraint('user_id', 'platform', name='uq_user_platform')
    )
    with op.batch_alter_table('user_platform_accounts', schema=None) as batch_op:
        batch_op.create_index('ix_platform_cookie_status', ['platform', 'cookie_status'], unique=False)
        batch_op.create_index(batch_op.f('ix_user_platform_accounts_user_id'), ['user_id'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('user_platform_accounts', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_user_platform_accounts_user_id'))
        batch_op.drop_index('ix_platform_cookie_status')

    op.drop_table('user_platform_accounts')
