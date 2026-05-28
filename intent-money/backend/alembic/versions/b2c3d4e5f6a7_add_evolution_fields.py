"""add evolution fields to diagnosis_results and optimization_rules

Revision ID: b2c3d4e5f6a7
Revises: f1g2h3i4j5k6
Create Date: 2026-05-21 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'f1g2h3i4j5k6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('diagnosis_results', schema=None) as batch_op:
        batch_op.add_column(sa.Column('ai_analysis', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('rule_confidence', sa.Float(), nullable=True))

    with op.batch_alter_table('optimization_rules', schema=None) as batch_op:
        batch_op.add_column(sa.Column('hit_count', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('accuracy_count', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    with op.batch_alter_table('optimization_rules', schema=None) as batch_op:
        batch_op.drop_column('accuracy_count')
        batch_op.drop_column('hit_count')

    with op.batch_alter_table('diagnosis_results', schema=None) as batch_op:
        batch_op.drop_column('rule_confidence')
        batch_op.drop_column('ai_analysis')
