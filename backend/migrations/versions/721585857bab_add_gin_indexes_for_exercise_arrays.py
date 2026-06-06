"""add gin indexes for exercise arrays

Revision ID: 721585857bab
Revises: 3038bc135a2d
Create Date: 2026-06-04 23:12:29.490501

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '721585857bab'
down_revision: Union[str, None] = '3038bc135a2d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE INDEX IF NOT EXISTS ix_exercises_muscle_groups_gin ON exercises USING GIN (muscle_groups)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_exercises_equipment_required_gin ON exercises USING GIN (equipment_required)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_exercises_muscle_groups_gin")
    op.execute("DROP INDEX IF EXISTS ix_exercises_equipment_required_gin")
