"""merge multiple heads

Revision ID: f1g2h3i4j5k6
Revises: a1b2c3d4e5f6, a1b2c3d4e5f7
Create Date: 2026-05-28 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f1g2h3i4j5k6'
down_revision: Union[str, Sequence[str], None] = ('a1b2c3d4e5f6', 'a1b2c3d4e5f7')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
