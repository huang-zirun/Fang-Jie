"""add extracted_structures table

Revision ID: d4e5f6a7b8c9
Revises: b2c3d4e5f6a7
Create Date: 2026-05-22 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'extracted_structures',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('source_url', sa.String(length=500), nullable=False),
        sa.Column('platform_id', sa.Uuid(), nullable=False),
        sa.Column('hook_type', sa.String(length=50), nullable=False),
        sa.Column('emotion_structure', sa.JSON(), nullable=False),
        sa.Column('conversion_structure', sa.JSON(), nullable=False),
        sa.Column('key_elements', sa.JSON(), nullable=False),
        sa.Column('viral_score', sa.Integer(), nullable=False),
        sa.Column('analysis_summary', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['platform_id'], ['platforms.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('extracted_structures', schema=None) as batch_op:
        batch_op.create_index('ix_extracted_structures_platform_id', ['platform_id'])


def downgrade() -> None:
    op.drop_table('extracted_structures')
